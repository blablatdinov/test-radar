# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from gui.views.agent_create import AgentCreateView
from gui.views.agent_delete import AgentDeleteView
from gui.views.agent_token_regenerate import AgentTokenRegenerateView
from gui.views.index import IndexView
from gui.views.member_add import MemberAddView
from gui.views.member_remove import MemberRemoveView
from gui.views.project import ProjectView
from gui.views.project_create import ProjectCreateView
from gui.views.session import SessionView
from gui.views.test_history import TestHistoryView
from gui.views.test_info import TestInfoView

__all__ = [
    'AgentCreateView',
    'AgentDeleteView',
    'AgentTokenRegenerateView',
    'IndexView',
    'MemberAddView',
    'MemberRemoveView',
    'ProjectCreateView',
    'ProjectView',
    'SessionView',
    'TestHistoryView',
    'TestInfoView',
]
