# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from records.models import Project


@final
class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        # @todo #162:30min Filter projects via Membership using
        #  records/srv/permissions.is_project_member (or a projects_for(user)
        #  queryset helper) instead of the owner filter. Part of the read-views
        #  RBAC migration together with project.py, session.py, test_history.py,
        #  test_info.py. Covered by puzzle for unit tests of permissions service.
        projects = Project.objects.filter(owner=self.request.user)
        return {'projects': projects.only('guid', 'name', 'created_at')}
