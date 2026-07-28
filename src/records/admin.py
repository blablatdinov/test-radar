# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.contrib import admin

from records.models import Agent, ApiToken, Project, TestRecord  # noqa: WPS226


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['name']  # noqa: WPS226
    list_display = ['name', 'owner', 'created_at']  # noqa: WPS226


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'type', 'project', 'owner', 'created_at']


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    search_fields = ['token_mask']
    list_display = ['token_mask', 'agent', 'scopes', 'expires_at', 'last_used_at', 'created_at']


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    search_fields = ['label']
    list_display = ['label', 'project', 'timestamp', 'success']
