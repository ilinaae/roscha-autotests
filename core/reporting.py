import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from core.config import ROOT


REPORTS_ROOT = ROOT / 'reports'
ALLURE_PACKAGE = 'allure-commandline@2.46.1'


@dataclass(frozen=True)
class AllureRun:
    folder: Path
    results: Path
    owns_results: bool


ALLURE_RUN = pytest.StashKey[AllureRun]()


def prepare_report(config):
    REPORTS_ROOT.mkdir(exist_ok=True)
    stamp = datetime.now().astimezone().strftime('%Y-%m-%d_%H-%M-%S')
    folder = REPORTS_ROOT / stamp
    number = 2
    while True:
        try:
            folder.mkdir()
            break
        except FileExistsError:
            folder = REPORTS_ROOT / f'{stamp}_{number:02d}'
            number += 1

    explicit_results = config.getoption('allure_report_dir')
    results = Path(explicit_results).resolve() if explicit_results else folder / 'allure-results'
    config.option.allure_report_dir = str(results)
    return AllureRun(folder, results, owns_results=not explicit_results)


def allure_command():
    launcher = shutil.which('npx.cmd' if os.name == 'nt' else 'npx')
    if launcher is None:
        raise FileNotFoundError('Не найдена команда npx. Для сборки Allure нужен Node.js.')
    if os.name == 'nt':
        # The standard Windows installer ships the launcher as a JavaScript file too.
        node = shutil.which('node.exe')
        script = Path(launcher).parent / 'node_modules/npm/bin/npx-cli.js'
        if node and script.is_file():
            return [node, str(script), '--yes', ALLURE_PACKAGE]
    return [launcher, '--yes', ALLURE_PACKAGE]


def remove_staging(path, folder):
    if path.exists() and path.resolve().parent == folder.resolve() and not path.is_symlink():
        shutil.rmtree(path)


def finish_report(run, write_line):
    if not any(run.results.glob('*-result.json')):
        if run.owns_results:
            remove_staging(run.results, run.folder)
        run.folder.rmdir()
        return

    (run.results / 'environment.properties').write_text(
        'Project=Roscha UI autotests\nPlaywright=1.65.2\nPytest=9.2.0\n'
        'Allure.adapter=2.16.2\nCheckout.scope=Before order submission\n', encoding='utf-8'
    )
    staging = run.folder / '.html'
    write_line('Allure: собираю HTML-отчёт…')
    try:
        command = [*allure_command(), 'generate', str(run.results), '--single-file', '-o', str(staging)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=180, check=False)
        if result.returncode:
            lines = (result.stderr or result.stdout).strip().splitlines()
            detail = lines[-1] if lines else f'код выхода {result.returncode}'
            raise RuntimeError(detail)
        (staging / 'index.html').replace(run.folder / 'index.html')
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        write_line(f'Allure: не удалось собрать HTML. {exc}')
        write_line(f'Данные прогона сохранены: {run.results}')
    else:
        if run.owns_results:
            remove_staging(run.results, run.folder)
        write_line(f'Allure-отчёт: {run.folder / "index.html"}')
    finally:
        remove_staging(staging, run.folder)
