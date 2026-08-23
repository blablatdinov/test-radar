# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.urls import path

from gui.views import (
    AgentCreateView,
    AgentDeleteView,
    AgentTokenRegenerateView,
    IndexView,
    MemberAddView,
    MemberRemoveView,
    ProjectCreateView,
    ProjectView,
    SessionView,
    TestHistoryView,
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
    path('project/<uuid:guid>/test-history', TestHistoryView.as_view(), name='test_history'),
    path(
        'project/<uuid:guid>/agents/<uuid:agent_guid>/delete',
        AgentDeleteView.as_view(),
        name='agent_delete',
    ),
    path('project/<uuid:guid>/members/add', MemberAddView.as_view(), name='member_add'),
    path(
        'project/<uuid:guid>/members/<int:user_pk>/remove',
        MemberRemoveView.as_view(),
        name='member_remove',
    ),
]
