# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, Final, cast

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from records.forms import AgentForm, ProjectForm
from records.models import Agent, Project
from records.srv import record, token

if TYPE_CHECKING:
    from auth.models import User

type _CurrentUser = User
_PK: Final = 'pk'


class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        user = cast('_CurrentUser', self.request.user)
        return {'projects': Project.objects.filter(owner=user)}


class ProjectCreateView(FormView):
    """Form page for creating a new project."""

    template_name = 'project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('index_page')

    def form_valid(self, form: ProjectForm) -> HttpResponse:
        project = form.save(commit=False)
        project.owner = cast('_CurrentUser', self.request.user)
        project.save()
        return super().form_valid(form)


class ProjectView(TemplateView):
    """Page with test records for a specific project."""

    template_name = 'project.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        user = cast('_CurrentUser', self.request.user)
        project = Project.objects.get(pk=kwargs[_PK], owner=user)
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['agent_form'] = AgentForm()
        return context


class AgentCreateView(FormView):
    """Create an agent and generate an API token for it."""

    template_name = 'project.html'
    form_class = AgentForm

    def get_project(self) -> Project:
        user = cast('_CurrentUser', self.request.user)
        return get_object_or_404(Project, pk=self.kwargs[_PK], owner=user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        project = self.get_project()
        context = record.filtered_records(project.pk, self.request)
        context['project'] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['agent_form'] = kwargs.get('form') or AgentForm()
        return context

    def form_valid(self, form: AgentForm) -> HttpResponse:
        project = self.get_project()
        agent = form.save(commit=False)
        agent.project = project
        agent.owner = cast('_CurrentUser', self.request.user)
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
        return reverse('project_detail', kwargs={_PK: self.kwargs[_PK]})


class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return record.record_by_id(kwargs[_PK])
