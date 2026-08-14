# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from pytest_django.fixtures import Settings

from auth.models import User
from records.models import Agent, Membership, Project
from records.srv import permissions

pytestmark = pytest.mark.django_db

_CI = Agent.AgentType.CI
_LOCAL = Agent.AgentType.LOCAL


@pytest.fixture(autouse=True)
def _rbac_enabled(settings: Settings) -> None:
    settings.RBAC_ENABLED = True


@pytest.fixture
def anonymous() -> AnonymousUser:
    return AnonymousUser()


def _candidate(request: pytest.FixtureRequest, membership_fixture: str | None) -> User:
    if membership_fixture is None:
        return User.objects.get(username='testuser')
    membership: Membership = request.getfixturevalue(membership_fixture)
    return membership.user


@pytest.mark.parametrize(
    ('membership_fixture', 'expected'),
    [
        (None, Membership.Role.OWNER),
        ('maintainer_membership', Membership.Role.MAINTAINER),
        ('developer_membership', Membership.Role.DEVELOPER),
    ],
)
def test_get_role_known_roles(
    request: pytest.FixtureRequest,
    project: Project,
    membership_fixture: str | None,
    expected: Membership.Role,
) -> None:
    assert permissions.get_role(_candidate(request, membership_fixture), project) == expected


def test_get_role_outsider(outsider_user: User, project: Project) -> None:
    assert permissions.get_role(outsider_user, project) is None


def test_get_role_anonymous(anonymous: AnonymousUser, project: Project) -> None:
    assert permissions.get_role(anonymous, project) is None


@override_settings(RBAC_ENABLED=False)
def test_get_role_legacy_owner(user: User, project: Project) -> None:
    assert permissions.get_role(user, project) == Membership.Role.OWNER


@override_settings(RBAC_ENABLED=False)
@pytest.mark.usefixtures('maintainer_membership')
def test_get_role_legacy_ignores_membership(maintainer_user: User, project: Project) -> None:
    assert permissions.get_role(maintainer_user, project) is None


@pytest.mark.parametrize(
    'membership_fixture',
    [
        None,
        'maintainer_membership',
        'developer_membership',
    ],
)
def test_is_project_member_granted(
    request: pytest.FixtureRequest,
    project: Project,
    membership_fixture: str | None,
) -> None:
    assert permissions.is_project_member(_candidate(request, membership_fixture), project) is True


def test_is_project_member_denied(outsider_user: User, anonymous: AnonymousUser, project: Project) -> None:
    assert permissions.is_project_member(outsider_user, project) is False
    assert permissions.is_project_member(anonymous, project) is False


@override_settings(RBAC_ENABLED=False)
def test_is_project_member_legacy(user: User, outsider_user: User, project: Project) -> None:
    assert permissions.is_project_member(user, project) is True
    assert permissions.is_project_member(outsider_user, project) is False


@pytest.mark.usefixtures('developer_membership')
def test_projects_for_members(developer_user: User, user: User, project: Project) -> None:
    assert list(permissions.projects_for(user)) == [project]
    assert list(permissions.projects_for(developer_user)) == [project]


def test_projects_for_denied(outsider_user: User, anonymous: AnonymousUser, project: Project) -> None:
    assert list(permissions.projects_for(outsider_user)) == []
    assert list(permissions.projects_for(anonymous)) == []


@override_settings(RBAC_ENABLED=False)
def test_projects_for_legacy(user: User, outsider_user: User, developer_user: User, project: Project) -> None:
    assert list(permissions.projects_for(user)) == [project]
    assert list(permissions.projects_for(outsider_user)) == []
    assert list(permissions.projects_for(developer_user)) == []


@pytest.mark.parametrize(
    'membership_fixture',
    [
        None,
        'maintainer_membership',
    ],
)
def test_can_manage_agent_ci_granted(
    request: pytest.FixtureRequest,
    project: Project,
    membership_fixture: str | None,
) -> None:
    assert permissions.can_manage_agent(_candidate(request, membership_fixture), project, _CI) is True


def test_can_manage_agent_ci_denied(developer_membership: Membership, project: Project) -> None:
    assert permissions.can_manage_agent(developer_membership.user, project, _CI) is False


@pytest.mark.parametrize(
    'membership_fixture',
    [
        None,
        'maintainer_membership',
        'developer_membership',
    ],
)
def test_can_manage_agent_local_granted(
    request: pytest.FixtureRequest,
    project: Project,
    membership_fixture: str | None,
) -> None:
    assert permissions.can_manage_agent(_candidate(request, membership_fixture), project, _LOCAL) is True


def test_can_manage_agent_denied(outsider_user: User, anonymous: AnonymousUser, project: Project) -> None:
    assert permissions.can_manage_agent(outsider_user, project, _CI) is False
    assert permissions.can_manage_agent(outsider_user, project, _LOCAL) is False
    assert permissions.can_manage_agent(anonymous, project, _CI) is False
    assert permissions.can_manage_agent(anonymous, project, _LOCAL) is False


@override_settings(RBAC_ENABLED=False)
def test_can_manage_agent_legacy(user: User, outsider_user: User, project: Project) -> None:
    assert permissions.can_manage_agent(user, project, _CI) is True
    assert permissions.can_manage_agent(user, project, _LOCAL) is True
    assert permissions.can_manage_agent(outsider_user, project, _CI) is False
    assert permissions.can_manage_agent(outsider_user, project, _LOCAL) is False


@pytest.mark.parametrize(
    ('membership_fixture', 'agent_fixture'),
    [
        (None, 'agent'),
        (None, 'local_agent'),
        ('maintainer_membership', 'agent'),
        ('maintainer_membership', 'local_agent'),
        ('developer_membership', 'local_agent'),
    ],
)
def test_can_delete_agent_granted(
    request: pytest.FixtureRequest,
    membership_fixture: str | None,
    agent_fixture: str,
) -> None:
    agent: Agent = request.getfixturevalue(agent_fixture)

    assert permissions.can_delete_agent(_candidate(request, membership_fixture), agent) is True


def test_can_delete_agent_ci_denied_for_developer(developer_membership: Membership, agent: Agent) -> None:
    assert permissions.can_delete_agent(developer_membership.user, agent) is False


@pytest.mark.usefixtures('developer_membership')
def test_can_delete_agent_foreign_local_denied(
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    other_local_agent = Agent.objects.create(
        name='Other Laptop',
        type=_LOCAL,
        project=project,
        owner=user,
    )

    assert permissions.can_delete_agent(developer_user, other_local_agent) is False


def test_can_delete_agent_denied(
    outsider_user: User,
    anonymous: AnonymousUser,
    agent: Agent,
    local_agent: Agent,
) -> None:
    assert permissions.can_delete_agent(outsider_user, agent) is False
    assert permissions.can_delete_agent(outsider_user, local_agent) is False
    assert permissions.can_delete_agent(anonymous, local_agent) is False


@override_settings(RBAC_ENABLED=False)
def test_can_delete_agent_legacy(user: User, outsider_user: User, agent: Agent) -> None:
    assert permissions.can_delete_agent(user, agent) is True
    assert permissions.can_delete_agent(outsider_user, agent) is False


def test_can_manage_members_granted(user: User, project: Project) -> None:
    assert permissions.can_manage_members(user, project) is True


@pytest.mark.parametrize(
    'membership_fixture',
    [
        'maintainer_membership',
        'developer_membership',
    ],
)
def test_can_manage_members_denied(
    request: pytest.FixtureRequest,
    outsider_user: User,
    anonymous: AnonymousUser,
    project: Project,
    membership_fixture: str,
) -> None:
    membership: Membership = request.getfixturevalue(membership_fixture)

    assert permissions.can_manage_members(membership.user, project) is False
    assert permissions.can_manage_members(outsider_user, project) is False
    assert permissions.can_manage_members(anonymous, project) is False


@override_settings(RBAC_ENABLED=False)
def test_can_manage_members_legacy(user: User, outsider_user: User, project: Project) -> None:
    assert permissions.can_manage_members(user, project) is True
    assert permissions.can_manage_members(outsider_user, project) is False


def test_can_delete_project_granted(user: User, project: Project) -> None:
    assert permissions.can_delete_project(user, project) is True


@pytest.mark.parametrize(
    'membership_fixture',
    [
        'maintainer_membership',
        'developer_membership',
    ],
)
def test_can_delete_project_denied(
    request: pytest.FixtureRequest,
    outsider_user: User,
    anonymous: AnonymousUser,
    project: Project,
    membership_fixture: str,
) -> None:
    membership: Membership = request.getfixturevalue(membership_fixture)

    assert permissions.can_delete_project(membership.user, project) is False
    assert permissions.can_delete_project(outsider_user, project) is False
    assert permissions.can_delete_project(anonymous, project) is False


@override_settings(RBAC_ENABLED=False)
def test_can_delete_project_legacy(user: User, outsider_user: User, project: Project) -> None:
    assert permissions.can_delete_project(user, project) is True
    assert permissions.can_delete_project(outsider_user, project) is False
