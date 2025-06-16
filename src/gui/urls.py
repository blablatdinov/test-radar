from django.urls import path

from gui.views import IndexView

urlpatterns = [
    path('', IndexView.as_view()),
]
