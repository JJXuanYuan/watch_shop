from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.types import ProductStatus
from app.schemas.product import ProductDetailResponse, ProductListItem, ProductListResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse, summary="List active products")
def list_products(
    category_id: Optional[int] = Query(default=None, gt=0),
    category_slug: Optional[str] = Query(default=None, max_length=100),
    keyword: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    filters = [
        Product.status == ProductStatus.ACTIVE,
        ProductCategory.is_active.is_(True),
    ]

    if category_id is not None:
        filters.append(Product.category_id == category_id)

    if category_slug:
        filters.append(ProductCategory.slug == category_slug.strip())

    if keyword:
        filters.append(Product.title.ilike(f"%{keyword.strip()}%"))

    count_statement = (
        select(func.count(Product.id))
        .select_from(Product)
        .join(Product.category)
        .where(*filters)
    )
    total = db.scalar(count_statement) or 0

    statement = (
        select(Product)
        .join(Product.category)
        .options(selectinload(Product.category))
        .where(*filters)
        .order_by(Product.is_featured.desc(), Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = db.scalars(statement).all()

    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductListItem.model_validate(product) for product in products],
    )


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Get active product detail",
)
def get_product_detail(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> ProductDetailResponse:
    statement = (
        select(Product)
        .join(Product.category)
        .options(selectinload(Product.category))
        .where(
            Product.id == product_id,
            Product.status == ProductStatus.ACTIVE,
            ProductCategory.is_active.is_(True),
        )
    )
    product = db.scalar(statement)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductDetailResponse.model_validate(product)

