# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import record

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse


class AgentDeleteView(View):
    """Delete an agent together with its API token."""

    def post(self, request: Any, guid: uuid.UUID, agent_guid: uuid.UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=guid, owner=request.user)
        agent = get_object_or_404(Agent, guid=agent_guid, project=project, owner=request.user)
        agent.delete()
        context = record.filtered_records(project.pk, request)
        context['project'] = project
        context['agents'] = (
            Agent.objects.filter(project=project)
            .select_related('token')
            .only('id', 'name', 'type', 'guid', 'created_at', 'token__token_mask')
        )
        context['sessions'] = TestSession.objects.filter(project=project).only('id')
        context['agent_form'] = AgentForm()
        return render(request, 'project.html', context)