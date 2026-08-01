# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from records.models import TestRecord, TestSession


class SessionView(TemplateView):
    """Page with test records for a specific session."""

    template_name = 'session.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        session = get_object_or_404(
            TestSession,
            pk=kwargs['session_id'],
            project__owner=self.request.user,
        )
        records = TestRecord.objects.filter(session=session).select_related('agent').order_by('timestamp')
        return {'session': session, 'records': records}
