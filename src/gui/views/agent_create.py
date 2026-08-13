# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, final

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView

from records.forms import AgentForm
from records.models import Agent, Project, TestSession
from records.srv import record, token

if TYPE_CHECKING:
    from django.http import HttpResponse

_GUID_KWARG = 'guid'


@final
class AgentCreateView(FormView):
    """Create an agent and generate an API token for it."""

    template_name = 'project.html'
    form_class = AgentForm

    def get_project(self) -> Project:
        return get_object_or_404(Project, guid=self.kwargs[_GUID_KWARG], owner=self.request.user)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        project = self.get_project()
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = (
            Agent.objects.filter(project=project)
            .select_related('token')
            .only('id', 'name', 'type', _GUID_KWARG, 'created_at', 'token__token_mask')
        )
        context['sessions'] = TestSession.objects.filter(project=project).only('id')
        context['agent_form'] = kwargs.get('form') or AgentForm(project=project)
        return context

    def form_valid(self, form: AgentForm) -> HttpResponse:
        project = self.get_project()
        agent = form.save(commit=False)
        agent.project = project
        agent.owner = self.request.user
        agent.save()
        raw_token = token.create_token_for_agent(agent)
        self.request.session['new_token'] = raw_token
        self.request.session['new_agent_name'] = agent.name
        return redirect(self.get_success_url())

    def form_invalid(self, form: AgentForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self) -> str:
        return reverse('project_detail', kwargs={_GUID_KWARG: self.kwargs[_GUID_KWARG]})
