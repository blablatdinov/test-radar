# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

# @todo #162:30min Add RBAC integration tests for the full permission matrix:
#  Developer gets 403 on CI agent create/regenerate/delete, 302 on LOCAL
#  create/regenerate and on deleting own LOCAL agent, 403 on deleting someone
#  else's LOCAL agent; Maintainer gets 302 for both agent types; non-member
#  gets 404. Run each case with override_settings(RBAC_ENABLED=True) and also
#  verify legacy behavior with the flag off. Depends on the permissions
#  service and membership fixtures puzzles.

from typing import TYPE_CHECKING

import pytest
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker

from auth.models import User
from records.models import Agent, ApiToken, Project
from records.srv import token as token_srv

if TYPE_CHECKING:
    from django.test import Client
    from pytest_django import DjangoAssertNumQueries

pytestmark = [
    pytest.mark.django_db,
]


def test_project_detail_shows_agents_section(client: Client, user: User, project: Project) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'Agents' in response.text
    assert 'No agents yet.' in response.text
    assert response.context_data is not None
    assert response.context_data.get('agent_form') is not None


@pytest.mark.usefixtures('user', 'project')
def test_agent_create_creates_agent(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_create', kwargs={'guid': Project.objects.get().guid}),
        {'name': 'CI Pipeline', 'type': 'ci'},
    )

    assert response.status_code == 302
    agent = Agent.objects.get(name='CI Pipeline')
    assert agent.type == 'ci'
    assert agent.project == Project.objects.get()
    assert agent.owner == User.objects.get(username='testuser')
    assert hasattr(agent, 'token')


@pytest.mark.usefixtures('user', 'project')
def test_agent_create_redirects_to_project(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))
    project_guid = Project.objects.get().guid

    response = client.post(
        reverse('agent_create', kwargs={'guid': project_guid}),
        {'name': 'CI Pipeline', 'type': 'ci'},
    )

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('project_detail', kwargs={'guid': project_guid})


@pytest.mark.usefixtures('user', 'project')
def test_agent_create_returns_plain_token(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_create', kwargs={'guid': Project.objects.get().guid}),
        {'name': 'CI Pipeline', 'type': 'ci'},
        follow=True,
    )

    context = response.context_data
    assert context is not None
    new_token = context.get('new_token')
    assert new_token is not None
    assert new_token.startswith('ci_')


@pytest.mark.usefixtures('user', 'project')
def test_agent_shows_plain_token_once(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_create', kwargs={'guid': Project.objects.get().guid}),
        {'name': 'Dev Laptop', 'type': 'local'},
        follow=True,
    )

    assert response.status_code == 200
    context = response.context_data
    assert context is not None
    new_token = context['new_token']
    assert new_token.startswith('dev_')


@pytest.mark.usefixtures('user', 'project')
def test_agent_token_shown_with_warning(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_create', kwargs={'guid': Project.objects.get().guid}),
        {'name': 'Dev Laptop', 'type': 'local'},
        follow=True,
    )

    assert 'save it now' in response.text


@pytest.mark.usefixtures('user', 'project')
def test_project_view_no_token_after_creation(client: Client) -> None:
    client.force_login(User.objects.get(username='testuser'))

    creation_response = client.post(
        reverse('agent_create', kwargs={'guid': Project.objects.get().guid}),
        {'name': 'Dev Laptop', 'type': 'local'},
        follow=True,
    )
    assert creation_response.context_data
    assert creation_response.context_data.get('new_token') is not None

    project_guid = Project.objects.get().guid
    response2 = client.get(reverse('project_detail', kwargs={'guid': project_guid}))
    assert response2.context_data is not None
    assert response2.context_data.get('new_token') is None


@pytest.mark.usefixtures('user')
def test_agent_token_mask_stored_not_plain(client: Client, project: Project) -> None:
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_create', kwargs={'guid': project.guid}),
        {'name': 'CI Pipeline', 'type': 'ci'},
        follow=True,
    )

    context = response.context_data
    assert context is not None
    plain_token = context['new_token']
    agent = Agent.objects.get(name='CI Pipeline')
    assert agent.token.token_hash != plain_token
    assert agent.token.token_mask in response.text
    assert plain_token not in agent.token.token_hash


@pytest.mark.usefixtures('user')
def test_project_detail_lists_existing_agents(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    baker.make(
        ApiToken,
        agent=agent,
        token_hash='$2b$12$somehash',
        token_mask='ci_a8f...',
    )
    client.force_login(User.objects.get(username='testuser'))

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'CI Pipeline' in response.text
    assert 'ci_a8f...' in response.text
    assert 'No agents yet.' not in response.text


def test_agent_create_invalid_data(client: Client, user: User, project: Project) -> None:
    client.force_login(user)

    response = client.post(
        reverse('agent_create', kwargs={'guid': project.guid}),
        {'name': '', 'type': 'ci'},
    )

    assert response.status_code == 200
    assert Agent.objects.count() == 0


def test_agent_create_redirects_anonymous(client: Client, project: Project) -> None:
    response = client.get(f'/project/{project.guid}/agent/create')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


def test_agent_create_forbidden_for_outsider(
    client: Client,
    outsider_user: User,
    project: Project,
) -> None:
    client.force_login(outsider_user)

    response = client.get(reverse('agent_create', kwargs={'guid': project.guid}))

    assert response.status_code == 404


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_agent_create_local_allowed_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
) -> None:
    client.force_login(developer_user)

    response = client.post(
        reverse('agent_create', kwargs={'guid': project.guid}),
        {'name': 'Local Dev', 'type': 'local'},
    )

    assert response.status_code == 302


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_agent_create_ci_forbidden_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
) -> None:
    client.force_login(developer_user)

    response = client.post(
        reverse('agent_create', kwargs={'guid': project.guid}),
        {'name': 'CI Pipeline', 'type': 'ci'},
    )

    assert response.status_code == 403
    assert Agent.objects.count() == 0


@pytest.mark.usefixtures('user')
def test_token_verify_roundtrip(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    raw = token_srv.create_token_for_agent(agent)

    verified = token_srv.verify_token(raw)
    assert verified is not None
    assert verified.agent == agent

    invalid = token_srv.verify_token('ci_invalid_token_here')
    assert invalid is None


@pytest.mark.usefixtures('user')
def test_regenerate_token_creates_new_token(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    old_raw = token_srv.create_token_for_agent(agent)
    old_mask = agent.token.token_mask
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_token_regenerate', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
        follow=True,
    )
    new_raw = response.context['new_token']

    assert response.status_code == 200
    assert new_raw != old_raw
    assert new_raw.startswith('ci_')
    agent.refresh_from_db()
    assert agent.token.token_mask != old_mask


@pytest.mark.usefixtures('user')
def test_regenerate_token_shows_new_mask(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        f'/project/{project.guid}/agents/{agent.guid}/regenerate-token',
        follow=True,
    )

    agent.refresh_from_db()

    assert response.status_code == 200
    assert agent.token.token_mask in response.content.decode()


@pytest.mark.usefixtures('user')
def test_regenerate_token_old_token_invalid(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    old_raw = token_srv.create_token_for_agent(agent)
    client.force_login(User.objects.get(username='testuser'))

    client.post(
        f'/project/{project.guid}/agents/{agent.guid}/regenerate-token',
    )

    assert token_srv.verify_token(old_raw) is None


@pytest.mark.usefixtures('user')
def test_regenerate_token_redirects_anonymous(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    token_srv.create_token_for_agent(agent)

    response = client.post(
        f'project/{project.guid}/agents/{agent.guid}/regenerate-token',
    )

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


def test_regenerate_token_forbidden_for_outsider(
    client: Client,
    user: User,
    project: Project,
) -> None:
    other = baker.make(User, username='other', password='x')
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(other)

    response = client.post(
        f'project/{project.guid}/agents/{agent.guid}/regenerate-token',
    )

    assert response.status_code == 404


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_regenerate_ci_token_denied_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(developer_user)

    response = client.post(
        reverse(
            'agent_token_regenerate',
            kwargs={'guid': project.guid, 'agent_guid': agent.guid},
        ),
    )

    assert response.status_code == 403


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_regenerate_local_token_ok_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='Dev Laptop',
        type='local',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(developer_user)

    response = client.post(
        reverse(
            'agent_token_regenerate',
            kwargs={'guid': project.guid, 'agent_guid': agent.guid},
        ),
    )

    assert response.status_code == 302


@pytest.mark.n_plus_one('agent_create')
def test_agent_create_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    filled_project: Project,
    user: User,
) -> None:
    client.force_login(user)
    with django_assert_max_num_queries(10):
        response = client.post(
            reverse('agent_create', kwargs={'guid': filled_project.guid}),
            {'name': 'CI Pipeline', 'type': 'ci'},
        )

    assert response.status_code == 302, response.headers


@pytest.mark.n_plus_one('agent_token_regenerate')
def test_agent_token_regenerate_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    filled_project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=filled_project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(user)
    with django_assert_max_num_queries(11):
        response = client.post(
            reverse(
                'agent_token_regenerate',
                kwargs={'guid': filled_project.guid, 'agent_guid': agent.guid},
            ),
        )

    assert response.status_code == 302, response.headers


def test_delete_agent_removes_agent(client: Client, project: Project) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=User.objects.get(username='testuser'),
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(User.objects.get(username='testuser'))

    response = client.post(
        reverse('agent_delete', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
    )

    assert response.status_code == 302
    assert not Agent.objects.filter(pk=agent.pk).exists()


def test_delete_agent_forbidden_for_outsider(
    client: Client,
    outsider_user: User,
    project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(outsider_user)

    response = client.post(
        reverse('agent_delete', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
    )

    assert response.status_code == 404


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_delete_ci_agent_denied_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(developer_user)

    response = client.post(
        reverse('agent_delete', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
    )

    assert response.status_code == 403
    assert Agent.objects.filter(pk=agent.pk).exists()


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_delete_own_local_agent_ok_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
) -> None:
    agent = baker.make(
        Agent,
        name='Dev Laptop',
        type='local',
        project=project,
        owner=developer_user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(developer_user)

    response = client.post(
        reverse('agent_delete', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
    )

    assert response.status_code == 302
    assert not Agent.objects.filter(pk=agent.pk).exists()


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_delete_foreign_local_denied_dev(
    client: Client,
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='Dev Laptop',
        type='local',
        project=project,
        owner=user,
    )
    token_srv.create_token_for_agent(agent)
    client.force_login(developer_user)

    response = client.post(
        reverse('agent_delete', kwargs={'guid': project.guid, 'agent_guid': agent.guid}),
    )

    assert response.status_code == 403
    assert Agent.objects.filter(pk=agent.pk).exists()


@pytest.mark.usefixtures('user')
def test_uniq_agent_name(client: Client, project: Project) -> None:
    client.force_login(User.objects.get(username='testuser'))
    name = 'github-ci'
    baker.make(Agent, name=name, project=project)

    response = client.post(
        reverse('agent_create', kwargs={'guid': project.guid}),
        {'name': name, 'type': 'ci'},
    )

    assert response.status_code == 200
    assert Agent.objects.filter(name=name, project=project).count() == 1


@pytest.mark.n_plus_one('agent_delete')
def test_agent_delete_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    filled_project: Project,
    user: User,
) -> None:
    agent = baker.make(
        Agent,
        name='CI Pipeline',
        type='ci',
        project=filled_project,
        owner=user,
    )
    client.force_login(user)
    with django_assert_max_num_queries(9):
        response = client.post(
            reverse(
                'agent_delete',
                kwargs={'guid': filled_project.guid, 'agent_guid': agent.guid},
            ),
        )

    assert response.status_code == 302, response.headers
