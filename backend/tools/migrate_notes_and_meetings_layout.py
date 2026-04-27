"""
One-time migration: docs/meetings/* -> docs/notes/{org}/meetings/*, update DB file_ref,
docs/{org}/images -> docs/notes/{org}/notes/images, seed strategy.md from organizations.

Usage (from repository or workspace root):
  uv run python -m tools.migrate_notes_and_meetings_layout --workspace /path/to/workspaces/biz-db \\
      --db /path/to/biz-assistant.db

  # Dry run (no moves or writes, prints actions):
  uv run python -m tools.migrate_notes_and_meetings_layout --workspace /path/ws --db /path/db --dry-run

Back up the workspace and database before running.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

from app.core.utils import sanitize_org_name


def new_file_ref(old: str) -> str:
    """Old paths relative to docs/meetings; new paths relative to docs/notes."""
    old = (old or "").strip().lstrip("/")
    if not old:
        return old
    parts = [p for p in old.split("/") if p]
    if "meetings" in parts:
        return "/".join(parts)
    if len(parts) == 1:
        return f"general/meetings/general/{parts[0]}"
    return "/".join([parts[0], "meetings"] + parts[1:])


def migrate_filesystem(workspace: Path, dry_run: bool) -> None:
    meetings = workspace / "docs" / "meetings"
    notes = workspace / "docs" / "notes"
    if not meetings.is_dir():
        print(f"Skip: no directory {meetings}", file=sys.stderr)
        return
    for child in list(meetings.iterdir()):
        if not child.is_dir():
            continue
        org_slug = child.name
        target = notes / org_slug / "meetings"
        if target.exists():
            print(f"Skip move (target exists): {child} -> {target}", file=sys.stderr)
            continue
        print(f"Move {child} -> {target}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(child), str(target))
    if not dry_run and meetings.is_dir() and not any(meetings.iterdir()):
        try:
            meetings.rmdir()
        except OSError as e:
            print(f"Note: could not remove {meetings}: {e}", file=sys.stderr)


def migrate_db_v2(db_path: Path, dry_run: bool) -> int:
    """Update file_ref for every row where the path was under the old layout."""
    conn = sqlite3.connect(str(db_path))
    n = 0
    try:
        cur = conn.execute("SELECT id, file_ref FROM meetings")
        for mid, file_ref in cur.fetchall():
            if not file_ref:
                continue
            new_ref = new_file_ref(file_ref)
            if new_ref == file_ref:
                continue
            n += 1
            print(f"  meeting {mid}: {file_ref!r} -> {new_ref!r}")
            if not dry_run:
                conn.execute("UPDATE meetings SET file_ref = ? WHERE id = ?", (new_ref, mid))
        if not dry_run:
            conn.commit()
    finally:
        conn.close()
    return n


def migrate_org_images(workspace: Path, dry_run: bool) -> None:
    docs = workspace / "docs"
    if not docs.is_dir():
        return
    skip = {"meetings", "notes", "km", ".ds_store"}
    for child in docs.iterdir():
        if not child.is_dir() or child.name.lower() in skip:
            continue
        img = child / "images"
        if not img.is_dir():
            continue
        dest = docs / "notes" / child.name / "notes" / "images"
        if dest.exists():
            print(f"Skip org images (dest exists): {img} -> {dest}", file=sys.stderr)
            continue
        print(f"Move {img} -> {dest}")
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(img), str(dest))


def run_org_description_path_migration(
    workspace: Path, db_path: Path, dry_run: bool
) -> None:
    """Move legacy organization.description (TEXT) to files + description_path column."""
    from tools.migrate_org_description_to_path import migrate as migrate_org_to_path

    migrate_org_to_path(db_path, workspace, dry_run, drop_legacy=False)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Workspace root (contains docs/ folder)",
    )
    p.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to SQLite database file (e.g. data/biz-assistant.db)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only, do not modify files or database",
    )
    args = p.parse_args()
    workspace = args.workspace.resolve()
    db_path = args.db.resolve()
    if not db_path.is_file():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        return 1
    if not (workspace / "docs").is_dir():
        print(f"Error: workspace has no docs/: {workspace}", file=sys.stderr)
        return 1

    print("=== Filesystem: docs/meetings -> docs/notes/{org}/meetings ===")
    migrate_filesystem(workspace, args.dry_run)
    print("=== Database: meeting file_ref paths ===")
    n = migrate_db_v2(db_path, args.dry_run)
    print(f"Updated {n} meeting row(s).")
    print("=== org images: docs/{org}/images -> docs/notes/{org}/notes/images ===")
    migrate_org_images(workspace, args.dry_run)
    print("=== organizations: inline description -> file + description_path ===")
    run_org_description_path_migration(workspace, db_path, args.dry_run)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
