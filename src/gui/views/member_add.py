# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, final

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView

from records.forms import AddMemberForm, AgentForm
from records.models import Agent, Membership, Project, TestSession
from records.srv import permissions, record

if TYPE_CHECKING:
    from django.http import HttpResponse

_GUID_KWARG = 'guid'


@final
class MemberAddView(FormView):
    """Add a member to a project."""

    template_name = 'project.html'
    form_class = AddMemberForm

    def get_project(self) -> Project:
        project = get_object_or_404(Project, guid=self.kwargs[_GUID_KWARG])
        if not permissions.is_project_member(self.request.user, project):
            raise Http404
        return project

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
            .only('id', 'name', 'type', 'guid', 'created_at', 'token__token_mask')
        )
        context['sessions'] = TestSession.objects.filter(project=project).only('id')
        context['agent_form'] = kwargs.get('agent_form') or AgentForm()
        context['member_form'] = kwargs.get('form') or AddMemberForm(project=project)
        context['members'] = (
            Membership.objects.filter(project=project)
            .select_related('user')
            .order_by('created_at')
        )
        context['can_manage_members'] = permissions.can_manage_members(self.request.user, project)
        return context

    def form_valid(self, form: AddMemberForm) -> HttpResponse:
        project = self.get_project()
        if not permissions.can_manage_members(self.request.user, project):
            msg = 'You do not have permission to manage members.'
            raise PermissionDenied(msg)
        Membership.objects.create(
            user=form.cleaned_data['user'],
            project=project,
            role=form.cleaned_data['role'],
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form: AddMemberForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self) -> str:
        return reverse('project_detail', kwargs={_GUID_KWARG: self.kwargs[_GUID_KWARG]})
