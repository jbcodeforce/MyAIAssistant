from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class MeetingRefBase(BaseModel):
    """Base fields for meeting reference (stored in database)."""
    meeting_id: str = Field(..., min_length=1, max_length=255, description="Unique meeting identifier")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    file_ref: str = Field(..., min_length=1, max_length=2048, description="File path where meeting note is saved")


class MeetingRefCreate(BaseModel):
    """Schema for creating a meeting reference. Content is saved to file system."""
    meeting_id: str = Field(..., min_length=1, max_length=255, description="Unique meeting identifier")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    content: str = Field(..., min_length=1, max_length=1000000, description="Meeting note content in markdown")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "meeting_id": "mtg-2026-01-05-acme-kickoff",
                    "project_id": 1,
                    "org_id": 2,
                    "content": "# Meeting: Acme Kickoff\n\n## Attendees\n- John Doe\n- Jane Smith\n\n## Notes\n..."
                }
            ]
        }
    )


class MeetingRefUpdate(BaseModel):
    """Schema for updating a meeting reference. Content update will overwrite the file."""
    project_id: Optional[int] = None
    org_id: Optional[int] = None
    content: Optional[str] = Field(None, min_length=1, max_length=1000000, description="Updated content (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "# Updated Meeting Notes\n\n## Summary\n..."
                }
            ]
        }
    )


class MeetingRefResponse(MeetingRefBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MeetingRefListResponse(BaseModel):
    meeting_refs: list[MeetingRefResponse]
    total: int
    skip: int
    limit: int

