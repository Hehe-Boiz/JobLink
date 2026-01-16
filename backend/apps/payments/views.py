import json

from django.http import HttpResponseRedirect, JsonResponse
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ServicePack, Receipt, PaymentStatus
from .serializers import ServicePackSerializer, ReceiptSerializer
from django.utils import timezone
from .utils.momo_utils import create_momo_payment
from .utils.vnpay_utils import create_vnpay_payment_url, get_client_ip, validate_vnpay_signature, VNP_HASH_SECRET
from django.http import HttpResponse
import os
from dotenv import load_dotenv
load_dotenv()

class ServicePackViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = ServicePack.objects.filter(active=True)
    serializer_class = ServicePackSerializer


class ReceiptViewSet(viewsets.ViewSet, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return Receipt.objects.filter(user=self.request.user)

    @action(methods=['post'], detail=False, url_path='create-payment')
    def create_payment(self, request):
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
        if method == 'VNPAY':
            order_id = f"JOBLINK_{receipt.id}_{int(timezone.now().timestamp())}"
            ip_addr = get_client_ip(request)

            domain = os.getenv('URL_BACKEND')
            return_url = f"{domain}/payments/receipts/vnpay-return/"
            payment_url = create_vnpay_payment_url(
                order_id=order_id,
                amount=int(pack.price),
                order_desc=f"Muagoi",
                return_url=return_url,
                ip_addr=ip_addr,
            )

            receipt.transaction_id = order_id
            receipt.save()
        return Response({
            "receipt_id": receipt.id,
            "payment_url": payment_url
        }, status=201)

    @action(methods=['get', 'post'], detail=False, url_path='vnpay-return', permission_classes=[AllowAny])
    def vnpay_return(self, request):
        vnp_ResponseCode = request.GET.get('vnp_ResponseCode')
        vnp_TxnRef = request.GET.get('vnp_TxnRef')

        text_color = "#dc3545"
        try:
            receipt = Receipt.objects.get(transaction_id=vnp_TxnRef)
            if vnp_ResponseCode == '00':

                if not receipt.is_paid:
                    receipt.is_paid = True
                    receipt.status = PaymentStatus.SUCCESS
                    receipt.save()
                    if receipt.related_job:
                        job = receipt.related_job
                        job.is_featured = True
                        job.save()

                transaction_status = "Thanh toán thành công!"
                transaction_info = "Gói tin của bạn đã được kích hoạt"
                deep_link_status = "success"
                text_color = "#28a745"

            else:
                receipt.is_paid = False
                receipt.status = PaymentStatus.FAILED
                receipt.save()

                transaction_status = "Giao dịch thất bại hoặc bị hủy"
                transaction_info = "Có lỗi xảy ra"
                deep_link_status = "failed"
                text_color = "#dc3545"

        except Receipt.DoesNotExist:
            transaction_status = "Không tìm thấy đơn hàng"
            transaction_info = "Vui lòng chọn đơn hàng thanh toán"
            deep_link_status = "failed"
        app_url = f"joblink://payment-result?status={deep_link_status}&order_id={vnp_TxnRef}&transaction_status={transaction_status}&transaction_info={transaction_info}"

        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Kết quả thanh toán</title>
                <style>
                    body {{ font-family: sans-serif; text-align: center; padding: 40px 20px; background-color: #f8f9fa; }}
                    .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }}
                    h2 {{ color: {text_color}; margin-bottom: 10px; }}
                    p {{ color: #6c757d; margin-bottom: 30px; }}
                    .btn {{
                        display: inline-block; padding: 12px 24px; font-size: 16px; font-weight: bold;
                        color: white; background-color: #007bff; text-decoration: none;
                        border-radius: 50px; transition: opacity 0.3s;
                    }}
                    .btn:hover {{ opacity: 0.9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>{transaction_status}</h2>
                    <p>Mã giao dịch: <strong>{vnp_TxnRef}</strong></p>

                    <a href="{app_url}" class="btn">Quay về ứng dụng</a>
                </div>

                <script>
                    // Tự động chuyển hướng về App sau 1 giây
                    setTimeout(function() {{
                        window.location.href = "{app_url}";
                    }}, 1000);
                </script>
            </body>
            </html>
            """

        return HttpResponse(html_content)

    @action(methods=['get'], detail=False, url_path='vnpay-ipn', permission_classes=[AllowAny])
    def vnpay_ipn(self, request):
        inputData = request.GET
        print('Okie')
        if not validate_vnpay_signature(inputData, VNP_HASH_SECRET):
            return JsonResponse({"RspCode": "97", "Message": "Invalid Signature"})

        vnp_ResponseCode = inputData.get('vnp_ResponseCode')
        vnp_TxnRef = inputData.get('vnp_TxnRef')
        vnp_Amount = inputData.get('vnp_Amount')

        try:
            receipt = Receipt.objects.get(transaction_id=vnp_TxnRef)

            if int(vnp_Amount) != int(receipt.amount) * 100:
                return JsonResponse({"RspCode": "04", "Message": "Invalid Amount"})
            if receipt.is_paid:
                return JsonResponse({"RspCode": "02", "Message": "Order Already Confirmed"})
            if vnp_ResponseCode == '00':
                receipt.is_paid = True
                receipt.status = PaymentStatus.SUCCESS
                receipt.save()

                if receipt.related_job and receipt.service_pack:
                    job = receipt.related_job
                    job.is_featured = True
                    job.save()

                return JsonResponse({"RspCode": "00", "Message": "Confirm Success"})
            else:
                receipt.status = PaymentStatus.FAILED
                receipt.save()
                return JsonResponse({"RspCode": "00", "Message": "Confirm Success"})

        except Receipt.DoesNotExist:
            return JsonResponse({"RspCode": "01", "Message": "Order Not Found"})
        except Exception as e:
            print(f"IPN Error: {str(e)}")
            return JsonResponse({"RspCode": "99", "Message": "Unknown Error"})