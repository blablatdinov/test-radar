# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.contrib import admin

from auth.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['username']
