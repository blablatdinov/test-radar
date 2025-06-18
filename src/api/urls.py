from django.urls import path

from api.views import CreateTestRecordView

urlpatterns = [
    path('test_record/create/', CreateTestRecordView.as_view(), name='api_create_test'),
]
