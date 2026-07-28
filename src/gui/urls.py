# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.urls import path

from gui.views import AgentCreateView, AgentTokenRegenerateView, IndexView, ProjectCreateView, ProjectView, TestInfoView

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('project/create', ProjectCreateView.as_view(), name='project_create'),
    path('project/<pk>', ProjectView.as_view(), name='project_detail'),
    path('project/<pk>/agents/create', AgentCreateView.as_view(), name='agent_create'),
    path(
        'project/<pk>/agents/<agent_pk>/regenerate-token',
        AgentTokenRegenerateView.as_view(),
        name='agent_token_regenerate',
    ),
    path('test/<pk>', TestInfoView.as_view(), name='test_info'),
]
