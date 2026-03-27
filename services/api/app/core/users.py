from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.user import User


def build_user_key(user_id: int) -> str:
    return f"user:{user_id}"


def merge_anonymous_user_data(user: User, anonymous_user_key: str, db: Session) -> None:
    cleaned_key = anonymous_user_key.strip()
    if not cleaned_key:
        return

    canonical_user_key = build_user_key(user.id)

    existing_user_items = {
        item.product_id: item
        for item in db.scalars(
            select(CartItem).where(CartItem.user_id == user.id)
        ).all()
    }
    for existing_item in existing_user_items.values():
        existing_item.user_key = canonical_user_key

    anonymous_items = db.scalars(
        select(CartItem).where(
            CartItem.user_id.is_(None),
            CartItem.user_key == cleaned_key,
        )
    ).all()

    for anonymous_item in anonymous_items:
        existing_item = existing_user_items.get(anonymous_item.product_id)
        if existing_item is not None:
            existing_item.quantity += anonymous_item.quantity
            db.delete(anonymous_item)
            continue

        anonymous_item.user_id = user.id
        anonymous_item.user_key = canonical_user_key
        existing_user_items[anonymous_item.product_id] = anonymous_item

    for order in db.scalars(
        select(Order).where(
            Order.user_id.is_(None),
            Order.user_key == cleaned_key,
        )
    ).all():
        order.user_id = user.id
        order.user_key = canonical_user_key

    for order in db.scalars(select(Order).where(Order.user_id == user.id)).all():
        order.user_key = canonical_user_key
