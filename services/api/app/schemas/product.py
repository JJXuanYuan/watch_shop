from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.types import ProductStatus


class ProductCategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category: ProductCategorySummary
    title: str
    subtitle: Optional[str]
    cover_image: str
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    is_featured: bool
    created_at: datetime


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductListItem]


class ProductDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category: ProductCategorySummary
    title: str
    subtitle: Optional[str]
    cover_image: str
    image_list: list[str]
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    is_featured: bool
    detail: Optional[str]
    created_at: datetime
    updated_at: datetime
