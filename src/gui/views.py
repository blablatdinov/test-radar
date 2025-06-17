from typing import Any

from django.views.generic import TemplateView
from records.srv import record


class IndexView(TemplateView):
    """Index page of Test Radar."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        return record.filtered_records(self.request)


class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return record.record_by_id(kwargs['pk'])
