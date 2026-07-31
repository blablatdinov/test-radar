# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django import DjangoAssertNumQueries

from auth.models import User
from records.models import Project, TestRecord, TestSession


@pytest.fixture
def filled_project(user: User) -> Project:
    project = baker.make(Project, owner=user)
    sessions = baker.make(TestSession, project=project, _quantity=15)
    records = []
    for session in sessions:
        records.extend([
            baker.prepare(TestRecord, session=session, project=project)
            for _ in range(5)
        ])
    TestRecord.objects.bulk_create(records)
    return project


@pytest.mark.django_db
def test_index_shows_projects(client: Client, user: User, project) -> None:  # noqa: ANN001
    client.force_login(user)

    response = client.get('/')

    assert response.status_code == 200
    assert 'Test project' in response.text
    assert response.context_data is not None
    assert response.context_data.get('projects') is not None


@pytest.mark.django_db
def test_index_no_projects(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.get('/')

    assert response.status_code == 200
    assert 'No projects yet.' in response.text


@pytest.mark.django_db
def test_project_detail_shows_records(
    client: Client, user: User, project, test_record_pk: str,  # noqa: ANN001
) -> None:
    client.force_login(user)

    response = client.get(f'/project/{project.pk}')

    assert 'test_file.py::test_view' in response.text
    assert response.status_code == 200
    assert response.context_data is not None
    assert response.context_data.get('records') is not None
    assert response.context_data['project'].pk == project.pk


@pytest.mark.django_db
def test_test_info(client: Client, user: User, test_record_pk: str) -> None:
    client.force_login(user)

    response = client.get(f'/test/{test_record_pk}')

    assert '✅' in response.text
    assert response.status_code == 200
    assert response.context_data
    assert response.context_data['record'].pk == test_record_pk


@pytest.mark.django_db
def test_index_redirects_anonymous(client: Client) -> None:
    response = client.get('/')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.django_db
def test_test_info_redirects_anonymous(client: Client, test_record_pk: str) -> None:
    response = client.get(f'/test/{test_record_pk}')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.django_db
def test_project_create_get(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.get('/project/create')

    assert response.status_code == 200
    assert 'Create project' in response.text
    assert response.context_data is not None
    assert response.context_data.get('form') is not None


@pytest.mark.django_db
def test_project_create_post(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post('/project/create', {'name': 'My new project'})

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('index_page')
    project = Project.objects.get(name='My new project')
    assert project.owner == user


@pytest.mark.django_db
def test_project_create_redirects_anonymous(client: Client) -> None:
    response = client.get('/project/create')

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.django_db
@pytest.mark.skip
# TODO: #70:30min Optimize gui.views.ProjectView
def test_project_page_not_n_plus_one(
    client: Client,
    filled_project: Project,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    user: User,
) -> None:
    client.force_login(user)
    with django_assert_max_num_queries(1):
        response = client.get(f'/project/{filled_project.id}')

    assert response.status_code == 200, response.headers
