"""
Migration script to add todo_id field to existing project steps.

Usage:
    python migrate_project_steps.py <path_to_sqlite_db>
    
Example:
    python migrate_project_steps.py /path/to/database.db
    python migrate_project_steps.py ../workspaces/biz-db/data/biz-assistant.db

This script:
1. Fetches all projects from the database
2. For each project with past_steps or next_steps:
   - Validates the step structure
   - Adds todo_id: None to steps that don't have it
   - Updates the project in the database
3. Reports on the migration progress
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.models import Project


async def migrate_project_steps(session_maker):
    """Migrate all project steps to include todo_id field."""
    
    print("Starting project steps migration...")
    print("-" * 60)
    
    async with session_maker() as db:
        # Fetch all projects
        result = await db.execute(select(Project))
        projects = result.scalars().all()
        
        total_projects = len(projects)
        migrated_count = 0
        skipped_count = 0
        
        print(f"Found {total_projects} projects to process")
        print()
        
        for project in projects:
            needs_update = False
            
            # Process past_steps
            if project.past_steps:
                for step in project.past_steps:
                    if 'todo_id' not in step:
                        step['todo_id'] = None
                        needs_update = True
            
            # Process next_steps
            if project.next_steps:
                for step in project.next_steps:
                    if 'todo_id' not in step:
                        step['todo_id'] = None
                        needs_update = True
            
            if needs_update:
                # Mark the JSON fields as modified
                from sqlalchemy.orm.attributes import flag_modified
                if project.past_steps:
                    flag_modified(project, 'past_steps')
                if project.next_steps:
                    flag_modified(project, 'next_steps')
                
                migrated_count += 1
                print(f"✓ Migrated project: {project.name} (ID: {project.id})")
            else:
                skipped_count += 1
        
        # Commit all changes
        await db.commit()
        
        print()
        print("-" * 60)
        print(f"Migration completed!")
        print(f"  Total projects: {total_projects}")
        print(f"  Migrated: {migrated_count}")
        print(f"  Skipped (already migrated): {skipped_count}")
        print("-" * 60)


async def validate_migration(session_maker):
    """Validate that all steps now have the todo_id field."""
    
    print("\nValidating migration...")
    print("-" * 60)
    
    async with session_maker() as db:
        result = await db.execute(select(Project))
        projects = result.scalars().all()
        
        invalid_count = 0
        
        for project in projects:
            # Check past_steps
            if project.past_steps:
                for i, step in enumerate(project.past_steps):
                    if 'todo_id' not in step:
                        print(f"✗ Project {project.id} - past_steps[{i}] missing todo_id")
                        invalid_count += 1
            
            # Check next_steps
            if project.next_steps:
                for i, step in enumerate(project.next_steps):
                    if 'todo_id' not in step:
                        print(f"✗ Project {project.id} - next_steps[{i}] missing todo_id")
                        invalid_count += 1
        
        if invalid_count == 0:
            print("✓ All steps have todo_id field")
        else:
            print(f"✗ Found {invalid_count} steps without todo_id field")
        
        print("-" * 60)
        
        return invalid_count == 0


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate project steps to include todo_id field",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_project_steps.py database.db
  python migrate_project_steps.py /absolute/path/to/database.db
  python migrate_project_steps.py ../workspaces/biz-db/data/biz-assistant.db
        """
    )
    parser.add_argument(
        'database_path',
        type=str,
        help='Path to the SQLite database file'
    )
    return parser.parse_args()


async def main():
    """Run the migration and validation."""
    args = parse_args()
    
    # Resolve database path
    db_path = Path(args.database_path)
    if not db_path.is_absolute():
        db_path = db_path.resolve()
    
    # Check if database file exists
    if not db_path.exists():
        print(f"❌ Error: Database file not found: {db_path}")
        sys.exit(1)
    
    print(f"Database: {db_path}")
    print()
    
    # Create engine for the specified database
    database_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        database_url,
        echo=False,  # Disable SQL logging for cleaner output
        future=True,
        connect_args={"check_same_thread": False},
    )
    
    # Create session maker
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    try:
        await migrate_project_steps(session_maker)
        
        # Validate the migration
        is_valid = await validate_migration(session_maker)
        
        if not is_valid:
            print("\n⚠️  Validation failed. Some steps may not have been migrated correctly.")
            sys.exit(1)
        else:
            print("\n✓ Migration successful and validated!")
            sys.exit(0)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
