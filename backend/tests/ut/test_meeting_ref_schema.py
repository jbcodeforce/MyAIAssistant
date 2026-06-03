"""Validation rules for meeting reference API schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.meeting_ref import MeetingRefCreate


def test_meeting_ref_create_requires_org_or_project() -> None:
    with pytest.raises(ValidationError) as exc_info:
        MeetingRefCreate(
            meeting_id="mtg-test",
            content="# Notes",
        )
    msg = str(exc_info.value)
    assert "at least one" in msg.lower()


def test_meeting_ref_create_accepts_org_only() -> None:
    m = MeetingRefCreate(meeting_id="mtg-test", org_id=1, content="# Notes")
    assert m.org_id == 1
    assert m.project_id is None


def test_meeting_ref_create_accepts_project_only() -> None:
    m = MeetingRefCreate(meeting_id="mtg-test", project_id=2, content="# Notes")
    assert m.project_id == 2
    assert m.org_id is None


def test_meeting_ref_create_accepts_past_and_next_steps() -> None:
    m = MeetingRefCreate(
        meeting_id="mtg-test",
        org_id=1,
        content="# Notes",
        past_steps=[{"what": "Reviewed scope", "who": "Alice"}],
        next_steps=[{"what": "Send proposal", "who": "Bob", "todo_id": 5}],
    )
    assert len(m.past_steps) == 1
    assert m.past_steps[0].what == "Reviewed scope"
    assert len(m.next_steps) == 1
    assert m.next_steps[0].todo_id == 5
