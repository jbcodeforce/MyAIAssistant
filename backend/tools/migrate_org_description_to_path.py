"""
SQLite migration: store organization strategy as a file path, not inline text.

- Adds organizations.description_path if missing.
- If legacy column `description` (TEXT) exists with long-form markdown, writes
  docs/notes/{slug}/notes/strategy.md and sets description_path.
- If `description` already looks like a path (*/notes/*.md), copies to description_path.
- Optionally drops legacy `description` column (SQLite 3.35+).

  uv run python -m tools.migrate_org_description_to_path --db path/to.db [--workspace path] --dry-run
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

from app.core.utils import sanitize_org_name

_PATH_RE = re.compile(r"^[\w\-]+/notes/.+\.md$", re.IGNORECASE)


def _table_columns(conn: sqlite3.Connection) -> set[str]:
    return {r[1] for r in conn.execute("PRAGMA table_info(organizations)").fetchall()}


def migrate(
    db_path: Path, workspace: Path | None, dry_run: bool, drop_legacy: bool
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        cols = _table_columns(conn)
        if "description_path" not in cols:
            print("ALTER TABLE: ADD description_path")
            if not dry_run:
                conn.execute(
                    "ALTER TABLE organizations ADD COLUMN description_path VARCHAR(2048)"
                )
                conn.commit()
            cols = _table_columns(conn)

        if "description" not in cols:
            print("No legacy `description` column; only description_path is used.", file=sys.stderr)
            return

        if "description_path" in cols:
            cur = conn.execute(
                "SELECT id, name, description, description_path FROM organizations"
            )
        else:
            # Dry-run may not have added the column yet; treat path as empty.
            cur = conn.execute("SELECT id, name, description FROM organizations")
        notes_root = (workspace or Path.cwd()) / "docs" / "notes"
        for row in cur.fetchall():
            if len(row) == 4:
                org_id, name, legacy_desc, current_path = row
            else:
                org_id, name, legacy_desc = row
                current_path = ""
            current_path = (current_path or "")
            legacy = legacy_desc
            if legacy is None:
                legacy = ""
            if current_path.strip():
                continue
            slug = sanitize_org_name(name)
            new_path = f"{slug}/notes/strategy.md"
            t = (legacy or "").strip()
            if not t:
                continue
            if _PATH_RE.match(t):
                new_path = t.replace("\\", "/").strip()
                if not dry_run:
                    conn.execute(
                        "UPDATE organizations SET description_path = ? WHERE id = ?",
                        (new_path, org_id),
                    )
                print(f"  org {org_id} ({name}): set description_path = {new_path!r} (from legacy path cell)")
            else:
                fpath = notes_root / slug / "notes" / "strategy.md"
                print(f"  org {org_id} ({name}): write {fpath} + set description_path = {new_path!r}")
                if not dry_run:
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    fpath.write_text(legacy, encoding="utf-8")
                    conn.execute(
                        "UPDATE organizations SET description_path = ? WHERE id = ?",
                        (new_path, org_id),
                    )
        if not dry_run:
            conn.commit()
        if drop_legacy and "description" in _table_columns(conn) and not dry_run:
            try:
                conn.execute("ALTER TABLE organizations DROP COLUMN description")
                conn.commit()
                print("Dropped legacy column: description", file=sys.stderr)
            except sqlite3.OperationalError as e:
                print(
                    f"Note: could not DROP COLUMN description (need SQLite 3.35+): {e}",
                    file=sys.stderr,
                )
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--workspace", type=Path, default=None, help="For writing strategy files (docs/notes)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--drop-legacy",
        action="store_true",
        help="After migration, DROP legacy description column (SQLite 3.35+)",
    )
    args = p.parse_args()
    if not args.db.is_file():
        print(f"Not found: {args.db}", file=sys.stderr)
        return 1
    migrate(
        args.db.resolve(),
        args.workspace.resolve() if args.workspace else None,
        args.dry_run,
        args.drop_legacy,
    )
    print("Done.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
