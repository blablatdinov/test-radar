# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from records.models import Project, TestRecord
from records.srv import permissions


@final
class TestHistoryView(TemplateView):
    """Page with all runs of a specific test across sessions."""

    template_name = 'test_history.html'
    __test__ = False

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if not self.request.user.is_authenticated:
            msg = 'User must be authorized.'
            raise PermissionDenied(msg)
        project = get_object_or_404(Project, guid=kwargs['guid'])
        if not permissions.is_project_member(self.request.user, project):
            raise Http404
        label = self.request.GET.get('label', '')
        records = (
            TestRecord.objects.filter(project=project, label=label)
            .select_related('session', 'agent')
            .only(
                'id', 'success', 'timestamp',
                'session', 'session__started_at', 'session__branch', 'session__commit_hash',
                'agent', 'agent__name',
            )
            .order_by('-timestamp')
        )
        return {'project': project, 'label': label, 'records': records}
