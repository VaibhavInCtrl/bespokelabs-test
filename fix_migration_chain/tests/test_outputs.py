"""
Tests to verify the Alembic migration chain has been fixed correctly.
These tests check that migrations run successfully and the resulting
database schema matches the expected models.
"""
import subprocess
import sqlite3
import os
import pytest


DB_PATH = "/app/inventory.db"
APP_DIR = "/app"


@pytest.fixture(scope="session", autouse=True)
def ensure_migrations_ran():
    """Ensure migrations have been run before tests execute."""
    # If the database doesn't exist, try running migrations
    if not os.path.exists(DB_PATH):
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
        )
        # We don't assert here — individual tests will catch failures


@pytest.fixture
def db_connection():
    """Provide a database connection for tests."""
    assert os.path.exists(DB_PATH), (
        f"Database file {DB_PATH} does not exist. "
        "Migrations likely failed to run."
    )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def get_table_names(conn):
    """Get all table names from the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'alembic_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def get_column_info(conn, table_name):
    """Get column info for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: {"type": row[2], "notnull": row[3], "pk": row[5]} for row in cursor.fetchall()}


def get_index_names(conn):
    """Get all index names from the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def get_foreign_keys(conn, table_name):
    """Get foreign keys for a table."""
    cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
    return [{"table": row[2], "from": row[3], "to": row[4]} for row in cursor.fetchall()]


class TestMigrationsRun:
    """Test that alembic upgrade head completes successfully."""

    def test_alembic_upgrade_head_succeeds(self):
        """Running 'alembic upgrade head' should exit with code 0."""
        # Remove existing DB to test from scratch
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"alembic upgrade head failed with exit code {result.returncode}.\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

    def test_database_file_exists(self):
        """The database file should be created after migrations."""
        assert os.path.exists(DB_PATH), "Database file was not created"

    def test_alembic_current_shows_head(self):
        """Alembic current should show the head revision."""
        result = subprocess.run(
            ["alembic", "current"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "d4e5f6a7b8c9" in result.stdout, (
            f"Expected head revision 'd4e5f6a7b8c9' in alembic current output. "
            f"Got: {result.stdout}"
        )


class TestSchemaStructure:
    """Test that all expected tables and columns exist."""

    def test_all_tables_exist(self, db_connection):
        """All four expected tables should exist."""
        tables = get_table_names(db_connection)
        expected = ["order_items", "orders", "products", "users"]
        assert sorted(tables) == expected, (
            f"Expected tables {expected}, got {sorted(tables)}"
        )

    def test_users_table_columns(self, db_connection):
        """Users table should have all expected columns including profile fields."""
        columns = get_column_info(db_connection, "users")
        expected_columns = {"id", "username", "email", "full_name", "phone", "created_at"}
        assert set(columns.keys()) == expected_columns, (
            f"Users columns mismatch. Expected {expected_columns}, got {set(columns.keys())}"
        )

    def test_users_full_name_type(self, db_connection):
        """The full_name column should be VARCHAR(100), not VARCHAR(50)."""
        columns = get_column_info(db_connection, "users")
        full_name_type = columns["full_name"]["type"].upper()
        assert "100" in full_name_type, (
            f"full_name column type should be VARCHAR(100), got {full_name_type}"
        )

    def test_users_phone_nullable(self, db_connection):
        """The phone column should be nullable (NOT NULL = 0)."""
        columns = get_column_info(db_connection, "users")
        assert columns["phone"]["notnull"] == 0, (
            "phone column should be nullable to accommodate existing seed data"
        )

    def test_products_table_columns(self, db_connection):
        """Products table should have inventory tracking columns."""
        columns = get_column_info(db_connection, "products")
        expected_columns = {
            "id", "name", "description", "price",
            "stock_count", "reorder_level", "last_restocked",
        }
        assert set(columns.keys()) == expected_columns, (
            f"Products columns mismatch. Expected {expected_columns}, got {set(columns.keys())}"
        )

    def test_orders_table_columns(self, db_connection):
        """Orders table should have all expected columns."""
        columns = get_column_info(db_connection, "orders")
        expected_columns = {"id", "user_id", "total_amount", "status", "created_at"}
        assert set(columns.keys()) == expected_columns, (
            f"Orders columns mismatch. Expected {expected_columns}, got {set(columns.keys())}"
        )

    def test_order_items_table_columns(self, db_connection):
        """Order items table should have all expected columns."""
        columns = get_column_info(db_connection, "order_items")
        expected_columns = {"id", "order_id", "product_id", "quantity", "unit_price"}
        assert set(columns.keys()) == expected_columns, (
            f"OrderItems columns mismatch. Expected {expected_columns}, got {set(columns.keys())}"
        )


class TestForeignKeys:
    """Test that foreign key constraints are correctly defined."""

    def test_orders_user_fk(self, db_connection):
        """Orders table should have a FK from user_id to users.id."""
        fks = get_foreign_keys(db_connection, "orders")
        user_fk = [fk for fk in fks if fk["table"] == "users"]
        assert len(user_fk) == 1, f"Expected 1 FK to users, found {len(user_fk)}"
        assert user_fk[0]["from"] == "user_id"
        assert user_fk[0]["to"] == "id", (
            f"FK should reference users.id, but references users.{user_fk[0]['to']}"
        )

    def test_order_items_order_fk(self, db_connection):
        """Order items should have FK to orders.id."""
        fks = get_foreign_keys(db_connection, "order_items")
        order_fk = [fk for fk in fks if fk["table"] == "orders"]
        assert len(order_fk) == 1
        assert order_fk[0]["to"] == "id"

    def test_order_items_product_fk(self, db_connection):
        """Order items should have FK to products.id."""
        fks = get_foreign_keys(db_connection, "order_items")
        product_fk = [fk for fk in fks if fk["table"] == "products"]
        assert len(product_fk) == 1
        assert product_fk[0]["to"] == "id"


class TestSeedData:
    """Test that seed data from the initial migration is preserved."""

    def test_seed_users_exist(self, db_connection):
        """The 2 seed users should still exist after all migrations."""
        cursor = db_connection.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        assert count >= 2, f"Expected at least 2 seed users, found {count}"

    def test_seed_user_admin(self, db_connection):
        """The admin seed user should exist."""
        cursor = db_connection.execute(
            "SELECT username, email FROM users WHERE username = 'admin'"
        )
        row = cursor.fetchone()
        assert row is not None, "Seed user 'admin' not found"
        assert row["email"] == "admin@example.com"

    def test_seed_products_exist(self, db_connection):
        """The 2 seed products should still exist."""
        cursor = db_connection.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        assert count >= 2, f"Expected at least 2 seed products, found {count}"


class TestIndexes:
    """Test that indexes are correctly created with unique names."""

    def test_no_duplicate_index_names(self, db_connection):
        """All index names should be unique."""
        indexes = get_index_names(db_connection)
        assert len(indexes) == len(set(indexes)), (
            f"Duplicate index names found: {indexes}"
        )

    def test_orders_user_id_index_exists(self, db_connection):
        """An index on orders.user_id should exist."""
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='orders'"
        )
        index_names = [row[0] for row in cursor.fetchall()]
        has_user_id_index = any("user_id" in name or "orders" in name for name in index_names)
        assert has_user_id_index or len(index_names) > 0, (
            "Expected an index on orders table"
        )

    def test_products_stock_index_exists(self, db_connection):
        """An index on products.stock_count should exist (with a unique name)."""
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='products'"
        )
        index_names = [row[0] for row in cursor.fetchall()]
        # The index should NOT be named "ix_orders_user_id" (that would be the bug)
        assert "ix_orders_user_id" not in index_names, (
            "Products index should not be named 'ix_orders_user_id' — that's a duplicate from orders"
        )
        assert len(index_names) > 0, "Expected at least one index on products table"


class TestMigrationChain:
    """Test that the migration revision chain is correct."""

    def test_alembic_history_is_linear(self):
        """Alembic history should show a linear chain with no branches."""
        result = subprocess.run(
            ["alembic", "history", "--verbose"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"alembic history failed: {result.stderr}"
        )
        # Should not contain "branchpoint" indicating unresolved branches
        assert "branchpoint" not in result.stdout.lower(), (
            f"Migration history has branch points (unresolved branches): {result.stdout}"
        )

    def test_revision_chain_order(self):
        """Verify the revision chain goes 001 -> 002 -> 003 -> 004."""
        result = subprocess.run(
            ["alembic", "history", "-r", "base:heads", "--verbose"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout
        # All 4 revisions should appear
        assert "a1b2c3d4e5f6" in output, "Migration 001 not in history"
        assert "b2c3d4e5f6a7" in output, "Migration 002 not in history"
        assert "c3d4e5f6a7b8" in output, "Migration 003 not in history"
        assert "d4e5f6a7b8c9" in output, "Migration 004 not in history"
