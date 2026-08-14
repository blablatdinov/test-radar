# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import record


# @todo #162:30min Add member management UI (list members, add member,
#  change role, remove member) guarded by
#  records/srv/permissions.can_manage_members (owner only). New view, form,
#  template; run makemessages/compilemessages for new strings. Separate
#  release after base RBAC stabilizes.
# @todo #162:30min Add project deletion endpoint guarded by
#  records/srv/permissions.can_delete_project (owner only). Separate release
#  after base RBAC stabilizes.
@final
class ProjectView(TemplateView):
    """Page with test records for a specific project."""

    template_name = 'project.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        # @todo #162:30min Replace owner check with
        #  records/srv/permissions.is_project_member so all project members
        #  can view dashboards.
        project = get_object_or_404(Project, guid=kwargs['guid'], owner=self.request.user)
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = (
            Agent.objects.filter(project=project)
            .select_related('token')
            .only('id', 'name', 'type', 'guid', 'created_at', 'token__token_mask')
        )
        context['sessions'] = TestSession.objects.filter(project=project).only('id')
        context['agent_form'] = AgentForm()
        context['new_token'] = self.request.session.pop('new_token', None)
        context['new_agent_name'] = self.request.session.pop('new_agent_name', None)
        return context
