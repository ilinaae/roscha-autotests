import logging

import allure
import pytest

from core.config import ConfigurationError, load_settings
from core.diagnostics import LOGGER, attach_failure, step
from core.reporting import ALLURE_RUN, finish_report, prepare_report
from core.wifi import direct_wifi_proxy, resolve_wifi_interface


def pytest_addoption(parser):
    parser.addoption('--wifi-interface', default=None, metavar='auto|IFINDEX',
                     help='Use a connected Windows Wi-Fi adapter for HTTPS to the configured site')


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if not config.option.collectonly and not config.getoption('help', default=False):
        config.stash[ALLURE_RUN] = prepare_report(config)


@pytest.fixture(scope='session')
def settings():
    try:
        return load_settings()
    except ConfigurationError as exc:
        pytest.fail(str(exc), pytrace=False)


@pytest.fixture(scope='session')
def browser_type_launch_args(browser_type_launch_args, settings, pytestconfig):
    interface = pytestconfig.getoption('--wifi-interface')
    if interface is None:
        yield browser_type_launch_args
        return
    try:
        index = resolve_wifi_interface(interface)
        LOGGER.info('Подключение к сайту через Wi-Fi, индекс %s.', index)
        with direct_wifi_proxy(settings.base_url, index) as endpoint:
            yield {**browser_type_launch_args, 'proxy': {'server': endpoint}}
    except ConfigurationError as exc:
        pytest.fail(str(exc), pytrace=False)


@pytest.fixture
def ui_page(browser, settings, request, caplog, browser_name):
    caplog.set_level(logging.DEBUG, logger='roscha.autotests')
    with step('Подготовить чистый сеанс браузера'):
        context = browser.new_context(locale='ru-RU')
        context.set_default_timeout(settings.timeout_ms)
        context.set_default_navigation_timeout(settings.navigation_timeout_ms)
        page = context.new_page()
        request.node.ui_page = page
        request.node.ui_logs = caplog
    allure.dynamic.parameter('Браузер', browser_name)
    try:
        yield page
    finally:
        with step('Закрыть сеанс браузера'):
            context.close()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.failed:
        capture = getattr(item, 'ui_logs', None)
        records = [] if capture is None else [record for when in ('setup', 'call', 'teardown')
                                             for record in capture.get_records(when)]
        level = logging.getLevelNamesMapping().get(item.config.getoption('log_cli_level')
                                                 or item.config.getini('log_cli_level'), logging.INFO)
        attach_failure(getattr(item, 'ui_page', None), report, records, level)
    return report


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_sessionfinish(session):
    outcome = yield
    run = session.config.stash.get(ALLURE_RUN, None)
    if run is not None:
        terminal = session.config.pluginmanager.get_plugin('terminalreporter')
        finish_report(run, terminal.write_line if terminal else print)
    return outcome
