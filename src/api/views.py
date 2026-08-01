# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import logging
from http import HTTPStatus

from django.db import transaction
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.bulk_record import BulkCreateSerializer
from records.models import Agent, TestRecord, TestSession
from records.srv.token import verify_token

_TOKEN_KEYWORD = 'Token'

logger = logging.getLogger('api.views')


class BulkCreateTestRecordView(APIView):

    def post(self, request: Request) -> Response:  # noqa: WPS210
        agent = self._authenticate(request)
        if agent is None:
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
        session, _ = TestSession.objects.get_or_create(
            id=validated_data['session_id'],
            defaults={'project': agent.project, 'started_at': timezone.now()},
        )
        records_data = validated_data['records']
        test_records = [
            TestRecord(
                label=record_data['label'],
                timestamp=record_data['timestamp'],
                success=record_data['success'],
                logs=record_data['logs'],
                branch=record_data['branch'],
                commit=record_data['commit'],
                agent=agent,
                project=agent.project,
                session=session,
            )
            for record_data in records_data
        ]
        with transaction.atomic():
            TestRecord.objects.bulk_create(test_records)

        return Response({'created': len(test_records)}, status=HTTPStatus.CREATED.value)

    def _authenticate(self, request: Request) -> Agent | None:
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith(f'{_TOKEN_KEYWORD} '):
            return None
        raw_token = header[len(_TOKEN_KEYWORD) + 1:]
        api_token = verify_token(raw_token)
        if api_token is None:
            return None
        return api_token.agent
