"""Pydantic models for legacy customer index.md → MyAIAssistant REST payloads."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MeetingImportStep(BaseModel):
    """Aligned with backend MeetingStepSchema / step dicts."""

    what: str = ""
    who: str = ""
    todo_id: Optional[int] = None


class ImportStep(BaseModel):
    """Same shape as backend Step for project past/next."""

    what: str = Field(..., description="Description of the step/action")
    who: str = Field(default="unknown", description="Person responsible")


class ExtractedOrganization(BaseModel):
    """Fields compatible with POST /api/organizations (OrganizationCreate)."""

    name: str = Field(..., min_length=1, max_length=255)
    stakeholders: Optional[str] = Field(None, description="Customer-side contacts")
    team: Optional[str] = Field(None, description="Your-side / partner team (e.g. Confluent SE, AE)")
    description: Optional[str] = None
    related_products: Optional[str] = None
    is_top_active: bool = False


class ExtractedProject(BaseModel):
    """Fields compatible with POST /api/projects (ProjectCreate); organization_id set by migrator."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(
        default="Active",
        description="Draft, Active, On Hold, Completed, Cancelled",
    )
    tasks: Optional[str] = None
    past_steps: Optional[list[ImportStep]] = Field(
        default=None,
        description="Account-level past steps (non-meeting bullets)",
    )
    next_steps: Optional[list[ImportStep]] = Field(
        default=None,
        description="Account-level forward steps (non-meeting bullets)",
    )


class ExtractedMeeting(BaseModel):
    """Payload for POST /api/meeting-refs plus optional PATCH for structured steps."""

    meeting_id: str = Field(..., min_length=1, max_length=255, description="Stable slug, e.g. att-2026-01-13")
    content: str = Field(..., min_length=1, description="Markdown for this meeting only")
    attendees: Optional[str] = Field(None, max_length=2048)
    title_hint: Optional[str] = Field(
        None,
        description="Original heading text for debugging (e.g. Meeting 1/13)",
    )
    past_steps: Optional[list[MeetingImportStep]] = None
    next_steps: Optional[list[MeetingImportStep]] = None


class LegacyCustomerIndexImport(BaseModel):
    """Full extraction result from one legacy index.md."""

    organization: ExtractedOrganization
    project: ExtractedProject
    meetings: list[ExtractedMeeting] = Field(default_factory=list)
    source_hint: Optional[str] = Field(None, description="Folder slug or filename stem")
    confidence_notes: Optional[str] = Field(
        None,
        description="Model notes on ambiguity or missing sections",
    )
