# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.apps import AppConfig


class GuiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gui'
