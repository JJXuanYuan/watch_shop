from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.product_category import ProductCategory
from app.models.types import CategoryStatus
from app.schemas.category import CategoryItem, CategoryListResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse, summary="List active product categories")
def list_categories(db: Session = Depends(get_db)) -> CategoryListResponse:
    statement = (
        select(ProductCategory)
        .where(ProductCategory.status == CategoryStatus.ENABLED)
        .order_by(ProductCategory.sort_order.asc(), ProductCategory.id.asc())
    )
    items = db.scalars(statement).all()

    return CategoryListResponse(
        items=[CategoryItem.model_validate(category) for category in items]
    )
