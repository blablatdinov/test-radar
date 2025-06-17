from django.urls import path

from gui.views import IndexView, TestInfoView

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('test/<pk>', TestInfoView.as_view(), name='test_info'),
]
