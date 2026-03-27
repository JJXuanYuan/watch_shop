from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.types import FulfillmentStatus, OrderStatus, PaymentStatus


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name_snapshot: str
    price_snapshot: Decimal
    quantity: int
    subtotal_amount: Decimal


class OrderSummaryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name_snapshot: str
    quantity: int


class OrderAddressSnapshotResponse(BaseModel):
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    full_address: str


class OrderCreateRequest(BaseModel):
    address_id: int = Field(..., gt=0)


class OrderShippingInfoResponse(BaseModel):
    shipping_company_code: str | None
    shipping_company: str | None
    tracking_no: str | None
    shipping_note: str | None
    shipped_at: datetime | None
    completed_at: datetime | None


class OrderResponse(OrderShippingInfoResponse):
    id: int
    order_no: str
    payment_no: str
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    can_cancel: bool
    can_pay: bool
    item_count: int
    total_quantity: int
    paid_at: datetime | None
    transaction_id: str | None
    address: OrderAddressSnapshotResponse | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]


class OrderListItemResponse(OrderShippingInfoResponse):
    id: int
    order_no: str
    payment_no: str
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    can_cancel: bool
    can_pay: bool
    item_count: int
    total_quantity: int
    paid_at: datetime | None
    receiver_name: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderSummaryItemResponse]


class OrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[OrderListItemResponse]


class OrderStatusResponse(BaseModel):
    id: int
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    can_cancel: bool
    can_pay: bool


class OrderPaymentQueryResponse(BaseModel):
    synced: bool
    trade_state: str | None
    trade_state_desc: str | None
    order: OrderResponse


class AdminOrderListItemResponse(OrderShippingInfoResponse):
    id: int
    order_no: str
    payment_no: str
    user_key: str
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    can_cancel: bool
    can_pay: bool
    item_count: int
    total_quantity: int
    paid_at: datetime | None
    receiver_name: str | None
    receiver_phone: str | None
    created_at: datetime
    updated_at: datetime


class AdminOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminOrderListItemResponse]


class AdminOrderResponse(OrderShippingInfoResponse):
    id: int
    order_no: str
    payment_no: str
    user_key: str
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    can_cancel: bool
    can_pay: bool
    item_count: int
    total_quantity: int
    paid_at: datetime | None
    transaction_id: str | None
    address: OrderAddressSnapshotResponse | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]


class AdminOrderShipRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    shipping_company_code: str | None = Field(default=None, max_length=32)
    shipping_company: str | None = Field(default=None, max_length=100)
    tracking_no: str = Field(..., min_length=1, max_length=64)
    shipping_note: str | None = Field(default=None, max_length=255)

    @field_validator("shipping_company_code")
    @classmethod
    def normalize_shipping_company_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        return cleaned or None

    @field_validator("shipping_company")
    @classmethod
    def normalize_shipping_company(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value or None

    @field_validator("shipping_note")
    @classmethod
    def normalize_shipping_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value or None

    @model_validator(mode="after")
    def validate_shipping_company_source(self) -> "AdminOrderShipRequest":
        if self.shipping_company_code or self.shipping_company:
            return self

        raise ValueError("请选择物流公司或手动输入物流公司名称")


class AdminOrderOperationLogResponse(BaseModel):
    log_id: int
    order_id: int
    admin_user_id: int | None
    operator_username: str | None
    action: str
    action_label: str
    before_status: OrderStatus | None
    after_status: OrderStatus | None
    before_fulfillment_status: FulfillmentStatus | None
    after_fulfillment_status: FulfillmentStatus | None
    detail: dict[str, Any] | None
    created_at: datetime


class AdminOrderOperationLogListResponse(BaseModel):
    items: list[AdminOrderOperationLogResponse]
