# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from rest_framework.generics import CreateAPIView

from api.serializers.record import TestRecordSerializer


class CreateTestRecordView(CreateAPIView):
    serializer_class = TestRecordSerializer
    # permission_classes = [IsAuthenticated]

# TODO #6:30min Save agent info in records.models.Record
