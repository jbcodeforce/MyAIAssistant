#!/usr/bin/env python3
"""
Migration script to convert past_steps and next_steps from TEXT to JSON format.

This script reads existing text data (markdown bullet lists) from the projects table
and converts them to JSON arrays of Step objects: [{"what": "...", "who": "..."}]

Usage:
    cd workspaces/biz-db
    uv run --project ../../backend python ../../backend/tools/migrate_steps_to_json.py data/biz-assistant.db
"""

import json
import re
import sqlite3
import sys
from pathlib import Path


def parse_steps_from_text(text: str | None) -> list[dict[str, str]] | None:
    """
    Parse bullet-point text into a list of Step objects.
    
    Supports formats:
    - "* action item" -> {"what": "action item", "who": ""}
    - "- action item" -> {"what": "action item", "who": ""}
    - "* action item (John)" -> {"what": "action item", "who": "John"}
    - "* action item - assigned to John" -> {"what": "action item", "who": "John"}
    - "* [] action item" -> {"what": "action item", "who": ""} (checkbox format)
    
    Returns None if text is empty/None, or a list of Step dicts.
    """
    if not text or not text.strip():
        return None
    
    # Check if it looks like incomplete/corrupt JSON (starts with [ or { but doesn't parse)
    stripped = text.strip()
    if stripped.startswith('[') or stripped.startswith('{'):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                # Validate and normalize the structure
                normalized = []
                for item in parsed:
                    if isinstance(item, dict):
                        # Handle various key names
                        what = item.get("what") or item.get("step") or item.get("action") or ""
                        who = item.get("who") or item.get("assignee") or ""
                        if what:  # Only add if there's something meaningful
                            normalized.append({"what": what.strip(), "who": who.strip()})
                return normalized if normalized else None
            return None
        except (json.JSONDecodeError, TypeError):
            # Corrupt JSON - return None to skip or clear this field
            print(f"    Warning: Found corrupt JSON data, will be cleared: {text[:50]}...")
            return []  # Return empty list to clear corrupt data
    
    steps = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove bullet markers: *, -, •, numbers with dots
        # Also handle checkbox format: [ ], [x], []
        cleaned = re.sub(r'^[\*\-•]\s*', '', line)
        cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
        cleaned = re.sub(r'^\[[\sx]?\]\s*', '', cleaned)  # Remove checkboxes
        
        if not cleaned.strip():
            continue
        
        what = cleaned.strip()
        who = ""
        
        # Try to extract "who" from various patterns
        
        # Pattern 1: "(Name)" at the end
        match = re.search(r'\s*\(([^)]+)\)\s*$', what)
        if match:
            potential_who = match.group(1).strip()
            # Only treat as "who" if it looks like a name (not a URL or long text)
            if len(potential_who) < 50 and not potential_who.startswith('http'):
                who = potential_who
                what = what[:match.start()].strip()
        
        # Pattern 2: "- assigned to Name" or "assigned to Name"
        if not who:
            match = re.search(r'[-–]\s*assigned\s+to\s+(.+)$', what, re.IGNORECASE)
            if match:
                who = match.group(1).strip()
                what = what[:match.start()].strip()
        
        # Pattern 3: "by Name" at the end (but be careful with URLs)
        if not who and not 'http' in what.lower():
            match = re.search(r'\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$', what)
            if match:
                who = match.group(1).strip()
                what = what[:match.start()].strip()
        
        if what:  # Only add if there's something meaningful
            steps.append({"what": what, "who": who})
    
    return steps if steps else None


def migrate_database(db_path: str, dry_run: bool = False) -> None:
    """
    Migrate past_steps and next_steps columns from TEXT to JSON format.
    
    Args:
        db_path: Path to the SQLite database file
        dry_run: If True, only show what would be done without making changes
    """
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all projects
    cursor.execute("SELECT id, name, past_steps, next_steps FROM projects")
    projects = cursor.fetchall()
    
    print(f"Found {len(projects)} projects to process\n")
    
    updates = []
    
    for project in projects:
        project_id = project['id']
        name = project['name']
        past_steps_text = project['past_steps']
        next_steps_text = project['next_steps']
        
        print(f"Project {project_id}: {name[:50]}...")
        
        # Parse past_steps
        past_steps_json = parse_steps_from_text(past_steps_text)
        past_steps_changed = False
        
        if past_steps_text:
            # Check if conversion actually changes something
            try:
                existing = json.loads(past_steps_text)
                if existing != past_steps_json:
                    past_steps_changed = True
            except json.JSONDecodeError:
                past_steps_changed = True
        
        if past_steps_changed:
            step_count = len(past_steps_json) if past_steps_json else 0
            if past_steps_json == []:
                print(f"  past_steps: CORRUPT DATA -> cleared")
            else:
                print(f"  past_steps: TEXT -> JSON ({step_count} steps)")
            if dry_run:
                print(f"    Original: {past_steps_text[:100]}..." if len(str(past_steps_text)) > 100 else f"    Original: {past_steps_text}")
                if past_steps_json:
                    print(f"    Converted: {json.dumps(past_steps_json, indent=2)[:200]}...")
        
        # Parse next_steps
        next_steps_json = parse_steps_from_text(next_steps_text)
        next_steps_changed = False
        
        if next_steps_text:
            try:
                existing = json.loads(next_steps_text)
                if existing != next_steps_json:
                    next_steps_changed = True
            except json.JSONDecodeError:
                next_steps_changed = True
        
        if next_steps_changed:
            step_count = len(next_steps_json) if next_steps_json else 0
            if next_steps_json == []:
                print(f"  next_steps: CORRUPT DATA -> cleared")
            else:
                print(f"  next_steps: TEXT -> JSON ({step_count} steps)")
            if dry_run:
                print(f"    Original: {next_steps_text[:100]}..." if len(str(next_steps_text)) > 100 else f"    Original: {next_steps_text}")
                if next_steps_json:
                    print(f"    Converted: {json.dumps(next_steps_json, indent=2)[:200]}...")
        
        if past_steps_changed or next_steps_changed:
            # Convert to JSON string, but use None for empty lists (corrupt data cleanup)
            past_steps_value = json.dumps(past_steps_json) if past_steps_json else None
            next_steps_value = json.dumps(next_steps_json) if next_steps_json else None
            
            updates.append({
                'id': project_id,
                'past_steps': past_steps_value,
                'next_steps': next_steps_value,
                'past_steps_changed': past_steps_changed,
                'next_steps_changed': next_steps_changed,
            })
        else:
            print("  No changes needed")
        
        print()
    
    print(f"\nSummary: {len(updates)} projects need updates\n")
    
    if dry_run:
        print("DRY RUN - No changes made. Run without --dry-run to apply changes.")
        conn.close()
        return
    
    if not updates:
        print("No updates needed.")
        conn.close()
        return
    
    # Apply updates
    print("Applying updates...")
    for update in updates:
        if update['past_steps_changed'] and update['next_steps_changed']:
            cursor.execute(
                "UPDATE projects SET past_steps = ?, next_steps = ? WHERE id = ?",
                (update['past_steps'], update['next_steps'], update['id'])
            )
        elif update['past_steps_changed']:
            cursor.execute(
                "UPDATE projects SET past_steps = ? WHERE id = ?",
                (update['past_steps'], update['id'])
            )
        elif update['next_steps_changed']:
            cursor.execute(
                "UPDATE projects SET next_steps = ? WHERE id = ?",
                (update['next_steps'], update['id'])
            )
        print(f"  Updated project {update['id']}")
    
    # Clean up any remaining empty strings to NULL
    print("\nCleaning up empty strings...")
    cursor.execute("UPDATE projects SET past_steps = NULL WHERE past_steps = ''")
    past_steps_cleaned = cursor.rowcount
    cursor.execute("UPDATE projects SET next_steps = NULL WHERE next_steps = ''")
    next_steps_cleaned = cursor.rowcount
    if past_steps_cleaned or next_steps_cleaned:
        print(f"  Converted {past_steps_cleaned} empty past_steps and {next_steps_cleaned} empty next_steps to NULL")
    
    conn.commit()
    print(f"\nSuccessfully updated {len(updates)} projects.")
    conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate past_steps and next_steps from TEXT to JSON format"
    )
    parser.add_argument(
        "database",
        help="Path to the SQLite database file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    migrate_database(args.database, args.dry_run)


if __name__ == "__main__":
    main()
