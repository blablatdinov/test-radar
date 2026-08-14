# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.http import Http404
from django.views.generic import TemplateView

from records.srv import permissions, record


@final
class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = record.record_by_id(kwargs['pk'])
        project = context['record'].project
        if project is None or not permissions.is_project_member(self.request.user, project):
            raise Http404
        return context
