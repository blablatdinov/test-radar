# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

# @todo #162:30min Create records/srv/permissions.py centralizing all RBAC
#  checks: get_role(user, project), is_project_member(user, project),
#  can_manage_agent(user, project, agent_type) (CI -> owner+maintainer,
#  LOCAL -> any member), can_delete_agent(user, agent) (CI -> owner+maintainer,
#  LOCAL -> owner+maintainer or developer owning the agent),
#  can_manage_members(user, project) and can_delete_project(user, project)
#  (owner only). Cover the full role x action matrix with unit tests.
#  No inline role checks in views — everything goes through this service.
#  Gate the new behavior behind settings.RBAC_ENABLED: when the flag is off,
#  every function must fall back to the legacy owner-based logic
#  (project.owner / agent.owner == user) so the rollout stays compatible.
