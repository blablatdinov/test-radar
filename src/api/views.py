# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.generics import CreateAPIView
from rest_framework.serializers import BaseSerializer

from api.serializers.record import TestRecordSerializer
from records.models import ApiToken


class CreateTestRecordView(CreateAPIView):
    serializer_class = TestRecordSerializer

    def perform_create(self, serializer: BaseSerializer) -> None:
        agent = None
        if isinstance(self.request.auth, ApiToken):
            agent = self.request.auth.agent
        serializer.save(agent=agent)
