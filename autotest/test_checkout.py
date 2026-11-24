import allure
import pytest

from autotest.flows import successful_login
from core.config import ConfigurationError
from core.diagnostics import step
from ui.auth import AuthPage
from ui.shop import CartPage, CatalogPage, CheckoutPage, ProductPage


@pytest.mark.e2e
@allure.feature('Путь покупки до оформления')
@allure.title('E2E-01. От входа до страницы оформления')
@allure.label('case_id', 'E2E-01')
def test_catalog_to_checkout(ui_page, settings, request):
    allure.dynamic.parameter('Кейсы из отчёта', 'ТК-А09 → ТК-М02 → ТК-М09 → ТК-М11 → ТК-М19')
    try:
        product = settings.product()
    except ConfigurationError as exc:
        pytest.skip(str(exc))
    allure.dynamic.parameter('Количество', 1)
    allure.dynamic.parameter('Товар', product.name)
    allure.dynamic.parameter('Идентификатор товара', product.article or product.product_id)
    allure.dynamic.parameter('Цена за единицу, ₽', str(product.price))
    successful_login(AuthPage(ui_page, settings), settings.account, 'email')

    cart = CartPage(ui_page, settings)
    with step('Проверить, что корзина аккаунта пуста'):
        cart.open('cart')
        if not cart.is_empty():
            pytest.skip('В корзине остались товары. Для E2E нужна пустая корзина существующего аккаунта.')

    with step('Найти товар и открыть его карточку'):
        CatalogPage(ui_page, settings).open_search_result(product)
    with step('Сверить название, идентификатор, единицу и цену'):
        product_page = ProductPage(ui_page, settings)
        product_page.verify(product)
        product_url = ui_page.url

    def cleanup():
        with step('Убрать добавленный тестом товар из корзины'):
            cart.remove_test_product(product, product_url)

    request.addfinalizer(cleanup)
    with step('Добавить одну единицу товара и открыть корзину'):
        product_page.add_one()
        cart.open('cart')
    with step('Сверить позицию, количество, цену и сумму корзины'):
        cart.verify(product, product_url)
    with step('Открыть оформление и сверить состав заказа'):
        cart.go_to_checkout()
        CheckoutPage(ui_page, settings).verify(product)
