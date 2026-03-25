"""Add inventory tracking fields to products

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2024-01-25 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("stock_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "products", sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10")
    )
    op.add_column("products", sa.Column("last_restocked", sa.DateTime(), nullable=True))

    op.create_index("ix_orders_user_id", "products", ["stock_count"])


def downgrade() -> None:
    op.drop_index("ix_orders_user_id", table_name="products")
    op.drop_column("products", "last_restocked")
    op.drop_column("products", "reorder_level")
    op.drop_column("products", "stock_count")
