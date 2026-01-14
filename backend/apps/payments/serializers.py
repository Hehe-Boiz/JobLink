from rest_framework import serializers
from .models import ServicePack, Receipt


class ServicePackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePack
        fields = ['id', 'name', 'price', 'duration_days', 'description']


class ReceiptSerializer(serializers.ModelSerializer):
    pack_name = serializers.CharField(source='service_pack.name', read_only=True)

    class Meta:
        model = Receipt
        fields = ['id', 'pack_name', 'amount', 'payment_method', 'is_paid', 'created_date', 'transaction_id']