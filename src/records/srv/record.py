from collections import defaultdict
from typing import Any

from django.http.request import HttpRequest

from records.models import TestRecord


def filtered_records(request: HttpRequest) -> dict[str, Any]:
    if request.GET.get('date'):
        records = TestRecord.objects.filter(timestamp__date__gte=request.GET['date'])
    else:
        records = TestRecord.objects.all()
    grouped_records = defaultdict(lambda: defaultdict(list))  # type: ignore
    for record in records:
        date = record.timestamp
        grouped_records[date.strftime('%d.%m.%Y')][date.strftime('%H:%M')].append(record)  # noqa: WPS221

    return {'records': {date: dict(times) for date, times in grouped_records.items()}}


def record_by_id(record_id: str) -> dict[str, TestRecord]:
    return {'record': TestRecord.objects.get(pk=record_id)}
