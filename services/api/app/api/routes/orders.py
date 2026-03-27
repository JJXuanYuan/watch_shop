from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.models.address import Address
from app.core.orders import (
    can_cancel_order,
    can_pay_order,
    cancel_order_with_restock,
    ensure_order_can_pay,
    ensure_order_can_query_payment,
    mark_order_paid,
)
from app.core.payments import (
    close_wechat_order_if_possible,
    create_wechat_payment,
    query_wechat_payment,
    validate_wechat_payment_success,
)
from app.core.trade import build_order_no, calculate_subtotal, resolve_product_purchase_issue
from app.core.users import build_user_key
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.types import FulfillmentStatus, OrderStatus, PaymentStatus
from app.schemas.address import build_full_address
from app.schemas.order import (
    OrderAddressSnapshotResponse,
    OrderCreateRequest,
    OrderItemResponse,
    OrderListItemResponse,
    OrderListResponse,
    OrderPaymentQueryResponse,
    OrderResponse,
    OrderStatusResponse,
    OrderSummaryItemResponse,
)
from app.schemas.payment import WechatPayCreateResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def _query_cart_items(user_id: int, db: Session) -> list[CartItem]:
    statement = (
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id.asc())
    )
    return db.scalars(statement).all()


def _order_statement():
    return select(Order).options(selectinload(Order.items))


def _get_order_or_404(order_id: int, user_id: int, db: Session) -> Order:
    order = db.scalar(
        _order_statement().where(Order.id == order_id, Order.user_id == user_id)
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return order


def _get_address_or_404(address_id: int, user_id: int, db: Session) -> Address:
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收货地址不存在",
        )
    return address


def _build_unique_order_no(db: Session) -> str:
    for _ in range(5):
        order_no = build_order_no()
        if db.scalar(select(Order.id).where(Order.order_no == order_no)) is None:
            return order_no

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="订单号生成失败，请稍后重试",
    )


def _build_order_item_responses(order: Order) -> list[OrderItemResponse]:
    return [
        OrderItemResponse.model_validate(item)
        for item in sorted(order.items, key=lambda current: current.id)
    ]


def _build_order_summary_items(order: Order) -> list[OrderSummaryItemResponse]:
    return [
        OrderSummaryItemResponse.model_validate(item)
        for item in sorted(order.items, key=lambda current: current.id)
    ]


def _calculate_total_quantity(order: Order) -> int:
    return sum(item.quantity for item in order.items)


def _build_order_address_snapshot(order: Order) -> OrderAddressSnapshotResponse | None:
    if not (
        order.receiver_name
        and order.receiver_phone
        and order.receiver_province
        and order.receiver_city
        and order.receiver_district
        and order.receiver_detail_address
    ):
        return None

    return OrderAddressSnapshotResponse(
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        province=order.receiver_province,
        city=order.receiver_city,
        district=order.receiver_district,
        detail_address=order.receiver_detail_address,
        full_address=build_full_address(
            order.receiver_province,
            order.receiver_city,
            order.receiver_district,
            order.receiver_detail_address,
        ),
    )


def _build_shipping_payload(order: Order) -> dict[str, str | datetime | None]:
    return {
        "shipping_company_code": order.shipping_company_code,
        "shipping_company": order.shipping_company,
        "tracking_no": order.tracking_no,
        "shipping_note": order.shipping_note,
        "shipped_at": order.shipped_at,
        "completed_at": order.completed_at,
    }


def _build_order_response(order: Order) -> OrderResponse:
    items = _build_order_item_responses(order)
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        payment_no=order.order_no,
        total_amount=order.total_amount,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        can_cancel=can_cancel_order(order),
        can_pay=can_pay_order(order),
        item_count=len(items),
        total_quantity=_calculate_total_quantity(order),
        paid_at=order.paid_at,
        transaction_id=order.transaction_id,
        address=_build_order_address_snapshot(order),
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items,
        **_build_shipping_payload(order),
    )


def _build_order_list_item(order: Order) -> OrderListItemResponse:
    summary_items = _build_order_summary_items(order)
    return OrderListItemResponse(
        id=order.id,
        order_no=order.order_no,
        payment_no=order.order_no,
        total_amount=order.total_amount,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        can_cancel=can_cancel_order(order),
        can_pay=can_pay_order(order),
        item_count=len(summary_items),
        total_quantity=_calculate_total_quantity(order),
        paid_at=order.paid_at,
        receiver_name=order.receiver_name,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=summary_items,
        **_build_shipping_payload(order),
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
)
def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    cart_items = _query_cart_items(current_user.id, db)
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="购物车为空",
        )

    for cart_item in cart_items:
        issue = resolve_product_purchase_issue(cart_item.product, cart_item.quantity)
        if issue is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{cart_item.product.name}：{issue}",
            )

    address = _get_address_or_404(payload.address_id, current_user.id, db)
    order = Order(
        order_no=_build_unique_order_no(db),
        user_id=current_user.id,
        user_key=build_user_key(current_user.id),
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
        fulfillment_status=FulfillmentStatus.UNFULFILLED,
        total_amount=Decimal("0.00"),
        receiver_name=address.receiver_name,
        receiver_phone=address.receiver_phone,
        receiver_province=address.province,
        receiver_city=address.city,
        receiver_district=address.district,
        receiver_detail_address=address.detail_address,
    )
    db.add(order)
    db.flush()

    total_amount = Decimal("0.00")
    for cart_item in cart_items:
        product = cart_item.product
        subtotal_amount = calculate_subtotal(product.price, cart_item.quantity)
        total_amount += subtotal_amount

        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name_snapshot=product.name,
                price_snapshot=product.price,
                quantity=cart_item.quantity,
                subtotal_amount=subtotal_amount,
            )
        )
        product.stock -= cart_item.quantity

    order.total_amount = total_amount

    for cart_item in cart_items:
        db.delete(cart_item)

    db.commit()

    return _build_order_response(_get_order_or_404(order.id, current_user.id, db))


@router.post(
    "/{order_id}/pay",
    response_model=WechatPayCreateResponse,
    summary="Create Wechat pay params for current user order",
)
def create_order_payment(
    order_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WechatPayCreateResponse:
    order = _get_order_or_404(order_id, current_user.id, db)
    ensure_order_can_pay(order)
    pay_params = create_wechat_payment(order, current_user)

    return WechatPayCreateResponse(
        order_id=order.id,
        order_no=order.order_no,
        payment_no=order.order_no,
        appId=pay_params.app_id,
        timeStamp=pay_params.time_stamp,
        nonceStr=pay_params.nonce_str,
        package=pay_params.package,
        signType=pay_params.sign_type,
        paySign=pay_params.pay_sign,
        prepayId=pay_params.prepay_id,
    )


@router.get("", response_model=OrderListResponse, summary="List current user orders")
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    total = (
        db.scalar(select(func.count(Order.id)).where(Order.user_id == current_user.id)) or 0
    )

    orders = db.scalars(
        _order_statement()
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return OrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_build_order_list_item(order) for order in orders],
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get current user order detail",
)
def get_order_detail(
    order_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return _build_order_response(_get_order_or_404(order_id, current_user.id, db))


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderStatusResponse,
    summary="Cancel current user pending order",
)
@router.post(
    "/{order_id}/cancel",
    response_model=OrderStatusResponse,
    summary="Cancel current user pending order",
)
def cancel_order(
    order_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderStatusResponse:
    order = _get_order_or_404(order_id, current_user.id, db)
    close_wechat_order_if_possible(order)
    cancel_order_with_restock(order, db)
    db.commit()

    return OrderStatusResponse(
        id=order.id,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        can_cancel=can_cancel_order(order),
        can_pay=can_pay_order(order),
    )


@router.post(
    "/{order_id}/payment-query",
    response_model=OrderPaymentQueryResponse,
    summary="Query current user wechat payment result",
)
def query_order_payment_result(
    order_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderPaymentQueryResponse:
    order = _get_order_or_404(order_id, current_user.id, db)
    ensure_order_can_query_payment(order)

    try:
        wechat_payload = query_wechat_payment(order)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="当前订单尚未产生可确认的微信支付记录，请重新发起支付",
            ) from exc
        raise

    trade_state = wechat_payload.get("trade_state")
    trade_state_value = trade_state if isinstance(trade_state, str) else None
    trade_state_desc = (
        wechat_payload.get("trade_state_desc")
        if isinstance(wechat_payload.get("trade_state_desc"), str)
        else None
    )

    synced = False
    if trade_state_value == "SUCCESS":
        transaction_id, paid_at = validate_wechat_payment_success(
            order,
            current_user,
            wechat_payload,
        )
        synced = mark_order_paid(
            order,
            transaction_id=transaction_id,
            paid_at=paid_at,
        )
        db.commit()
        db.refresh(order)

    return OrderPaymentQueryResponse(
        synced=synced,
        trade_state=trade_state_value,
        trade_state_desc=trade_state_desc,
        order=_build_order_response(_get_order_or_404(order.id, current_user.id, db)),
    )
