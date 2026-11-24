import re
from decimal import Decimal
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError, expect

from core.diagnostics import CheckFailed, LOGGER, failure_reason
from ui.selectors import DEFAULTS


class BaseElement:
    def __init__(self, locator, key, timeout):
        self.locator = locator
        self.key = key
        self.timeout = timeout

    def _action(self, label, action):
        LOGGER.debug('%s (%s, ожидание до %s мс).', label, self.key, self.timeout)
        try:
            return action()
        except (PlaywrightError, AssertionError) as exc:
            raise CheckFailed(f'{label} ({self.key}, {self.timeout} мс). {failure_reason(exc)}') from None

    def visible(self):
        self._action('Ожидание элемента', lambda: expect(self.locator).to_be_visible(timeout=self.timeout))

    def hidden(self):
        self._action('Ожидание исчезновения', lambda: expect(self.locator).to_have_count(0, timeout=self.timeout))

    def enabled(self):
        self._action('Ожидание доступности элемента', lambda: expect(self.locator).to_be_enabled(timeout=self.timeout))

    def click(self):
        self._action('Нажатие', lambda: self.locator.click(timeout=self.timeout))

    def hover(self):
        self._action('Наведение на элемент', lambda: self.locator.hover(timeout=self.timeout))

    def fill(self, value):
        self._action('Заполнение поля', lambda: self.locator.fill(value, timeout=self.timeout))

    def press(self, key):
        self._action('Ввод с клавиатуры', lambda: self.locator.press(key, timeout=self.timeout))

    def text(self):
        self.visible()
        return self._action('Чтение текста', lambda: self.locator.inner_text(timeout=self.timeout))

    def attribute(self, name):
        return self._action('Чтение атрибута', lambda: self.locator.get_attribute(name, timeout=self.timeout))

    def value(self):
        return self._action('Чтение значения', lambda: self.locator.input_value(timeout=self.timeout))

    def contains(self, pattern):
        self._action('Сверка текста', lambda: expect(self.locator).to_contain_text(pattern, timeout=self.timeout))

    def match_value(self, value):
        self._action('Сверка значения поля', lambda: expect(self.locator).to_have_value(value, timeout=self.timeout))


class BasePage:
    def __init__(self, page, settings):
        self.page = page
        self.settings = settings
        self.timeout = settings.timeout_ms

    def element(self, key, parent=None):
        scope = self.page if parent is None else parent.locator
        return BaseElement(scope.locator(self.settings.selectors.get(key, DEFAULTS[key])), key, self.timeout)

    def from_locator(self, locator, key):
        return BaseElement(locator, key, self.timeout)

    def open(self, key):
        LOGGER.debug('Переход к %s. Тайм-аут %s мс.', key, self.settings.navigation_timeout_ms)
        try:
            response = self.page.goto(self.settings.url(key), wait_until='domcontentloaded')
        except PlaywrightError as exc:
            raise CheckFailed(f'Страница {key}, {self.settings.navigation_timeout_ms} мс. {failure_reason(exc)}') from None
        if response is None or response.status >= 400:
            status = response.status if response is not None else 'нет ответа'
            raise CheckFailed(f'Страница {key} недоступна. Ответ: {status}.')
        self.check_captcha()

    def check_captcha(self):
        if self.element('captcha').locator.count():
            raise CheckFailed('Обнаружена CAPTCHA. По спецификации требуется согласовать замену сайта.')

    def current_path(self):
        return urlsplit(self.page.url).path.rstrip('/')

    def is_same_site(self, url):
        actual = urlsplit(url)
        target = urlsplit(self.settings.base_url)
        return ((actual.scheme, actual.hostname, actual.port) == (target.scheme, target.hostname, target.port)
                and not actual.username and not actual.password)


def money(text, label):
    amounts = re.findall(r'\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d{1,2})?', text)
    if len(amounts) != 1:
        raise CheckFailed(f'Для {label} нужен локатор одного числового значения цены.')
    return Decimal(re.sub(r'\s', '', amounts[0]).replace(',', '.'))
