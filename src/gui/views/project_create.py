# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, final

from django.urls import reverse_lazy
from django.views.generic import FormView

from records.forms import ProjectForm

if TYPE_CHECKING:
    from django.http import HttpResponse


@final
class ProjectCreateView(FormView):
    """Form page for creating a new project."""

    template_name = 'project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('index_page')

    def form_valid(self, form: ProjectForm) -> HttpResponse:
        project = form.save(commit=False)
        project.owner = self.request.user
        project.save()
        # @todo #162:30min Create a Membership(user=self.request.user,
        #  project=project, role=Membership.Role.OWNER) here so project
        #  creators become members. Keep Project.owner assignment until the
        #  owner-field cleanup puzzle is done.
        return super().form_valid(form)
