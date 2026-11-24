import logging
from contextlib import contextmanager

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout

LOGGER = logging.getLogger('roscha.autotests')


class CheckFailed(AssertionError):
    """Сообщение пригодно для отчёта и не содержит значений полей сайта."""


@contextmanager
def step(title):
    LOGGER.info(title)
    with allure.step(title):
        try:
            yield
        except CheckFailed as exc:
            LOGGER.error('%s. %s', title, exc)
            raise
        except (PlaywrightError, AssertionError) as exc:
            reason = failure_reason(exc)
            LOGGER.error('%s. %s', title, reason)
            raise CheckFailed(f'{title}. {reason}') from None


def failure_reason(exc):
    if isinstance(exc, PlaywrightTimeout):
        return 'Истекло время ожидания Playwright.'
    if isinstance(exc, PlaywrightError):
        return 'Playwright не смог выполнить действие. Проверьте доступность страницы и уникальность локатора.'
    return 'Ожидаемое состояние интерфейса не подтверждено.'


# Сохраняется расположение элементов. Текст, изображения, поля и встроенные виджеты скрываются.
SCREENSHOT_STYLE = """
*, *::before, *::after {
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: none !important;
    background-image: none !important;
    border-image: none !important;
    list-style-image: none !important;
}
img, svg, canvas, iframe, object, embed, video, input, textarea, select, [contenteditable] {
    visibility: hidden !important;
}
"""


def attach_failure(page, report, logs, level):
    message = '\n'.join(f'{record.levelname} {record.getMessage()}' for record in logs
                        if record.name == LOGGER.name and record.levelno >= level)
    allure.attach(message or 'Шаги браузера ещё не начались.', 'Лог шагов', allure.attachment_type.TEXT)
    try:
        if page is None or page.is_closed():
            reason = 'Страница браузера недоступна.'
        else:
            screenshot = page.screenshot(style=SCREENSHOT_STYLE, animations='disabled', timeout=5000)
            allure.attach(screenshot, f'Скриншот без персональных данных ({report.when})', allure.attachment_type.PNG)
            return
    except PlaywrightError as exc:
        reason = failure_reason(exc)
    allure.attach(reason, 'Почему скриншот недоступен', allure.attachment_type.TEXT)
