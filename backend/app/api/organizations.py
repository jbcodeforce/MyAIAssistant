import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationExportResponse,
)
from app.api.schemas.todo import TodoListResponse
from app.core.config import get_settings
from app.services.meeting_notes import MeetingNotesService, get_meeting_notes_service

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/organizations", tags=["organizations"])


def _sanitize_org_name(name: str) -> str:
    """Sanitize organization name for use in file paths."""
    sanitized = (name or "").lower().replace(" ", "-")
    sanitized = re.sub(r"[^a-z0-9\-_]", "", sanitized)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized or "unknown"


def _format_steps(steps: Optional[list]) -> str:
    """Format past_steps/next_steps as markdown bullets."""
    if not steps or not isinstance(steps, list):
        return ""
    lines = []
    for s in steps:
        if isinstance(s, dict):
            what = s.get("what") or ""
            who = s.get("who") or ""
            lines.append(f"- {what} ({who})" if who else f"- {what}")
        else:
            lines.append(f"- {s}")
    return "\n".join(lines) if lines else ""


@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    organization: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization.
    """
    return await crud.create_organization(db=db, organization=organization)


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    top_active: Optional[bool] = Query(None, description="Filter by top-active flag"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of organizations with pagination.
    """
    organizations, total = await crud.get_organizations(
        db=db, skip=skip, limit=limit, top_active=top_active
    )
    return OrganizationListResponse(organizations=organizations, total=total, skip=skip, limit=limit)


@router.get("/search/by-name", response_model=OrganizationResponse)
async def get_organization_by_name(
    name: str = Query(..., description="Organization name to search for (case-insensitive)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find an organization by name (case-insensitive exact match).
    """
    organization = await crud.get_organization_by_name(db=db, name=name)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific organization by ID.
    """
    organization = await crud.get_organization(db=db, organization_id=organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    organization_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization.
    """
    organization = await crud.update_organization(
        db=db, organization_id=organization_id, organization_update=organization_update
    )
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.delete("/{organization_id}", status_code=204)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an organization.
    """
    success = await crud.delete_organization(db=db, organization_id=organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    return None


@router.post("/{organization_id}/export", response_model=OrganizationExportResponse)
async def export_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_meeting_notes_service),
):
    """
    Export organization content, its projects, and meeting notes to a single
    markdown file under the workspace docs folder: docs/<org_name>/index.md.
    """
    organization = await crud.get_organization(db=db, organization_id=organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    projects, _ = await crud.get_projects(
        db=db, organization_id=organization_id, skip=0, limit=500
    )
    meeting_refs, _ = await crud.get_meeting_refs(
        db=db, org_id=organization_id, skip=0, limit=500
    )

    sections = []

    # Organization header and sections
    sections.append(f"# {organization.name}\n")
    if organization.stakeholders:
        sections.append(f"## Stakeholders\n\n{organization.stakeholders.strip()}\n")
    if organization.team:
        sections.append(f"## Team\n\n{organization.team.strip()}\n")
    if organization.description:
        sections.append(f"## Strategy / Notes\n\n{organization.description.strip()}\n")
    if organization.related_products:
        sections.append(f"## Related Products\n\n{organization.related_products.strip()}\n")

    # Projects section
    sections.append("## Projects\n")
    for proj in projects:
        block = [f"### {proj.name}\n"]
        if proj.description:
            block.append(proj.description.strip() + "\n")
        block.append(f"**Status:** {proj.status}\n")
        if proj.tasks:
            block.append(f"**Tasks:**\n\n{proj.tasks.strip()}\n")
        past = _format_steps(proj.past_steps)
        if past:
            block.append(f"**Past steps:**\n\n{past}\n")
        next_s = _format_steps(proj.next_steps)
        if next_s:
            block.append(f"**Next steps:**\n\n{next_s}\n")
        sections.append("\n".join(block))

    # Meeting notes section
    sections.append("\n## Meeting notes\n")
    for meeting in meeting_refs:
        block = [f"### {meeting.meeting_id}\n"]
        if meeting.attendees:
            block.append(f"**Attendees:** {meeting.attendees}\n\n")
        try:
            content = await notes_service.read_note(meeting.file_ref)
            block.append(content.strip())
        except FileNotFoundError:
            logger.warning("Meeting note file not found: %s", meeting.file_ref)
            block.append("*(file not found)*")
        block.append("\n")
        sections.append("\n".join(block))

    markdown_content = "\n".join(sections)

    settings = get_settings()
    notes_root = Path(settings.notes_root)
    if not notes_root.is_absolute():
        notes_root = Path.cwd() / notes_root
    export_base = notes_root.resolve().parent
    sanitized = _sanitize_org_name(organization.name)
    export_dir = export_base / sanitized
    export_dir.mkdir(parents=True, exist_ok=True)
    export_file = export_dir / "index.md"
    export_file.write_text(markdown_content, encoding="utf-8")
    logger.info("Exported organization %s to %s", organization.name, export_file)

    try:
        relative_path = str(export_file.relative_to(Path.cwd()))
    except ValueError:
        relative_path = f"docs/{sanitized}/index.md"

    return OrganizationExportResponse(
        path=relative_path,
        absolute_path=str(export_file.resolve()),
    )


@router.get("/{organization_id}/todos", response_model=TodoListResponse)
async def list_organization_todos(
    organization_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all todos linked to projects belonging to this organization.
    """
    # Verify organization exists
    organization = await crud.get_organization(db=db, organization_id=organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    todos, total = await crud.get_todos_by_organization(
        db=db, organization_id=organization_id, skip=skip, limit=limit
    )
    return TodoListResponse(todos=todos, total=total, skip=skip, limit=limit)

