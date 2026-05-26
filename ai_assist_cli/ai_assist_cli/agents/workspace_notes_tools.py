"""Read-only access to markdown files under a workspace notes directory."""

from __future__ import annotations

import json
from pathlib import Path

from agno.tools import Toolkit

DEFAULT_MAX_READ_BYTES = 262_144


class WorkspaceNotesTools(Toolkit):
    """List and read markdown files under notes_root (path traversal blocked)."""

    def __init__(
        self,
        notes_root: Path,
        max_read_bytes: int = DEFAULT_MAX_READ_BYTES,
        **kwargs,
    ):
        self.notes_root = notes_root.resolve()
        self.max_read_bytes = max_read_bytes
        tools = [self.list_markdown_files, self.read_markdown_file]
        super().__init__(name="workspace_notes_tools", tools=tools, **kwargs)

    def _safe_relative_path(self, relative_path: str) -> Path | None:
        """Resolve relative_path under notes_root; return None if traversal escapes."""
        rel = relative_path.strip().replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            return None
        candidate = (self.notes_root / rel).resolve()
        try:
            candidate.relative_to(self.notes_root)
        except ValueError:
            return None
        return candidate

    def list_markdown_files(self, subdirectory: str = "") -> str:
        """List markdown files under notes_root, optionally scoped to a subdirectory.

        Args:
            subdirectory: Optional path relative to notes_root (no leading slash).

        Returns:
            JSON list of paths relative to notes_root (POSIX-style).
        """
        base = self.notes_root
        if subdirectory.strip():
            safe = self._safe_relative_path(subdirectory)
            if safe is None or not safe.is_dir():
                return json.dumps({"error": "invalid_or_missing_subdirectory"})
            base = safe
        if not base.exists():
            return json.dumps([])
        paths: list[str] = []
        for p in sorted(base.rglob("*.md")):
            try:
                rel = p.resolve().relative_to(self.notes_root)
                paths.append(rel.as_posix())
            except ValueError:
                continue
        return json.dumps(paths)

    def read_markdown_file(self, relative_path: str) -> str:
        """Read one markdown file under notes_root (size capped).

        Args:
            relative_path: Path relative to notes_root (e.g. acme/notes/index.md).

        Returns:
            File contents or an error message string.
        """
        target = self._safe_relative_path(relative_path)
        if target is None:
            return "Error: invalid path or path traversal rejected."
        if not target.is_file():
            return "Error: file not found."
        size = target.stat().st_size
        if size > self.max_read_bytes:
            return (
                f"Error: file too large ({size} bytes; max {self.max_read_bytes}). "
                "Request a smaller file or summarize via SQL meeting refs."
            )
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return f"Error reading file: {e}"
