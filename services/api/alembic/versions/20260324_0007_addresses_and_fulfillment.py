"""add addresses and fulfillment snapshot fields

Revision ID: 20260324_0007
Revises: 20260324_0006
Create Date: 2026-03-24 23:59:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260324_0007"
down_revision: Union[str, None] = "20260324_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("receiver_name", sa.String(length=50), nullable=False),
        sa.Column("receiver_phone", sa.String(length=20), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("city", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=50), nullable=False),
        sa.Column("detail_address", sa.String(length=255), nullable=False),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_addresses")),
    )
    op.create_index(op.f("ix_addresses_user_id"), "addresses", ["user_id"], unique=False)
    op.create_index(
        "ix_addresses_user_id_is_default",
        "addresses",
        ["user_id", "is_default"],
        unique=False,
    )
    op.create_index(
        "ix_addresses_user_id_updated_at",
        "addresses",
        ["user_id", "updated_at"],
        unique=False,
    )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column(
                "fulfillment_status",
                sa.String(length=20),
                server_default=sa.text("'unfulfilled'"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("receiver_name", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("receiver_phone", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("receiver_province", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("receiver_city", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("receiver_district", sa.String(length=50), nullable=True))
        batch_op.add_column(
            sa.Column("receiver_detail_address", sa.String(length=255), nullable=True)
        )
        batch_op.create_index(
            "ix_orders_fulfillment_status_created_at",
            ["fulfillment_status", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_fulfillment_status_created_at")
        batch_op.drop_column("receiver_detail_address")
        batch_op.drop_column("receiver_district")
        batch_op.drop_column("receiver_city")
        batch_op.drop_column("receiver_province")
        batch_op.drop_column("receiver_phone")
        batch_op.drop_column("receiver_name")
        batch_op.drop_column("fulfillment_status")

    op.drop_index("ix_addresses_user_id_updated_at", table_name="addresses")
    op.drop_index("ix_addresses_user_id_is_default", table_name="addresses")
    op.drop_index(op.f("ix_addresses_user_id"), table_name="addresses")
    op.drop_table("addresses")
