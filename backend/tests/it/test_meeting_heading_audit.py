"""
Integration audit: walk a notes root and list strategy / index / meeting files
with dated vs dirty Meeting headings.

Skip unless MEETING_METRICS_AUDIT_ROOT is set to an existing directory.

Example:

    MEETING_METRICS_AUDIT_ROOT=/path/to/docs/notes \\
      uv run pytest tests/it/test_meeting_heading_audit.py -m integration -s -v

    # Customer-style tree (org folders with index.md):
    MEETING_METRICS_AUDIT_ROOT=/path/to/customers \\
      uv run pytest tests/it/test_meeting_heading_audit.py -m integration -s -v

Fail if any dirty Meeting heading is found (undated heading that is not a
known section title like "## Meeting notes" / "## Meetings").
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.services.meeting_heading_metrics import (
    audit_notes_root_meeting_headings,
    format_notes_root_audit_report,
)

ENV_AUDIT_ROOT = "MEETING_METRICS_AUDIT_ROOT"


def _audit_root() -> Path | None:
    raw = (os.environ.get(ENV_AUDIT_ROOT) or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


@pytest.mark.integration
def test_audit_notes_root_lists_strategy_and_meetings():
    root = _audit_root()
    if root is None:
        pytest.skip(
            f"Set {ENV_AUDIT_ROOT} to a notes/customers root to run this audit"
        )
    if not root.is_dir():
        pytest.fail(f"{ENV_AUDIT_ROOT} is not a directory: {root}")

    report = audit_notes_root_meeting_headings(root)
    print("\n" + format_notes_root_audit_report(report))

    assert report.files_scanned > 0, (
        f"No strategy.md, index.md, or meetings/**/*.md under {root}"
    )

    dirty_rows = [
        (f.path, h.line, h.text)
        for f in report.files
        for h in f.headings
        if h.kind == "dirty"
    ]
    assert not dirty_rows, (
        f"Found {len(dirty_rows)} dirty Meeting heading(s) "
        f"(undated / unparseable, not a section title):\n"
        + "\n".join(f"  {path}:{line}  {text}" for path, line, text in dirty_rows)
    )
