# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import datetime
import zlib

import pytest
from django.test import Client
from django.urls import reverse

from auth.models import User
from records.models import Agent, Project, TestRecord
from records.srv import token as token_srv


@pytest.fixture
def agent_with_token(user: User, project: Project) -> tuple[Agent, str]:
    agent = Agent.objects.create(
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    raw_token = token_srv.create_token_for_agent(agent)
    return agent, raw_token


@pytest.mark.django_db
def test_bulk_create_success(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()

    response = client.post(
        reverse('api_bulk_create_test'),
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
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 200, response.content
    assert response.json() == {'created': 2}
    assert TestRecord.objects.count() == 2


@pytest.mark.django_db
def test_bulk_create_empty_records(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token

    response = client.post(
        reverse('api_bulk_create_test'),
        content_type='application/json',
        data={'records': []},
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 400
    assert response.json()['error'] == 'records array is empty'


@pytest.mark.django_db
def test_bulk_create_missing_records_key(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token

    response = client.post(
        reverse('api_bulk_create_test'),
        content_type='application/json',
        data={},
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 400
    assert response.json()['error'] == 'records is required'


@pytest.mark.django_db
def test_bulk_create_invalid_token(client: Client) -> None:
    response = client.post(
        reverse('api_bulk_create_test'),
        content_type='application/json',
        data={'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}]},
        HTTP_AUTHORIZATION='Token ci_invalid_token',
    )

    assert response.status_code == 401
    assert response.json()['error'] == 'Invalid token'


@pytest.mark.django_db
def test_bulk_create_missing_auth_header(client: Client) -> None:
    response = client.post(
        reverse('api_bulk_create_test'),
        content_type='application/json',
        data={'records': [{'label': 'x', 'timestamp': '2026-01-01T00:00:00Z', 'success': True, 'logs': ''}]},
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_bulk_create_record_without_label(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token

    response = client.post(
        reverse('api_bulk_create_test'),
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
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 400
    assert TestRecord.objects.count() == 0


@pytest.mark.django_db
def test_bulk_create_exceeds_limit(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token
    records = [
        {
            'label': f'tests/test.py::test_{i}',
            'timestamp': '2026-07-28T12:00:00Z',
            'success': True,
            'logs': '',
            'branch': 'main',
            'commit': 'abc123',
        }
        for i in range(501)
    ]

    response = client.post(
        reverse('api_bulk_create_test'),
        content_type='application/json',
        data={'records': records},
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 400
    assert 'limit' in response.json()['error']
    assert TestRecord.objects.count() == 0


@pytest.mark.django_db
def test_bulk_create_all_records_in_db(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    agent, raw_token = agent_with_token
    timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()

    response = client.post(
        reverse('api_bulk_create_test'),
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
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 200
    assert response.json() == {'created': 3}
    records = list(TestRecord.objects.order_by('label'))
    assert len(records) == 3
    assert records[0].label == 'tests/test_a.py::test_one'
    assert records[0].agent == agent
    assert records[1].label == 'tests/test_b.py::test_two'
    assert not records[1].success
    assert records[2].branch == ''


@pytest.mark.django_db
def test_bulk_create_atomic_on_validation_error(client: Client, agent_with_token: tuple[Agent, str]) -> None:
    _, raw_token = agent_with_token

    response = client.post(
        reverse('api_bulk_create_test'),
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
        HTTP_AUTHORIZATION=f'Token {raw_token}',
    )

    assert response.status_code == 400
    assert TestRecord.objects.count() == 0
