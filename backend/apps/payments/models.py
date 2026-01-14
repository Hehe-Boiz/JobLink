from django.db import models
from apps.core.models import BaseModel
from apps.jobs.models import Job  # Để link hóa đơn với Job (nếu mua gói đẩy tin)
from apps.users.models import User

class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Tiền mặt"
    MOMO = "MOMO", "Ví MoMo"
    ZALOPAY = "ZALOPAY", "ZaloPay"
    STRIPE = "STRIPE", "Stripe (Visa/Master)"
    PAYPAL = "PAYPAL", "PayPal"
    VNPAY = "VNPAY", "VNPAY-QR / ATM"


class ServicePack(BaseModel):
    name = models.CharField(max_length=100)  # VD: Gói tin nổi bật 7 ngày
    price = models.DecimalField(max_digits=12, decimal_places=0)  # VD: 500000
    duration_days = models.IntegerField(default=7)  # Thời hạn gói
    description = models.TextField(blank=True)

    # Loại gói: Đẩy tin (JOB_PUSH) hay Xem hồ sơ (PROFILE_VIEW)
    pack_type = models.CharField(max_length=20, default="JOB_PUSH")

    def __str__(self):
        return f"{self.name} - {self.price} VND"


class Receipt(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    service_pack = models.ForeignKey(ServicePack, on_delete=models.SET_NULL, null=True)

    # Nếu mua gói đẩy tin thì phải biết đẩy cho tin nào
    related_job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)

    # Trạng thái thanh toán
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Mã giao dịch từ MoMo/Stripe trả về

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Receipt #{self.id} - {self.user.username} - {self.amount}"
