from rest_framework.serializers import ModelSerializer

from records.models import TestRecord


class TestRecordSerializer(ModelSerializer):
    class Meta:
        model = TestRecord
        fields = '__all__'
