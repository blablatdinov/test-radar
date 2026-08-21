# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from django.shortcuts import get_object_or_404
from django.utils import timezone

from records.models import TestRecord

if TYPE_CHECKING:
    from django.http.request import HttpRequest

ColIndex = dict[int, int]
SessionMeta = dict[int, datetime.datetime]
RecordCell = dict[str, Any]
RecordMatrix = dict[str, dict[int, RecordCell]]
_SESSION_PARAM = 'session'


def _build_columns(col_index: ColIndex, session_meta: SessionMeta) -> list[dict[str, str]]:
    return [
        {
            'pk': str(session_id),
            'date': session_meta[session_id].strftime('%d.%m.%y'),
            'time': session_meta[session_id].strftime('%H:%M'),
        }
        for session_id in col_index
    ]


def _build_rows(matrix: RecordMatrix, col_count: int) -> list[dict[str, Any]]:
    return [
        {
            'label': label,
            'cells': [matrix[label].get(col_idx) for col_idx in range(col_count)],
        }
        for label in sorted(matrix)
    ]


def _index_record(
    record: dict[str, Any],
    col_index: ColIndex,
    session_meta: SessionMeta,
    matrix: RecordMatrix,
) -> None:
    session_id = record['session']
    if session_id is None:
        return
    if session_id not in col_index:
        col_index[session_id] = len(col_index)
        session_meta[session_id] = record['session__started_at']
    matrix[record['label']][col_index[session_id]] = record


def _build_matrix(records: list[dict[str, Any]]) -> dict[str, Any]:
    col_index: ColIndex = {}
    session_meta: SessionMeta = {}
    matrix: RecordMatrix = defaultdict(dict)

    for record in records:
        _index_record(record, col_index, session_meta, matrix)

    return {
        'columns': _build_columns(col_index, session_meta),
        'rows': _build_rows(matrix, len(col_index)),
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
    filters = _build_filters(project_id, request)
    records = list(
        TestRecord.objects.filter(**filters)
        .values(
            'pk', 'label', 'success', 'session', 'session__started_at',
            'session__commit_hash',
        )
        .order_by('timestamp'),
    )
    return {'records': _build_matrix(records)}


def record_by_id(record_id: str) -> dict[str, TestRecord]:
    return {'record': get_object_or_404(TestRecord.objects.select_related('project'), pk=record_id)}
