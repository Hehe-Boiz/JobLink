from django.contrib import admin
from django.urls import path, include, re_path


urlpatterns = [
    path('', include('apps.jobs.urls')),
    path('', include('apps.users.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
]
