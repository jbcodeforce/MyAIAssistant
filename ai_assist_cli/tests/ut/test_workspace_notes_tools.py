"""Tests for WorkspaceNotesTools path safety and list/read."""

from __future__ import annotations

import json
from pathlib import Path

from ai_assist_cli.agents.workspace_notes_tools import WorkspaceNotesTools


def test_list_markdown_files(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("# B", encoding="utf-8")
    tools = WorkspaceNotesTools(notes_root=tmp_path)
    raw = tools.list_markdown_files()
    paths = json.loads(raw)
    assert "a.md" in paths
    assert "sub/b.md" in paths


def test_read_markdown_file(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("hello", encoding="utf-8")
    tools = WorkspaceNotesTools(notes_root=tmp_path)
    assert tools.read_markdown_file("x.md") == "hello"


def test_path_traversal_rejected(tmp_path: Path) -> None:
    tools = WorkspaceNotesTools(notes_root=tmp_path)
    out = tools.read_markdown_file("../../etc/passwd")
    assert "invalid" in out.lower() or "traversal" in out.lower() or "Error" in out


def test_oversized_file_rejected(tmp_path: Path) -> None:
    (tmp_path / "big.md").write_bytes(b"x" * 300_000)
    tools = WorkspaceNotesTools(notes_root=tmp_path, max_read_bytes=1024)
    out = tools.read_markdown_file("big.md")
    assert "too large" in out.lower()
