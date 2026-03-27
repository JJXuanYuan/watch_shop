"""product management phase 1

Revision ID: 20260324_0002
Revises: 20260321_0001
Create Date: 2026-03-24 10:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0002"
down_revision: Union[str, None] = "20260321_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_PRODUCT_STATUS = sa.Enum(
    "draft",
    "active",
    "inactive",
    name="product_status",
    native_enum=False,
    length=20,
)


def upgrade() -> None:
    with op.batch_alter_table("product_categories") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'enabled'"),
                nullable=False,
            )
        )

    op.execute(
        """
        UPDATE product_categories
        SET status = CASE
            WHEN is_active = 1 THEN 'enabled'
            ELSE 'disabled'
        END
        """
    )

    with op.batch_alter_table("product_categories") as batch_op:
        batch_op.drop_index("ix_product_categories_is_active_sort_order")
        batch_op.drop_column("is_active")
        batch_op.create_index(
            "ix_product_categories_status_sort_order",
            ["status", "sort_order"],
            unique=False,
        )

    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sort_order",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )
        batch_op.alter_column(
            "status",
            existing_type=OLD_PRODUCT_STATUS,
            type_=sa.String(length=20),
            existing_nullable=False,
            existing_server_default=sa.text("'draft'"),
            server_default=sa.text("'draft'"),
        )

    op.execute("UPDATE products SET status = 'on_sale' WHERE status = 'active'")
    op.execute("UPDATE products SET status = 'off_sale' WHERE status = 'inactive'")


def downgrade() -> None:
    op.execute("UPDATE products SET status = 'active' WHERE status = 'on_sale'")
    op.execute("UPDATE products SET status = 'inactive' WHERE status = 'off_sale'")

    with op.batch_alter_table("products") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            type_=OLD_PRODUCT_STATUS,
            existing_nullable=False,
            existing_server_default=sa.text("'draft'"),
            server_default=sa.text("'draft'"),
        )
        batch_op.drop_column("sort_order")

    with op.batch_alter_table("product_categories") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("1"),
                nullable=False,
            )
        )

    op.execute(
        """
        UPDATE product_categories
        SET is_active = CASE
            WHEN status = 'enabled' THEN 1
            ELSE 0
        END
        """
    )

    with op.batch_alter_table("product_categories") as batch_op:
        batch_op.drop_index("ix_product_categories_status_sort_order")
        batch_op.drop_column("status")
        batch_op.create_index(
            "ix_product_categories_is_active_sort_order",
            ["is_active", "sort_order"],
            unique=False,
        )
