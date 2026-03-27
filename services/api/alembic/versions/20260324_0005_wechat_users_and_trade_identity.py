"""add users table and bind trade data to users

Revision ID: 20260324_0005
Revises: 20260324_0004
Create Date: 2026-03-24 23:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0005"
down_revision: Union[str, None] = "20260324_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("openid", sa.String(length=64), nullable=False),
        sa.Column("unionid", sa.String(length=64), nullable=True),
        sa.Column("nickname", sa.String(length=100), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("openid", name=op.f("uq_users_openid")),
    )
    op.create_index("ix_users_status_created_at", "users", ["status", "created_at"], unique=False)

    with op.batch_alter_table("cart_items") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f("fk_cart_items_user_id_users"),
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_cart_items_user_id"), ["user_id"], unique=False)
        batch_op.create_index("ix_cart_items_user_id_updated_at", ["user_id", "updated_at"], unique=False)

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f("fk_orders_user_id_users"),
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(batch_op.f("ix_orders_user_id"), ["user_id"], unique=False)
        batch_op.create_index("ix_orders_user_id_status", ["user_id", "status"], unique=False)
        batch_op.create_index("ix_orders_user_id_created_at", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_user_id_created_at")
        batch_op.drop_index("ix_orders_user_id_status")
        batch_op.drop_index(batch_op.f("ix_orders_user_id"))
        batch_op.drop_constraint(batch_op.f("fk_orders_user_id_users"), type_="foreignkey")
        batch_op.drop_column("user_id")

    with op.batch_alter_table("cart_items") as batch_op:
        batch_op.drop_index("ix_cart_items_user_id_updated_at")
        batch_op.drop_index(batch_op.f("ix_cart_items_user_id"))
        batch_op.drop_constraint(batch_op.f("fk_cart_items_user_id_users"), type_="foreignkey")
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_status_created_at", table_name="users")
    op.drop_table("users")
