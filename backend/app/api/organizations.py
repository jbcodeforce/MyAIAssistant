import logging
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
from app.core.utils import sanitize_org_name
from app.services.meeting_notes import MeetingNotesService, get_meeting_notes_service
from app.services.organization_notes import (
    default_description_path,
    read_description_file,
    write_description,
    move_org_notes_tree_if_renamed,
    rebase_description_path,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/organizations", tags=["organizations"])


def _organization_to_response(org) -> OrganizationResponse:
    """`description` in JSON is always file content; `description_path` is stored in the database."""
    text = read_description_file(org.name, org.description_path)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        stakeholders=org.stakeholders,
        team=org.team,
        description=text if text else None,
        description_path=org.description_path,
        related_products=org.related_products,
        is_top_active=bool(org.is_top_active),
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


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
    Create a new organization. Optional `description` in the body is written to the file
    at description_path (default: {org}/notes/strategy.md under notes_root); the DB stores only the path.
    """
    created = await crud.create_organization(db=db, organization=organization)
    return _organization_to_response(created)


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
    return OrganizationListResponse(
        organizations=[_organization_to_response(o) for o in organizations],
        total=total,
        skip=skip,
        limit=limit,
    )


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
    return _organization_to_response(organization)


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
    return _organization_to_response(organization)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    organization_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization. When `description` is in the request body, it is written to the
    file at `description_path` (default path if unset). The database stores only the path, not
    the markdown text. Renaming the organization renames the on-disk org folder when needed.
    """
    existing = await crud.get_organization(db=db, organization_id=organization_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Organization not found")

    old_name = existing.name
    update_keys = set(organization_update.model_dump(exclude_unset=True).keys())
    update_payload = organization_update.model_dump(exclude_unset=True)
    content_update = (
        update_payload["description"] if "description" in update_keys else None
    )

    organization = await crud.update_organization(
        db=db, organization_id=organization_id, organization_update=organization_update
    )
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if old_name != organization.name:
        move_org_notes_tree_if_renamed(old_name, organization.name)
        new_path = rebase_description_path(
            organization.description_path, old_name, organization.name
        )
        if new_path != organization.description_path:
            organization.description_path = new_path
            await db.commit()
            await db.refresh(organization)

    if "description" in update_keys:
        path_ref = organization.description_path or default_description_path(organization.name)
        write_description(organization.name, path_ref, content_update or "")
        if not organization.description_path:
            organization.description_path = path_ref
            await db.commit()
            await db.refresh(organization)

    return _organization_to_response(organization)


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
    markdown file under docs/notes/<org-slug>/full_export.md (does not overwrite strategy.md).
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
    strategy_text = read_description_file(organization.name, organization.description_path).strip()
    if strategy_text:
        sections.append(f"## Strategy / Notes\n\n{strategy_text}\n")
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
    sanitized = sanitize_org_name(organization.name)
    export_dir = export_base / "notes" / sanitized
    export_dir.mkdir(parents=True, exist_ok=True)
    export_file = export_dir / "full_export.md"
    export_file.write_text(markdown_content, encoding="utf-8")
    logger.info("Exported organization %s to %s", organization.name, export_file)

    try:
        relative_path = str(export_file.relative_to(Path.cwd()))
    except ValueError:
        relative_path = f"docs/notes/{sanitized}/full_export.md"

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

