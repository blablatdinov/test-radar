# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from records.models import Agent, Project
from records.srv import token

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse


class AgentTokenRegenerateView(View):
    """Regenerate the API token for an existing agent."""

    def post(self, request: Any, guid: uuid.UUID, agent_guid: uuid.UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=guid, owner=request.user)
        agent = get_object_or_404(Agent, guid=agent_guid, project=project, owner=request.user)
        raw_token = token.regenerate_token_for_agent(agent)
        request.session['new_token'] = raw_token
        request.session['new_agent_name'] = agent.name
        return redirect('project_detail', guid=guid)
