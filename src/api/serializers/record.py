# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.serializers import ModelSerializer

from records.models import TestRecord


class TestRecordSerializer(ModelSerializer):
    class Meta:
        model = TestRecord
        fields = '__all__'
