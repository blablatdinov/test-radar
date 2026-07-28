# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import pytest
from django.test import Client
from django.urls import reverse

from auth.models import User
from records.models import Agent, ApiToken, Project
from records.srv import token as token_srv


@pytest.mark.django_db
def test_project_detail_shows_agents_section(client: Client, user: User, project: Project) -> None:
    client.force_login(user)

    response = client.get(reverse('project_detail', kwargs={'pk': project.pk}))

    assert response.status_code == 200
    assert 'Agents' in response.text
    assert 'No agents yet.' in response.text
    assert response.context_data is not None
    assert response.context_data.get('agent_form') is not None


@pytest.mark.django_db
def test_agent_create_creates_agent_and_token(  # noqa: WPS218
    client: Client, user: User, project: Project,  # noqa: ARG001
) -> None:
    client.force_login(user)

    response = client.post(
        reverse('agent_create', kwargs={'pk': project.pk}),
        {'name': 'CI Pipeline', 'type': 'ci'},
    )

    assert response.status_code == 200
    agent = Agent.objects.get(name='CI Pipeline')
    assert agent.type == 'ci'
    assert agent.project == project
    assert agent.owner == user
    assert hasattr(agent, 'token')
    context = response.context_data
    assert context is not None
    new_token = context.get('new_token')
    assert new_token is not None
    assert new_token.startswith('ci_')


@pytest.mark.django_db
def test_agent_shows_plain_token_once(  # noqa: WPS218
    client: Client, user: User, project: Project,  # noqa: ARG001
) -> None:
    client.force_login(user)

    response = client.post(
        reverse('agent_create', kwargs={'pk': project.pk}),
        {'name': 'Dev Laptop', 'type': 'local'},
    )

    assert response.status_code == 200
    context = response.context_data
    assert context is not None
    new_token = context['new_token']
    assert new_token.startswith('dev_')
    assert 'save it now' in response.text

    response2 = client.get(reverse('project_detail', kwargs={'pk': project.pk}))
    assert response2.context_data is not None
    assert response2.context_data.get('new_token') is None


@pytest.mark.django_db
def test_agent_token_mask_stored_not_plain(
    client: Client, user: User, project: Project,  # noqa: ARG001
) -> None:
    client.force_login(user)

    response = client.post(
        reverse('agent_create', kwargs={'pk': project.pk}),
        {'name': 'CI Pipeline', 'type': 'ci'},
    )

    context = response.context_data
    assert context is not None
    plain_token = context['new_token']
    agent = Agent.objects.get(name='CI Pipeline')
    assert agent.token.token_hash != plain_token
    assert agent.token.token_mask in response.text
    assert plain_token not in agent.token.token_hash


@pytest.mark.django_db
def test_project_detail_lists_existing_agents(
    client: Client, user: User, project: Project,  # noqa: ARG001
) -> None:
    agent = Agent.objects.create(
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    ApiToken.objects.create(
        agent=agent,
        token_hash='$2b$12$somehash',  # noqa: S106
        token_mask='ci_a8f...',  # noqa: S106
    )
    client.force_login(user)

    response = client.get(reverse('project_detail', kwargs={'pk': project.pk}))

    assert response.status_code == 200
    assert 'CI Pipeline' in response.text
    assert 'ci_a8f...' in response.text
    assert 'No agents yet.' not in response.text


@pytest.mark.django_db
def test_agent_create_invalid_data(client: Client, user: User, project: Project) -> None:
    client.force_login(user)

    response = client.post(
        reverse('agent_create', kwargs={'pk': project.pk}),
        {'name': '', 'type': 'ci'},
    )

    assert response.status_code == 200
    assert Agent.objects.count() == 0


@pytest.mark.django_db
def test_agent_create_redirects_anonymous(client: Client, project: Project) -> None:
    response = client.get(reverse('agent_create', kwargs={'pk': project.pk}))

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.django_db
def test_token_verify_roundtrip(client: Client, user: User, project: Project) -> None:  # noqa: ARG001
    agent = Agent.objects.create(
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    raw = token_srv.create_token_for_agent(agent)

    verified = token_srv.verify_token(raw)
    assert verified is not None
    assert verified.agent == agent

    invalid = token_srv.verify_token('ci_invalid_token_here')
    assert invalid is None
