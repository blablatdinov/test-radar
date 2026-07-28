# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime

import pytest

from auth.models import User
from records.models import Project, TestRecord


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username='testuser', password='test-password-123')  # noqa: S106


@pytest.fixture
def project(user: User) -> Project:
    # TODO #19:30min Use model_bakery for generate records
    return Project.objects.create(name='Test project', owner=user)


@pytest.fixture
def test_record_pk(project: Project) -> str:
    record = TestRecord.objects.create(
        label='test_file.py::test_view',
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        success=True,
        logs='',
        project=project,
    )

    return record.pk
