# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
import uuid

import pytest

from auth.models import User
from records.models import Agent, Project, TestRecord, TestSession
from records.srv import token as token_srv


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username='testuser', password='test-password-123')  # noqa: S106


@pytest.fixture
def project(user: User) -> Project:
    # TODO #19:30min Use model_bakery for generate records
    return Project.objects.create(name='Test project', owner=user)


@pytest.fixture
def agent(user: User, project: Project) -> Agent:
    return Agent.objects.create(
        name='CI Pipeline',
        type='ci',
        project=project,
        owner=user,
    )


@pytest.fixture
def agent_token(agent: Agent) -> str:
    return token_srv.create_token_for_agent(agent)


@pytest.fixture
def test_session(project: Project) -> TestSession:
    return TestSession.objects.create(
        id=uuid.uuid4(),
        project=project,
        started_at=datetime.datetime.now(tz=datetime.UTC),
    )


@pytest.fixture
def test_record_pk(project: Project, test_session: TestSession) -> str:
    record = TestRecord.objects.create(
        label='test_file.py::test_view',
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        success=True,
        logs='',
        project=project,
        session=test_session,
    )

    return record.pk
