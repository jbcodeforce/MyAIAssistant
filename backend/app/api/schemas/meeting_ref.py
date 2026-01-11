from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class MeetingRefBase(BaseModel):
    """Base fields for meeting reference (stored in database)."""
    meeting_id: str = Field(..., min_length=1, max_length=255, description="Unique meeting identifier")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    file_ref: str = Field(..., min_length=1, max_length=2048, description="File path where meeting note is saved")
    presents: Optional[str] = Field(None, max_length=2048, description="Comma or semicolon separated list of attendees")


class MeetingRefCreate(BaseModel):
    """Schema for creating a meeting reference. Content is saved to file system."""
    meeting_id: str = Field(..., min_length=1, max_length=255, description="Unique meeting identifier")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    presents: Optional[str] = Field(None, max_length=2048, description="Comma or semicolon separated list of attendees")
    content: str = Field(..., min_length=1, max_length=1000000, description="Meeting note content in markdown")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "meeting_id": "mtg-2026-01-05-acme-kickoff",
                    "project_id": 1,
                    "org_id": 2,
                    "presents": "John Doe, Jane Smith",
                    "content": "# Meeting: Acme Kickoff\n\n## Attendees\n- John Doe\n- Jane Smith\n\n## Notes\n..."
                }
            ]
        }
    )


class MeetingRefUpdate(BaseModel):
    """Schema for updating a meeting reference. Content update will overwrite the file."""
    project_id: Optional[int] = None
    org_id: Optional[int] = None
    presents: Optional[str] = Field(None, max_length=2048, description="Comma or semicolon separated list of attendees")
    content: Optional[str] = Field(None, min_length=1, max_length=1000000, description="Updated content (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "presents": "John Doe, Jane Smith, Bob Wilson",
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


class PersonResponse(BaseModel):
    """A person extracted from meeting notes."""
    name: str
    last_met_date: Optional[str] = None


class NextStepResponse(BaseModel):
    """An actionable next step from the meeting."""
    what: str
    who: str = "to_be_decided"


class KeyPointResponse(BaseModel):
    """A key discussion point from the meeting."""
    point: str


class MeetingAgentOutputResponse(BaseModel):
    """Structured output from meeting agent extraction."""
    persons: list[PersonResponse] = Field(default_factory=list)
    next_steps: list[NextStepResponse] = Field(default_factory=list)
    key_points: list[KeyPointResponse] = Field(default_factory=list)


class MeetingAgentResponse(BaseModel):
    """Response from the meeting agent endpoint."""
    meeting_ref_id: int
    meeting_id: str
    meeting_output: Optional[MeetingAgentOutputResponse] = None
    raw_response: str = Field(..., description="Raw LLM response")
    parse_error: Optional[str] = Field(None, description="Error message if parsing failed")
    model: str = Field(..., description="Model used for extraction")
    provider: str = Field(..., description="LLM provider used")

