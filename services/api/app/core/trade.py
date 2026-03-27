from __future__ import annotations

from decimal import Decimal
from secrets import randbelow
from typing import Optional

from fastapi import HTTPException, status

from app.models.product import Product
from app.models.types import CategoryStatus, ProductStatus


def resolve_product_purchase_issue(
    product: Product,
    quantity: Optional[int] = None,
) -> str | None:
    if product.deleted_at is not None:
        return "商品已删除"

    if product.category.status != CategoryStatus.ENABLED:
        return "商品分类已停用"

    if product.status != ProductStatus.ON_SALE:
        return "商品暂未上架"

    if quantity is not None and product.stock < quantity:
        return "库存不足"

    return None


def ensure_product_purchasable(product: Product, quantity: int) -> None:
    issue = resolve_product_purchase_issue(product, quantity)
    if issue is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=issue,
        )


def build_order_no() -> str:
    from datetime import datetime

    return f"ORD{datetime.now():%Y%m%d%H%M%S}{randbelow(1_000_000):06d}"


def calculate_subtotal(price: Decimal, quantity: int) -> Decimal:
    return price * Decimal(quantity)
