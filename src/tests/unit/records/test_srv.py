# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
from unittest.mock import Mock

import pytest
from django.http import HttpRequest

from records.srv.record import filtered_records, record_by_id


@pytest.mark.django_db
def test_filtered_records(project, test_record_pk: str) -> None:  # noqa: ANN001
    request = Mock(HttpRequest)
    request.GET = {
        'date': datetime.datetime.now(tz=datetime.UTC).strftime('%Y-%m-%d'),
    }

    result = filtered_records(project.pk, request)

    assert len(result['records']['columns']) == 1
    assert len(result['records']['rows']) == 1


@pytest.mark.django_db
def test_filtered_records_no_date(project, test_record_pk: str) -> None:  # noqa: ANN001
    request = Mock(HttpRequest)
    request.GET = {}

    result = filtered_records(project.pk, request)

    assert len(result['records']['columns']) == 1
    assert len(result['records']['rows']) == 1


@pytest.mark.django_db
def test_record_by_id(test_record_pk: str) -> None:
    record = record_by_id(test_record_pk)

    assert record['record'].pk == test_record_pk
