from django.db import models
from apps.core.models import BaseModel
from apps.jobs.models import Job  # Để link hóa đơn với Job (nếu mua gói đẩy tin)
from apps.users.models import User

class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Tiền mặt"
    VNPAY = "VNPAY", "VNPAY-QR / ATM"

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Chờ thanh toán'
    SUCCESS = 'SUCCESS', 'Thanh toán thành công'
    FAILED = 'FAILED', 'Thanh toán thất bại'
    CANCELLED = 'CANCELLED', 'Đã hủy'


class ServicePack(BaseModel):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    duration_days = models.IntegerField(default=7)  # Thời hạn gói
    description = models.TextField(blank=True)
    pack_type = models.CharField(max_length=20, default="JOB_PUSH")

    def __str__(self):
        return f"{self.name} - {self.price} VND"


class Receipt(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    service_pack = models.ForeignKey(ServicePack, on_delete=models.SET_NULL, null=True)


    related_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Receipt #{self.id} - {self.user.username} - {self.amount}"
