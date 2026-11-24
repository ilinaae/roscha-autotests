import json
import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, repr=False)
class Account:
    email: str
    phone: str
    login: str
    password: str
    marker: str


@dataclass(frozen=True)
class Product:
    query: str
    name: str
    article: str
    price: Decimal
    unit: str
    variant: str
    product_id: str = ''


@dataclass(frozen=True, repr=False)
class Settings:
    base_url: str
    timeout_ms: int
    navigation_timeout_ms: int
    account: Account
    product_data: dict
    paths: dict = field(default_factory=dict)
    selectors: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)

    def url(self, key):
        return self.base_url + self.paths[key]

    def product(self):
        data = self.product_data
        required = ('query', 'name', 'price', 'unit')
        missing = [key for key in required if not str(data.get(key, '')).strip()]
        article = str(data.get('article', '')).strip()
        product_id = str(data.get('id', '')).strip()
        if not (article or product_id):
            missing.append('article или id')
        if missing:
            raise ConfigurationError('Заполните product в local.json: ' + ', '.join(missing) + '.')
        try:
            price = Decimal(str(data['price']).replace(',', '.'))
            if not price.is_finite() or price <= 0 or price != price.quantize(Decimal('0.01')):
                raise InvalidOperation
        except InvalidOperation:
            raise ConfigurationError('product.price должен быть положительной ценой с точностью до копеек.') from None
        return Product(str(data['query']).strip(), str(data['name']).strip(), article,
                       price, str(data['unit']).strip(), str(data.get('variant', '')).strip(), product_id)


def load_settings():
    path = Path(os.environ.get('ROSCHA_CONFIG', ROOT / 'local.json'))
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
    except (OSError, ValueError):
        raise ConfigurationError('Проверьте доступность и синтаксис локального JSON-файла.') from None
    if not isinstance(data, dict):
        raise ConfigurationError('Локальная конфигурация должна быть объектом JSON.')

    def section(key):
        value = data.get(key, {})
        if not isinstance(value, dict):
            raise ConfigurationError(f'Раздел {key} должен быть объектом JSON.')
        return value

    def timeout(key, default):
        value = data.get(key, default)
        if type(value) is not int or value <= 0:
            raise ConfigurationError(f'{key} должен быть положительным целым числом.')
        return value

    values = section('account')
    credentials = {}
    for key in ('email', 'phone', 'login', 'password', 'marker'):
        value = os.environ.get('ROSCHA_' + key.upper(), values.get(key, ''))
        if not isinstance(value, str):
            raise ConfigurationError(f'account.{key} должен быть строкой.')
        credentials[key] = value if key == 'password' else value.strip()
    if not credentials['marker']:
        credentials['marker'] = credentials['email']

    base_url = os.environ.get('ROSCHA_BASE_URL', data.get('base_url', 'https://roscha.net'))
    if not isinstance(base_url, str):
        raise ConfigurationError('base_url должен быть URL сайта.')
    try:
        base = urlsplit(base_url)
        valid_base = (base.scheme in ('http', 'https') and base.hostname and not base.username
                      and not base.password and base.path in ('', '/') and not base.query and not base.fragment)
    except ValueError:
        valid_base = False
    if not valid_base:
        raise ConfigurationError('Укажите base_url без учётных данных, пути и параметров.')
    profile = '/personal/private/' if base.hostname in {'roscha.net', 'www.roscha.net'} else '/personal/'
    paths = {'login': '/login/', 'profile': profile,
             'catalog': '/catalog/stroitelnye_materialy/', 'cart': '/personal/cart/'}
    paths.update(section('paths'))
    if any(not isinstance(value, str) or not value.startswith('/') or value.startswith('//') or '\\' in value
           for value in paths.values()):
        raise ConfigurationError('В paths указывайте внутренние пути сайта, начинающиеся с / .')
    selectors, errors = section('selectors'), section('errors')
    if any(not isinstance(value, str) or not value.strip()
           for group in (selectors, errors) for value in group.values()):
        raise ConfigurationError('В selectors и errors должны быть непустые строки.')
    return Settings(base_url.rstrip('/'), timeout('timeout_ms', 8000),
                    timeout('navigation_timeout_ms', 20000), Account(**credentials), section('product'),
                    paths, selectors, errors)
