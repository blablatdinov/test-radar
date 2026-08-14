# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

# @todo #162:30min Optimize permission checks with prefetched membership
#  data to avoid extra queries per check. Views should select_related /
#  prefetch_related project memberships and the functions should accept
#  the prefetched queryset instead of hitting the DB on every call.
#  Cover both RBAC_ENABLED modes with django_assert_num_queries.

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from records.models import Agent, Membership, Project

if TYPE_CHECKING:
    from auth.models import User

_MANAGERS = frozenset((Membership.Role.OWNER, Membership.Role.MAINTAINER))


def get_role(user: User | AnonymousUser, project: Project) -> Membership.Role | None:
    if not user.is_authenticated:
        return None
    if not settings.RBAC_ENABLED:
        if project.owner_id == user.pk:
            return Membership.Role.OWNER
        return None
    membership = Membership.objects.filter(user=user, project=project).first()
    if membership is None:
        return None
    return Membership.Role(membership.role)


def is_project_member(user: User | AnonymousUser, project: Project) -> bool:
    return get_role(user, project) is not None


def can_manage_agent(user: User | AnonymousUser, project: Project, agent_type: str) -> bool:
    role = get_role(user, project)
    if role is None:
        return False
    if agent_type == Agent.AgentType.CI:
        return role in _MANAGERS
    return True


def can_delete_agent(user: User | AnonymousUser, agent: Agent) -> bool:
    role = get_role(user, agent.project)
    if role is None:
        return False
    if agent.type == Agent.AgentType.CI:
        return role in _MANAGERS
    return role in _MANAGERS or agent.owner_id == user.pk


def can_manage_members(user: User | AnonymousUser, project: Project) -> bool:
    return get_role(user, project) == Membership.Role.OWNER


def can_delete_project(user: User | AnonymousUser, project: Project) -> bool:
    return get_role(user, project) == Membership.Role.OWNER
