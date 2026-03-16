"""Service for storing and resolving note images under the workspace docs/meetings layout."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@dataclass
class UploadResult:
    """Result of uploading an image for a note."""

    path: str  # Relative path for markdown, e.g. ./images/name.png
    context_base: str  # Base path for serve API, e.g. meetings/acme/proj or my-org


def _sanitize_filename(name: str) -> str:
    """Sanitize filename: no path components, safe chars only."""
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-.")
    return base[:200] or "image"


def _sanitize_org_name(name: str) -> str:
    """Sanitize organization name for path (match organizations.py)."""
    sanitized = (name or "").lower().replace(" ", "-")
    sanitized = re.sub(r"[^a-z0-9\-_]", "", sanitized)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "unknown"


class NotesImagesService:
    """
    Handles saving note images under the workspace and resolving paths.
    - Meeting context: images under notes_root / dir(file_ref) / images/
    - Organization context: images under docs_root / org_name / images/
    """

    def __init__(self):
        settings = get_settings()
        self.notes_root = Path(settings.notes_root)
        if not self.notes_root.is_absolute():
            self.notes_root = Path.cwd() / self.notes_root
        self.notes_root = self.notes_root.resolve()
        self.docs_root = self.notes_root.parent
        logger.debug(
            "NotesImagesService: notes_root=%s docs_root=%s",
            self.notes_root,
            self.docs_root,
        )

    def _dir_of_file_ref(self, file_ref: str) -> str:
        """Return the directory part of file_ref (relative to notes_root)."""
        ref = file_ref.strip("/")
        if "/" in ref:
            return str(Path(ref).parent).replace("\\", "/")
        return "."

    def save_meeting_image(self, file_ref: str, filename: str, content: bytes) -> UploadResult:
        """
        Save an image for a meeting note. file_ref is e.g. acme/proj/2026-01-10-mtg.md.
        Saves to notes_root / acme/proj / images / filename.
        Returns path ./images/filename and context_base meetings/acme/proj.
        """
        dir_part = self._dir_of_file_ref(file_ref)
        if dir_part == ".":
            images_dir = self.notes_root / "images"
        else:
            images_dir = self.notes_root / dir_part / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _sanitize_filename(filename)
        target = images_dir / safe_name
        target.write_bytes(content)
        logger.info("Saved meeting image to %s", target)
        # context_base for serve: path relative to docs_root
        if dir_part == ".":
            serve_base = "meetings"
        else:
            serve_base = f"meetings/{dir_part}"
        return UploadResult(path=f"./images/{safe_name}", context_base=serve_base)

    def save_organization_image(
        self, org_name: str, filename: str, content: bytes
    ) -> UploadResult:
        """
        Save an image for organization (and export). org_name is sanitized.
        Saves to docs_root / org_name / images / filename.
        Returns path ./images/filename and context_base org_name.
        """
        safe_org = _sanitize_org_name(org_name)
        images_dir = self.docs_root / safe_org / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _sanitize_filename(filename)
        target = images_dir / safe_name
        target.write_bytes(content)
        logger.info("Saved organization image to %s", target)
        return UploadResult(path=f"./images/{safe_name}", context_base=safe_org)

    def resolve_serve_path(self, path: str) -> Optional[Path]:
        """
        Resolve a request path (relative to docs_root) to a file path.
        path is e.g. meetings/acme/proj/images/name.png or my-org/images/name.png.
        Returns absolute Path if valid and under docs_root; None otherwise.
        """
        path = path.strip("/")
        if not path or ".." in path or path.startswith("/"):
            return None
        resolved = (self.docs_root / path).resolve()
        try:
            resolved.relative_to(self.docs_root)
        except ValueError:
            return None
        if not resolved.is_file():
            return None
        return resolved
