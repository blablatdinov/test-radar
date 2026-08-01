# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.urls import path

from gui.views import (
    AgentCreateView,
    AgentTokenRegenerateView,
    IndexView,
    ProjectCreateView,
    ProjectView,
    SessionView,
    TestInfoView,
)

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('project/create', ProjectCreateView.as_view(), name='project_create'),
    path('project/<uuid:guid>', ProjectView.as_view(), name='project_detail'),
    path('project/<uuid:guid>/agents/create', AgentCreateView.as_view(), name='agent_create'),
    path(
        'project/<uuid:guid>/agents/<uuid:agent_guid>/regenerate-token',
        AgentTokenRegenerateView.as_view(),
        name='agent_token_regenerate',
    ),
    path('test/<pk>', TestInfoView.as_view(), name='test_info'),
    path('session/<uuid:session_id>', SessionView.as_view(), name='session_detail'),
]
