from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.types import CategoryStatus
from app.schemas.category import (
    AdminCategoryCreateRequest,
    AdminCategoryItem,
    AdminCategoryListResponse,
    AdminCategoryUpdateRequest,
    CategoryStatusResponse,
)

router = APIRouter(
    prefix="/admin/categories",
    tags=["admin-categories"],
    dependencies=[Depends(get_current_admin)],
)

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _build_slug(source: str) -> str:
    normalized = source.strip().lower()
    slug = SLUG_PATTERN.sub("-", normalized).strip("-")
    return slug or "category"


def _find_category_by_name(
    name: str,
    db: Session,
    exclude_id: Optional[int] = None,
) -> ProductCategory | None:
    statement = select(ProductCategory).where(ProductCategory.name == name)
    if exclude_id is not None:
        statement = statement.where(ProductCategory.id != exclude_id)
    return db.scalar(statement)


def _find_category_by_slug(
    slug_value: str,
    db: Session,
    exclude_id: Optional[int] = None,
) -> ProductCategory | None:
    statement = select(ProductCategory).where(ProductCategory.slug == slug_value)
    if exclude_id is not None:
        statement = statement.where(ProductCategory.id != exclude_id)
    return db.scalar(statement)


def _ensure_unique_slug(
    slug_value: str,
    db: Session,
    exclude_id: Optional[int] = None,
) -> str:
    base_slug = _build_slug(slug_value)
    candidate = base_slug
    index = 2

    while _find_category_by_slug(candidate, db, exclude_id=exclude_id) is not None:
        candidate = f"{base_slug}-{index}"
        index += 1

    return candidate


def _get_category_or_404(category_id: int, db: Session) -> ProductCategory:
    category = db.get(ProductCategory, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


def _serialize_category(
    category: ProductCategory,
    product_count: int = 0,
) -> AdminCategoryItem:
    item = AdminCategoryItem.model_validate(category)
    return item.model_copy(update={"product_count": product_count})


@router.get(
    "",
    response_model=AdminCategoryListResponse,
    summary="List admin categories",
)
def list_admin_categories(db: Session = Depends(get_db)) -> AdminCategoryListResponse:
    product_count_subquery = (
        select(Product.category_id, func.count(Product.id).label("product_count"))
        .group_by(Product.category_id)
        .subquery()
    )

    statement = (
        select(
            ProductCategory,
            func.coalesce(product_count_subquery.c.product_count, 0),
        )
        .outerjoin(
            product_count_subquery,
            product_count_subquery.c.category_id == ProductCategory.id,
        )
        .order_by(ProductCategory.sort_order.asc(), ProductCategory.id.asc())
    )

    rows = db.execute(statement).all()
    items = [
        _serialize_category(category, product_count=product_count)
        for category, product_count in rows
    ]
    return AdminCategoryListResponse(items=items)


@router.post(
    "",
    response_model=AdminCategoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
def create_category(
    payload: AdminCategoryCreateRequest,
    db: Session = Depends(get_db),
) -> AdminCategoryItem:
    if _find_category_by_name(payload.name, db) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        )

    requested_slug = payload.slug or payload.name
    slug_value = _ensure_unique_slug(requested_slug, db)

    category = ProductCategory(
        name=payload.name,
        slug=slug_value,
        sort_order=payload.sort_order,
        status=CategoryStatus.ENABLED,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return _serialize_category(category)


@router.put(
    "/{category_id}",
    response_model=AdminCategoryItem,
    summary="Update category",
)
def update_category(
    payload: AdminCategoryUpdateRequest,
    category_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AdminCategoryItem:
    category = _get_category_or_404(category_id, db)

    if _find_category_by_name(payload.name, db, exclude_id=category_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        )

    category.name = payload.name
    category.sort_order = payload.sort_order

    if payload.slug is not None:
        category.slug = _ensure_unique_slug(payload.slug, db, exclude_id=category_id)

    db.commit()
    db.refresh(category)

    product_count = db.scalar(
        select(func.count(Product.id)).where(Product.category_id == category.id)
    ) or 0
    return _serialize_category(category, product_count=product_count)


@router.patch(
    "/{category_id}/enable",
    response_model=CategoryStatusResponse,
    summary="Enable category",
)
def enable_category(
    category_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> CategoryStatusResponse:
    category = _get_category_or_404(category_id, db)
    category.status = CategoryStatus.ENABLED
    db.commit()

    return CategoryStatusResponse(id=category.id, status=category.status)


@router.patch(
    "/{category_id}/disable",
    response_model=CategoryStatusResponse,
    summary="Disable category",
)
def disable_category(
    category_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> CategoryStatusResponse:
    category = _get_category_or_404(category_id, db)
    category.status = CategoryStatus.DISABLED
    db.commit()

    return CategoryStatusResponse(id=category.id, status=category.status)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
)
def delete_category(
    category_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> Response:
    category = _get_category_or_404(category_id, db)
    product_count = db.scalar(
        select(func.count(Product.id)).where(Product.category_id == category.id)
    ) or 0
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category still has related products and cannot be deleted",
        )

    db.delete(category)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
