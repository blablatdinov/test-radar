# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, Final

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView, View

from records.forms import AgentForm, ProjectForm
from records.models import Agent, Project, TestRecord, TestSession
from records.srv import record, token

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse

_GUID: Final = 'guid'
_AGENT_GUID: Final = 'agent_guid'
_SESSION_ID: Final = 'session_id'
_LABEL: Final = 'label'
_AUTH_REQUIRED_MSG: Final = 'User must be authorized.'
_PROJECT_KEY: Final = 'project'


class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        if not self.request.user.is_authenticated:
            msg = _AUTH_REQUIRED_MSG
            raise PermissionDenied(msg)
        return {'projects': Project.objects.filter(owner=self.request.user)}


class ProjectCreateView(FormView):
    """Form page for creating a new project."""

    template_name = 'project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('index_page')

    def form_valid(self, form: ProjectForm) -> HttpResponse:
        project = form.save(commit=False)
        project.owner = self.request.user
        project.save()
        return super().form_valid(form)


class ProjectView(TemplateView):
    """Page with test records for a specific project."""

    template_name = 'project.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = _AUTH_REQUIRED_MSG
            raise PermissionDenied(msg)
        project = Project.objects.get(guid=kwargs[_GUID], owner=self.request.user)
        context = record.filtered_records(project.pk, self.request)
        context[_PROJECT_KEY] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['sessions'] = TestSession.objects.filter(project=project)
        context['agent_form'] = AgentForm()
        return context


class AgentCreateView(FormView):
    """Create an agent and generate an API token for it."""

    template_name = 'project.html'
    form_class = AgentForm

    def get_project(self) -> Project:
        return get_object_or_404(Project, guid=self.kwargs[_GUID], owner=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        project = self.get_project()
        context = record.filtered_records(project.pk, self.request)
        context[_PROJECT_KEY] = project
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
        return reverse('project_detail', kwargs={_GUID: self.kwargs[_GUID]})


class AgentTokenRegenerateView(View):
    """Regenerate the API token for an existing agent."""

    def post(self, request: Any, guid: uuid.UUID, agent_guid: uuid.UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            msg = _AUTH_REQUIRED_MSG
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=guid, owner=request.user)
        agent = get_object_or_404(Agent, guid=agent_guid, project=project, owner=request.user)
        raw_token = token.regenerate_token_for_agent(agent)
        context = record.filtered_records(project.pk, request)
        context[_PROJECT_KEY] = project
        context['agents'] = Agent.objects.filter(project=project).select_related('token')
        context['sessions'] = TestSession.objects.filter(project=project)
        context['agent_form'] = AgentForm()
        context['new_token'] = raw_token
        context['new_agent_name'] = agent.name
        return render(request, 'project.html', context)


class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return record.record_by_id(kwargs['pk'])


class SessionView(TemplateView):
    """Page with test records for a specific session."""

    template_name = 'session.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = _AUTH_REQUIRED_MSG
            raise PermissionDenied(msg)
        session = get_object_or_404(
            TestSession,
            pk=kwargs[_SESSION_ID],
            project__owner=self.request.user,
        )
        records = TestRecord.objects.filter(session=session).select_related('agent').order_by('timestamp')
        return {'session': session, 'records': records}


class TestHistoryView(TemplateView):
    """Page with all runs of a specific test across sessions."""

    template_name = 'test_history.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = _AUTH_REQUIRED_MSG
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=kwargs[_GUID], owner=self.request.user)
        label = self.request.GET.get(_LABEL, '')
        records = (
            TestRecord.objects.filter(project=project, label=label)
            .select_related('session', 'agent')
            .order_by('-timestamp')
        )
        return {'project': project, 'label': label, 'records': records}
