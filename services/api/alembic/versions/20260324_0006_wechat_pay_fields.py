"""add payment fields for orders

Revision ID: 20260324_0006
Revises: 20260324_0005
Create Date: 2026-03-24 23:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0006"
down_revision: Union[str, None] = "20260324_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column(
                "payment_status",
                sa.String(length=20),
                server_default=sa.text("'unpaid'"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("paid_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("transaction_id", sa.String(length=64), nullable=True))
        batch_op.create_index(
            "ix_orders_payment_status_created_at",
            ["payment_status", "created_at"],
            unique=False,
        )
        batch_op.create_index("ix_orders_transaction_id", ["transaction_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_transaction_id")
        batch_op.drop_index("ix_orders_payment_status_created_at")
        batch_op.drop_column("transaction_id")
        batch_op.drop_column("paid_at")
        batch_op.drop_column("payment_status")
