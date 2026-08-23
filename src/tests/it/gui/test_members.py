# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING

import pytest
from django.test import override_settings
from django.urls import reverse
from lxml import etree
from model_bakery import baker

from auth.models import User
from records.models import Membership, Project

if TYPE_CHECKING:
    from django.test import Client
    from pytest_django import DjangoAssertNumQueries

pytestmark = [
    pytest.mark.django_db,
]


@override_settings(RBAC_ENABLED=True)
def test_owner_sees_members_section(client: Client, user: User, project: Project) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'Members' in response.text
    assert 'Add member' in response.text
    assert response.context_data is not None
    assert response.context_data.get('can_manage_members') is True


@override_settings(RBAC_ENABLED=True)
def test_members_list_shows_all_members(
    client: Client,
    user: User,
    project: Project,
    maintainer_membership: Membership,
    developer_membership: Membership,
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'testuser' in response.text
    assert 'maintainer' in response.text
    assert 'developer' in response.text


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_developer_no_member_management(
    client: Client,
    developer_user: User,
    project: Project,
) -> None:
    client.force_login(developer_user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'Members' in response.text
    assert 'Add member' not in response.text
    assert response.context_data is not None
    assert response.context_data.get('can_manage_members') is False


@override_settings(RBAC_ENABLED=False)
def test_members_hidden_no_rbac(
    client: Client,
    user: User,
    project: Project,
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    assert 'Members' not in response.text


@override_settings(RBAC_ENABLED=True)
def test_member_add_by_username(
    client: Client,
    user: User,
    project: Project,
    developer_user: User,
) -> None:
    client.force_login(user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'developer', 'role': 'developer'},
    )

    assert response.status_code == 302
    assert Membership.objects.filter(user=developer_user, project=project).exists()


@override_settings(RBAC_ENABLED=True)
def test_member_add_by_email(
    client: Client,
    user: User,
    project: Project,
    developer_user: User,
) -> None:
    client.force_login(user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'developer@example.com', 'role': 'maintainer'},
    )

    assert response.status_code == 302
    membership = Membership.objects.get(user=developer_user, project=project)
    assert membership.role == Membership.Role.MAINTAINER


@override_settings(RBAC_ENABLED=True)
def test_member_add_already_member(
    client: Client,
    user: User,
    project: Project,
    maintainer_membership: Membership,
) -> None:
    client.force_login(user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'maintainer', 'role': 'developer'},
    )

    assert response.status_code == 200
    assert 'already a member' in response.text


@override_settings(RBAC_ENABLED=True)
def test_member_add_nonexistent_user(
    client: Client,
    user: User,
    project: Project,
) -> None:
    client.force_login(user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'ghost', 'role': 'developer'},
    )

    assert response.status_code == 200
    assert 'User not found' in response.text


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_member_add_forbidden_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
    outsider_user: User,
) -> None:
    client.force_login(developer_user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'outsider', 'role': 'developer'},
    )

    assert response.status_code == 403


def test_member_add_forbidden_for_outsider(
    client: Client,
    outsider_user: User,
    project: Project,
) -> None:
    client.force_login(outsider_user)

    response = client.post(
        f'/project/{project.guid}/members/add',
        {'identifier': 'outsider', 'role': 'developer'},
    )

    assert response.status_code == 404


def test_member_add_redirects_anonymous(client: Client, project: Project) -> None:
    response = client.get(f'/project/{project.guid}/members/add')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@override_settings(RBAC_ENABLED=True)
def test_member_remove(
    client: Client,
    user: User,
    project: Project,
    developer_membership: Membership,
) -> None:
    client.force_login(user)

    response = client.post(
        '/project/{0}/members/{1}/remove'.format(project.guid, developer_membership.user.pk),
    )

    assert response.status_code == 302
    assert not Membership.objects.filter(pk=developer_membership.pk).exists()


@override_settings(RBAC_ENABLED=True)
def test_member_remove_self_forbidden(
    client: Client,
    user: User,
    project: Project,
) -> None:
    client.force_login(user)

    response = client.post(
        f'/project/{project.guid}/members/{user.pk}/remove',
    )

    assert response.status_code == 403
    assert Membership.objects.filter(user=user, project=project).exists()


@pytest.mark.usefixtures('developer_membership')
@override_settings(RBAC_ENABLED=True)
def test_member_remove_forbidden_for_developer(
    client: Client,
    developer_user: User,
    project: Project,
    user: User,
) -> None:
    client.force_login(developer_user)

    response = client.post(
        f'/project/{project.guid}/members/{user.pk}/remove',
    )

    assert response.status_code == 403


def test_member_remove_forbidden_for_outsider(
    client: Client,
    outsider_user: User,
    project: Project,
    user: User,
) -> None:
    client.force_login(outsider_user)

    response = client.post(
        f'/project/{project.guid}/members/{user.pk}/remove',
    )

    assert response.status_code == 404


def test_member_remove_redirects_anonymous(client: Client, project: Project, user: User) -> None:
    response = client.post(f'/project/{project.guid}/members/{user.pk}/remove')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@override_settings(RBAC_ENABLED=True)
def test_member_remove_form_present_for_owner(
    client: Client,
    user: User,
    project: Project,
    developer_membership: Membership,
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    tree = etree.fromstring(response.text, etree.HTMLParser())
    assert tree.xpath('//form[contains(@action, "members") and contains(@action, "remove")]')


@override_settings(RBAC_ENABLED=True)
def test_member_remove_form_absent_for_self(
    client: Client,
    user: User,
    project: Project,
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.guid}')

    assert response.status_code == 200
    tree = etree.fromstring(response.text, etree.HTMLParser())
    remove_forms = tree.xpath('//form[contains(@action, "remove")]')
    assert len(remove_forms) == 0


@pytest.mark.n_plus_one('member_add')
@override_settings(RBAC_ENABLED=True)
def test_member_add_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    filled_project: Project,
    user: User,
) -> None:
    baker.make(User, username='extra', email='extra@example.com')
    client.force_login(user)
    with django_assert_max_num_queries(11):
        response = client.post(
            f'/project/{filled_project.guid}/members/add',
            {'identifier': 'extra', 'role': 'developer'},
        )

    assert response.status_code == 302, response.headers


@pytest.mark.n_plus_one('member_remove')
@override_settings(RBAC_ENABLED=True)
def test_member_remove_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    filled_project: Project,
    user: User,
) -> None:
    extra_user: User = baker.make(User, username='extra', email='extra@example.com')
    baker.make(Membership, user=extra_user, project=filled_project, role=Membership.Role.DEVELOPER)
    client.force_login(user)
    with django_assert_max_num_queries(7):
        response = client.post(
            f'/project/{filled_project.guid}/members/{extra_user.pk}/remove',
        )

    assert response.status_code == 302, response.headers
