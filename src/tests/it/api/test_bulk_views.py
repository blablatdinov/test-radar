# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import datetime
import zlib

import pytest
from django.test import Client

from records.models import Agent, ApiToken, TestRecord
from records.srv import token as token_srv


@pytest.mark.django_db
def test_bulk_create_success(client: Client, agent: Agent, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test_sample.py::test_pass',
                    'timestamp': timestamp,
                    'logs': '',
                    'success': True,
                    'branch': 'main',
                    'commit': 'abc123def456',
                },
                {
                    'label': 'tests/test_sample.py::test_fail',
                    'timestamp': timestamp,
                    'logs': base64.b64encode(zlib.compress(b'assert error')).decode(),
                    'success': False,
                    'branch': 'main',
                    'commit': 'abc123def456',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200, response.content
    assert response.json() == {'created': 2}
    assert TestRecord.objects.count() == 2


@pytest.mark.django_db
def test_bulk_create_empty_records(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'records': []},
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()


@pytest.mark.django_db
def test_bulk_create_missing_records_key(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={},
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()


@pytest.mark.django_db
def test_bulk_create_invalid_token(client: Client) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}]},
        HTTP_AUTHORIZATION='Token ci_invalid_token',
    )

    assert response.status_code == 401
    assert response.json()['error'] == 'Invalid token'


@pytest.mark.django_db
def test_bulk_create_missing_auth_header(client: Client) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}]},
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_bulk_create_expired_token_rejected(client: Client, agent: Agent) -> None:
    raw_token = _create_expired_token(agent)

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}]},
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_bulk_create_record_without_label(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'timestamp': '2026-07-28T12:00:00Z',
                    'success': True,
                    'logs': '',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert TestRecord.objects.count() == 0


@pytest.mark.django_db
def test_bulk_create_exceeds_limit(client: Client, agent_token: str) -> None:
    records = [
        {
            'label': f'tests/test.py::test_{idx}',
            'timestamp': '2026-07-28T12:00:00Z',
            'success': True,
            'logs': '',
            'branch': 'main',
            'commit': 'abc123',
        }
        for idx in range(501)
    ]

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'records': records},
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()
    assert TestRecord.objects.count() == 0


@pytest.mark.django_db
def test_bulk_create_all_records_in_db(client: Client, agent: Agent, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test_a.py::test_one',
                    'timestamp': timestamp,
                    'logs': '',
                    'success': True,
                    'branch': 'main',
                    'commit': 'abc123',
                },
                {
                    'label': 'tests/test_b.py::test_two',
                    'timestamp': timestamp,
                    'logs': '',
                    'success': False,
                    'branch': 'dev',
                    'commit': 'def456',
                },
                {
                    'label': 'tests/test_c.py::test_three',
                    'timestamp': timestamp,
                    'logs': '',
                    'success': True,
                    'branch': '',
                    'commit': '',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200
    assert response.json() == {'created': 3}
    records = list(TestRecord.objects.order_by('label'))
    labels = [record.label for record in records]
    assert labels == ['tests/test_a.py::test_one', 'tests/test_b.py::test_two', 'tests/test_c.py::test_three']
    assert not records[1].success
    assert records[2].branch == ''


@pytest.mark.django_db
def test_bulk_create_binds_agent_and_project(client: Client, agent: Agent, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test.py::test_project_binding',
                    'timestamp': '2026-07-28T12:00:00Z',
                    'logs': '',
                    'success': True,
                    'branch': 'main',
                    'commit': 'abc123',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200
    record = TestRecord.objects.get(label='tests/test.py::test_project_binding')
    assert record.project == agent.project
    assert record.agent == agent


@pytest.mark.django_db
def test_bulk_create_atomic_on_validation_error(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test_a.py::test_one',
                    'timestamp': '2026-07-28T12:00:00Z',
                    'logs': '',
                    'success': True,
                },
                {
                    'label': '',
                    'timestamp': '2026-07-28T12:00:00Z',
                    'logs': '',
                    'success': False,
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert TestRecord.objects.count() == 0


@pytest.mark.django_db
def test_bulk_create_decompress_logs(client: Client, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
    logs = 'AssertionError: assert 1 == 0'
    compressed = base64.b64encode(zlib.compress(logs.encode('utf-8'))).decode()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test.py::test_fail',
                    'timestamp': timestamp,
                    'logs': compressed,
                    'success': False,
                    'branch': 'main',
                    'commit': 'abc123',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200
    record = TestRecord.objects.get(label='tests/test.py::test_fail')
    assert record.logs == logs


@pytest.mark.django_db
def test_bulk_create_optional_branch_commit(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test.py::test_no_git',
                    'timestamp': '2026-07-28T12:00:00Z',
                    'logs': '',
                    'success': True,
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200
    record = TestRecord.objects.get(label='tests/test.py::test_no_git')
    assert record.branch == ''
    assert record.commit == ''


@pytest.mark.django_db
def test_bulk_create_single_record(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [
                {
                    'label': 'tests/test.py::test_single',
                    'timestamp': '2026-07-28T12:00:00Z',
                    'logs': '',
                    'success': True,
                    'branch': 'main',
                    'commit': 'abc123',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 200
    assert response.json() == {'created': 1}


def _create_expired_token(agent: Agent) -> str:
    raw_token = token_srv.create_token_for_agent(agent)
    token_obj = ApiToken.objects.get(agent=agent)
    one_hour_ago = datetime.timedelta(hours=1)
    token_obj.expires_at = datetime.datetime.now(tz=datetime.UTC) - one_hour_ago
    token_obj.save(update_fields=['expires_at'])
    return raw_token
