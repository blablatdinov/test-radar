# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    *debug_toolbar_urls(),
    path('admin/', admin.site.urls),
    path('', include('gui.urls')),
    path('api/v1/', include('api.urls')),
]
