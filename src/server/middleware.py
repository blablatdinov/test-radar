# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, final

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

PUBLIC_PREFIXES = ('/admin/', '/__debug__/', '/health/')
_EMAIL_PUBLIC_PREFIX = '/email/'


@final
class AuthRequiredMiddleware:
    """Protect all URLs by default, allowing only whitelisted paths for anonymous users."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._public_paths: frozenset[str] = self._build_public_paths()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated or self._is_public(request.path):
            return self.get_response(request)
        if request.path.startswith('/api/'):
            return self.get_response(request)
        return redirect('login')

    def _is_public(self, path: str) -> bool:
        if path in self._public_paths or path.startswith(PUBLIC_PREFIXES):
            return True
        return settings.REGISTRATION_ENABLED and path.startswith(_EMAIL_PUBLIC_PREFIX)

    def _build_public_paths(self) -> frozenset[str]:
        paths = [reverse('login'), reverse('logout')]
        if settings.REGISTRATION_ENABLED:
            paths.append(reverse('register'))
            paths.append(reverse('email_confirmation_sent'))
            paths.append(reverse('email_resend'))
        return frozenset(paths)
