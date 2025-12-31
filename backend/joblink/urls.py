from django.contrib import admin
from django.urls import path, include, re_path

from apps.jobs.admin import admin_site

urlpatterns = [
    path('', include('apps.jobs.urls')),
    path('admin/', admin_site.urls),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls'))
]
