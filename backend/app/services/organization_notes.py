"""File-backed organization strategy/notes: DB stores description_path; content lives on disk."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.utils import sanitize_org_name

logger = logging.getLogger(__name__)

STRATEGY_FILENAME = "strategy.md"


def _resolved_notes_root() -> Path:
    settings = get_settings()
    p = Path(settings.notes_root)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def default_description_path(organization_name: str) -> str:
    """Path relative to notes_root for the default strategy file."""
    return f"{sanitize_org_name(organization_name)}/notes/{STRATEGY_FILENAME}"


def resolve_description_path(organization_name: str, path_ref: Optional[str]) -> Path:
    """
    Absolute path to the strategy file. path_ref is relative to notes_root (e.g. acme/notes/strategy.md).
    Rejects '..' in path.
    """
    rel = (path_ref or default_description_path(organization_name)).strip().lstrip("/")
    if ".." in rel.split("/") or rel.startswith(".."):
        return strategy_file_path(organization_name)
    return _resolved_notes_root() / rel


def strategy_file_path(organization_name: str) -> Path:
    """Absolute path to default strategy.md (when using default layout)."""
    return resolve_description_path(organization_name, default_description_path(organization_name))


def read_description_file(organization_name: str, path_ref: Optional[str]) -> str:
    """Read markdown for API response `description`; empty string if file missing."""
    p = resolve_description_path(organization_name, path_ref)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")


def write_description(organization_name: str, path_ref: Optional[str], content: str) -> Path:
    """Write strategy file; creates parent dirs."""
    path = resolve_description_path(organization_name, path_ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")
    logger.info("Wrote organization description file: %s", path)
    return path


def move_org_notes_tree_if_renamed(
    old_organization_name: str, new_organization_name: str
) -> None:
    """
    If the sanitized org folder name changed, rename notes_root/{old} -> notes_root/{new}
    (moves notes + meetings and any other content under the org).
    """
    old_s, new_s = sanitize_org_name(old_organization_name), sanitize_org_name(
        new_organization_name
    )
    if old_s == new_s:
        return
    root = _resolved_notes_root()
    old_dir, new_dir = root / old_s, root / new_s
    if not old_dir.is_dir():
        return
    if new_dir.exists():
        logger.warning(
            "Not moving org notes tree: target exists (old=%s, new=%s)", old_dir, new_dir
        )
        return
    new_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_dir), str(new_dir))
    logger.info("Renamed org notes tree %s -> %s", old_dir, new_dir)


def rebase_description_path(
    path_ref: Optional[str], old_organization_name: str, new_organization_name: str
) -> Optional[str]:
    """If description_path lives under the old org slug, rewrite to the new slug after rename."""
    if not path_ref:
        return path_ref
    old_s = sanitize_org_name(old_organization_name)
    new_s = sanitize_org_name(new_organization_name)
    if old_s == new_s or not path_ref.strip().startswith(f"{old_s}/"):
        return path_ref
    return f"{new_s}/" + path_ref.strip()[len(old_s) + 1 :]
