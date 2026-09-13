# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.db.models import Max
from django.views.generic import TemplateView

from records.srv import permissions


@final
class IndexView(TemplateView):
    """Index page of Test Radar — shows list of user projects."""

    template_name = 'index.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        projects = permissions.projects_for(self.request.user).annotate(
            last_update=Max('records__timestamp'),
        )
        return {'projects': projects.only('guid', 'name', 'created_at')}
