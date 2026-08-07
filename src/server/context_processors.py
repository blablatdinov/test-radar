# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import os

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest


def registration_enabled(request: HttpRequest) -> dict[str, bool]:  # noqa: ARG001
    return {'registration_enabled': settings.REGISTRATION_ENABLED}


def app_version(request: HttpRequest) -> dict[str, str]:
    return {'app_version': os.environ.get('APP_VERSION', 'dev')}
