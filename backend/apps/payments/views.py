from django.http import HttpResponseRedirect
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ServicePack, Receipt, PaymentMethod
from .serializers import ServicePackSerializer, ReceiptSerializer
from datetime import timedelta
from django.utils import timezone

from .utils.momo_utils import create_momo_payment
from .utils.vnpay_utils import create_vnpay_payment_url, get_client_ip


class ServicePackViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = ServicePack.objects.filter(active=True)
    serializer_class = ServicePackSerializer


class ReceiptViewSet(viewsets.ViewSet, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return Receipt.objects.filter(user=self.request.user)

    # API tạo thanh toán
    @action(methods=['post'], detail=False, url_path='create-payment')
    def create_payment(self, request):
        # Input: { "pack_id": 1, "job_id": 10, "method": "MOMO" }
        pack_id = request.data.get('pack_id')
        job_id = request.data.get('job_id')
        method = request.data.get('method')

        try:
            pack = ServicePack.objects.get(pk=pack_id)
        except ServicePack.DoesNotExist:
            return Response({"error": "Gói dịch vụ không tồn tại"}, status=400)

        # Tạo hóa đơn (Pending)
        receipt = Receipt.objects.create(
            user=request.user,
            service_pack=pack,
            amount=pack.price,
            payment_method=method,
            related_job_id=job_id,
            is_paid=False
        )

        payment_url = ""
        if method == 'MOMO':
            # Tạo Order ID duy nhất (VD: JOBLINK_RECPT_10)
            order_id = f"JOBLINK_{receipt.id}_{int(timezone.now().timestamp())}"

            # Cấu hình URL
            # return_url: Nơi user được chuyển về sau khi thanh toán trên app MoMo (về lại App Mobile)
            # notify_url: Nơi MoMo gọi ngầm để báo kết quả (IPN) - PHẢI LÀ LINK PUBLIC (Ngrok)

            # Tạm thời để localhost, tí nữa chạy Ngrok sẽ thay domain vào đây
            domain = "https://0559111a69ee.ngrok-free.app"
            return_url = "exp://192.168.1.14:8081"
            notify_url = f"{domain}/payments/receipts/momo-ipn/"

            momo_response = create_momo_payment(
                order_id=order_id,
                amount=int(pack.price),
                order_info=f"Mua goi {pack.name}",
                return_url=return_url,
                notify_url=notify_url
            )

            if momo_response and 'payUrl' in momo_response:
                payment_url = momo_response['payUrl']
                # Lưu lại order_id của MoMo vào hóa đơn để sau này đối soát
                receipt.transaction_id = order_id
                receipt.save()
            else:
                return Response({"error": "Lỗi kết nối MoMo"}, status=400)
        if method == 'VNPAY':
            # Order ID
            order_id = f"JOBLINK_{receipt.id}_{int(timezone.now().timestamp())}"

            # Lấy IP người dùng (VNPAY bắt buộc)
            ip_addr = get_client_ip(request)

            domain = "https://0559111a69ee.ngrok-free.app"
            return_url = f"{domain}/payments/receipts/vnpay-return/"

            payment_url = create_vnpay_payment_url(
                order_id=order_id,
                amount_vnd=int(pack.price),
                order_desc=f"Mua_goi_{pack.name}",
                return_url=return_url,
                ip_addr=ip_addr
            )

            receipt.transaction_id = order_id
            receipt.save()
        return Response({
            "receipt_id": receipt.id,
            "payment_url": payment_url
        }, status=201)

    @action(methods=['post'], detail=False, url_path='momo-ipn', permission_classes=[ AllowAny])
    def momo_ipn(self, request):
        """
        MoMo sẽ gọi vào đây khi thanh toán thành công
        """
        data = request.data
        print("MOMO IPN DATA:", data)

        # Kiểm tra chữ ký (Signature) verify lại cho chắc ăn (Bỏ qua để đơn giản hóa MVP)

        if str(data.get('resultCode')) == '0':  # 0 là thành công
            order_id = data.get('orderId')
            try:
                # Tìm hóa đơn theo order_id đã lưu lúc tạo
                receipt = Receipt.objects.get(transaction_id=order_id)
                if not receipt.is_paid:
                    receipt.is_paid = True
                    receipt.save()

                    # Kích hoạt dịch vụ (Đẩy tin/VIP...)
                    if receipt.related_job:
                        # Logic kích hoạt...
                        pass

                return Response(status=204)
            except Receipt.DoesNotExist:
                pass

        return Response(status=204)

    @action(methods=['get'], detail=False, url_path='vnpay-return', permission_classes=[AllowAny])
    def vnpay_return(self, request):
        vnp_ResponseCode = request.GET.get('vnp_ResponseCode')
        vnp_TxnRef = request.GET.get('vnp_TxnRef')

        if vnp_ResponseCode == '00':
            try:
                receipt = Receipt.objects.get(transaction_id=vnp_TxnRef)
                if not receipt.is_paid:
                    receipt.is_paid = True
                    receipt.save()
            except Receipt.DoesNotExist:
                pass
            return HttpResponseRedirect(f"joblink://payment-result?status=success&order_id={vnp_TxnRef}")
        return HttpResponseRedirect(f"joblink://payment-result?status=failed&order_id={vnp_TxnRef}")
    @action(methods=['post'], detail=False, url_path='confirm-payment')
    def confirm_payment(self, request):
        # Input: { "receipt_id": 5 }
        receipt_id = request.data.get('receipt_id')
        try:
            receipt = Receipt.objects.get(pk=receipt_id, user=request.user)

            if receipt.is_paid:
                return Response({"msg": "Đã thanh toán rồi."}, status=200)

            # 1. Cập nhật trạng thái hóa đơn
            receipt.is_paid = True
            receipt.transaction_id = f"TRANS_{timezone.now().timestamp()}"
            receipt.save()

            # 2. KÍCH HOẠT DỊCH VỤ (Logic quan trọng nhất)
            # Ví dụ: Mua gói đẩy tin -> Update Job
            if receipt.related_job:
                job = receipt.related_job
                # Giả sử trong Job model bạn thêm field 'is_featured' hoặc 'expiration_date'
                # job.is_featured = True
                # job.featured_until = timezone.now() + timedelta(days=receipt.service_pack.duration_days)
                job.save()

            return Response({"message": "Thanh toán thành công! Dịch vụ đã được kích hoạt."}, status=200)

        except Receipt.DoesNotExist:
            return Response({"error": "Hóa đơn không tồn tại"}, status=400)