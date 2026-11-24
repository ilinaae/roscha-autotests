import re

import pytest


def successful_login(auth, account, kind):
    required = (kind, 'password', 'marker')
    missing = [field for field in required if not getattr(account, field)]
    if missing:
        pytest.skip('Для существующего аккаунта заполните account в local.json: ' + ', '.join(missing))
    if kind == 'login':
        same_email = account.login.casefold() == account.email.casefold()
        same_phone = (re.fullmatch(r'[+\d\s()-]+', account.login) and account.phone
                      and re.sub(r'\D', '', account.login)[-10:] == re.sub(r'\D', '', account.phone)[-10:])
        if same_email or same_phone:
            pytest.skip('Для проверки логина нужен отдельный идентификатор, отличный от email и телефона.')
    auth.submit_credentials(kind, getattr(account, kind), account.password)
    auth.expect_account(account.marker)
