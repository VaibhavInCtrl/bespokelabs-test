#!/bin/bash
set -e

cd /app

# Fix 1: Migration 002 has wrong down_revision (points to non-existent "f9e8d7c6b5a4")
# Should point to migration 001: "a1b2c3d4e5f6"
sed -i 's/down_revision: Union\[str, None\] = "f9e8d7c6b5a4"/down_revision: Union[str, None] = "a1b2c3d4e5f6"/' \
    alembic/versions/002_add_orders_tables.py

# Fix 2: Migration 002 has wrong FK reference "users.user_id" should be "users.id"
sed -i 's/\["users.user_id"\]/["users.id"]/' \
    alembic/versions/002_add_orders_tables.py

# Fix 3: Migration 003 uses String(50) for full_name but model says String(100)
sed -i 's/sa.String(50)/sa.String(100)/' \
    alembic/versions/003_add_user_profile_fields.py

# Fix 4: Migration 003 adds "phone" as NOT NULL without server_default
# Existing rows (seed data) would fail. Make it nullable=True to match model.
sed -i 's/sa.Column("phone", sa.String(20), nullable=False)/sa.Column("phone", sa.String(20), nullable=True)/' \
    alembic/versions/003_add_user_profile_fields.py

# Fix 5: Migration 004 has wrong down_revision pointing to 001 ("a1b2c3d4e5f6")
# Should point to migration 003: "c3d4e5f6a7b8"
sed -i 's/down_revision: Union\[str, None\] = "a1b2c3d4e5f6"/down_revision: Union[str, None] = "c3d4e5f6a7b8"/' \
    alembic/versions/004_add_inventory_tracking.py

# Fix 6: Migration 004 uses duplicate index name "ix_orders_user_id" (already used in 002)
# Rename to "ix_products_stock_count"
sed -i 's/op.create_index("ix_orders_user_id", "products"/op.create_index("ix_products_stock_count", "products"/' \
    alembic/versions/004_add_inventory_tracking.py

# Also fix the downgrade for the index name
sed -i 's/op.drop_index("ix_orders_user_id", table_name="products")/op.drop_index("ix_products_stock_count", table_name="products")/' \
    alembic/versions/004_add_inventory_tracking.py

# Remove any existing database
rm -f inventory.db

# Run all migrations
alembic upgrade head

echo "All migrations applied successfully!"
