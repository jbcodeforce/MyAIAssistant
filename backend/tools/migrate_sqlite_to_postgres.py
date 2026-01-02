#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL.

Usage:
    uv run python tools/migrate_sqlite_to_postgres.py \
        --sqlite /path/to/myaiassistant.db \
        --postgres "postgresql://user:pass@localhost:5432/myaiassistant"

Or with environment variables:
    SQLITE_URL="sqlite:///./myaiassistant.db" \
    POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/myaiassistant" \
    uv run python tools/migrate_sqlite_to_postgres.py
"""

import argparse
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Organization, Project, Todo, Knowledge, TaskPlan, Settings


# Tables in order of dependency (parents first)
TABLES_IN_ORDER = [
    ("organizations", Organization),
    ("settings", Settings),
    ("knowledge", Knowledge),
    ("projects", Project),
    ("todos", Todo),
    ("task_plans", TaskPlan),
]


def get_sqlite_engine(sqlite_path: str):
    """Create SQLite engine from file path or URL."""
    if sqlite_path.startswith("sqlite"):
        url = sqlite_path
    else:
        url = f"sqlite:///{sqlite_path}"
    return create_engine(url, echo=False)


def get_postgres_engine(postgres_url: str):
    """Create PostgreSQL engine from URL."""
    # Convert async URL to sync if needed
    url = postgres_url.replace("+asyncpg", "").replace("+psycopg2", "")
    if not url.startswith("postgresql"):
        raise ValueError(f"Invalid PostgreSQL URL: {postgres_url}")
    return create_engine(url, echo=False)


def table_exists(engine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def get_row_count(engine, table_name: str) -> int:
    """Get the number of rows in a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()


def migrate_table(sqlite_engine, postgres_engine, table_name: str, model_class) -> int:
    """Migrate a single table from SQLite to PostgreSQL."""
    
    # Check if source table exists and has data
    if not table_exists(sqlite_engine, table_name):
        print(f"  Skipping {table_name}: table does not exist in SQLite")
        return 0
    
    source_count = get_row_count(sqlite_engine, table_name)
    if source_count == 0:
        print(f"  Skipping {table_name}: no data to migrate")
        return 0
    
    print(f"  Migrating {table_name}: {source_count} rows...")
    
    # Read all data from SQLite
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    try:
        rows = sqlite_session.query(model_class).all()
        
        # Convert to dictionaries (detach from SQLite session)
        data = []
        for row in rows:
            row_dict = {}
            for column in model_class.__table__.columns:
                value = getattr(row, column.name)
                # Handle datetime conversion if needed
                if isinstance(value, str) and column.type.python_type == datetime:
                    try:
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                row_dict[column.name] = value
            data.append(row_dict)
    finally:
        sqlite_session.close()
    
    # Insert into PostgreSQL
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgresSession()
    
    try:
        # Clear existing data in target table (optional, for idempotent migrations)
        # Uncomment if you want to replace existing data:
        # postgres_session.query(model_class).delete()
        
        for row_dict in data:
            obj = model_class(**row_dict)
            postgres_session.merge(obj)  # Use merge to handle existing records
        
        postgres_session.commit()
        
        # Reset PostgreSQL sequence to max ID + 1
        if "id" in [c.name for c in model_class.__table__.columns]:
            max_id = max(d["id"] for d in data) if data else 0
            sequence_name = f"{table_name}_id_seq"
            try:
                postgres_session.execute(
                    text(f"SELECT setval('{sequence_name}', :max_id, true)"),
                    {"max_id": max_id}
                )
                postgres_session.commit()
            except Exception as e:
                print(f"    Note: Could not reset sequence {sequence_name}: {e}")
        
        return len(data)
    except Exception as e:
        postgres_session.rollback()
        raise e
    finally:
        postgres_session.close()


def create_tables(postgres_engine):
    """Create all tables in PostgreSQL if they don't exist."""
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(postgres_engine)
    print("  Tables created successfully")


def migrate(sqlite_path: str, postgres_url: str, create_tables_flag: bool = True):
    """Run the full migration from SQLite to PostgreSQL."""
    
    print(f"\nMigration: SQLite -> PostgreSQL")
    print(f"  Source: {sqlite_path}")
    print(f"  Target: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    print()
    
    # Create engines
    sqlite_engine = get_sqlite_engine(sqlite_path)
    postgres_engine = get_postgres_engine(postgres_url)
    
    # Create tables if requested
    if create_tables_flag:
        create_tables(postgres_engine)
    
    # Migrate each table
    print("\nMigrating data...")
    total_rows = 0
    
    for table_name, model_class in TABLES_IN_ORDER:
        try:
            count = migrate_table(sqlite_engine, postgres_engine, table_name, model_class)
            total_rows += count
        except Exception as e:
            print(f"  ERROR migrating {table_name}: {e}")
            raise
    
    print(f"\nMigration complete: {total_rows} total rows migrated")
    
    # Verify counts
    print("\nVerification:")
    for table_name, model_class in TABLES_IN_ORDER:
        if table_exists(sqlite_engine, table_name):
            sqlite_count = get_row_count(sqlite_engine, table_name)
            postgres_count = get_row_count(postgres_engine, table_name)
            status = "OK" if sqlite_count == postgres_count else "MISMATCH"
            print(f"  {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count} [{status}]")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite",
        default=os.environ.get("SQLITE_URL", "./data/myaiassistant.db"),
        help="Path to SQLite database file or SQLite URL"
    )
    parser.add_argument(
        "--postgres",
        default=os.environ.get(
            "POSTGRES_URL",
            "postgresql://postgres:postgres@localhost:5432/myaiassistant"
        ),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--no-create-tables",
        action="store_true",
        help="Skip creating tables (assume they exist)"
    )
    
    args = parser.parse_args()
    
    try:
        migrate(
            sqlite_path=args.sqlite,
            postgres_url=args.postgres,
            create_tables_flag=not args.no_create_tables
        )
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

