# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Final

from django.contrib import admin

from records.models import Agent, ApiToken, Project, TestRecord, TestSession

_NAME: Final = 'name'
_OWNER: Final = 'owner'
_CREATED_AT: Final = 'created_at'
_TYPE: Final = 'type'
_PROJECT: Final = 'project'
_TOKEN_MASK: Final = 'token_mask'
_AGENT: Final = 'agent'
_SCOPES: Final = 'scopes'
_EXPIRES_AT: Final = 'expires_at'
_LAST_USED_AT: Final = 'last_used_at'
_LABEL: Final = 'label'
_TIMESTAMP: Final = 'timestamp'
_SUCCESS: Final = 'success'
_ID: Final = 'id'
_STARTED_AT: Final = 'started_at'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = [_NAME]
    list_display = [_NAME, _OWNER, _CREATED_AT]


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    search_fields = [_NAME]
    list_display = [_NAME, _TYPE, _PROJECT, _OWNER, _CREATED_AT]


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    search_fields = [_TOKEN_MASK]
    list_display = [_TOKEN_MASK, _AGENT, _SCOPES, _EXPIRES_AT, _LAST_USED_AT, _CREATED_AT]


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    search_fields = [_LABEL]
    list_display = [_LABEL, _PROJECT, _TIMESTAMP, _SUCCESS]


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    search_fields = [_STARTED_AT, _PROJECT]
    list_display = [_ID, _PROJECT, _STARTED_AT]
