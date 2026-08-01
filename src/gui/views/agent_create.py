# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import record, token

if TYPE_CHECKING:
    from django.http import HttpResponse


class AgentCreateView(FormView):
    """Create an agent and generate an API token for it."""

    template_name = 'project.html'
    form_class = AgentForm

    def get_project(self) -> Project:
        return get_object_or_404(Project, guid=self.kwargs['guid'], owner=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        project = self.get_project()
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['sessions'] = TestSession.objects.filter(project=project)
        context['agent_form'] = kwargs.get('form') or AgentForm()
        return context

    def form_valid(self, form: AgentForm) -> HttpResponse:
        project = self.get_project()
        agent = form.save(commit=False)
        agent.project = project
        agent.owner = self.request.user
        agent.save()
        raw_token = token.create_token_for_agent(agent)
        context = self.get_context_data(form=form)
        context['new_token'] = raw_token
        context['new_agent_name'] = agent.name
        return self.render_to_response(context)

    def form_invalid(self, form: AgentForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self) -> str:
        return reverse('project_detail', kwargs={'guid': self.kwargs['guid']})
