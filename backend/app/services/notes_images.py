"""Service for storing and resolving note images under the workspace docs/ tree."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.utils import sanitize_org_name, sanitize_upload_basename

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
    context_base: str  # Base path for serve API (relative to docs), e.g. notes/acme/meetings/proj


class NotesImagesService:
    """
    Handles saving note images under the workspace and resolving paths.
    - Meeting context: images under notes_root / dir(file_ref) / images/
    - Organization context: images under docs_root / notes / org / notes / images/
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

    def _serve_base_for_note_dir(self, dir_part: str) -> str:
        """Directory containing the .md file, as a path relative to docs_root (for API URLs)."""
        if dir_part == ".":
            note_dir = self.notes_root
        else:
            note_dir = self.notes_root / dir_part
        return note_dir.resolve().relative_to(self.docs_root).as_posix()

    def save_meeting_image(self, file_ref: str, filename: str, content: bytes) -> UploadResult:
        """
        Save an image for a meeting note. file_ref is relative to notes_root, e.g. acme/meetings/proj/2026-01-10-mtg.md.
        Saves under notes_root / ... / images / filename.
        Returns path ./images/filename and context_base = note directory relative to docs_root.
        """
        dir_part = self._dir_of_file_ref(file_ref)
        if dir_part == ".":
            images_dir = self.notes_root / "images"
        else:
            images_dir = self.notes_root / dir_part / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_upload_basename(filename)
        target = images_dir / safe_name
        target.write_bytes(content)
        logger.info("Saved meeting image to %s", target)
        serve_base = self._serve_base_for_note_dir(dir_part)
        return UploadResult(path=f"./images/{safe_name}", context_base=serve_base)

    def save_organization_image(
        self, org_name: str, filename: str, content: bytes
    ) -> UploadResult:
        """
        Save an image for organization strategy/notes markdown. org_name is sanitized.
        Saves to docs/notes/{org}/notes/images/ (i.e. alongside strategy.md).
        Returns path ./images/filename and context_base notes/{org}/notes.
        """
        safe_org = sanitize_org_name(org_name)
        images_dir = self.docs_root / "notes" / safe_org / "notes" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_upload_basename(filename)
        target = images_dir / safe_name
        target.write_bytes(content)
        logger.info("Saved organization image to %s", target)
        return UploadResult(
            path=f"./images/{safe_name}",
            context_base=f"notes/{safe_org}/notes",
        )

    def resolve_serve_path(self, path: str) -> Optional[Path]:
        """
        Resolve a request path (relative to docs_root) to a file path.
        path is e.g. notes/acme/meetings/proj/images/name.png or notes/acme/notes/images/name.png.
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
