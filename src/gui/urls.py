# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.urls import path

from gui.views import IndexView, ProjectView, TestInfoView

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('project/<pk>', ProjectView.as_view(), name='project_detail'),
    path('test/<pk>', TestInfoView.as_view(), name='test_info'),
]
