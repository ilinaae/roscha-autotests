import re
from urllib.parse import urljoin

from core.diagnostics import CheckFailed, step
from ui.base import BasePage
from ui.selectors import ERRORS


class AuthPage(BasePage):
    def open_password_form(self, kind):
        self.open('login')
        form = self.element('password_form')
        switch = self.element('password_toggle')
        self.from_locator(switch.locator.or_(form.locator).first, 'password_toggle или password_form').visible()
        if switch.locator.count():
            with step('Нажать «Войти с помощью пароля»'):
                switch.click()
        with step('Дождаться парольной формы'):
            form.visible()
        self.check_captcha()
        action = form.attribute('action') or self.page.url
        if not self.is_same_site(self.page.url) or not self.is_same_site(urljoin(self.page.url, action)):
            raise CheckFailed('Парольная форма ведёт за пределы настроенного сайта.')
        submit = self.element('login_submit', form)
        button_action = submit.attribute('formaction')
        if button_action and not self.is_same_site(urljoin(self.page.url, button_action)):
            raise CheckFailed('Кнопка входа ведёт за пределы настроенного сайта.')
        specific = self.element('identifier_' + kind, form)
        identifier = specific if specific.locator.count() else self.element('identifier', form)
        return identifier, self.element('password', form), submit

    def submit_credentials(self, kind, identifier, password):
        with step(f'Открыть парольную форму и ввести данные ({kind})'):
            login_field, password_field, submit = self.open_password_form(kind)
            login_field.fill(identifier)
            password_field.fill(password)
        with step('Отправить парольную форму'):
            submit.click()
            self.check_captcha()
        return login_field, password_field

    def expect_account(self, marker):
        with step('Проверить вход и принадлежность личного кабинета'):
            self.check_captcha()
            self.element('logged_in').visible()
            self.open('profile')
            if self.current_path() == self.settings.paths['login'].rstrip('/'):
                raise CheckFailed('Личный раздел запросил повторный вход.')
            self.element('logged_in').visible()
            candidates = self.element('account_marker')
            fields = candidates.locator.and_(self.page.locator('input:visible, textarea:visible'))
            if fields.count():
                value = self.from_locator(fields, 'account_marker: поле профиля')
                value.match_value(re.compile(r'^\s*' + re.escape(marker) + r'\s*$', re.IGNORECASE))
                return
            pattern = re.compile(r'(?<![\w@.])' + re.escape(marker) + r'(?![\w@.])', re.IGNORECASE)
            public_text = candidates.locator.filter(has_text=pattern)
            self.from_locator(public_text.first, 'account_marker').visible()

    def expect_rejected(self, error_class, invalid_field=None):
        with step('Проверить ожидаемую ошибку входа'):
            self.check_captcha()
            pattern = re.compile(self.settings.errors.get(error_class, ERRORS[error_class]), re.IGNORECASE)
            if invalid_field is not None:
                native_message = invalid_field.locator.evaluate(
                    '(element) => element.validationMessage || ""', timeout=self.timeout
                ) if invalid_field.locator.count() == 1 else ''
                if native_message and pattern.search(native_message):
                    return
            errors = self.element('auth_error').locator.filter(has_text=pattern)
            self.from_locator(errors.first, 'auth_error / ' + error_class).visible()

    def expect_guest(self):
        with step('Убедиться, что личный кабинет требует входа'):
            self.open('profile')
            self.element('guest_form').visible()
            self.element('logged_in').hidden()
