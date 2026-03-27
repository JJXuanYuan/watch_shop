from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.types import CategoryStatus


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


class CategoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sort_order: int
    status: CategoryStatus


class CategoryListResponse(BaseModel):
    items: list[CategoryItem]


class AdminCategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: Optional[str] = Field(default=None, max_length=100)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        return _clean_optional_text(value)


class AdminCategoryCreateRequest(AdminCategoryPayload):
    pass


class AdminCategoryUpdateRequest(AdminCategoryPayload):
    pass


class AdminCategoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sort_order: int
    status: CategoryStatus
    product_count: int = 0
    created_at: datetime
    updated_at: datetime


class AdminCategoryListResponse(BaseModel):
    items: list[AdminCategoryItem]


class CategoryStatusResponse(BaseModel):
    id: int
    status: CategoryStatus
