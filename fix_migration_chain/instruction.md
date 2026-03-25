# Fix the Broken Database Migration Chain

You are a backend developer who just joined a team working on an inventory management application built with Python, Flask, SQLAlchemy, and Alembic (for database migrations). The application uses SQLite as its database.

## The Problem

A junior developer recently merged a feature branch that added several new database migrations to support orders, user profiles, and inventory tracking. However, since the merge, **no one can run the migrations successfully**. Running `alembic upgrade head` fails with errors, and the application cannot start because the database schema is out of date.

Your job is to **diagnose and fix all issues in the Alembic migration chain** so that:

1. `alembic upgrade head` runs successfully from a clean database
2. The resulting database schema matches the SQLAlchemy models defined in `/app/app/models.py`
3. All seed data inserted by the initial migration is preserved

## Environment

- All application code is located in `/app/`
- The Alembic configuration is at `/app/alembic.ini`
- Migration files are in `/app/alembic/versions/`
- The SQLAlchemy models (the source of truth for the desired schema) are in `/app/app/models.py`
- The database connection is configured in `/app/app/database.py`

## What You Need To Do

Examine the migration files, understand the revision dependency chain, compare the migrations against the models, and fix all issues preventing `alembic upgrade head` from completing successfully. There are multiple interrelated issues across the migration files that need to be resolved.

After fixing the migrations, run `alembic upgrade head` from the `/app` directory to verify your fixes work. The database file will be created at `/app/inventory.db`.

**Important**: Do not modify the models in `/app/app/models.py` — those represent the correct, desired schema. Only fix the migration files.
