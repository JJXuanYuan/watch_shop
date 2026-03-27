from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.types import FulfillmentStatus, OrderStatus, PaymentStatus


def can_cancel_order(order: Order) -> bool:
    return order.status == OrderStatus.PENDING and order.payment_status == PaymentStatus.UNPAID


def can_pay_order(order: Order) -> bool:
    return order.status == OrderStatus.PENDING and order.payment_status == PaymentStatus.UNPAID


def can_prepare_order(order: Order) -> bool:
    return (
        order.status == OrderStatus.PAID
        and order.payment_status == PaymentStatus.PAID
        and order.fulfillment_status == FulfillmentStatus.UNFULFILLED
    )


def can_ship_order(order: Order) -> bool:
    return (
        order.status == OrderStatus.PAID
        and order.payment_status == PaymentStatus.PAID
        and order.fulfillment_status == FulfillmentStatus.PREPARING
    )


def can_complete_order(order: Order) -> bool:
    return (
        order.status == OrderStatus.PAID
        and order.payment_status == PaymentStatus.PAID
        and order.fulfillment_status == FulfillmentStatus.SHIPPED
    )


def ensure_order_can_pay(order: Order) -> None:
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已取消订单不能支付",
        )

    if order.status == OrderStatus.PAID or order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单已支付，不能重复支付",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前订单状态不支持支付",
        )


def ensure_order_can_query_payment(order: Order) -> None:
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已取消订单不能查单",
        )

    if order.status == OrderStatus.PAID or order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单已支付，无需重复查单",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前订单状态不支持查单",
        )


def ensure_order_can_cancel(order: Order) -> None:
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单已取消，不能重复取消",
        )

    if order.status == OrderStatus.PAID or order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已支付订单当前不支持取消",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前订单状态不支持取消",
        )


def _ensure_order_in_paid_fulfillment_chain(order: Order, action_name: str) -> None:
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已取消订单不能执行{action_name}",
        )

    if order.status != OrderStatus.PAID or order.payment_status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"只有已支付订单才能执行{action_name}",
        )


def ensure_order_can_prepare(order: Order) -> None:
    _ensure_order_in_paid_fulfillment_chain(order, "备货")

    if order.fulfillment_status == FulfillmentStatus.UNFULFILLED:
        return

    if order.fulfillment_status == FulfillmentStatus.PREPARING:
        detail = "订单已在备货中，不能重复备货"
    elif order.fulfillment_status == FulfillmentStatus.SHIPPED:
        detail = "订单已发货，不能回退到备货中"
    else:
        detail = "订单已完成，不能回退到备货中"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def ensure_order_can_ship(order: Order) -> None:
    _ensure_order_in_paid_fulfillment_chain(order, "发货")

    if order.fulfillment_status == FulfillmentStatus.PREPARING:
        return

    if order.fulfillment_status == FulfillmentStatus.UNFULFILLED:
        detail = "订单需先进入备货中，才能发货"
    elif order.fulfillment_status == FulfillmentStatus.SHIPPED:
        detail = "订单已发货，不能重复发货"
    else:
        detail = "订单已完成，不能重复发货"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def ensure_order_can_complete(order: Order) -> None:
    _ensure_order_in_paid_fulfillment_chain(order, "完成履约")

    if order.fulfillment_status == FulfillmentStatus.SHIPPED:
        return

    if order.fulfillment_status == FulfillmentStatus.UNFULFILLED:
        detail = "订单尚未发货，不能直接完成"
    elif order.fulfillment_status == FulfillmentStatus.PREPARING:
        detail = "订单仍在备货中，不能直接完成"
    else:
        detail = "订单已完成，不能重复完成"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def cancel_order_with_restock(order: Order, db: Session) -> None:
    ensure_order_can_cancel(order)

    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="订单关联商品不存在，无法回补库存",
            )

        product.stock += item.quantity

    order.status = OrderStatus.CANCELLED


def mark_order_preparing(order: Order) -> None:
    ensure_order_can_prepare(order)
    order.fulfillment_status = FulfillmentStatus.PREPARING


def mark_order_shipped(
    order: Order,
    *,
    shipping_company_code: str | None,
    shipping_company: str,
    tracking_no: str,
    shipping_note: str | None,
) -> None:
    ensure_order_can_ship(order)
    order.fulfillment_status = FulfillmentStatus.SHIPPED
    order.shipping_company_code = shipping_company_code
    order.shipping_company = shipping_company
    order.tracking_no = tracking_no
    order.shipping_note = shipping_note
    order.shipped_at = datetime.now()


def mark_order_completed(order: Order) -> None:
    ensure_order_can_complete(order)
    order.fulfillment_status = FulfillmentStatus.COMPLETED
    order.completed_at = datetime.now()


def mark_order_paid(
    order: Order,
    *,
    transaction_id: str | None,
    paid_at: datetime | None,
) -> bool:
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="订单已取消，不能更新为已支付",
        )

    if order.status == OrderStatus.PAID or order.payment_status == PaymentStatus.PAID:
        if transaction_id and not order.transaction_id:
            order.transaction_id = transaction_id
        if paid_at and order.paid_at is None:
            order.paid_at = paid_at
        order.status = OrderStatus.PAID
        order.payment_status = PaymentStatus.PAID
        order.fulfillment_status = order.fulfillment_status or FulfillmentStatus.UNFULFILLED
        return False

    ensure_order_can_pay(order)

    order.status = OrderStatus.PAID
    order.payment_status = PaymentStatus.PAID
    order.fulfillment_status = FulfillmentStatus.UNFULFILLED
    order.transaction_id = transaction_id
    order.paid_at = paid_at
    return True
