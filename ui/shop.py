import re
from urllib.parse import urljoin, urlsplit

from core.diagnostics import CheckFailed
from ui.base import BasePage, money


def exact(text):
    return re.compile(r'^\s*' + r'\s+'.join(re.escape(word) for word in text.split()) + r'\s*$')


def quantity_text(text):
    match = re.fullmatch(r'\s*(\d+)(?:[.,]0+)?\s*(?:шт\.?|ед\.?|[x×])?\s*', text, re.IGNORECASE)
    if match is None:
        raise CheckFailed('Количество должно быть целым числом, возможно с обозначением единицы товара.')
    return int(match[1])


class CatalogPage(BasePage):
    def open_search_result(self, product):
        self.open('catalog')
        search = self.element('search')
        search.fill(product.query)
        search.press('Enter')
        matches = self.element('search_result').locator.filter(has_text=exact(product.name))
        result = self.from_locator(matches, 'search_result: точное название товара')
        result.visible()
        href = result.attribute('href')
        if not href or not self.is_same_site(urljoin(self.page.url, href)):
            raise CheckFailed('Найденная ссылка на товар не ведёт на настроенный сайт.')
        result.click()


class ProductPage(BasePage):
    def verify(self, product):
        self.element('product_title').contains(exact(product.name))
        if product.article:
            self.element('product_article').contains(re.compile(r'(?<!\w)' + re.escape(product.article) + r'(?!\w)'))
        if product.product_id and self.element('product_add').attribute('data-product-id') != product.product_id:
            raise CheckFailed('ID кнопки добавления отличается от ID товара в local.json.')
        self.element('product_unit').contains(re.compile(re.escape(product.unit), re.IGNORECASE))
        if product.variant:
            self.element('product_variant').contains(exact(product.variant))
        if money(self.element('product_price').text(), 'product_price') != product.price:
            raise CheckFailed('Цена в карточке отличается от цены товара в local.json.')
        self.element('product_add').enabled()

    def add_one(self):
        self.element('product_add').click()
        self.element('product_added').visible()


class CartPage(BasePage):
    def wait_ready(self):
        empty = self.element('cart_empty').locator
        rows = self.element('cart_row').locator
        self.from_locator(empty.or_(rows).first, 'cart_empty или cart_row').visible()

    def is_empty(self):
        self.wait_ready()
        return self.element('cart_row').locator.count() == 0 and self.element('cart_empty').locator.count() > 0

    def row_for(self, name, product_url):
        links = self.element('cart_product_link').locator.filter(has_text=exact(name))
        rows = self.element('cart_row').locator.filter(has=links)
        row = self.from_locator(rows, 'cart_row: строка выбранного товара')
        if rows.count() != 1:
            raise CheckFailed('В корзине должна быть ровно одна строка выбранного товара.')
        row_links = self.element('cart_product_link', row).locator.filter(has_text=exact(name))
        href = self.from_locator(row_links, 'cart_product_link').attribute('href')
        actual = urljoin(self.page.url, href or '')
        if not self.is_same_site(actual) or urlsplit(actual).path.rstrip('/') != urlsplit(product_url).path.rstrip('/'):
            raise CheckFailed('Ссылка в строке корзины ведёт на другой товар.')
        return row

    def verify(self, product, product_url):
        self.wait_ready()
        if self.element('cart_row').locator.count() != 1:
            raise CheckFailed('После добавления в пустой корзине ожидается одна позиция.')
        row = self.row_for(product.name, product_url)
        quantity = self.element('cart_quantity', row)
        quantity.match_value(re.compile(r'^1(?:[.,]0+)?$'))
        if product.variant:
            self.element('cart_variant', row).contains(exact(product.variant))
        price = money(self.element('cart_unit_price', row).text(), 'cart_unit_price')
        line = money(self.element('cart_line_total', row).text(), 'cart_line_total')
        total = money(self.element('cart_total').text(), 'cart_total')
        if price != product.price or line != price or total != line:
            raise CheckFailed('Цена за единицу, сумма строки и итог корзины не совпадают с ожидаемой ценой товара.')

    def go_to_checkout(self):
        if self.current_path() != urlsplit(self.settings.paths['cart']).path.rstrip('/'):
            raise CheckFailed('Переход к оформлению должен начинаться со страницы корзины.')
        link = self.element('checkout_link')
        href = link.attribute('href')
        if href and not self.is_same_site(urljoin(self.page.url, href)):
            raise CheckFailed('Ссылка оформления ведёт за пределы магазина.')
        link.click()

    def remove_test_product(self, product, product_url):
        self.open('cart')
        if self.is_empty():
            return
        row = self.row_for(product.name, product_url)
        # При изменении корзины другим сеансом не удаляем строку с изменившимся количеством.
        if quantity_text(self.element('cart_quantity', row).value()) != 1:
            raise CheckFailed('Количество тестовой строки изменилось. Проверьте корзину вручную.')
        row.hover()
        remove = self.element('cart_remove', row)
        if urlsplit(self.settings.base_url).hostname in {'roscha.net', 'www.roscha.net'}:
            with self.page.expect_response(
                lambda response: self.is_same_site(response.url)
                and response.request.method == 'POST'
                and urlsplit(response.url).path == '/bitrix/components/bitrix/sale.basket.basket/ajax.php',
                timeout=self.timeout,
            ) as removal:
                remove.click()
            if not removal.value.ok:
                raise CheckFailed(f'Сервер вернул HTTP {removal.value.status} при удалении тестовой позиции.')
        else:
            remove.click()
        row.hidden()
        self.open('cart')
        self.wait_ready()
        links = self.element('cart_product_link').locator.filter(has_text=exact(product.name))
        self.from_locator(links, 'cart_product_link: тестовая позиция удалена').hidden()


class CheckoutPage(BasePage):
    def verify(self, product):
        self.element('checkout_heading').visible()
        if not self.is_same_site(self.page.url):
            raise CheckFailed('Оформление открылось за пределами настроенного сайта.')
        self.check_captcha()
        if 'checkout_expand' in self.settings.selectors:
            self.element('checkout_expand').click()
        row = self.from_locator(self.element('checkout_row').locator.filter(has_text=product.name), 'checkout_row')
        row.visible()
        if self.element('checkout_row').locator.count() != 1:
            raise CheckFailed('На оформлении ожидается ровно одна позиция из корзины.')
        if product.variant:
            self.element('checkout_variant', row).contains(exact(product.variant))
        if quantity_text(self.element('checkout_quantity', row).text()) != 1:
            raise CheckFailed('Количество товара на оформлении отличается от корзины.')
        if money(self.element('checkout_total').text(), 'checkout_total') != product.price:
            raise CheckFailed('Сумма товаров на оформлении отличается от корзины.')
