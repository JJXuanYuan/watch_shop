from __future__ import annotations

import base64
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.models.order import Order
from app.models.user import User

try:
    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    x509 = None
    InvalidSignature = Exception
    hashes = None
    serialization = None
    padding = None
    AESGCM = None

settings = get_settings()


@dataclass(frozen=True)
class WechatPayParams:
    app_id: str
    time_stamp: str
    nonce_str: str
    package: str
    sign_type: str
    pay_sign: str
    prepay_id: str


def _ensure_payment_dependencies() -> None:
    if None in (x509, hashes, serialization, padding, AESGCM):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信支付依赖缺失，请先安装 requirements 中的 cryptography",
        )


def _missing_config(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"微信支付配置缺失：{name}",
    )


def _ensure_payment_ready(settings: Settings) -> None:
    required_values = {
        "WECHAT_MINI_APPID": settings.wechat_mini_appid,
        "WECHAT_PAY_MCH_ID": settings.wechat_pay_mch_id,
        "WECHAT_PAY_MERCHANT_SERIAL_NO": settings.wechat_pay_merchant_serial_no,
        "WECHAT_PAY_PRIVATE_KEY_PATH": str(settings.resolved_wechat_pay_private_key_path or ""),
        "WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH": str(
            settings.resolved_wechat_pay_platform_public_key_path or ""
        ),
        "WECHAT_PAY_API_V3_KEY": settings.wechat_pay_api_v3_key,
        "WECHAT_PAY_NOTIFY_URL": settings.wechat_pay_notify_url,
    }

    for name, value in required_values.items():
        if not str(value).strip():
            raise _missing_config(name)

    if len(settings.wechat_pay_api_v3_key.encode("utf-8")) != 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信支付配置缺失：WECHAT_PAY_API_V3_KEY 必须为 32 字节",
        )

    _ensure_payment_dependencies()


def _has_close_payment_config(settings: Settings) -> bool:
    return bool(
        settings.wechat_pay_mch_id.strip()
        and settings.wechat_pay_merchant_serial_no.strip()
        and settings.resolved_wechat_pay_private_key_path
    )


def _read_text(path: str | None) -> str:
    if not path:
        raise _missing_config("支付证书文件路径")

    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"微信支付证书文件不存在：{path}",
        ) from exc


@lru_cache(maxsize=1)
def _load_merchant_private_key():
    _ensure_payment_dependencies()
    key_path = settings.resolved_wechat_pay_private_key_path
    if key_path is None:
        raise _missing_config("WECHAT_PAY_PRIVATE_KEY_PATH")

    try:
        return serialization.load_pem_private_key(
            _read_text(str(key_path)).encode("utf-8"),
            password=None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信支付商户私钥加载失败，请检查 PEM 文件格式",
        ) from exc


@lru_cache(maxsize=1)
def _load_platform_public_key():
    _ensure_payment_dependencies()
    key_path = settings.resolved_wechat_pay_platform_public_key_path
    if key_path is None:
        raise _missing_config("WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH")

    pem_bytes = _read_text(str(key_path)).encode("utf-8")

    try:
        if b"BEGIN CERTIFICATE" in pem_bytes:
            certificate = x509.load_pem_x509_certificate(pem_bytes)
            return certificate.public_key()
        return serialization.load_pem_public_key(pem_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信支付平台公钥加载失败，请检查 PEM 文件格式",
        ) from exc


def _sign_message(message: str) -> str:
    private_key = _load_merchant_private_key()
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _verify_signature(message: str, signature: str) -> None:
    public_key = _load_platform_public_key()
    try:
        public_key.verify(
            base64.b64decode(signature),
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except (ValueError, InvalidSignature) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="微信支付回调验签失败",
        ) from exc


def _build_authorization_header(method: str, request_url: str, body: str) -> str:
    parsed = urlparse(request_url)
    canonical_url = parsed.path or "/"
    if parsed.query:
        canonical_url = f"{canonical_url}?{parsed.query}"

    timestamp = str(int(time.time()))
    nonce_str = secrets.token_hex(16)
    signing_message = f"{method.upper()}\n{canonical_url}\n{timestamp}\n{nonce_str}\n{body}\n"
    signature = _sign_message(signing_message)

    return (
        'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{settings.wechat_pay_mch_id}",'
        f'nonce_str="{nonce_str}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{settings.wechat_pay_merchant_serial_no}",'
        f'signature="{signature}"'
    )


def _request_wechat_pay(
    method: str,
    request_url: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    method_upper = method.upper()
    body = ""
    request_data: bytes | None = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        request_data = body.encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "watch-shop-api/1.0",
        "Authorization": _build_authorization_header(method, request_url, body),
    }

    request_kwargs: dict[str, Any] = {
        "headers": headers,
        "method": method_upper,
    }
    if request_data is not None:
        request_kwargs["data"] = request_data

    request = Request(request_url, **request_kwargs)

    try:
        with urlopen(request, timeout=settings.wechat_pay_timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError:
            payload = {"message": response_text or "微信支付服务返回异常"}

        code = payload.get("code")
        message = payload.get("message") or "微信支付服务返回异常"

        if code == "ORDERPAID":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单已支付，不能重复发起支付",
            ) from exc

        if code == "ORDERCLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单已关闭，不能继续支付",
            ) from exc

        if code == "ORDERNOTEXIST":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="微信支付订单不存在",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"微信支付接口调用失败：{message}",
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="调用微信支付服务失败，请稍后重试",
        ) from exc

    if not response_body.strip():
        return {}

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="微信支付服务返回了无法解析的内容",
        ) from exc


def _build_order_description(order: Order) -> str:
    item_names = [
        item.product_name_snapshot
        for item in sorted(order.items, key=lambda current: current.id)
    ]
    if not item_names:
        return f"商城订单 {order.order_no}"

    if len(item_names) == 1:
        description = item_names[0]
    else:
        description = f"{item_names[0]} 等 {len(item_names)} 件商品"

    return description[:120]


def _convert_amount_to_fen(amount: Decimal) -> int:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单金额必须大于 0 才能发起支付",
        )

    normalized = (amount * Decimal("100")).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )
    return int(normalized)


def create_wechat_payment(order: Order, user: User) -> WechatPayParams:
    _ensure_payment_ready(settings)

    if not user.openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户缺少 openid，无法发起微信支付",
        )

    request_url = f"{settings.wechat_pay_base_url.rstrip('/')}/v3/pay/transactions/jsapi"
    payload = {
        "appid": settings.wechat_mini_appid,
        "mchid": settings.wechat_pay_mch_id,
        "description": _build_order_description(order),
        "out_trade_no": order.order_no,
        "notify_url": settings.wechat_pay_notify_url,
        "amount": {
            "total": _convert_amount_to_fen(order.total_amount),
            "currency": "CNY",
        },
        "payer": {
            "openid": user.openid,
        },
    }
    response = _request_wechat_pay("POST", request_url, payload)
    prepay_id = response.get("prepay_id")
    if not isinstance(prepay_id, str) or not prepay_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="微信支付下单成功，但未返回 prepay_id",
        )

    nonce_str = secrets.token_hex(16)
    time_stamp = str(int(time.time()))
    package = f"prepay_id={prepay_id}"
    sign_type = "RSA"
    pay_sign = _sign_message(
        f"{settings.wechat_mini_appid}\n{time_stamp}\n{nonce_str}\n{package}\n"
    )

    return WechatPayParams(
        app_id=settings.wechat_mini_appid,
        time_stamp=time_stamp,
        nonce_str=nonce_str,
        package=package,
        sign_type=sign_type,
        pay_sign=pay_sign,
        prepay_id=prepay_id,
    )


def query_wechat_payment(order: Order) -> dict[str, Any]:
    _ensure_payment_ready(settings)

    request_url = (
        f"{settings.wechat_pay_base_url.rstrip('/')}"
        f"/v3/pay/transactions/out-trade-no/{quote(order.order_no)}"
        f"?mchid={quote(settings.wechat_pay_mch_id)}"
    )
    return _request_wechat_pay("GET", request_url, None)


def close_wechat_order_if_possible(order: Order) -> None:
    if not _has_close_payment_config(settings):
        return

    request_url = (
        f"{settings.wechat_pay_base_url.rstrip('/')}"
        f"/v3/pay/transactions/out-trade-no/{quote(order.order_no)}/close"
    )
    payload = {
        "mchid": settings.wechat_pay_mch_id,
    }

    try:
        _request_wechat_pay("POST", request_url, payload)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return

        if exc.status_code == status.HTTP_400_BAD_REQUEST and "已支付" in exc.detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="订单支付状态已变化，请刷新后重试",
            ) from exc

        raise


def _expected_amount_in_fen(order: Order) -> int:
    return int(
        (order.total_amount * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _decrypt_resource(ciphertext: str, nonce: str, associated_data: str) -> dict[str, Any]:
    aesgcm = AESGCM(settings.wechat_pay_api_v3_key.encode("utf-8"))
    plaintext = aesgcm.decrypt(
        nonce.encode("utf-8"),
        base64.b64decode(ciphertext),
        associated_data.encode("utf-8"),
    )
    try:
        return json.loads(plaintext.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调解密成功，但内容不是合法 JSON",
        ) from exc


def verify_and_decrypt_wechat_notify(headers: dict[str, str], body: bytes) -> dict[str, Any]:
    _ensure_payment_ready(settings)

    serial = headers.get("wechatpay-serial", "").strip()
    signature = headers.get("wechatpay-signature", "").strip()
    timestamp = headers.get("wechatpay-timestamp", "").strip()
    nonce = headers.get("wechatpay-nonce", "").strip()

    if settings.wechat_pay_platform_serial.strip():
        expected_serial = settings.wechat_pay_platform_serial.strip()
        if serial != expected_serial:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="微信支付回调序列号不匹配",
            )

    if not signature or not timestamp or not nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调缺少必要签名头",
        )

    body_text = body.decode("utf-8")
    _verify_signature(f"{timestamp}\n{nonce}\n{body_text}\n", signature)

    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调内容不是合法 JSON",
        ) from exc

    resource = payload.get("resource")
    if not isinstance(resource, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调缺少 resource",
        )

    algorithm = resource.get("algorithm")
    ciphertext = resource.get("ciphertext")
    resource_nonce = resource.get("nonce")
    associated_data = resource.get("associated_data", "")

    if algorithm != "AEAD_AES_256_GCM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调加密算法不受支持",
        )

    if not isinstance(ciphertext, str) or not isinstance(resource_nonce, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信支付回调缺少加密字段",
        )

    payload["resource_data"] = _decrypt_resource(
        ciphertext=ciphertext,
        nonce=resource_nonce,
        associated_data=associated_data if isinstance(associated_data, str) else "",
    )
    return payload


def parse_wechat_success_time(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def validate_wechat_payment_success(
    order: Order,
    user: User,
    payload: dict[str, Any],
) -> tuple[str | None, datetime | None]:
    callback_appid = payload.get("appid")
    if (
        isinstance(callback_appid, str)
        and callback_appid
        and callback_appid != settings.wechat_mini_appid
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="支付结果 appid 不匹配",
        )

    callback_mchid = payload.get("mchid")
    if (
        isinstance(callback_mchid, str)
        and callback_mchid
        and callback_mchid != settings.wechat_pay_mch_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="支付结果商户号不匹配",
        )

    payer = payload.get("payer")
    if isinstance(payer, dict):
        payer_openid = payer.get("openid")
        if isinstance(payer_openid, str) and payer_openid and payer_openid != user.openid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="支付结果 openid 不匹配",
            )

    amount = payload.get("amount")
    if isinstance(amount, dict):
        total = amount.get("total")
        if isinstance(total, int) and total != _expected_amount_in_fen(order):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="支付结果金额与订单金额不一致",
            )

    transaction_id = payload.get("transaction_id")
    normalized_transaction_id = transaction_id if isinstance(transaction_id, str) else None
    if (
        order.transaction_id
        and normalized_transaction_id
        and order.transaction_id != normalized_transaction_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="支付结果交易号与订单已记录交易号不一致",
        )

    return (
        normalized_transaction_id,
        parse_wechat_success_time(
            payload.get("success_time") if isinstance(payload.get("success_time"), str) else None
        ),
    )
