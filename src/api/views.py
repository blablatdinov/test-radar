# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaetdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import logging

from rest_framework.generics import CreateAPIView
from rest_framework.serializers import BaseSerializer
from rest_framework.generics import CreateAPIView
from http import HTTPStatus

from django.db import transaction
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.bulk_record import BulkRecordSerializer
from api.serializers.record import TestRecordSerializer
from records.models import ApiToken

from records.models import Agent, TestRecord
from records.srv.token import verify_token

_MAX_RECORDS = 500
_TOKEN_KEYWORD = 'Token'

logger = logging.getLogger('api.views')


class CreateTestRecordView(CreateAPIView):
    serializer_class = TestRecordSerializer

    def perform_create(self, serializer: BaseSerializer) -> None:
        agent = None
        project = None
        if isinstance(self.request.auth, ApiToken):
            agent = self.request.auth.agent
            project = agent.project
            logger.info(
                'Creating test record for agent %r (project=%r)',
                agent.name,
                project.name,
            )
        else:
            logger.debug('Creating test record via session auth (user=%r)', self.request.user.username)
        serializer.save(agent=agent, project=project)


class BulkCreateTestRecordView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request) -> Response:
        agent = self._authenticate(request)
        if agent is None:
            return Response(
                {'error': 'Invalid token'},
                status=HTTPStatus.UNAUTHORIZED.value,
            )

        if not isinstance(request.data, dict):
            return Response(
                {'error': 'invalid body', 'detail': 'Request body must be a JSON object'},
                status=HTTPStatus.BAD_REQUEST.value,
            )

        records = request.data.get('records')
        if records is None:
            return Response(
                {'error': 'records is required', 'detail': "Field 'records' is required"},
                status=HTTPStatus.BAD_REQUEST.value,
            )
        if not isinstance(records, list):
            return Response(
                {'error': 'records must be an array', 'detail': "Field 'records' must be an array"},
                status=HTTPStatus.BAD_REQUEST.value,
            )
        if len(records) == 0:
            return Response(
                {'error': 'records array is empty', 'detail': "Field 'records' must contain at least 1 record"},
                status=HTTPStatus.BAD_REQUEST.value,
            )
        if len(records) > _MAX_RECORDS:
            return Response(
                {'error': 'records exceeds limit', 'detail': f"Field 'records' must contain at most {_MAX_RECORDS} records"},
                status=HTTPStatus.BAD_REQUEST.value,
            )

        serializer = BulkRecordSerializer(data=records, many=True)
        if not serializer.is_valid():
            return Response(
                {'error': 'validation error', 'detail': serializer.errors},
                status=HTTPStatus.BAD_REQUEST.value,
            )

        validated = serializer.validated_data
        test_records = [
            TestRecord(
                label=item['label'],
                timestamp=item['timestamp'],
                success=item['success'],
                logs=item['logs'],
                branch=item['branch'],
                commit=item['commit'],
                agent=agent,
            )
            for item in validated
        ]
        with transaction.atomic():
            TestRecord.objects.bulk_create(test_records)

        return Response({'created': len(test_records)}, status=HTTPStatus.OK.value)

    def _authenticate(self, request: Request) -> Agent | None:
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith(f'{_TOKEN_KEYWORD} '):
            return None
        raw_token = header[len(_TOKEN_KEYWORD) + 1:]
        api_token = verify_token(raw_token)
        if api_token is None:
            return None
        return api_token.agent
