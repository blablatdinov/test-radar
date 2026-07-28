# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, cast

from django.views.generic import TemplateView

from auth.models import User  # noqa: TC001
from records.models import Project
from records.srv import record

# TODO #6:30min Add form for creating projects from UI


class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        user = cast('User', self.request.user)
        return {'projects': Project.objects.filter(owner=user)}


class ProjectView(TemplateView):
    """Page with test records for a specific project."""

    template_name = 'project.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        user = cast('User', self.request.user)
        project = Project.objects.get(pk=kwargs['pk'], owner=user)
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        return context


class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return record.record_by_id(kwargs['pk'])
