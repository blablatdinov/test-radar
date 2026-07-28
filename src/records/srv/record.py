# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from collections import defaultdict
from typing import Any

from django.http.request import HttpRequest

from records.models import TestRecord


def filtered_records(project_id: int, request: HttpRequest) -> dict[str, Any]:
    if request.GET.get('date'):
        records = TestRecord.objects.filter(
            project_id=project_id,
            timestamp__date__gte=request.GET['date'],
        ).order_by('timestamp')
    else:
        records = TestRecord.objects.filter(project_id=project_id).order_by('timestamp')

    columns: list[dict[str, str]] = []
    col_index: dict[tuple[str, str], int] = {}
    labels: set[str] = set()
    matrix: dict[str, dict[int, TestRecord]] = defaultdict(dict)

    for record in records:
        date_str = record.timestamp.strftime('%d.%m.%Y')
        time_str = record.timestamp.strftime('%H:%M')
        col_key = (date_str, time_str)
        if col_key not in col_index:
            col_index[col_key] = len(columns)
            columns.append({'date': date_str, 'time': time_str})
        matrix[record.label][col_index[col_key]] = record
        labels.add(record.label)

    rows = [
        {
            'label': label,
            'cells': [matrix[label].get(i) for i in range(len(columns))],
        }
        for label in sorted(labels)
    ]

    return {'records': {'columns': columns, 'rows': rows}}


def record_by_id(record_id: str) -> dict[str, TestRecord]:
    return {'record': TestRecord.objects.get(pk=record_id)}
