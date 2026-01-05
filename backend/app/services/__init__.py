"""Application services."""

from app.services.meeting_notes import (
    MeetingNotesService,
    get_meeting_notes_service,
)

__all__ = [
    "MeetingNotesService",
    "get_meeting_notes_service",
]

