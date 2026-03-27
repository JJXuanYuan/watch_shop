"""soft delete products and add admin users

Revision ID: 20260324_0003
Revises: 20260324_0002
Create Date: 2026-03-24 16:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0003"
down_revision: Union[str, None] = "20260324_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_products_deleted_at_status",
            ["deleted_at", "status"],
            unique=False,
        )

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("username", name=op.f("uq_admin_users_username")),
    )
    op.create_index(
        "ix_admin_users_status_username",
        "admin_users",
        ["status", "username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_users_status_username", table_name="admin_users")
    op.drop_table("admin_users")

    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_index("ix_products_deleted_at_status")
        batch_op.drop_column("deleted_at")
