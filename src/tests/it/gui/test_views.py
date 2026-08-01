# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from lxml import etree
from model_bakery import baker

from records.models import Project, TestRecord, TestSession

if TYPE_CHECKING:
    from django.test import Client
    from pytest_django import DjangoAssertNumQueries

    from auth.models import User

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def filled_project(user: User) -> Project:
    project = baker.make(Project, owner=user)
    sessions = baker.make(TestSession, project=project, _quantity=15)
    records: list[TestRecord] = []
    for session in sessions:
        for _ in range(5):
            records.append(baker.prepare(TestRecord, session=session, project=project))
    TestRecord.objects.bulk_create(records)
    return project


@pytest.fixture
def one_time_created_records(user: User) -> Project:
    project = baker.make(Project, owner=user)
    sessions = baker.make(TestSession, project=project, _quantity=2)
    dt = datetime.datetime(2026, 8, 1, 0, 0, 0, tzinfo=datetime.UTC)
    TestRecord.objects.bulk_create(
        [
            baker.prepare(
                TestRecord,
                session=session,
                project=project,
                timestamp=dt,
            )
            for session in sessions
        ],
    )
    return project


def test_index_shows_projects(client: Client, user: User, project) -> None:  # noqa: ANN001
    client.force_login(user)

    response = client.get('/')

    assert response.status_code == 200
    assert 'Test project' in response.text
    assert response.context_data is not None
    assert response.context_data.get('projects') is not None


def test_index_no_projects(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.get('/')

    assert response.status_code == 200
    assert 'No projects yet.' in response.text


def test_project_detail_shows_records(
    client: Client,
    user: User,
    project: Project,
    test_record_pk: str,  # noqa: ANN001
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.pk}')

    assert 'test_file.py::test_view' in response.text
    assert response.status_code == 200
    assert response.context_data is not None
    assert response.context_data.get('records') is not None
    assert response.context_data['project'].pk == project.pk


def test_test_info(client: Client, user: User, test_record_pk: str) -> None:
    client.force_login(user)

    response = client.get(f'/test/{test_record_pk}')

    assert '✅' in response.text
    assert response.status_code == 200
    assert response.context_data
    assert response.context_data['record'].pk == test_record_pk


def test_index_redirects_anonymous(client: Client) -> None:
    response = client.get('/')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


def test_test_info_redirects_anonymous(client: Client, test_record_pk: str) -> None:
    response = client.get(f'/test/{test_record_pk}')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


def test_project_create_get(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.get('/project/create')

    assert response.status_code == 200
    assert 'Create project' in response.text
    assert response.context_data is not None
    assert response.context_data.get('form') is not None


def test_project_create_post(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post('/project/create', {'name': 'My new project'})

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('index_page')
    project = Project.objects.get(name='My new project')
    assert project.owner == user


def test_project_create_redirects_anonymous(client: Client) -> None:
    response = client.get('/project/create')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.n_plus_one('project_detail')
def test_project_page_not_n_plus_one(
    client: Client,
    filled_project: Project,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    user: User,
) -> None:
    client.force_login(user)
    with django_assert_max_num_queries(6):
        response = client.get(f'/project/{filled_project.id}')

    assert response.status_code == 200, response.headers


@pytest.mark.n_plus_one('index_page')
def test_index_page_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    user: User,
) -> None:
    baker.make(Project, owner=user, _quantity=15)
    client.force_login(user)
    with django_assert_max_num_queries(3):
        response = client.get('/')
        tree = etree.fromstring(response.text, etree.HTMLParser())

    assert response.status_code == 200, response.headers
    assert len(tree.xpath('//a[@data-project-link]')) == 15, 'Project list empty'


@pytest.mark.n_plus_one('test_info')
def test_test_info_not_n_plus_one(
    client: Client,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    test_record_pk: str,
    user: User,
) -> None:
    client.force_login(user)
    with django_assert_max_num_queries(3):
        response = client.get(f'/test/{test_record_pk}')

    assert response.status_code == 200


def test_template(
    client: Client,
    one_time_created_records: Project,
    user: User,
) -> None:
    client.force_login(user)
    response = client.get(f'/project/{one_time_created_records.id}')
    tree = etree.fromstring(response.text, etree.HTMLParser())

    assert response.status_code == 200
    assert len(tree.xpath('//th[@data-column-name]')) == 2
