from collections import defaultdict
from typing import Any

from django.views.generic import TemplateView
from records.models import TestRecord


class IndexView(TemplateView):
    """Index page of Test Radar."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        if self.request.GET.get('date'):
            records = TestRecord.objects.filter(timestamp__date__gte=self.request.GET['date'])
        else:
            records = TestRecord.objects.all()
        grouped_records = defaultdict(lambda: defaultdict(list))  # type: ignore
        for record in records:
            date = record.timestamp
            grouped_records[date.strftime('%d.%m.%Y')][date.strftime('%H:%M')].append(record)

        return {'records': {date: dict(times) for date, times in grouped_records.items()}}


class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {'record': TestRecord.objects.get(pk=kwargs['pk'])}
