# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaetdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import logging

from rest_framework.generics import CreateAPIView
from rest_framework.serializers import BaseSerializer

from api.serializers.record import TestRecordSerializer
from records.models import ApiToken

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
