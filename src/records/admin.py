from django.contrib import admin

from records.models import TestRecord


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    search_fields = ['label']
    list_display = ['label', 'timestamp', 'success']
