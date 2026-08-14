# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, final

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from records.models import Agent, Project
from records.srv import permissions, token

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse


@final
class AgentTokenRegenerateView(View):
    """Regenerate the API token for an existing agent."""

    def post(self, request: Any, guid: uuid.UUID, agent_guid: uuid.UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=guid)
        if not permissions.is_project_member(request.user, project):
            raise Http404
        agent = get_object_or_404(Agent, guid=agent_guid, project=project)
        if not permissions.can_manage_agent(request.user, project, agent.type):
            msg = 'You do not have permission to manage this agent.'
            raise PermissionDenied(msg)
        raw_token = token.regenerate_token_for_agent(agent)
        request.session['new_token'] = raw_token
        request.session['new_agent_name'] = agent.name
        return redirect('project_detail', guid=guid)
