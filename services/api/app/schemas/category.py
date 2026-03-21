from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CategoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sort_order: int


class CategoryListResponse(BaseModel):
    items: list[CategoryItem]
