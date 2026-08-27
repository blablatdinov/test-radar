# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from records.models import TestRecord, TestSession
from records.srv import permissions


@final
class SessionView(TemplateView):
    """Page with test records for a specific session."""

    template_name = 'session.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        session = get_object_or_404(
            TestSession.objects.select_related('project'),
            pk=kwargs['session_id'],
        )
        project = session.project
        if project is None or not permissions.is_project_member(self.request.user, project):
            raise Http404
        records = (
            TestRecord.objects.filter(session=session)
            .select_related('agent', 'session')
            .only(
                'id',
                'label',
                'success',
                'timestamp',
                'session',
                'session__branch',
                'session__commit_hash',
                'agent',
                'agent__name',
            )
            .order_by('timestamp')
        )
        return {'session': session, 'records': records}
