# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.serializers import BooleanField, CharField, DateTimeField, ListField, Serializer, UUIDField

_MAX_RECORDS = 500
_LABEL_MAX_LENGTH = 5120
_BRANCH_MAX_LENGTH = 512
_COMMIT_MAX_LENGTH = 40


class BulkRecordSerializer(Serializer):
    label = CharField(max_length=_LABEL_MAX_LENGTH)  # type: ignore[assignment]
    timestamp = DateTimeField()
    logs = CharField(allow_blank=True)
    success = BooleanField()
    branch = CharField(max_length=_BRANCH_MAX_LENGTH, min_length=1)
    commit = CharField(max_length=_COMMIT_MAX_LENGTH, min_length=1)


class BulkCreateSerializer(Serializer):
    session_id = UUIDField()
    records = ListField(
        child=BulkRecordSerializer(),
        min_length=1,
        max_length=_MAX_RECORDS,
    )
