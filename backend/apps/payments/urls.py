from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router dành cho ViewSet
router = DefaultRouter()
router.register('payments/receipts', views.ReceiptViewSet, basename='receipts')
router.register('payments/service-packs', views.ServicePackViewSet, basename='service-pack')
urlpatterns = [
    path('', include(router.urls)),
]