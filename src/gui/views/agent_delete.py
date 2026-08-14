# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, final

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import permissions, record

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse


@final
class AgentDeleteView(View):
    """Delete an agent together with its API token."""

    def post(self, request: Any, guid: uuid.UUID, agent_guid: uuid.UUID) -> HttpResponse:
        project = get_object_or_404(Project, guid=guid)
        if not permissions.is_project_member(request.user, project):
            raise Http404
        agent = get_object_or_404(Agent, guid=agent_guid, project=project)
        if not permissions.can_delete_agent(request.user, agent):
            msg = 'You do not have permission to delete this agent.'
            raise PermissionDenied(msg)
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
        return redirect('project_detail', guid=project.guid)
