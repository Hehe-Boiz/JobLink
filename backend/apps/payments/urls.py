from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('payments/receipts', views.ReceiptViewSet, basename='receipts')
router.register('payments/service-packs', views.ServicePackViewSet, basename='service-pack')
urlpatterns = [
    path('', include(router.urls)),
]