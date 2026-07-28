# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.conf import settings
from django.http import HttpRequest


def registration_enabled(request: HttpRequest) -> dict[str, bool]:  # noqa: ARG001
    return {'registration_enabled': settings.REGISTRATION_ENABLED}
