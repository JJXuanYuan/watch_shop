"""add cart items and orders tables

Revision ID: 20260324_0004
Revises: 20260324_0003
Create Date: 2026-03-24 20:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0004"
down_revision: Union[str, None] = "20260324_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_key", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_cart_items_product_id_products"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cart_items")),
        sa.UniqueConstraint(
            "user_key",
            "product_id",
            name="uq_cart_items_user_key_product_id",
        ),
    )
    op.create_index(op.f("ix_cart_items_product_id"), "cart_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_cart_items_user_key"), "cart_items", ["user_key"], unique=False)
    op.create_index(
        "ix_cart_items_user_key_updated_at",
        "cart_items",
        ["user_key", "updated_at"],
        unique=False,
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("user_key", sa.String(length=64), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("order_no", name=op.f("uq_orders_order_no")),
    )
    op.create_index(op.f("ix_orders_user_key"), "orders", ["user_key"], unique=False)
    op.create_index("ix_orders_created_at_status", "orders", ["created_at", "status"], unique=False)
    op.create_index("ix_orders_user_key_status", "orders", ["user_key", "status"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_items_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_order_items_product_id_products"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)
    op.create_index(
        "ix_order_items_order_id_product_id",
        "order_items",
        ["order_id", "product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id_product_id", table_name="order_items")
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_user_key_status", table_name="orders")
    op.drop_index("ix_orders_created_at_status", table_name="orders")
    op.drop_index(op.f("ix_orders_user_key"), table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_cart_items_user_key_updated_at", table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_user_key"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_product_id"), table_name="cart_items")
    op.drop_table("cart_items")
