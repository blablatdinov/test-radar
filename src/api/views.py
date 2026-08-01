# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.bulk_record import BulkCreateSerializer
from records.models import ApiToken, TestRecord, TestSession

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger('api.views')


class BulkCreateTestRecordView(APIView):
    def post(self, request: Request) -> Response:  # noqa: WPS210
        if not isinstance(request.auth, ApiToken):
            raise TypeError
        if request.auth.agent is None:
            return Response(
                {'error': 'Invalid token'},
                status=HTTPStatus.UNAUTHORIZED.value,
            )
        serializer = BulkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=HTTPStatus.BAD_REQUEST.value,
            )
        validated_data = serializer.validated_data
        environment = validated_data['environment']
        context = validated_data['context']
        session, _ = TestSession.objects.get_or_create(
            id=validated_data['session_id'],
            defaults={
                'project': request.auth.agent.project,
                'started_at': validated_data['started_at'],
                'os': environment['os'],
                'os_version': environment['os_version'],
                'arch': environment['arch'],
                'branch': context['branch'],
                'commit_hash': context['commit_hash'],
            },
        )
        records_data = validated_data['records']
        test_records = [
            TestRecord(
                label=record_data['label'],
                timestamp=record_data['timestamp'],
                success=record_data['success'],
                logs=base64.b64decode(record_data['logs']) if record_data['logs'] else b'',
                agent=request.auth.agent,
                project=request.auth.agent.project,
                session=session,
            )
            for record_data in records_data
        ]
        with transaction.atomic():
            TestRecord.objects.bulk_create(test_records)
        return Response({'created': len(test_records)}, status=HTTPStatus.CREATED.value)
