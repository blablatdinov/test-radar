# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import final

from rest_framework.serializers import BooleanField, CharField, DateTimeField, ListField, Serializer, UUIDField

_MAX_RECORDS = 500
_LABEL_MAX_LENGTH = 5120
_BRANCH_MAX_LENGTH = 512
_COMMIT_MAX_LENGTH = 40
_OS_MAX_LENGTH = 50
_OS_VERSION_MAX_LENGTH = 100
_ARCH_MAX_LENGTH = 20


@final
class BulkRecordSerializer(Serializer):
    label = CharField(max_length=_LABEL_MAX_LENGTH)  # type: ignore[assignment]
    timestamp = DateTimeField()
    logs = CharField(allow_blank=True)
    success = BooleanField()


@final
class EnvironmentSerializer(Serializer):
    os = CharField(max_length=_OS_MAX_LENGTH)
    os_version = CharField(max_length=_OS_VERSION_MAX_LENGTH)
    arch = CharField(max_length=_ARCH_MAX_LENGTH)


@final
class ContextSerializer(Serializer):
    branch = CharField(max_length=_BRANCH_MAX_LENGTH, min_length=1)
    commit_hash = CharField(max_length=_COMMIT_MAX_LENGTH, min_length=1)


@final
class BulkCreateSerializer(Serializer):
    session_id = UUIDField()
    started_at = DateTimeField()
    environment = EnvironmentSerializer()  # type: ignore[assignment]
    context = ContextSerializer()  # type: ignore[assignment]
    records = ListField(
        child=BulkRecordSerializer(),
        min_length=1,
        max_length=_MAX_RECORDS,
    )
