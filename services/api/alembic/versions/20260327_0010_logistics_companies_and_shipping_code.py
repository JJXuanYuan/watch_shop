"""add logistics companies and shipping company code

Revision ID: 20260327_0010
Revises: 20260327_0009
Create Date: 2026-03-27 19:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260327_0010"
down_revision: Union[str, None] = "20260327_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'enabled'"),
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_logistics_companies")),
        sa.UniqueConstraint("code", name=op.f("uq_logistics_companies_code")),
    )
    op.create_index(
        "ix_logistics_companies_status_name",
        "logistics_companies",
        ["status", "name"],
        unique=False,
    )
    op.create_index(
        "ix_logistics_companies_status_sort_order",
        "logistics_companies",
        ["status", "sort_order"],
        unique=False,
    )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("shipping_company_code", sa.String(length=32), nullable=True))
        batch_op.create_index(op.f("ix_orders_shipping_company_code"), ["shipping_company_code"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index(op.f("ix_orders_shipping_company_code"))
        batch_op.drop_column("shipping_company_code")

    op.drop_index("ix_logistics_companies_status_sort_order", table_name="logistics_companies")
    op.drop_index("ix_logistics_companies_status_name", table_name="logistics_companies")
    op.drop_table("logistics_companies")
