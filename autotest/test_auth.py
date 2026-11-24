from dataclasses import dataclass

import allure
import pytest

from autotest.flows import successful_login
from ui.auth import AuthPage

pytestmark = pytest.mark.auth


def label(case_id, title, source, kind):
    allure.dynamic.title(f'{case_id}. {title}')
    allure.dynamic.label('case_id', case_id)
    allure.dynamic.parameter('Кейс из отчёта', source)
    allure.dynamic.parameter('Тип идентификатора', kind)


@allure.feature('Авторизация')
def test_login_with_email(ui_page, settings):
    label('AUTH-P01', 'Вход по email и паролю', 'ТК-А09 / ФТ-А08', 'email')
    successful_login(AuthPage(ui_page, settings), settings.account, 'email')


@allure.feature('Авторизация')
def test_login_with_phone(ui_page, settings):
    label('AUTH-P02', 'Вход по телефону и паролю', 'ТК-А09 / ФТ-А08, телефонная пара', 'phone')
    successful_login(AuthPage(ui_page, settings), settings.account, 'phone')


@allure.feature('Авторизация')
def test_login_with_username(ui_page, settings):
    label('AUTH-P03', 'Вход по логину и паролю', 'ТК-А09 / ФТ-А08', 'login')
    successful_login(AuthPage(ui_page, settings), settings.account, 'login')


@dataclass(frozen=True)
class NegativeCase:
    id: str
    title: str
    kind: str
    input_case: str
    expectation: str
    invalid_field: str = ''

    def __repr__(self):
        return self.id


NEGATIVE_CASES = (
    NegativeCase('AUTH-N01', 'Пустой идентификатор', 'email', 'missing_identifier', 'required', 'identifier'),
    NegativeCase('AUTH-N02', 'Пустой пароль', 'email', 'missing_password', 'required', 'password'),
    NegativeCase('AUTH-N03', 'Неполный телефон в парольной форме', 'phone', 'short_phone', 'phone_format', 'identifier'),
    NegativeCase('AUTH-N04', 'Несуществующий email', 'email', 'unknown_email', 'credentials'),
    NegativeCase('AUTH-N05', 'Email и неверный пароль', 'email', 'bad_password', 'credentials'),
    NegativeCase('AUTH-N06', 'Телефон и неверный пароль', 'phone', 'bad_password', 'credentials'),
    NegativeCase('AUTH-N07', 'Логин и неверный пароль', 'login', 'bad_password', 'credentials'),
)


def negative_input(case, account):
    identifier = getattr(account, case.kind)
    password = account.password
    if case.input_case == 'missing_identifier':
        identifier = ''
    elif case.input_case == 'missing_password':
        password = ''
    elif case.input_case == 'short_phone':
        identifier = '+7000000000'
    elif case.input_case == 'unknown_email':
        identifier = 'roscha-automation-no-account@example.invalid'
    elif case.input_case == 'bad_password':
        password = 'Rejected-Password!1' if password != 'Rejected-Password!1' else 'Rejected-Password!2'
    if (not identifier and case.input_case != 'missing_identifier') or (not password and case.input_case != 'missing_password'):
        pytest.skip('Для проверки нужна допустимая часть пары существующего аккаунта. Заполните account в local.json.')
    return identifier, password


@allure.feature('Авторизация')
@pytest.mark.parametrize('case', NEGATIVE_CASES, ids=[case.id for case in NEGATIVE_CASES])
def test_reject_invalid_credentials(ui_page, settings, case):
    source = 'ТК-А10 / ФТ-А08' if case.input_case == 'bad_password' else 'ФТ-А08, дополнительный класс'
    label(case.id, case.title, source, case.kind)
    allure.dynamic.parameter('Класс входных данных', case.input_case)
    allure.dynamic.parameter('Ожидаемая ошибка', case.expectation)
    identifier, password = negative_input(case, settings.account)
    auth = AuthPage(ui_page, settings)
    identifier_field, password_field = auth.submit_credentials(case.kind, identifier, password)
    fields = {'identifier': identifier_field, 'password': password_field}
    auth.expect_rejected(case.expectation, fields.get(case.invalid_field))
    auth.expect_guest()
