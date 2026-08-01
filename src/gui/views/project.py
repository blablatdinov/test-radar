# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import record


class ProjectView(TemplateView):
    """Page with test records for a specific project."""

    template_name = 'project.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=kwargs['guid'], owner=self.request.user)
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['sessions'] = TestSession.objects.filter(project=project)
        context['agent_form'] = AgentForm()
        return context
