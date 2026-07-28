# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import datetime
import zlib

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from auth.models import User
from records.models import Agent, ApiToken, TestRecord
from records.srv import token as token_srv


@pytest.mark.django_db
def test_success_record_create(client: Client, user: User) -> None:
    client.force_login(user)
    timestamp = datetime.datetime.now(tz=datetime.UTC)

    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={
            'label': 'test_file.py::test_some',
            'timestamp': timestamp.isoformat(),
            'success': True,
            'logs': '',
            'branch': 'feature-1',
            'commit': 'f447b5b',
        },
    )
    json = response.json()

    assert response.status_code == 201, response.content
    assert json['label'] == 'test_file.py::test_some'
    assert json['timestamp'] == timestamp.isoformat().replace('+00:00', 'Z')
    assert json['success']


@pytest.mark.django_db
def test_failed_record_create(client: Client, user: User) -> None:
    client.force_login(user)
    timestamp = datetime.datetime.now(tz=datetime.UTC)
    logs = '\n'.join(
        [
            '   def test_some() -> None:',
            '>      assert 1 == 0',
            'E      assert 1 == 0',
        ],
    )

    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={
            'label': 'test_file.py::test_some',
            'timestamp': timestamp.isoformat(),
            'success': False,
            'logs': base64.b64encode(zlib.compress(logs.encode('utf-8'))).decode('utf-8'),
            'branch': 'feature-1',
            'commit': 'f447b5b',
        },
    )
    json = response.json()

    assert response.status_code == 201, response.content
    assert json['label'] == 'test_file.py::test_some'
    assert json['timestamp'] == timestamp.isoformat().replace('+00:00', 'Z')
    assert not json['success']
    assert zlib.decompress(
        base64.b64decode(json['logs']),
    ).decode('utf-8') == logs


@pytest.mark.django_db
def test_create_unauthorized(client: Client) -> None:
    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={},
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_agent_token_auth_creates_record(
    client: Client, agent: Agent, agent_token: str,
) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC)
    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {agent_token}',
        data={
            'label': 'test_file.py::test_via_agent',
            'timestamp': timestamp.isoformat(),
            'success': True,
            'logs': '',
            'branch': 'main',
            'commit': 'abc123',
        },
    )

    assert response.status_code == 201, response.content
    record = TestRecord.objects.get(label='test_file.py::test_via_agent')
    assert record.agent == agent
    assert record.project == agent.project


@pytest.mark.django_db
def test_agent_token_invalid_returns_unauthorized(client: Client) -> None:
    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        HTTP_AUTHORIZATION='Token ci_invalid_token',
        data={},
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_agent_token_auth_updates_last_used(
    client: Client, agent: Agent, agent_token: str,
) -> None:
    token_obj = ApiToken.objects.get(agent=agent)
    assert token_obj.last_used_at is None

    timestamp = datetime.datetime.now(tz=datetime.UTC)
    client.post(
        reverse('api_create_test'),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {agent_token}',
        data={
            'label': 'test_file.py::test_last_used',
            'timestamp': timestamp.isoformat(),
            'success': True,
            'logs': '',
            'branch': 'main',
            'commit': 'abc123',
        },
    )

    token_obj.refresh_from_db()
    assert token_obj.last_used_at is not None
    assert timezone.is_aware(token_obj.last_used_at)


@pytest.mark.django_db
def test_expired_token_rejected(client: Client, agent: Agent) -> None:
    raw_token = token_srv.create_token_for_agent(agent)
    token_obj = ApiToken.objects.get(agent=agent)
    now = datetime.datetime.now(tz=datetime.UTC)
    token_obj.expires_at = now - datetime.timedelta(hours=1)
    token_obj.save(update_fields=['expires_at'])

    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {raw_token}',
        data={},
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_no_credentials_returns_unauthorized(client: Client) -> None:
    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={},
    )

    assert response.status_code == 401
