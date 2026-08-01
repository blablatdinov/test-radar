# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import datetime
import uuid

import pytest
import zstandard
from django.test import Client
from django.utils import timezone
from model_bakery import baker

from records.models import Agent, ApiToken, TestRecord, TestSession
from records.srv import token as token_srv

pytestmark = [
    pytest.mark.django_db,
]


def test_bulk_create_success(client: Client, agent: Agent, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
    session_id = uuid.uuid4()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(session_id),
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
                    'logs': base64.b64encode(zstandard.ZstdCompressor().compress(b'assert error')).decode(),
                    'success': False,
                    'branch': 'main',
                    'commit': 'abc123def456',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 201, response.content
    assert response.json() == {'created': 2}
    assert TestRecord.objects.count() == 2


def test_label_max_length(client: Client, agent: Agent, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [
                {
                    'label': 't' * 5120,
                    'timestamp': datetime.datetime.now(tz=datetime.UTC).isoformat(),
                    'logs': '',
                    'success': True,
                    'branch': 'main',
                    'commit': 'abc123def456',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 201, response.content


def test_bulk_create_empty_records(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()


def test_bulk_create_missing_records_key(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={'session_id': str(uuid.uuid4())},
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()


def test_bulk_create_missing_session_id(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'session_id' in response.json()


def test_bulk_create_invalid_session_id(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': 'not-a-uuid',
            'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'session_id' in response.json()


def test_bulk_create_invalid_token(client: Client) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}],
        },
        HTTP_AUTHORIZATION='Token ci_invalid_token',
    )

    assert response.status_code == 401
    assert response.text == '{"detail":"Invalid agent token."}'


def test_bulk_create_missing_auth_header(client: Client) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}],
        },
    )

    assert response.status_code == 401


def test_bulk_create_expired_token_rejected(client: Client, agent: Agent) -> None:
    raw_token = _create_expired_token(agent)

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}],
        },
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 401


def test_bulk_create_record_without_label(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
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
        data={'session_id': str(uuid.uuid4()), 'records': records},
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
    assert 'records' in response.json()
    assert TestRecord.objects.count() == 0


def test_bulk_create_all_records_in_db(client: Client, agent: Agent, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
    session_id = uuid.uuid4()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(session_id),
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
                    'branch': 'ci',
                    'commit': 'ci-765',
                },
            ],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 201
    assert response.json() == {'created': 3}
    records = list(TestRecord.objects.order_by('label'))
    labels = [record.label for record in records]
    assert labels == ['tests/test_a.py::test_one', 'tests/test_b.py::test_two', 'tests/test_c.py::test_three']
    assert not records[1].success


def test_bulk_create_creates_session(client: Client, agent: Agent, agent_token: str) -> None:
    session_id = uuid.uuid4()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(session_id),
            'records': [
                {
                    'label': 'tests/test.py::test_session_creation',
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

    assert response.status_code == 201
    db_session = TestSession.objects.get()
    assert db_session.id == session_id
    assert db_session.project == agent.project
    assert db_session.started_at is not None


def test_bulk_create_reuses_existing_session(client: Client, agent: Agent, agent_token: str) -> None:
    session_id = uuid.uuid4()
    baker.make(TestSession, id=session_id, project=agent.project, started_at=timezone.now())

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(session_id),
            'records': [
                {
                    'label': 'tests/test.py::test_reuse',
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

    assert response.status_code == 201
    assert TestSession.objects.count() == 1
    record = TestRecord.objects.get()
    assert record.session_id == session_id


def test_bulk_create_binds_agent_and_project(client: Client, agent: Agent, agent_token: str) -> None:
    session_id = uuid.uuid4()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(session_id),
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

    assert response.status_code == 201
    record = TestRecord.objects.get(label='tests/test.py::test_project_binding')
    assert record.project == agent.project
    assert record.agent == agent


def test_bulk_create_atomic_on_validation_error(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
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


def test_bulk_create_decompress_logs(client: Client, agent_token: str) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
    logs = 'AssertionError: assert 1 == 0'
    compressed = base64.b64encode(
        zstandard.ZstdCompressor().compress(logs.encode('utf-8')),
    ).decode()

    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
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

    assert response.status_code == 201
    record = TestRecord.objects.get(label='tests/test.py::test_fail')
    assert record.decompressed_logs == logs


def test_bulk_create_single_record(client: Client, agent_token: str) -> None:
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
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

    assert response.status_code == 201
    assert response.json() == {'created': 1}


def _create_expired_token(agent: Agent) -> str:
    raw_token = token_srv.create_token_for_agent(agent)
    token_obj = ApiToken.objects.get(agent=agent)
    one_hour_ago = datetime.timedelta(hours=1)
    token_obj.expires_at = datetime.datetime.now(tz=datetime.UTC) - one_hour_ago
    token_obj.save(update_fields=['expires_at'])
    return raw_token


@pytest.mark.parametrize('field', ['branch', 'commit'])
def test_empty_branch_commit(client: Client, agent_token: str, field: str) -> None:
    record = {
        'label': 'tests/test.py::test_single',
        'timestamp': '2026-07-28T12:00:00Z',
        'logs': '',
        'success': True,
        'branch': 'fake',
        'commit': 'fake',
    }
    record[field] = ''
    response = client.post(
        '/api/v1/test_record/bulk_create/',
        content_type='application/json',
        data={
            'session_id': str(uuid.uuid4()),
            'records': [record],
        },
        HTTP_AUTHORIZATION=f'Token {agent_token}',
    )

    assert response.status_code == 400
