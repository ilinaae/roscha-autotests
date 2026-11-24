# CSS по типовым атрибутам форм. Для конкретной темы сайта допустимы точные переопределения.
PASSWORD_FORM = ('form:has(input[type="password"]:visible):visible, '
                 '.bxmaker-authuserphone-enter-auth-by-password-form:has(input[name="PASSWORD"]:visible):visible')
DEFAULTS = {
    'password_toggle': ':is(a, button):text-is("Войти с помощью пароля"):visible, '
                       'a:text-matches("^(Войти|Вход) (с|по) парол(ем|ю)$", "i"):visible, '
                       'button:text-matches("^(Войти|Вход) (с|по) парол(ем|ю)$", "i"):visible, '
                       ':is(a, button):text-is("По паролю"):visible, '
                       ':is(a, button):text-is("Войти по логину и паролю"):visible',
    'password_form': PASSWORD_FORM,
    'identifier': 'input:is([name="PHONE_LOGIN_EMAIL"], [name="USER_LOGIN" i], [name="login" i], '
                  '[name="identifier" i], [type="email"]):visible',
    'identifier_email': 'input[type="email"]:visible, input[name="email" i]:visible',
    'identifier_phone': 'input[type="tel"]:visible, input[name="phone" i]:visible, input[name="telephone" i]:visible',
    'identifier_login': 'input[name="USER_LOGIN" i]:visible, input[name="login" i]:visible, input[name="username" i]:visible',
    'password': 'input[type="password"]:visible',
    'login_submit': ':is(button.bxmaker-authuserphone-button, button[type="submit"], '
                    'input[type="submit"], button:text-is("Войти")):visible',
    'auth_error': ':is(.bxmaker-authuserphone-message--error, [role="alert"], .alert-danger, '
                  '.errortext, .error-text, .error-message, '
                  '.form-error, .validation-error, .text-danger, .error):visible',
    'guest_form': '.bxmaker-authuserphone-enter-auth:has(input:visible):visible, '
                  ':is(form:has(input[type="password"]), form:has(input[type="tel"]), '
                  'form:has(input[name="USER_LOGIN" i])):visible',
    'account_marker': 'input#main-profile-email:visible, main, #content, #workarea',
    'logged_in': 'a[href*="logout=yes"]:visible, a[href*="logout="]:visible, '
                 'a:text-is("Выйти"):visible, button:text-is("Выйти"):visible',
    'captcha': 'iframe[src*="recaptcha"]:visible, iframe[src*="hcaptcha"]:visible, '
               'iframe[src*="smartcaptcha"]:visible, input[name*="captcha_word" i]:visible',
    'search': 'header input[type="search"]:visible, header input[name="q"]:visible, '
              'input[name="q"][type="text"]:visible, input[type="search"]:visible',
    'search_result': 'a.product-grid-card__name[href*="/catalog/"]:visible, '
                     'main a[href*="/catalog/"]:visible, #workarea a[href*="/catalog/"]:visible, '
                     '#content a[href*="/catalog/"]:visible',
    'product_title': 'h1:visible',
    'product_article': ':is([itemprop="sku"], [data-role="product-article"], .article, .product-article):visible',
    'product_price': ':is(.product-detail__price, [itemprop="price"], [data-role="product-price"], '
                     '.price_value, .product-price):visible',
    'product_unit': ':is(.product-detail__price-currency, [itemprop="unitText"], [data-role="product-unit"], '
                    '.price_measure, .product-unit):visible',
    'product_variant': ':is([data-role="product-variant"], .sku-props .selected, .product-variant):visible',
    'product_add': ':is(button.product-detail__add-to-cart, [data-role="add-to-cart"], '
                   'button:text-is("В корзину"):not(.product-grid-card__buy), a:text-is("В корзину"), '
                   'button:text-is("Добавить в корзину"), a:text-is("Добавить в корзину")):visible',
    'product_added': ':is(.product-detail__go-to-cart, [data-role="added-to-cart"], .bx-basket-popup, '
                     'a:text-is("В корзине"), button:text-is("В корзине"), '
                     'a:text-is("Перейти в корзину")):visible',
    'cart_link': 'header a[href*="/personal/cart/"]:visible, '
                 'a[href*="/personal/cart/"]:text-is("Перейти в корзину"):visible',
    'cart_row': ':is([data-entity="basket-item"], [data-role="cart-item"], .basket-item, .basket-items-list-item):visible',
    'cart_product_link': 'a[href*="/catalog/"]:visible',
    'cart_empty': ':is(.bx-sbb-empty-cart-text, .basket-items-list-empty, [data-role="cart-empty"], '
                  'p:text-matches("корзина пуста|в корзине нет товаров", "i"), '
                  'div:text-matches("^корзина пуста[.!]?$", "i")):visible',
    'cart_quantity': 'input:is([data-entity="basket-item-quantity-field"], [name*="QUANTITY" i], [type="number"]):visible',
    'cart_unit_price': ':is([data-entity="basket-item-price"], [data-role="unit-price"], '
                       '.basket-items-list-item-price-for-one .basket-item-price-current-text):visible',
    'cart_line_total': ':is([data-entity="basket-item-sum-price"], [data-role="line-total"], .basket-item-sum-price, '
                       '.basket-items-list-item-price:not(.basket-items-list-item-price-for-one) .basket-item-price-current-text):visible',
    'cart_variant': ':is([data-role="cart-variant"], .basket-item-property-custom-value):visible',
    'cart_total': ':is([data-entity="basket-total-price"], [data-role="cart-total"], '
                  '.basket-checkout-block-total-price-inner:not(:has([data-entity="basket-total-price"]))):visible',
    'cart_remove': ':is([data-entity="basket-item-delete"], [data-role="remove-item"], button[aria-label="Удалить"], '
                   'a:text-is("Удалить"), button:text-is("Удалить")):visible',
    'checkout_link': '[data-entity="basket-checkout-button"]:visible, '
                     'a:text-is("Оформить заказ"):visible, button:text-is("Оформить заказ"):visible, '
                     'a:text-is("Перейти к оформлению"):visible, button:text-is("Перейти к оформлению"):visible',
    'checkout_heading': ':is(h1, h2):text-matches("оформление заказа", "i"):visible',
    'checkout_expand': '[data-role="expand-order-items"]:visible',
    'checkout_row': ':is([data-role="checkout-item"], .bx-soa-item-tr, .order-item):visible',
    'checkout_quantity': ':is([data-role="order-quantity"], .bx-soa-item-quantity, .order-item-quantity, '
                         '.bx-soa-item-td-text > span:not(.bx-price)):visible',
    'checkout_variant': ':is([data-role="order-variant"], .bx-soa-item-td_text .bx-soa-item-properties):visible',
    'checkout_total': ':is([data-role="order-items-total"], .bx-soa-cart-total .bx-soa-cart-total-line'
                      ':has(.bx-soa-cart-t:text-matches("^(Товары|Стоимость товаров|Товаров на( сумму)?):?$", "i")) '
                      '.bx-soa-cart-d, .order-items-total):visible',
}

ERRORS = {
    'required': r'заполн|обязател|введите|укажит|не указан|required|fill out|enter|неверн.*(логин|парол)',
    'credentials': r'неверн|неправильн|не найден|не существует|ошибк[аи] (входа|авторизац)|invalid|incorrect|not found',
    'phone_format': r'телефон|формат|номер|неверн.*логин|такой пользователь не найден|invalid|phone',
}
