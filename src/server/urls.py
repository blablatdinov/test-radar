from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    *debug_toolbar_urls(),
    path('admin/', admin.site.urls),
    path('', include('gui.urls')),
]
