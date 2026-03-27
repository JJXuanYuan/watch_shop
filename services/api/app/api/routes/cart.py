from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.core.trade import calculate_subtotal, resolve_product_purchase_issue
from app.core.users import build_user_key
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreateRequest, CartItemResponse, CartItemUpdateRequest, CartResponse

router = APIRouter(prefix="/cart", tags=["cart"])


def _query_cart_items(user_id: int, db: Session) -> list[CartItem]:
    return db.scalars(
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.updated_at.desc(), CartItem.id.desc())
    ).all()


def _build_cart_response(cart_items: list[CartItem]) -> CartResponse:
    items: list[CartItemResponse] = []
    total_amount = Decimal("0.00")
    total_quantity = 0

    for cart_item in cart_items:
        product = cart_item.product
        subtotal_amount = calculate_subtotal(product.price, cart_item.quantity)
        availability_message = resolve_product_purchase_issue(product, cart_item.quantity)

        items.append(
            CartItemResponse(
                id=cart_item.id,
                product_id=product.id,
                name=product.name,
                subtitle=product.subtitle,
                cover_image=product.cover_image,
                price=product.price,
                quantity=cart_item.quantity,
                subtotal_amount=subtotal_amount,
                stock=product.stock,
                status=product.status,
                is_available=availability_message is None,
                availability_message=availability_message,
                created_at=cart_item.created_at,
                updated_at=cart_item.updated_at,
            )
        )
        total_amount += subtotal_amount
        total_quantity += cart_item.quantity

    return CartResponse(
        items=items,
        item_count=len(items),
        total_quantity=total_quantity,
        total_amount=total_amount,
    )


def _get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在",
        )
    return product


def _get_cart_item_or_404(item_id: int, user_id: int, db: Session) -> CartItem:
    cart_item = db.scalar(
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
    )
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="购物车项不存在",
        )
    return cart_item


def _ensure_cart_product_available(product: Product, quantity: int) -> None:
    issue = resolve_product_purchase_issue(product, quantity)
    if issue is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=issue,
        )


@router.get("", response_model=CartResponse, summary="Get current cart")
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartResponse:
    return _build_cart_response(_query_cart_items(current_user.id, db))


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
)
def add_cart_item(
    payload: CartItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartResponse:
    product = _get_product_or_404(payload.product_id, db)

    existing_item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.product_id == payload.product_id,
        )
    )
    next_quantity = payload.quantity if existing_item is None else existing_item.quantity + payload.quantity
    _ensure_cart_product_available(product, next_quantity)

    if existing_item is None:
        db.add(
            CartItem(
                user_id=current_user.id,
                user_key=build_user_key(current_user.id),
                product_id=payload.product_id,
                quantity=payload.quantity,
            )
        )
    else:
        existing_item.quantity = next_quantity
        existing_item.user_key = build_user_key(current_user.id)

    db.commit()
    return _build_cart_response(_query_cart_items(current_user.id, db))


@router.patch(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
)
@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
)
def update_cart_item(
    payload: CartItemUpdateRequest,
    item_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartResponse:
    cart_item = _get_cart_item_or_404(item_id, current_user.id, db)
    _ensure_cart_product_available(cart_item.product, payload.quantity)

    cart_item.quantity = payload.quantity
    cart_item.user_key = build_user_key(current_user.id)
    db.commit()

    return _build_cart_response(_query_cart_items(current_user.id, db))


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cart item",
)
def delete_cart_item(
    item_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    cart_item = _get_cart_item_or_404(item_id, current_user.id, db)
    db.delete(cart_item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
