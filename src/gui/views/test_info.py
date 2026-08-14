# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.views.generic import TemplateView

from records.srv import record


@final
class TestInfoView(TemplateView):
    """Page with information about test."""

    template_name = 'test_info.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # @todo #162:30min Add access check: currently any authenticated user
        #  can view any test record by pk. Verify membership for record.project
        #  via records/srv/permissions.is_project_member, return 404 otherwise.
        return record.record_by_id(kwargs['pk'])
