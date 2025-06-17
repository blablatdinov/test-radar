import base64
import datetime
import zlib

import httpx
import pytest

http_session = httpx.Client()
session_start_date = datetime.datetime.now(tz=datetime.UTC).isoformat()


def pytest_addoption(parser: pytest.Parser) -> None:
    help_text = 'Test radar endpoint'
    parser.addini('radar_endpoint', type='string', help=help_text)
    parser.addoption('--radar-endpoint', help=help_text)


def pytest_configure(config: pytest.Config) -> None:
    if config.option.help:
        return
    if not config.getini('radar_endpoint') and not config.getoption('--radar-endpoint'):
        msg = 'Provide `--radar-endpoint` in cli option or `radar_endpoint` in config file`'
        raise pytest.UsageError(msg)


def pytest_sessionstart(session: pytest.Session) -> None:
    http_session.base_url = session.config.getoption('--radar-endpoint') or session.config.getini('radar_endpoint')


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    logs = ''
    if report.when == 'call' and report.failed:
        compressed = zlib.compress(report.longreprtext.encode('utf-8'))
        encoded = base64.b64encode(compressed)
        logs = encoded.decode('utf-8')
    if report.when == 'call':
        try:
            response = http_session.post(
                '/api/v1/test_record/create/',
                json={
                    'label': report.nodeid,
                    'timestamp': session_start_date,
                    'logs': logs,
                    'success': not report.failed,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            print('Some error occured on sending test record to radar.')


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    http_session.close()
