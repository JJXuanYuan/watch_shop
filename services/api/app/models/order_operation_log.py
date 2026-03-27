from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import FulfillmentStatus, OrderStatus


class OrderOperationLog(Base):
    __tablename__ = "order_operation_logs"
    __table_args__ = (
        Index("ix_order_operation_logs_order_id_created_at", "order_id", "created_at"),
        Index(
            "ix_order_operation_logs_admin_user_id_created_at",
            "admin_user_id",
            "created_at",
        ),
        Index("ix_order_operation_logs_action_created_at", "action", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    admin_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    operator_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    action_label: Mapped[str] = mapped_column(String(100), nullable=False)
    before_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=True,
    )
    after_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=True,
    )
    before_fulfillment_status: Mapped[FulfillmentStatus | None] = mapped_column(
        Enum(
            FulfillmentStatus,
            name="fulfillment_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=True,
    )
    after_fulfillment_status: Mapped[FulfillmentStatus | None] = mapped_column(
        Enum(
            FulfillmentStatus,
            name="fulfillment_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=True,
    )
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.now(),
    )

    order = relationship("Order", back_populates="operation_logs")
    admin_user = relationship("AdminUser")
