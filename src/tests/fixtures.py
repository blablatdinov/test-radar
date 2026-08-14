# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
import uuid

import pytest
from model_bakery import baker

from auth.models import User
from records.models import Agent, Project, TestRecord, TestSession
from records.srv import token as token_srv


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='test-password-123',  # noqa: S106
    )


@pytest.fixture
def verified_user(user: User) -> User:
    user.is_email_verified = True
    user.save(update_fields=['is_email_verified'])
    return user


@pytest.fixture
def unverified_user() -> User:
    return User.objects.create_user(
        username='unverified',
        email='unverified@example.com',
        password='test-password-123',  # noqa: S106
    )


# @todo #162:30min Create a Membership(user, project, role=OWNER) alongside
#  every baked Project in these fixtures, and add maintainer/developer
#  membership fixtures, so RBAC integration tests can reuse them.
#  Membership creation is unconditional (not gated by RBAC_ENABLED);
#  tests for new behavior use override_settings(RBAC_ENABLED=True).
@pytest.fixture
def project(user: User) -> Project:
    return baker.make(Project, name='Test project', owner=user)


@pytest.fixture
def agent(user: User, project: Project) -> Agent:
    return baker.make(
        Agent,
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
    return baker.make(
        TestSession,
        id=uuid.uuid4(),
        project=project,
        started_at=datetime.datetime.now(tz=datetime.UTC),
        os='linux',
        os_version='6.6.0',
        arch='x64',
        branch='main',
        commit_hash='abc123def456',
    )


@pytest.fixture
def test_record_pk(project: Project, test_session: TestSession) -> str:
    record = baker.make(
        TestRecord,
        label='test_file.py::test_view',
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        success=True,
        logs=b'',
        project=project,
        session=test_session,
    )

    return record.pk


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
def filled_session(project: Project) -> TestSession:
    session = baker.make(TestSession, project=project)
    records: list[TestRecord] = []
    for _ in range(15):
        records.append(baker.prepare(TestRecord, session=session, project=project))
    TestRecord.objects.bulk_create(records)
    return session


@pytest.fixture
def filled_test_history(project: Project) -> str:
    sessions = baker.make(TestSession, project=project, _quantity=15)
    records: list[TestRecord] = []
    for session in sessions:
        records.append(
            baker.prepare(
                TestRecord,
                label='test_file.py::test_view',
                session=session,
                project=project,
            ),
        )
    TestRecord.objects.bulk_create(records)
    return 'test_file.py::test_view'
