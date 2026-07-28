# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.conf import settings
from django.urls import path

from auth.views import CustomLoginView, CustomLogoutView, RegisterView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]

if settings.REGISTRATION_ENABLED:
    urlpatterns += [
        path('register/', RegisterView.as_view(), name='register'),
    ]
