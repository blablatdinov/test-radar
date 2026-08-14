# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, final

from django.urls import reverse_lazy
from django.views.generic import FormView

from records.forms import ProjectForm
from records.models import Membership

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
        Membership.objects.create(
            user=project.owner,
            project=project,
            role=Membership.Role.OWNER,
        )
        return super().form_valid(form)
