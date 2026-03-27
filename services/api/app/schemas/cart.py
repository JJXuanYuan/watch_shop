from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.types import ProductStatus


class CartItemCreateRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    name: str
    subtitle: Optional[str]
    cover_image: str
    price: Decimal
    quantity: int
    subtotal_amount: Decimal
    stock: int
    status: ProductStatus
    is_available: bool
    availability_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    item_count: int
    total_quantity: int
    total_amount: Decimal
