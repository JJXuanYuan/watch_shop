from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.orders import mark_order_paid
from app.core.payments import (
    validate_wechat_payment_success,
    verify_and_decrypt_wechat_notify,
)
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


def _notify_success(message: str = "成功") -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"code": "SUCCESS", "message": message},
    )


def _notify_fail(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": "FAIL", "message": message},
    )


@router.post("/notify/wechat", summary="Handle Wechat Pay notification")
async def handle_wechat_pay_notify(
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    body = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}

    try:
        payload = verify_and_decrypt_wechat_notify(headers, body)
    except Exception as exc:
        message = exc.detail if hasattr(exc, "detail") else "微信支付回调处理失败"
        status_code = exc.status_code if hasattr(exc, "status_code") else 400
        return _notify_fail(str(message), status_code)

    resource_data = payload.get("resource_data")
    if not isinstance(resource_data, dict):
        return _notify_fail("微信支付回调缺少解密后的资源数据")

    if resource_data.get("trade_state") != "SUCCESS":
        return _notify_success("已忽略非成功支付通知")

    out_trade_no = resource_data.get("out_trade_no")
    if not isinstance(out_trade_no, str) or not out_trade_no:
        return _notify_fail("微信支付回调缺少商户订单号")

    order = db.scalar(select(Order).where(Order.order_no == out_trade_no))
    if order is None:
        return _notify_fail("订单不存在", 404)

    if order.user_id is None:
        return _notify_fail("订单未绑定用户，无法确认支付", 409)

    user = db.get(User, order.user_id)
    if user is None or not user.openid:
        return _notify_fail("订单缺少有效用户 openid", 409)

    try:
        transaction_id, paid_at = validate_wechat_payment_success(order, user, resource_data)
        mark_order_paid(
            order,
            transaction_id=transaction_id,
            paid_at=paid_at,
        )
        db.commit()
    except Exception as exc:
        message = exc.detail if hasattr(exc, "detail") else "订单支付状态更新失败"
        status_code = exc.status_code if hasattr(exc, "status_code") else 409
        return _notify_fail(str(message), status_code)

    return _notify_success()
