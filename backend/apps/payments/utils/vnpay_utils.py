import hashlib
import hmac
import urllib.parse
from datetime import datetime
import unicodedata

# --- CẤU HÌNH VNPAY SANDBOX ---
VNP_TMN_CODE = "KFSYL2LL"
VNP_HASH_SECRET = "1335EFGABOXCEP66HW0HMWKUKW2DMRFJ"
VNP_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"


# ------------------------------

def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def get_client_ip(request):
    """Lấy IP của người dùng"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_vnpay_payment_url(order_id, amount, order_desc, return_url, ip_addr):
    """
    Tạo URL thanh toán chuẩn VNPAY 2.1.0
    """
    date = datetime.now().strftime('%Y%m%d%H%M%S')

    # 1. Xử lý nội dung: Bỏ dấu tiếng Việt
    clean_order_desc = remove_accents(order_desc)

    # 2. Chuẩn bị dữ liệu (Input Data)
    # Lưu ý: vnp_Amount phải nhân 100 theo tài liệu
    inputData = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": VNP_TMN_CODE,
        "vnp_Amount": str(int(amount)*100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_id,
        "vnp_OrderInfo": clean_order_desc,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": ip_addr,
        "vnp_CreateDate": date,
    }
    print(inputData)
    # 3. Sắp xếp dữ liệu a-z (Bắt buộc để tạo chữ ký đúng)
    sorted_inputData = sorted(inputData.items())

    # 4. Tạo Query String
    query_string = urllib.parse.urlencode(sorted_inputData)

    # 5. Tạo Chữ ký bảo mật (HMAC SHA512)
    secure_hash = hmac.new(
        bytes(VNP_HASH_SECRET, 'utf-8'),
        bytes(query_string, 'utf-8'),
        hashlib.sha512
    ).hexdigest()
    query_string += f"&vnp_SecureHash={secure_hash}"


    payment_url = f"{VNP_URL}?{query_string}"
    print(payment_url)
    return payment_url


def validate_vnpay_signature(request_data, secret_key):
    """
    Kiểm tra chữ ký (Checksum) từ IPN gửi về
    """
    inputData = request_data.dict()
    if 'vnp_SecureHash' in inputData:
        vnp_SecureHash = inputData.pop('vnp_SecureHash')
    else:
        return False

    # Sắp xếp và tạo lại chữ ký để so sánh
    inputData = sorted(inputData.items())
    query_string = urllib.parse.urlencode(inputData)

    secure_hash = hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    return vnp_SecureHash == secure_hash