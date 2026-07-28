# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.urls import path

from api.views import BulkCreateTestRecordView, CreateTestRecordView

urlpatterns = [
    path('test_record/create/', CreateTestRecordView.as_view(), name='api_create_test'),
    path('test_record/bulk_create/', BulkCreateTestRecordView.as_view(), name='api_bulk_create_test'),
]
