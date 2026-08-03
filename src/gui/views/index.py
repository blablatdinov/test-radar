# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from records.models import Project


class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        projects = Project.objects.filter(owner=self.request.user)
        return {'projects': projects.only('guid', 'name', 'created_at')}
