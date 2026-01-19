import json
import hmac
import hashlib
import requests
import uuid

MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
PARTNER_CODE = "MOMO"
ACCESS_KEY = "F8BBA842ECF85"
SECRET_KEY = "K951B6PE1waDMi640xX08PD3vg6EkVlz"


def create_momo_payment(order_id, amount, order_info, return_url, notify_url):
    """
    Hàm tạo request thanh toán gửi sang MoMo
    """
    request_id = str(uuid.uuid4())
    raw_signature = (
        f"accessKey={ACCESS_KEY}&amount={amount}&extraData=&"
        f"ipnUrl={notify_url}&orderId={order_id}&orderInfo={order_info}&"
        f"partnerCode={PARTNER_CODE}&redirectUrl={return_url}&"
        f"requestId={request_id}&requestType=captureWallet"
    )

    h = hmac.new(
        SECRET_KEY.encode('utf-8'),
        raw_signature.encode('utf-8'),
        hashlib.sha256
    )
    signature = h.hexdigest()

    data = {
        'partnerCode': PARTNER_CODE,
        'partnerName': "JobLink Demo",
        'storeId': "MomoTestStore",
        'requestId': request_id,
        'amount': str(amount),
        'orderId': order_id,
        'orderInfo': order_info,
        'redirectUrl': return_url,
        'ipnUrl': notify_url,
        'lang': 'vi',
        'extraData': '',
        'requestType': 'captureWallet',
        'signature': signature
    }
    print("--------------------JSON REQUEST----------------\n")
    data = json.dumps(data)
    print(data)

    try:
        response = requests.post(MOMO_ENDPOINT, json=data)
        return response.json()
    except Exception as e:
        print(f"MoMo Error: {e}")
        return None