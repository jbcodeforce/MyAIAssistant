#!/usr/bin/env python3
"""
Report dated and dirty Meeting headings per organization under a notes root.

Uses the same filesystem rules as the Metrics scanner / integration audit
(strategy.md, index.md, meetings/**/*.md). Does not modify files or the DB.

Usage (from backend/):

    uv run python scripts/report_org_meetings.py /path/to/docs/notes
    uv run python scripts/report_org_meetings.py /path/to/customers --dirty-only
    uv run python scripts/report_org_meetings.py /path/to/notes --org acme -v

Exit codes:
    0 — no dirty headings (or report completed with --no-fail)
    1 — one or more dirty headings found
    2 — usage / path error
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Allow `uv run python scripts/...` from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.meeting_heading_metrics import (
    FileAuditRow,
    NotesRootAuditReport,
    audit_notes_root_meeting_headings,
)


@dataclass
class OrgMeetingReport:
    org: str
    files: list[FileAuditRow] = field(default_factory=list)

    @property
    def dated_count(self) -> int:
        return sum(f.dated_count for f in self.files)

    @property
    def dirty_count(self) -> int:
        return sum(f.dirty_count for f in self.files)

    @property
    def section_count(self) -> int:
        return sum(1 for f in self.files for h in f.headings if h.kind == "section")


def org_slug_from_path(rel_path: str) -> str:
    """First path segment is the organization folder under the notes root."""
    parts = Path(rel_path).parts
    return parts[0] if parts else "(root)"


def group_report_by_org(report: NotesRootAuditReport) -> list[OrgMeetingReport]:
    by_org: dict[str, OrgMeetingReport] = {}
    for f in report.files:
        org = org_slug_from_path(f.path)
        if org not in by_org:
            by_org[org] = OrgMeetingReport(org=org)
        by_org[org].files.append(f)
    return sorted(by_org.values(), key=lambda o: o.org.lower())


def format_summary_table(orgs: list[OrgMeetingReport]) -> str:
    rows = [("organization", "dated", "dirty", "files")]
    for o in orgs:
        rows.append((o.org, str(o.dated_count), str(o.dirty_count), str(len(o.files))))
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    lines = []
    for i, row in enumerate(rows):
        line = "  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row))
        lines.append(line)
        if i == 0:
            lines.append("  ".join("-" * widths[j] for j in range(4)))
    total_dated = sum(o.dated_count for o in orgs)
    total_dirty = sum(o.dirty_count for o in orgs)
    lines.append("")
    lines.append(f"orgs={len(orgs)}  dated={total_dated}  dirty={total_dirty}")
    return "\n".join(lines)


def format_org_detail(org: OrgMeetingReport, *, dirty_only: bool, verbose: bool) -> str:
    lines = [
        f"## {org.org}  dated={org.dated_count}  dirty={org.dirty_count}  "
        f"files={len(org.files)}"
    ]
    for f in org.files:
        if dirty_only and f.dirty_count == 0:
            continue
        lines.append(f"  [{f.file_kind}] {f.path}")
        for h in f.headings:
            if dirty_only and h.kind != "dirty":
                continue
            if h.kind == "dated":
                if verbose or not dirty_only:
                    lines.append(f"    L{h.line} dated {h.meeting_date}  {h.text}")
            elif h.kind == "dirty":
                lines.append(f"    L{h.line} DIRTY  {h.text}")
            elif verbose:
                lines.append(f"    L{h.line} section  {h.text}")
        if not dirty_only and not f.headings and verbose:
            lines.append("    (no ##/### Meeting headings)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Report Meeting headings per organization under a notes root "
            "(strategy.md, index.md, meetings/**/*.md)."
        )
    )
    p.add_argument(
        "root",
        type=Path,
        help="Notes or customers root directory to scan",
    )
    p.add_argument(
        "--dirty-only",
        action="store_true",
        help="Only list organizations/files that have dirty headings",
    )
    p.add_argument(
        "--org",
        metavar="SLUG",
        help="Limit detail to one organization folder name",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Include dated and section headings in the detail listing",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the per-org summary table",
    )
    p.add_argument(
        "--no-fail",
        action="store_true",
        help="Always exit 0 even when dirty headings exist",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    try:
        report = audit_notes_root_meeting_headings(root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    orgs = group_report_by_org(report)
    if args.org:
        orgs = [o for o in orgs if o.org.lower() == args.org.lower()]
        if not orgs:
            print(f"error: no organization folder matching {args.org!r}", file=sys.stderr)
            return 2

    print(f"Meeting headings by organization: {report.root}")
    print()
    summary_orgs = orgs
    if args.dirty_only:
        summary_orgs = [o for o in orgs if o.dirty_count > 0]
    print(format_summary_table(summary_orgs if args.dirty_only else orgs))

    if not args.summary_only:
        print()
        detail_orgs = [o for o in orgs if (not args.dirty_only) or o.dirty_count > 0]
        if not detail_orgs and args.dirty_only:
            print("(no dirty headings)")
        for o in detail_orgs:
            print(format_org_detail(o, dirty_only=args.dirty_only, verbose=args.verbose))
            print()

    dirty_total = sum(o.dirty_count for o in orgs)
    if dirty_total and not args.no_fail:
        print(f"Found {dirty_total} dirty heading(s). Fix dates then re-run.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
