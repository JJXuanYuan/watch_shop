"""add order operation logs

Revision ID: 20260327_0009
Revises: 20260327_0008
Create Date: 2026-03-27 16:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260327_0009"
down_revision: Union[str, None] = "20260327_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_operation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("operator_username", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("action_label", sa.String(length=100), nullable=False),
        sa.Column("before_status", sa.String(length=20), nullable=True),
        sa.Column("after_status", sa.String(length=20), nullable=True),
        sa.Column("before_fulfillment_status", sa.String(length=20), nullable=True),
        sa.Column("after_fulfillment_status", sa.String(length=20), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_operation_logs")),
    )
    op.create_index(
        "ix_order_operation_logs_action_created_at",
        "order_operation_logs",
        ["action", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_order_operation_logs_admin_user_id_created_at",
        "order_operation_logs",
        ["admin_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_order_operation_logs_order_id_created_at",
        "order_operation_logs",
        ["order_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_operation_logs_order_id_created_at", table_name="order_operation_logs")
    op.drop_index(
        "ix_order_operation_logs_admin_user_id_created_at",
        table_name="order_operation_logs",
    )
    op.drop_index("ix_order_operation_logs_action_created_at", table_name="order_operation_logs")
    op.drop_table("order_operation_logs")
