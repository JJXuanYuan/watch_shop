"""add manual shipping fields to orders

Revision ID: 20260327_0008
Revises: 20260324_0007
Create Date: 2026-03-27 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260327_0008"
down_revision: Union[str, None] = "20260324_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("shipping_company", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("tracking_no", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("shipping_note", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("shipped_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_column("completed_at")
        batch_op.drop_column("shipped_at")
        batch_op.drop_column("shipping_note")
        batch_op.drop_column("tracking_no")
        batch_op.drop_column("shipping_company")
