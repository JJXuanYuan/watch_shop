from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.order_operation_log import OrderOperationLog
from app.models.types import FulfillmentStatus, OrderStatus


@dataclass(frozen=True)
class OrderStateSnapshot:
    status: OrderStatus
    fulfillment_status: FulfillmentStatus


def snapshot_order_state(order: Order) -> OrderStateSnapshot:
    return OrderStateSnapshot(
        status=order.status,
        fulfillment_status=order.fulfillment_status,
    )


def record_order_operation_log(
    db: Session,
    *,
    order: Order,
    action: str,
    action_label: str,
    before_state: OrderStateSnapshot,
    admin_user: AdminUser | None = None,
    detail: dict[str, Any] | None = None,
) -> OrderOperationLog:
    log = OrderOperationLog(
        order_id=order.id,
        admin_user_id=admin_user.id if admin_user is not None else None,
        operator_username=admin_user.username if admin_user is not None else None,
        action=action,
        action_label=action_label,
        before_status=before_state.status,
        after_status=order.status,
        before_fulfillment_status=before_state.fulfillment_status,
        after_fulfillment_status=order.fulfillment_status,
        detail_json=detail or None,
    )
    db.add(log)
    return log
