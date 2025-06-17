from rest_framework.generics import CreateAPIView

from api.serializers.record import TestRecordSerializer


class CreateTestRecordView(CreateAPIView):
    serializer_class = TestRecordSerializer
    # permission_classes = [IsAuthenticated]
