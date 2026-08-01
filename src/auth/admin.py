# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.contrib import admin

from auth.models import EmailConfirmationToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_email_verified', 'is_staff']
    list_filter = ['is_email_verified', 'is_staff']
    search_fields = ['username', 'email']


@admin.register(EmailConfirmationToken)
class EmailConfirmationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expired_at']
    search_fields = ['user__username', 'user__email', 'token']
