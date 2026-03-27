from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin, get_db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.types import CategoryStatus, ProductDeletedFilter, ProductStatus
from app.schemas.product import (
    AdminProductCreateRequest,
    AdminProductListItem,
    AdminProductListResponse,
    AdminProductResponse,
    AdminProductUpdateRequest,
    ProductDeletionResponse,
    ProductStatusResponse,
)

router = APIRouter(
    prefix="/admin/products",
    tags=["admin-products"],
    dependencies=[Depends(get_current_admin)],
)


def _get_category_or_404(category_id: int, db: Session) -> ProductCategory:
    category = db.get(ProductCategory, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


def _get_product_or_404(product_id: int, db: Session) -> Product:
    statement = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )
    product = db.scalar(statement)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


def _ensure_product_not_deleted(product: Product) -> None:
    if product.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deleted products cannot be edited or put on sale",
        )


def _validate_product_status(
    category: ProductCategory,
    product_status: ProductStatus,
) -> None:
    if (
        product_status == ProductStatus.ON_SALE
        and category.status != CategoryStatus.ENABLED
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot put a product on sale under a disabled category",
        )


def _apply_payload(
    product: Product,
    payload: AdminProductCreateRequest | AdminProductUpdateRequest,
) -> None:
    product.category_id = payload.category_id
    product.name = payload.name
    product.subtitle = payload.subtitle
    product.price = payload.price
    product.original_price = payload.original_price
    product.stock = payload.stock
    product.sales = payload.sales
    product.status = payload.status
    product.cover_image = payload.cover_image
    product.banner_images = payload.banner_images
    product.detail_content = payload.detail_content
    product.sort_order = payload.sort_order
    product.is_featured = payload.is_featured


def _apply_deleted_filter(
    filters: list,
    deleted_filter: ProductDeletedFilter,
) -> None:
    if deleted_filter == ProductDeletedFilter.NOT_DELETED:
        filters.append(Product.deleted_at.is_(None))
    elif deleted_filter == ProductDeletedFilter.DELETED:
        filters.append(Product.deleted_at.is_not(None))


@router.get("", response_model=AdminProductListResponse, summary="List admin products")
def list_admin_products(
    category_id: Optional[int] = Query(default=None, gt=0),
    status_value: Optional[ProductStatus] = Query(default=None, alias="status"),
    keyword: Optional[str] = Query(default=None, max_length=100),
    deleted_filter: ProductDeletedFilter = Query(
        default=ProductDeletedFilter.NOT_DELETED,
        alias="deleted",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminProductListResponse:
    filters = []

    _apply_deleted_filter(filters, deleted_filter)

    if category_id is not None:
        filters.append(Product.category_id == category_id)

    if status_value is not None:
        filters.append(Product.status == status_value)

    if keyword:
        filters.append(Product.name.ilike(f"%{keyword.strip()}%"))

    total = db.scalar(select(func.count(Product.id)).where(*filters)) or 0

    statement = (
        select(Product)
        .options(selectinload(Product.category))
        .where(*filters)
        .order_by(
            case((Product.deleted_at.is_(None), 0), else_=1).asc(),
            Product.sort_order.asc(),
            Product.created_at.desc(),
            Product.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = db.scalars(statement).all()

    return AdminProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AdminProductListItem.model_validate(product) for product in products],
    )


@router.get(
    "/{product_id}",
    response_model=AdminProductResponse,
    summary="Get admin product detail",
)
def get_admin_product_detail(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AdminProductResponse:
    product = _get_product_or_404(product_id, db)
    return AdminProductResponse.model_validate(product)


@router.post(
    "",
    response_model=AdminProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
def create_product(
    payload: AdminProductCreateRequest,
    db: Session = Depends(get_db),
) -> AdminProductResponse:
    category = _get_category_or_404(payload.category_id, db)
    _validate_product_status(category, payload.status)

    product = Product()
    _apply_payload(product, payload)
    product.deleted_at = None

    db.add(product)
    db.commit()
    product = _get_product_or_404(product.id, db)

    return AdminProductResponse.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=AdminProductResponse,
    summary="Update product",
)
def update_product(
    payload: AdminProductUpdateRequest,
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> AdminProductResponse:
    product = _get_product_or_404(product_id, db)
    _ensure_product_not_deleted(product)

    category = _get_category_or_404(payload.category_id, db)
    _validate_product_status(category, payload.status)

    _apply_payload(product, payload)

    db.commit()
    product = _get_product_or_404(product.id, db)

    return AdminProductResponse.model_validate(product)


@router.patch(
    "/{product_id}/on-sale",
    response_model=ProductStatusResponse,
    summary="Put product on sale",
)
def put_product_on_sale(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProductStatusResponse:
    product = _get_product_or_404(product_id, db)
    _ensure_product_not_deleted(product)

    if product.category.status != CategoryStatus.ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot put a product on sale under a disabled category",
        )

    product.status = ProductStatus.ON_SALE
    db.commit()

    return ProductStatusResponse(id=product.id, status=product.status)


@router.patch(
    "/{product_id}/off-sale",
    response_model=ProductStatusResponse,
    summary="Take product off sale",
)
def take_product_off_sale(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProductStatusResponse:
    product = _get_product_or_404(product_id, db)
    _ensure_product_not_deleted(product)

    product.status = ProductStatus.OFF_SALE
    db.commit()

    return ProductStatusResponse(id=product.id, status=product.status)


@router.patch(
    "/{product_id}/restore",
    response_model=ProductDeletionResponse,
    summary="Restore deleted product",
)
def restore_product(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProductDeletionResponse:
    product = _get_product_or_404(product_id, db)
    if product.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not deleted",
        )

    product.deleted_at = None
    db.commit()

    return ProductDeletionResponse(
        id=product.id,
        deleted_at=product.deleted_at,
        is_deleted=False,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
def delete_product(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> Response:
    product = _get_product_or_404(product_id, db)
    if product.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is already deleted",
        )

    if product.status == ProductStatus.ON_SALE:
        product.status = ProductStatus.OFF_SALE

    product.deleted_at = datetime.utcnow()
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
