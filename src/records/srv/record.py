# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from django.shortcuts import get_object_or_404
from django.utils import timezone

from records.models import TestRecord, TestSession
from records.srv.flaky import detect_flaky_labels

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http.request import HttpRequest

ColIndex = dict[TestSession, int]
RecordMatrix = dict[str, dict[int, TestRecord]]
_SESSION_PARAM = 'session'


def _build_columns(col_index: ColIndex) -> list[dict[str, str]]:
    return [
        {
            'pk': str(key.pk),
            'date': key.started_at.strftime('%d.%m.%y'),
            'time': key.started_at.strftime('%H:%M'),
        }
        for key in col_index
    ]


def _build_rows(
    matrix: RecordMatrix, col_count: int, flaky_labels: set[str],
) -> list[dict[str, Any]]:
    return [
        {
            'label': label,
            'cells': [matrix[label].get(col_idx) for col_idx in range(col_count)],
            'is_flaky': any(
                cell.status == TestRecord.Status.FLAKY
                for cell in matrix[label].values()
                if cell is not None
            ),
        }
        for label in sorted(matrix)
    ]


def _index_record(record: TestRecord, col_index: ColIndex, matrix: RecordMatrix) -> None:
    if not record.session:
        return
    col_key = record.session
    if col_key not in col_index:
        col_index[col_key] = len(col_index)
    matrix[record.label][col_index[col_key]] = record


def _build_matrix(records: QuerySet[TestRecord], flaky_labels: set[str]) -> dict[str, Any]:
    col_index: ColIndex = {}
    matrix: RecordMatrix = defaultdict(dict)

    for record in records:
        _index_record(record, col_index, matrix)

    return {
        'columns': _build_columns(col_index),
        'rows': _build_rows(matrix, len(col_index), flaky_labels),
    }


def _build_filters(project_id: int, request: HttpRequest) -> dict[str, Any]:
    filters: dict[str, Any] = {'project_id': project_id}
    get = request.GET
    if get.get('datetime_from'):
        # Timezone setted in next line
        naive_dt = datetime.datetime.strptime(get['datetime_from'], '%Y-%m-%dT%H:%M')  # noqa: DTZ007
        aware_dt = timezone.make_aware(naive_dt)
        filters['timestamp__gte'] = aware_dt
    if get.get('datetime_to'):
        # Timezone setted in next line
        naive_dt = datetime.datetime.strptime(get['datetime_to'], '%Y-%m-%dT%H:%M')  # noqa: DTZ007
        aware_dt = timezone.make_aware(naive_dt)
        filters['timestamp__lte'] = aware_dt
    if get.get('agent'):
        filters['agent_id'] = get['agent']
    if get.get('branch'):
        filters['session__branch__icontains'] = get['branch']
    if get.get(_SESSION_PARAM):
        filters['session_id'] = get[_SESSION_PARAM]
    return filters


def filtered_records(project_id: int, request: HttpRequest) -> dict[str, Any]:
    records = TestRecord.objects.filter(**_build_filters(project_id, request))
    records = records.select_related('session').only(
        'id', 'label', 'success', 'status', 'session', 'session__started_at',
    ).order_by('timestamp')
    return {'records': _build_matrix(records)}


def record_by_id(record_id: str) -> dict[str, TestRecord]:
    return {'record': get_object_or_404(TestRecord, pk=record_id)}
