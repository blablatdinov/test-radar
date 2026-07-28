# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.serializers import ModelSerializer

from records.models import TestRecord


# TODO #38 We should change a test record creating logic
class TestRecordSerializer(ModelSerializer):
    class Meta:
        model = TestRecord
        fields = '__all__'
        read_only_fields = ('project', 'agent')
