# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect

PUBLIC_PATHS = frozenset({
    '/login/',
    '/logout/',
    '/register/',
})
PUBLIC_PREFIXES = ('/admin/', '/__debug__/')


class AuthRequiredMiddleware:
    """Protect all URLs by default, allowing only whitelisted paths for anonymous users."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated or self._is_public(request.path):
            return self.get_response(request)
        if request.path.startswith('/api/'):
            return JsonResponse(
                {'detail': 'Authentication credentials were not provided.'},
                status=401,
            )
        return redirect('login')

    def _is_public(self, path: str) -> bool:
        return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)
