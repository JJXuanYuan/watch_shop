from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.types import FulfillmentStatus, OrderStatus, PaymentStatus


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_key_status", "user_key", "status"),
        Index("ix_orders_user_id_status", "user_id", "status"),
        Index("ix_orders_user_id_created_at", "user_id", "created_at"),
        Index("ix_orders_created_at_status", "created_at", "status"),
        Index("ix_orders_payment_status_created_at", "payment_status", "created_at"),
        Index("ix_orders_fulfillment_status_created_at", "fulfillment_status", "created_at"),
        Index("ix_orders_transaction_id", "transaction_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    user_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=text("'pending'"),
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=PaymentStatus.UNPAID,
        server_default=text("'unpaid'"),
    )
    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        Enum(
            FulfillmentStatus,
            name="fulfillment_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=FulfillmentStatus.UNFULFILLED,
        server_default=text("'unfulfilled'"),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    receiver_province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_detail_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_company_code: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )
    shipping_company: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    operation_logs = relationship(
        "OrderOperationLog",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    user = relationship("User", back_populates="orders")
