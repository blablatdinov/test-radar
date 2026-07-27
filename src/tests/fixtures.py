# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime

import pytest

from records.models import TestRecord


@pytest.fixture
def test_record_pk() -> str:
    record = TestRecord.objects.create(
        label='test_file.py::test_view',
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        success=True,
        logs='',
    )

    return record.pk
