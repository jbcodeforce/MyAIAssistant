"""Tests for dated Meeting heading parsing and metrics scan/dedupe."""

from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.models import Meeting, MeetingHeadingEvent, Organization
from app.services.meeting_heading_metrics import (
    SOURCE_MEETING_FILE,
    SOURCE_STRATEGY,
    ExtractedHeading,
    _dedupe_events,
    extract_headings_from_markdown,
    parse_meeting_date_from_heading,
    scan_and_persist_meeting_headings,
)


@pytest.mark.parametrize(
    "tail,today,expected",
    [
        (" 01/07", date(2026, 7, 13), date(2026, 1, 7)),
        (" 3/17", date(2026, 7, 13), date(2026, 3, 17)),
        (" Workshop 2/11/2026", date(2026, 7, 13), date(2026, 2, 11)),
        (" 02/11/26", date(2026, 7, 13), date(2026, 2, 11)),
        (" 12/20", date(2026, 1, 10), date(2025, 12, 20)),  # future >30d → prior year
        (" notes", date(2026, 7, 13), None),
        ("s", date(2026, 7, 13), None),
    ],
)
def test_parse_meeting_date_from_heading(tail, today, expected):
    assert parse_meeting_date_from_heading(tail, today=today) == expected


def test_extract_ignores_undated_section_titles():
    content = """
# Org

## Meeting notes

## Meetings

## Meeting 01/07

### Meeting 3/17

### Meeting Workshop 2/11/2026
"""
    events = extract_headings_from_markdown(
        content,
        org_id=1,
        source=SOURCE_STRATEGY,
        source_path="acme/notes/strategy.md",
        today=date(2026, 7, 13),
    )
    assert len(events) == 3
    assert [e.meeting_date for e in events] == [
        date(2026, 1, 7),
        date(2026, 3, 17),
        date(2026, 2, 11),
    ]


def test_audit_classifies_section_dated_and_dirty(tmp_path):
    from app.services.meeting_heading_metrics import (
        audit_notes_root_meeting_headings,
        format_notes_root_audit_report,
    )

    strategy = tmp_path / "acme" / "notes" / "strategy.md"
    strategy.parent.mkdir(parents=True)
    strategy.write_text(
        "## Meeting notes\n\n## Meeting 01/07\n\n## Meeting Workshop TBD\n",
        encoding="utf-8",
    )
    meeting = tmp_path / "acme" / "meetings" / "p" / "note.md"
    meeting.parent.mkdir(parents=True)
    meeting.write_text("### Meeting 3/17\n", encoding="utf-8")
    index = tmp_path / "beta" / "index.md"
    index.parent.mkdir(parents=True)
    index.write_text("## Meetings\n\n## Meeting 02/11/26\n", encoding="utf-8")

    report = audit_notes_root_meeting_headings(tmp_path, today=date(2026, 7, 13))
    printed = format_notes_root_audit_report(report)
    assert "strategy.md" in printed
    assert report.files_scanned == 3
    assert report.dated_total == 3
    assert report.dirty_total == 1
    dirty = [h for f in report.files for h in f.headings if h.kind == "dirty"]
    assert dirty[0].text.startswith("## Meeting Workshop TBD")


def test_same_day_headings_in_one_file_all_count():
    content = "## Meeting 01/07 a\n\n## Meeting 01/07 b\n"
    events = extract_headings_from_markdown(
        content,
        org_id=1,
        source=SOURCE_STRATEGY,
        source_path="acme/notes/strategy.md",
        today=date(2026, 7, 13),
    )
    assert len(events) == 2


def test_dedupe_strategy_wins_for_org_date():
    strategy = [
        ExtractedHeading(
            org_id=1,
            meeting_date=date(2026, 1, 7),
            source=SOURCE_STRATEGY,
            source_path="acme/notes/strategy.md",
            heading_text="## Meeting 01/07",
            heading_line=10,
        )
    ]
    meeting_files = [
        ExtractedHeading(
            org_id=1,
            meeting_date=date(2026, 1, 7),
            source=SOURCE_MEETING_FILE,
            source_path="acme/meetings/p/2026-01-07-x.md",
            heading_text="## Meeting 01/07",
            heading_line=1,
        ),
        ExtractedHeading(
            org_id=1,
            meeting_date=date(2026, 2, 1),
            source=SOURCE_MEETING_FILE,
            source_path="acme/meetings/p/2026-02-01-y.md",
            heading_text="## Meeting 02/01",
            heading_line=1,
        ),
    ]
    kept = _dedupe_events(strategy, meeting_files)
    assert len(kept) == 2
    assert kept[0].source == SOURCE_STRATEGY
    assert kept[1].meeting_date == date(2026, 2, 1)


@pytest_asyncio.fixture
async def notes_root_and_org(db_session, tmp_path, monkeypatch):
    notes_root = tmp_path / "docs" / "notes"
    strategy = notes_root / "acme" / "notes" / "strategy.md"
    strategy.parent.mkdir(parents=True)
    strategy.write_text(
        "# Acme\n\n## Meeting notes\n\n## Meeting 01/07\n\nnotes\n\n## Meeting 02/01\n",
        encoding="utf-8",
    )
    meeting_path = notes_root / "acme" / "meetings" / "general" / "2026-01-07-kickoff.md"
    meeting_path.parent.mkdir(parents=True)
    meeting_path.write_text(
        "# Kickoff\n\n## Meeting 01/07\n\nalready in strategy\n\n## Meeting 03/15\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.meeting_heading_metrics.get_settings",
        lambda: type("S", (), {"notes_root": str(notes_root)})(),
    )
    monkeypatch.setattr(
        "app.services.organization_notes.get_settings",
        lambda: type("S", (), {"notes_root": str(notes_root)})(),
    )

    org = Organization(
        name="acme",
        description_path="acme/notes/strategy.md",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    meeting = Meeting(
        meeting_id="mtg-kickoff",
        org_id=org.id,
        file_ref="acme/meetings/general/2026-01-07-kickoff.md",
    )
    db_session.add(meeting)
    await db_session.commit()

    return notes_root, org


@pytest.mark.asyncio
async def test_scan_and_persist_dedupes_and_counts(db_session, notes_root_and_org):
    _notes_root, org = notes_root_and_org
    meta = await scan_and_persist_meeting_headings(
        db_session,
        today=date(2026, 7, 13),
    )

    assert meta.files_scanned == 2
    # strategy: 01/07, 02/01; meeting file: 03/15 (01/07 skipped)
    assert meta.meetings_found == 3
    assert meta.last_evaluated_at is not None

    result = await db_session.execute(
        select(MeetingHeadingEvent).order_by(MeetingHeadingEvent.meeting_date)
    )
    events = list(result.scalars().all())
    assert [e.meeting_date for e in events] == [
        date(2026, 1, 7),
        date(2026, 2, 1),
        date(2026, 3, 15),
    ]
    assert events[0].source == SOURCE_STRATEGY
    assert events[2].source == SOURCE_MEETING_FILE
    assert all(e.org_id == org.id for e in events)


@pytest.mark.asyncio
async def test_refresh_endpoint(client, tmp_path, monkeypatch):
    notes_root = tmp_path / "notes"
    strategy = notes_root / "beta" / "notes" / "strategy.md"
    strategy.parent.mkdir(parents=True)
    strategy.write_text("## Meeting 04/21\n", encoding="utf-8")

    monkeypatch.setattr(
        "app.services.meeting_heading_metrics.get_settings",
        lambda: type("S", (), {"notes_root": str(notes_root)})(),
    )
    monkeypatch.setattr(
        "app.services.organization_notes.get_settings",
        lambda: type("S", (), {"notes_root": str(notes_root)})(),
    )

    create = await client.post(
        "/api/organizations/",
        json={"name": "beta", "description": "## Meeting 04/21\n"},
    )
    # Org create may write its own strategy; ensure path content has heading
    assert create.status_code in (200, 201)

    # Ensure description_path content has the meeting (create may use different text)
    from app.services.organization_notes import write_description

    write_description("beta", "beta/notes/strategy.md", "## Meeting 04/21\n")

    refresh = await client.post("/api/metrics/meetings/refresh")
    assert refresh.status_code == 200
    body = refresh.json()
    assert body["meetings_found"] >= 1
    assert body["files_scanned"] >= 1
    assert "last_evaluated_at" in body

    metrics = await client.get(
        "/api/metrics/meetings/created",
        params={"period": "monthly", "days": 365},
    )
    assert metrics.status_code == 200
    data = metrics.json()
    assert data["total"] >= 1
    assert data["last_evaluated_at"] is not None
