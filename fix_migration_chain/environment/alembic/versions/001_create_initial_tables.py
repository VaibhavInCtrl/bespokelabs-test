"""Create initial tables - users and products

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Insert seed data
    op.execute(
        "INSERT INTO users (username, email, created_at) VALUES ('admin', 'admin@example.com', '2024-01-15 10:00:00')"
    )
    op.execute(
        "INSERT INTO users (username, email, created_at) VALUES ('testuser', 'test@example.com', '2024-01-15 10:00:00')"
    )
    op.execute(
        "INSERT INTO products (name, description, price) VALUES ('Widget A', 'A standard widget', 9.99)"
    )
    op.execute(
        "INSERT INTO products (name, description, price) VALUES ('Gadget B', 'A fancy gadget', 24.99)"
    )


def downgrade() -> None:
    op.drop_table("products")
    op.drop_table("users")
