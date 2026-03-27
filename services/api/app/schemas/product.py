from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.models.types import CategoryStatus, ProductStatus


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


class ProductCategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    status: CategoryStatus


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category: ProductCategorySummary
    name: str
    subtitle: Optional[str]
    cover_image: str
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    sort_order: int
    is_featured: bool
    created_at: datetime

    @computed_field(return_type=str)
    @property
    def title(self) -> str:
        return self.name


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
    name: str
    subtitle: Optional[str]
    cover_image: str
    banner_images: list[str]
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    sort_order: int
    is_featured: bool
    detail_content: Optional[str]
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=str)
    @property
    def title(self) -> str:
        return self.name

    @computed_field(return_type=list[str])
    @property
    def image_list(self) -> list[str]:
        return self.banner_images

    @computed_field(return_type=Optional[str])
    @property
    def detail(self) -> Optional[str]:
        return self.detail_content


class AdminProductPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    category_id: int = Field(gt=0)
    price: Decimal = Field(gt=0)
    original_price: Optional[Decimal] = Field(default=None, gt=0)
    stock: int = Field(default=0, ge=0)
    sales: int = Field(default=0, ge=0)
    status: ProductStatus = ProductStatus.DRAFT
    cover_image: str = Field(min_length=1, max_length=500)
    banner_images: list[str] = Field(default_factory=list)
    detail_content: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)
    is_featured: bool = False

    @field_validator("name", "cover_image")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned

    @field_validator("subtitle", "detail_content", mode="before")
    @classmethod
    def validate_optional_text(cls, value: Optional[str]) -> Optional[str]:
        return _clean_optional_text(value)

    @field_validator("banner_images")
    @classmethod
    def validate_banner_images(cls, value: list[str]) -> list[str]:
        images = [item.strip() for item in value if item and item.strip()]
        return images

    @model_validator(mode="after")
    def validate_prices_and_images(self) -> "AdminProductPayload":
        if self.original_price is not None and self.original_price < self.price:
            raise ValueError("original_price must be greater than or equal to price")

        if not self.banner_images:
            self.banner_images = [self.cover_image]

        return self


class AdminProductCreateRequest(AdminProductPayload):
    pass


class AdminProductUpdateRequest(AdminProductPayload):
    pass


class AdminProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category: ProductCategorySummary
    name: str
    subtitle: Optional[str]
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    cover_image: str
    sort_order: int
    is_featured: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=str)
    @property
    def category_name(self) -> str:
        return self.category.name

    @computed_field(return_type=bool)
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class AdminProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminProductListItem]


class AdminProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category: ProductCategorySummary
    name: str
    subtitle: Optional[str]
    price: Decimal
    original_price: Optional[Decimal]
    stock: int
    sales: int
    status: ProductStatus
    cover_image: str
    banner_images: list[str]
    detail_content: Optional[str]
    sort_order: int
    is_featured: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=bool)
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class ProductStatusResponse(BaseModel):
    id: int
    status: ProductStatus


class ProductDeletionResponse(BaseModel):
    id: int
    deleted_at: Optional[datetime]
    is_deleted: bool
