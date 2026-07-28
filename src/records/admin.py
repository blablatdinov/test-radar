# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.contrib import admin

from records.models import Project, TestRecord


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'owner', 'created_at']


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    search_fields = ['label']
    list_display = ['label', 'project', 'timestamp', 'success']
