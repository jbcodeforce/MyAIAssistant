"""Pydantic models for customer note extraction (aligned with legacy NoteParserAgent shape)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrganizationExtract(BaseModel):
    """Extracted organization from customer note."""

    name: str
    description: str | None = None


class PersonExtract(BaseModel):
    """Extracted person from customer note."""

    name: str
    role: str | None = None
    context: str | None = None


class StepExtract(BaseModel):
    """A step with action and assignee."""

    what: str
    who: str = "to_be_decided"


class ProjectExtract(BaseModel):
    """Extracted project from customer note."""

    name: str | None = None
    description: str | None = None
    past_steps: list[StepExtract] = Field(default_factory=list)
    next_steps: list[StepExtract] = Field(default_factory=list)


class MeetingExtract(BaseModel):
    """Extracted meeting section from customer note."""

    title: str
    content: str


class NoteParserExtraction(BaseModel):
    """Root structure for LLM extraction output."""

    organization: OrganizationExtract | None = None
    persons: list[PersonExtract] = Field(default_factory=list)
    project: ProjectExtract | None = None
    meetings: list[MeetingExtract] = Field(default_factory=list)


class NoteParseResult(BaseModel):
    """Result returned to `note parse` command (no agent_core dependency)."""

    organization: OrganizationExtract | None = None
    persons: list[PersonExtract] = Field(default_factory=list)
    project: ProjectExtract | None = None
    meetings: list[MeetingExtract] = Field(default_factory=list)
    parse_error: str | None = None
