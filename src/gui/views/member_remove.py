# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, final

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from records.models import Membership, Project
from records.srv import permissions

if TYPE_CHECKING:
    import uuid

    from django.http import HttpResponse


@final
class MemberRemoveView(View):
    """Remove a member from a project."""

    def post(self, request: Any, guid: uuid.UUID, user_pk: int) -> HttpResponse:
        project = get_object_or_404(Project, guid=guid)
        if not permissions.is_project_member(request.user, project):
            raise Http404
        if not permissions.can_manage_members(request.user, project):
            msg = 'You do not have permission to manage members.'
            raise PermissionDenied(msg)
        membership = get_object_or_404(Membership, user_id=user_pk, project=project)
        if membership.user_id == request.user.pk:
            msg = 'You cannot remove yourself from the project.'
            raise PermissionDenied(msg)
        membership.delete()
        return redirect('project_detail', guid=project.guid)
