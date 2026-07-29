# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from collections import defaultdict
from typing import Any

from django.db.models import QuerySet
from django.http.request import HttpRequest

from records.models import TestRecord

ColIndex = dict[tuple[str, str], int]
RecordMatrix = dict[str, dict[int, TestRecord]]


def _build_columns(col_index: ColIndex) -> list[dict[str, str]]:
    return [{'date': key[0], 'time': key[1]} for key in col_index]


def _build_rows(matrix: RecordMatrix, col_count: int) -> list[dict[str, Any]]:
    return [
        {
            'label': label,
            'cells': [matrix[label].get(col_idx) for col_idx in range(col_count)],
        }
        for label in sorted(matrix)
    ]


def _index_record(record: TestRecord, col_index: ColIndex, matrix: RecordMatrix) -> None:
    col_key = (record.timestamp.strftime('%d.%m.%Y'), record.timestamp.strftime('%H:%M'))
    if col_key not in col_index:
        col_index[col_key] = len(col_index)
    matrix[record.label][col_index[col_key]] = record


def _build_matrix(records: QuerySet[TestRecord]) -> dict[str, Any]:
    col_index: ColIndex = {}
    matrix: RecordMatrix = defaultdict(dict)

    for record in records:
        _index_record(record, col_index, matrix)

    return {
        'columns': _build_columns(col_index),
        'rows': _build_rows(matrix, len(col_index)),
    }


def _build_filters(project_id: int, request: HttpRequest) -> dict[str, Any]:
    filters: dict[str, Any] = {'project_id': project_id}
    get = request.GET
    if get.get('datetime_from'):
        filters['timestamp__gte'] = get['datetime_from']
    if get.get('datetime_to'):
        filters['timestamp__lte'] = get['datetime_to']
    if get.get('agent'):
        filters['agent_id'] = get['agent']
    if get.get('branch'):
        filters['branch__icontains'] = get['branch']
    if get.get('session'):
        filters['session_id'] = get['session']
    return filters


def filtered_records(project_id: int, request: HttpRequest) -> dict[str, Any]:
    records = (
        TestRecord.objects
        .filter(**_build_filters(project_id, request))
        .order_by('timestamp')
    )
    return {'records': _build_matrix(records)}


def record_by_id(record_id: str) -> dict[str, TestRecord]:
    return {'record': TestRecord.objects.get(pk=record_id)}
