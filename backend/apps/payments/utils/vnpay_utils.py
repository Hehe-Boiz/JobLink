VNP_TMN_CODE = "KFSYL2LL"
VNP_HASH_SECRET = "1335EFGABOXCEP66HW0HMWKUKW2DMRFJ"
VNP_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
# payments/utils/vnpay_utils.py
import hmac
import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from django.conf import settings


def _strip_accents(text: str) -> str:
    """
    VNPAY yêu cầu vnp_OrderInfo: tiếng Việt không dấu.
    """
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # Giữ lại chữ/số/space và một số ký tự an toàn
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch in [" ", "-", "_", ".", ",", "/"]:
            cleaned.append(ch)
    return "".join(cleaned).strip()


def _hmac_sha512(key: str, data: str) -> str:
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha512).hexdigest()


def create_vnpay_payment_url(
    *,
    order_id: str,
    amount_vnd: int,
    order_desc: str,
    return_url: str,
    ip_addr: str,
) -> str:
    """
    Build payment URL for VNPAY (vnp_Command=pay)

    amount_vnd: số tiền VND (ví dụ 10000). Khi gửi sang VNPAY phải *100. :contentReference[oaicite:4]{index=4}
    """
    vnp_url = VNP_URL
    tmn_code = VNP_TMN_CODE
    hash_secret = VNP_HASH_SECRET

    if not tmn_code or not hash_secret:
        raise ValueError("Missing VNPAY_TMN_CODE / VNPAY_HASH_SECRET in settings")

    vnp_amount = int(amount_vnd) * 100

    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz=vn_tz)
    create_date = now_vn.strftime("%Y%m%d%H%M%S")
    expire_date = (now_vn + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")

    vnp_params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn_code,
        "vnp_Amount": str(vnp_amount),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": str(order_id),
        "vnp_OrderInfo": _strip_accents(order_desc)[:255],
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": ip_addr,
        "vnp_CreateDate": create_date,
        "vnp_ExpireDate": expire_date,
    }


    items = [(k, v) for k, v in vnp_params.items() if v is not None and str(v) != ""]
    items.sort(key=lambda x: x[0])  # sort alphabet


    hash_data = "&".join([f"{k}={v}" for k, v in items])


    query = "&".join([f"{quote_plus(k)}={quote_plus(str(v))}" for k, v in items])

    secure_hash = _hmac_sha512(hash_secret, hash_data)
    payment_url = f"{vnp_url}?{query}&vnp_SecureHash={secure_hash}"
    print(payment_url)
    return payment_url


def verify_vnpay_signature(query_params: dict) -> bool:
    """
    Verify callback from VNPAY (return/ipn):
    - Remove vnp_SecureHash (and vnp_SecureHashType if present)
    - Sort remaining params
    - Build hashData same rule
    """
    hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "").strip()
    if not hash_secret:
        return False

    received_hash = (query_params.get("vnp_SecureHash") or "").strip()
    if not received_hash:
        return False

    data = {}
    for k, v in query_params.items():
        if k in ["vnp_SecureHash", "vnp_SecureHashType"]:
            continue
        if v is None or str(v) == "":
            continue
        data[k] = str(v)

    items = sorted(data.items(), key=lambda x: x[0])
    hash_data = "&".join([f"{k}={v}" for k, v in items])
    calculated = _hmac_sha512(hash_secret, hash_data)

    return hmac.compare_digest(calculated.lower(), received_hash.lower())


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")
