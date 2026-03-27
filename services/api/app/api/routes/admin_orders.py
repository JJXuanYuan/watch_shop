from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin, get_db
from app.core.order_logs import record_order_operation_log, snapshot_order_state
from app.core.orders import (
    can_cancel_order,
    can_pay_order,
    cancel_order_with_restock,
    mark_order_completed,
    mark_order_preparing,
    mark_order_shipped,
)
from app.models.admin_user import AdminUser
from app.core.payments import close_wechat_order_if_possible
from app.models.logistics_company import LogisticsCompany
from app.models.order import Order
from app.models.order_operation_log import OrderOperationLog
from app.models.types import (
    FulfillmentStatus,
    LogisticsCompanyStatus,
    OrderStatus,
    PaymentStatus,
)
from app.schemas.address import build_full_address
from app.schemas.order import (
    AdminOrderOperationLogListResponse,
    AdminOrderOperationLogResponse,
    AdminOrderShipRequest,
    AdminOrderListItemResponse,
    AdminOrderListResponse,
    AdminOrderResponse,
    OrderAddressSnapshotResponse,
    OrderItemResponse,
    OrderStatusResponse,
)

router = APIRouter(
    prefix="/admin/orders",
    tags=["admin-orders"],
    dependencies=[Depends(get_current_admin)],
)


def _order_statement():
    return select(Order).options(selectinload(Order.items))


def _get_order_or_404(order_id: int, db: Session) -> Order:
    order = db.scalar(_order_statement().where(Order.id == order_id))
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return order


def _build_order_items(order: Order) -> list[OrderItemResponse]:
    return [
        OrderItemResponse.model_validate(item)
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


def _resolve_shipping_company(
    payload: AdminOrderShipRequest,
    db: Session,
) -> tuple[str | None, str]:
    if payload.shipping_company_code:
        company = db.scalar(
            select(LogisticsCompany).where(
                LogisticsCompany.code == payload.shipping_company_code,
                LogisticsCompany.status == LogisticsCompanyStatus.ENABLED,
            )
        )
        if company is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="所选物流公司不存在或已停用",
            )

        return company.code, company.name

    if payload.shipping_company is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择物流公司或手动输入物流公司名称",
        )

    return None, payload.shipping_company


def _build_admin_order_response(order: Order) -> AdminOrderResponse:
    items = _build_order_items(order)
    return AdminOrderResponse(
        id=order.id,
        order_no=order.order_no,
        payment_no=order.order_no,
        user_key=order.user_key,
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


def _build_admin_order_list_item(order: Order) -> AdminOrderListItemResponse:
    return AdminOrderListItemResponse(
        id=order.id,
        order_no=order.order_no,
        payment_no=order.order_no,
        user_key=order.user_key,
        total_amount=order.total_amount,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        can_cancel=can_cancel_order(order),
        can_pay=can_pay_order(order),
        item_count=len(order.items),
        total_quantity=_calculate_total_quantity(order),
        paid_at=order.paid_at,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        created_at=order.created_at,
        updated_at=order.updated_at,
        **_build_shipping_payload(order),
    )


def _build_admin_order_operation_log_response(
    log: OrderOperationLog,
) -> AdminOrderOperationLogResponse:
    return AdminOrderOperationLogResponse(
        log_id=log.id,
        order_id=log.order_id,
        admin_user_id=log.admin_user_id,
        operator_username=log.operator_username,
        action=log.action,
        action_label=log.action_label,
        before_status=log.before_status,
        after_status=log.after_status,
        before_fulfillment_status=log.before_fulfillment_status,
        after_fulfillment_status=log.after_fulfillment_status,
        detail=log.detail_json,
        created_at=log.created_at,
    )


@router.get("", response_model=AdminOrderListResponse, summary="List admin orders")
def list_admin_orders(
    order_no: str | None = Query(default=None, max_length=64),
    user_key: str | None = Query(default=None, max_length=64),
    status_value: OrderStatus | None = Query(default=None, alias="status"),
    payment_status_value: PaymentStatus | None = Query(default=None, alias="payment_status"),
    fulfillment_status_value: FulfillmentStatus | None = Query(
        default=None,
        alias="fulfillment_status",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminOrderListResponse:
    filters = []

    if order_no:
        filters.append(Order.order_no.ilike(f"%{order_no.strip()}%"))

    if user_key:
        filters.append(Order.user_key.ilike(f"%{user_key.strip()}%"))

    if status_value is not None:
        filters.append(Order.status == status_value)

    if payment_status_value is not None:
        filters.append(Order.payment_status == payment_status_value)

    if fulfillment_status_value is not None:
        filters.append(Order.status == OrderStatus.PAID)
        filters.append(Order.payment_status == PaymentStatus.PAID)
        filters.append(Order.fulfillment_status == fulfillment_status_value)

    total = db.scalar(select(func.count(Order.id)).where(*filters)) or 0

    orders = db.scalars(
        _order_statement()
        .where(*filters)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return AdminOrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_build_admin_order_list_item(order) for order in orders],
    )


@router.get(
    "/{order_id}",
    response_model=AdminOrderResponse,
    summary="Get admin order detail",
)
def get_admin_order_detail(
    order_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AdminOrderResponse:
    return _build_admin_order_response(_get_order_or_404(order_id, db))


@router.get(
    "/{order_id}/logs",
    response_model=AdminOrderOperationLogListResponse,
    summary="Get admin order operation logs",
)
def get_admin_order_logs(
    order_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AdminOrderOperationLogListResponse:
    _get_order_or_404(order_id, db)
    logs = db.scalars(
        select(OrderOperationLog)
        .where(OrderOperationLog.order_id == order_id)
        .order_by(OrderOperationLog.created_at.desc(), OrderOperationLog.id.desc())
    ).all()

    return AdminOrderOperationLogListResponse(
        items=[_build_admin_order_operation_log_response(log) for log in logs],
    )


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderStatusResponse,
    summary="Cancel admin pending order",
)
def cancel_admin_order(
    order_id: int = Path(..., gt=0),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> OrderStatusResponse:
    order = _get_order_or_404(order_id, db)
    before_state = snapshot_order_state(order)
    close_wechat_order_if_possible(order)
    cancel_order_with_restock(order, db)
    record_order_operation_log(
        db,
        order=order,
        action="cancel",
        action_label="管理员取消订单",
        before_state=before_state,
        admin_user=current_admin,
        detail={"inventory_restocked": True},
    )
    db.commit()

    return OrderStatusResponse(
        id=order.id,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        can_cancel=can_cancel_order(order),
        can_pay=can_pay_order(order),
    )


@router.patch(
    "/{order_id}/prepare",
    response_model=AdminOrderResponse,
    summary="Mark admin paid order as preparing",
)
def prepare_admin_order(
    order_id: int = Path(..., gt=0),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminOrderResponse:
    order = _get_order_or_404(order_id, db)
    before_state = snapshot_order_state(order)
    mark_order_preparing(order)
    record_order_operation_log(
        db,
        order=order,
        action="prepare",
        action_label="管理员备货",
        before_state=before_state,
        admin_user=current_admin,
    )
    db.commit()
    db.refresh(order)
    return _build_admin_order_response(order)


@router.patch(
    "/{order_id}/ship",
    response_model=AdminOrderResponse,
    summary="Ship admin preparing order",
)
def ship_admin_order(
    payload: AdminOrderShipRequest = Body(...),
    order_id: int = Path(..., gt=0),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminOrderResponse:
    order = _get_order_or_404(order_id, db)
    before_state = snapshot_order_state(order)
    shipping_company_code, shipping_company = _resolve_shipping_company(payload, db)
    mark_order_shipped(
        order,
        shipping_company_code=shipping_company_code,
        shipping_company=shipping_company,
        tracking_no=payload.tracking_no,
        shipping_note=payload.shipping_note,
    )
    record_order_operation_log(
        db,
        order=order,
        action="ship",
        action_label="管理员发货",
        before_state=before_state,
        admin_user=current_admin,
        detail={
            "shipping_company_code": order.shipping_company_code,
            "shipping_company": order.shipping_company,
            "tracking_no": order.tracking_no,
            "shipping_note": order.shipping_note,
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        },
    )
    db.commit()
    db.refresh(order)
    return _build_admin_order_response(order)


@router.patch(
    "/{order_id}/complete",
    response_model=AdminOrderResponse,
    summary="Complete admin shipped order",
)
def complete_admin_order(
    order_id: int = Path(..., gt=0),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminOrderResponse:
    order = _get_order_or_404(order_id, db)
    before_state = snapshot_order_state(order)
    mark_order_completed(order)
    record_order_operation_log(
        db,
        order=order,
        action="complete",
        action_label="管理员完成履约",
        before_state=before_state,
        admin_user=current_admin,
        detail={
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        },
    )
    db.commit()
    db.refresh(order)
    return _build_admin_order_response(order)
