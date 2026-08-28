# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import os

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse

def health_view(request):
    return JsonResponse(
        'status': 'ok',
        'color': os.environ.get('DEPLOY_COLOR', 'unknown'),
        'version': os.environ.get('APP_VERSION', 'unknown'),
    )

urlpatterns = [
    *debug_toolbar_urls(),
    path('{0}admin/'.format(settings.ADMIN_SECRET_PATH), admin.site.urls),
    path('', include('auth.urls')),
    path('', include('gui.urls')),
    path('/health', include('gui.urls')),
    path('api/v1/', include('api.urls')),
]
if settings.SILK_ENABLE:
    urlpatterns += [
        path('silk/', include('silk.urls', namespace='silk')),
    ]
