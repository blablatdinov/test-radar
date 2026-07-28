# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.serializers import BooleanField, CharField, DateTimeField, Serializer


class BulkRecordSerializer(Serializer):
    label = CharField(max_length=128)
    timestamp = DateTimeField()
    logs = CharField(allow_blank=True)
    success = BooleanField()
    branch = CharField(max_length=512, allow_blank=True, required=False, default='')
    commit = CharField(max_length=40, allow_blank=True, required=False, default='')
