# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import pytest
from model_bakery import baker

from records.models import TestRecord
from records.tasks import recalculate_flaky_statuses

pytestmark = [pytest.mark.django_db]


def test_record_status_nullable() -> None:
    record = baker.make(TestRecord)
    recalculate_flaky_statuses()
    record.refresh_from_db()

    assert record.status is None
