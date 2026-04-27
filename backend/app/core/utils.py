"""
Shared string/path helpers (no app.services or app.api imports).

Path segment slugs are aligned in spirit with the frontend
``sanitizeOrgNameForPath`` in ``markdownNotes.js``; keep both in sync if rules change.
"""

import re
from pathlib import Path
from typing import Optional

__all__ = [
    "sanitize_path_segment",
    "sanitize_org_name",
    "sanitize_upload_basename",
]


def sanitize_path_segment(value: Optional[str]) -> str:
    """
    Lowercase path segment for org, project, meeting_id folders and similar.

    Allows only alphanumerics, hyphens, and underscores. Returns 'unknown' if
    the result is empty.
    """
    s = (value or "").lower().replace(" ", "-")
    s = re.sub(r"[^a-z0-9\-_]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"


# Semantic alias: same as sanitize_path_segment (org folder names, etc.)
sanitize_org_name = sanitize_path_segment


def sanitize_upload_basename(name: str) -> str:
    """
    Sanitize a single filename (no path components) for image uploads: safe
    alphanumerics, dots, underscores, hyphens; max 200 characters.
    """
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-.")
    return base[:200] or "image"
