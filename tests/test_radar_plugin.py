import os
import pathlib
import subprocess

import pytest


@pytest.fixture
def install_plugin(tmp_path: pathlib.Path) -> None:
    project_path = pathlib.Path().absolute()
    os.chdir(tmp_path)
    subprocess.run(['python', '-m', 'venv', 'venv'], check=True)
    subprocess.run(['./venv/bin/pip', 'install', str(project_path)], check=True)


@pytest.fixture
def test_file(tmp_path: pathlib.Path) -> pathlib.Path:
    file = tmp_path / 'test_success.py'
    file.write_text('\n'.join(['def test_success() -> None:', '   assert True']))
    return file.absolute()


def test_plugin(install_plugin: None, test_file: pathlib.Path) -> None:
    result = subprocess.run(
        [
            './venv/bin/pytest',
            '-p',
            'pytest_radar',
            '--radar-endpoint=https://reqbin.com/echo',
            str(test_file),
        ],
        check=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert 'AssertionError' not in result.stdout.decode('utf-8')
