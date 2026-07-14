"""Scan org strategy and meeting markdown for dated Meeting headings; persist metrics events."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Meeting, MeetingHeadingEvent, MeetingMetricsMeta, Organization
from app.services.organization_notes import resolve_description_path

logger = logging.getLogger(__name__)

SOURCE_STRATEGY = "strategy"
SOURCE_MEETING_FILE = "meeting_file"

# ## Meeting … / ### Meeting …
HEADING_RE = re.compile(r"^(#{2,3})\s+[Mm]eeting\b(.*)$")
# Date token anywhere in heading tail: M/D, M/D/YY, M/D/YYYY
DATE_RE = re.compile(
    r"(?<!\d)(\d{1,2})/(\d{1,2})(?:/(\d{2}|\d{4}))?(?!\d)"
)

FUTURE_SLACK_DAYS = 30


@dataclass(frozen=True)
class ExtractedHeading:
    org_id: Optional[int]
    meeting_date: date
    source: str
    source_path: str
    heading_text: str
    heading_line: int


def _resolved_notes_root() -> Path:
    settings = get_settings()
    p = Path(settings.notes_root)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def parse_meeting_date_from_heading(
    heading_tail: str,
    *,
    today: Optional[date] = None,
) -> Optional[date]:
    """
    Parse a date from the text after 'Meeting' in a heading.

    Supports M/D, M/D/YY, M/D/YYYY. Bare M/D uses the current year, or previous
    year if that date would fall more than FUTURE_SLACK_DAYS in the future.
    """
    match = DATE_RE.search(heading_tail or "")
    if not match:
        return None

    month = int(match.group(1))
    day = int(match.group(2))
    year_raw = match.group(3)
    ref = today or date.today()

    if year_raw is None:
        year = ref.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            return None
        if candidate > ref + timedelta(days=FUTURE_SLACK_DAYS):
            try:
                candidate = date(year - 1, month, day)
            except ValueError:
                return None
        return candidate

    year = int(year_raw)
    if len(year_raw) == 2:
        year = 2000 + year
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_headings_from_markdown(
    content: str,
    *,
    org_id: Optional[int],
    source: str,
    source_path: str,
    today: Optional[date] = None,
) -> list[ExtractedHeading]:
    """Return dated Meeting headings found in markdown content."""
    results: list[ExtractedHeading] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        hm = HEADING_RE.match(line.strip())
        if not hm:
            continue
        tail = hm.group(2)
        meeting_date = parse_meeting_date_from_heading(tail, today=today)
        if meeting_date is None:
            continue
        results.append(
            ExtractedHeading(
                org_id=org_id,
                meeting_date=meeting_date,
                source=source,
                source_path=source_path,
                heading_text=line.strip()[:1024],
                heading_line=line_no,
            )
        )
    return results


def _dedupe_events(
    strategy_events: list[ExtractedHeading],
    meeting_file_events: list[ExtractedHeading],
) -> list[ExtractedHeading]:
    """Keep all strategy headings; skip meeting-file headings whose (org_id, date) is covered."""
    strategy_keys: set[tuple[Optional[int], date]] = {
        (e.org_id, e.meeting_date) for e in strategy_events
    }
    kept = list(strategy_events)
    for e in meeting_file_events:
        if (e.org_id, e.meeting_date) in strategy_keys:
            continue
        kept.append(e)
    return kept


async def scan_and_persist_meeting_headings(
    db: AsyncSession,
    *,
    today: Optional[date] = None,
) -> MeetingMetricsMeta:
    """
    Scan org strategy files and meeting note files, replace meeting_heading_events,
    and update meeting_metrics_meta. Commits the session.
    """
    notes_root = _resolved_notes_root()
    ref_today = today or date.today()
    files_scanned = 0
    strategy_events: list[ExtractedHeading] = []
    meeting_file_events: list[ExtractedHeading] = []

    org_result = await db.execute(select(Organization))
    organizations = list(org_result.scalars().all())

    for org in organizations:
        path = resolve_description_path(org.name, org.description_path)
        if not path.is_file():
            continue
        try:
            rel = str(path.relative_to(notes_root))
        except ValueError:
            rel = str(path)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read strategy file %s: %s", path, exc)
            continue
        files_scanned += 1
        strategy_events.extend(
            extract_headings_from_markdown(
                content,
                org_id=org.id,
                source=SOURCE_STRATEGY,
                source_path=rel,
                today=ref_today,
            )
        )

    meeting_result = await db.execute(select(Meeting))
    meetings = list(meeting_result.scalars().all())

    for meeting in meetings:
        rel = (meeting.file_ref or "").strip().lstrip("/")
        if not rel or ".." in rel.split("/"):
            continue
        path = notes_root / rel
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read meeting file %s: %s", path, exc)
            continue
        files_scanned += 1
        meeting_file_events.extend(
            extract_headings_from_markdown(
                content,
                org_id=meeting.org_id,
                source=SOURCE_MEETING_FILE,
                source_path=rel,
                today=ref_today,
            )
        )

    events = _dedupe_events(strategy_events, meeting_file_events)

    await db.execute(delete(MeetingHeadingEvent))
    for event in events:
        db.add(
            MeetingHeadingEvent(
                org_id=event.org_id,
                meeting_date=event.meeting_date,
                source=event.source,
                source_path=event.source_path,
                heading_text=event.heading_text,
                heading_line=event.heading_line,
            )
        )

    meta_result = await db.execute(select(MeetingMetricsMeta).limit(1))
    meta = meta_result.scalar_one_or_none()
    now = datetime.now()
    if meta is None:
        meta = MeetingMetricsMeta(
            last_evaluated_at=now,
            files_scanned=files_scanned,
            meetings_found=len(events),
        )
        db.add(meta)
    else:
        meta.last_evaluated_at = now
        meta.files_scanned = files_scanned
        meta.meetings_found = len(events)

    await db.commit()
    await db.refresh(meta)
    logger.info(
        "Meeting heading metrics: scanned=%s found=%s last_evaluated_at=%s",
        files_scanned,
        len(events),
        meta.last_evaluated_at,
    )
    return meta


async def get_meeting_metrics_meta(db: AsyncSession) -> Optional[MeetingMetricsMeta]:
    result = await db.execute(select(MeetingMetricsMeta).limit(1))
    return result.scalar_one_or_none()


# --- Filesystem audit (no DB): diagnose strategy / meeting markdown under a root ---

# Undated section titles that are not meeting events
_SECTION_TAIL_RE = re.compile(r"^\s*(s|notes?)?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class HeadingAuditRow:
    line: int
    text: str
    meeting_date: Optional[date]
    kind: str  # dated | section | dirty


@dataclass
class FileAuditRow:
    path: str
    file_kind: str  # strategy | index | meeting_file
    headings: list[HeadingAuditRow]

    @property
    def dated_count(self) -> int:
        return sum(1 for h in self.headings if h.kind == "dated")

    @property
    def dirty_count(self) -> int:
        return sum(1 for h in self.headings if h.kind == "dirty")


@dataclass
class NotesRootAuditReport:
    root: str
    files: list[FileAuditRow]

    @property
    def files_scanned(self) -> int:
        return len(self.files)

    @property
    def dated_total(self) -> int:
        return sum(f.dated_count for f in self.files)

    @property
    def dirty_total(self) -> int:
        return sum(f.dirty_count for f in self.files)

    @property
    def strategy_files(self) -> list[FileAuditRow]:
        return [f for f in self.files if f.file_kind == "strategy"]

    @property
    def index_files(self) -> list[FileAuditRow]:
        return [f for f in self.files if f.file_kind == "index"]

    @property
    def meeting_files(self) -> list[FileAuditRow]:
        return [f for f in self.files if f.file_kind == "meeting_file"]


def classify_meeting_heading_tail(
    tail: str,
    *,
    today: Optional[date] = None,
) -> tuple[str, Optional[date]]:
    """
    Classify text after 'Meeting' in a heading.

    Returns (kind, meeting_date) where kind is dated | section | dirty.
    """
    meeting_date = parse_meeting_date_from_heading(tail, today=today)
    if meeting_date is not None:
        return "dated", meeting_date
    if _SECTION_TAIL_RE.match(tail or ""):
        return "section", None
    return "dirty", None


def audit_markdown_meeting_headings(
    content: str,
    *,
    today: Optional[date] = None,
) -> list[HeadingAuditRow]:
    """Classify every ##/### Meeting heading in markdown (dated, section, or dirty)."""
    rows: list[HeadingAuditRow] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        hm = HEADING_RE.match(stripped)
        if not hm:
            continue
        kind, meeting_date = classify_meeting_heading_tail(hm.group(2), today=today)
        rows.append(
            HeadingAuditRow(
                line=line_no,
                text=stripped[:1024],
                meeting_date=meeting_date,
                kind=kind,
            )
        )
    return rows


def _classify_notes_path(rel: Path) -> Optional[str]:
    """Return strategy | index | meeting_file for a path relative to notes root."""
    parts = rel.parts
    name = rel.name.lower()
    if "meetings" in parts and name.endswith(".md"):
        return "meeting_file"
    if name == "strategy.md":
        return "strategy"
    if name == "index.md":
        return "index"
    return None


def audit_notes_root_meeting_headings(
    root: Path | str,
    *,
    today: Optional[date] = None,
) -> NotesRootAuditReport:
    """
    Walk a notes root and audit Meeting headings in strategy.md, index.md,
    and files under any meetings/ directory. Does not touch the database.
    """
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise FileNotFoundError(f"Notes root is not a directory: {root_path}")

    ref_today = today or date.today()
    files: list[FileAuditRow] = []

    for path in sorted(root_path.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root_path)
        except ValueError:
            continue
        file_kind = _classify_notes_path(rel)
        if file_kind is None:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read %s: %s", path, exc)
            continue
        headings = audit_markdown_meeting_headings(content, today=ref_today)
        files.append(
            FileAuditRow(
                path=str(rel).replace("\\", "/"),
                file_kind=file_kind,
                headings=headings,
            )
        )

    return NotesRootAuditReport(root=str(root_path), files=files)


def format_notes_root_audit_report(report: NotesRootAuditReport) -> str:
    """Human-readable audit report for CLI / pytest -s output."""
    lines: list[str] = [
        f"Meeting heading audit: {report.root}",
        f"  files_scanned={report.files_scanned}  dated={report.dated_total}  dirty={report.dirty_total}",
        f"  strategy={len(report.strategy_files)}  index={len(report.index_files)}  "
        f"meeting_files={len(report.meeting_files)}",
        "",
    ]
    for f in report.files:
        lines.append(f"[{f.file_kind}] {f.path}  dated={f.dated_count} dirty={f.dirty_count}")
        for h in f.headings:
            if h.kind == "dated":
                lines.append(f"  L{h.line} dated {h.meeting_date}  {h.text}")
            elif h.kind == "dirty":
                lines.append(f"  L{h.line} DIRTY  {h.text}")
            else:
                lines.append(f"  L{h.line} section  {h.text}")
        if not f.headings:
            lines.append("  (no ##/### Meeting headings)")
        lines.append("")
    return "\n".join(lines)
