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
