import logging
import json
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.database import get_db
from app.db import crud
from app.api.schemas.meeting_ref import (
    MeetingRefCreate,
    MeetingRefUpdate,
    MeetingRefResponse,
    MeetingRefListResponse,
    MeetingAgentOutputResponse,
    MeetingStepSchema,
    NextStepResponse,
    KeyPointResponse,
)
from app.services.meeting_notes import MeetingNotesService, get_meeting_notes_service
from app.api.schemas.project import ProjectEntity, Step
from app.core.config import get_settings, resolve_agent_config_dir
from app.services import agent_service_client
from app.services.organization_notes import read_description_file

logger = logging.getLogger(__name__)

try:
    from agent_core.agents.agent_factory import AgentFactory
    from agent_core.agents.base_agent import AgentInput
    from agent_core.agents.meeting_agent import MeetingAgentResponse
except ImportError:
    AgentFactory = None
    AgentInput = None
    MeetingAgentResponse = None


router = APIRouter(prefix="/meeting-refs", tags=["meeting-refs"])


def get_notes_service() -> MeetingNotesService:
    """Dependency for meeting notes service."""
    return get_meeting_notes_service()


def _steps_to_db_payload(raw: Optional[list]) -> Optional[list]:
    """Normalize validated steps to JSON-storable dicts; empty list becomes None."""
    if raw is None:
        return None
    out = []
    for item in raw:
        step = MeetingStepSchema.model_validate(item)
        out.append(step.model_dump(mode="python", exclude_none=True))
    return out if out else None


@router.post("/", response_model=MeetingRefResponse, status_code=201)
async def create_meeting_ref(
    meeting_ref: MeetingRefCreate,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_notes_service),
):
    """
    Create a new meeting reference.
    
    The content is saved to the file system, and the file reference
    is stored in the database.
    """
    # Check if meeting_id already exists
    existing = await crud.get_meeting_ref_by_meeting_id(db=db, meeting_id=meeting_ref.meeting_id)
    if existing:
        raise HTTPException(status_code=409, detail="Meeting reference with this meeting_id already exists")
    
    # Get organization and project names for folder structure
    org_name = None
    project_name = None
    
    if meeting_ref.org_id:
        org = await crud.get_organization(db=db, organization_id=meeting_ref.org_id)
        if org:
            org_name = org.name
        else:
            raise HTTPException(status_code=404, detail=f"Organization with id {meeting_ref.org_id} not found")
    
    if meeting_ref.project_id:
        project = await crud.get_project(db=db, project_id=meeting_ref.project_id)
        if project:
            project_name = project.name
        else:
            raise HTTPException(status_code=404, detail=f"Project with id {meeting_ref.project_id} not found")
    
    # Save the content to file system
    save_result = await notes_service.save_note(
        meeting_id=meeting_ref.meeting_id,
        content=meeting_ref.content,
        org_name=org_name,
        project_name=project_name,
    )
    
    # Create the database record with the file reference
    db_meeting_ref = await crud.create_meeting_ref(
        db=db,
        meeting_id=meeting_ref.meeting_id,
        file_ref=save_result.file_ref,
        project_id=meeting_ref.project_id,
        org_id=meeting_ref.org_id,
        attendees=meeting_ref.attendees,
    )
    
    return db_meeting_ref


@router.get("/", response_model=MeetingRefListResponse)
async def list_meeting_refs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    org_id: Optional[int] = Query(None, description="Filter by organization ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a list of meeting references with pagination and optional filters.
    """
    meeting_refs, total = await crud.get_meeting_refs(
        db=db, skip=skip, limit=limit, project_id=project_id, org_id=org_id
    )
    return MeetingRefListResponse(meeting_refs=meeting_refs, total=total, skip=skip, limit=limit)


@router.get("/search/by-meeting-id", response_model=MeetingRefResponse)
async def get_meeting_ref_by_meeting_id(
    meeting_id: str = Query(..., description="Meeting ID to search for"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find a meeting reference by meeting_id.
    """
    meeting_ref = await crud.get_meeting_ref_by_meeting_id(db=db, meeting_id=meeting_id)
    if not meeting_ref:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    return meeting_ref


@router.get("/{meeting_ref_id}", response_model=MeetingRefResponse)
async def get_meeting_ref(
    meeting_ref_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific meeting reference by ID.
    """
    meeting_ref = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not meeting_ref:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    return meeting_ref


@router.get("/{meeting_ref_id}/content")
async def get_meeting_ref_content(
    meeting_ref_id: int,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_notes_service),
):
    """
    Retrieve the content of a meeting note from the file system.
    """
    meeting_ref = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not meeting_ref:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    
    try:
        content = await notes_service.read_note(meeting_ref.file_ref)
        return {"content": content, "file_ref": meeting_ref.file_ref}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting note file not found")


@router.put("/{meeting_ref_id}", response_model=MeetingRefResponse)
async def update_meeting_ref(
    meeting_ref_id: int,
    meeting_ref_update: MeetingRefUpdate,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_notes_service),
):
    """
    Update a meeting reference. If content is provided, the file is updated.
    """
    # Get existing meeting ref
    existing = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    
    # Update file content if provided
    if meeting_ref_update.content is not None:
        try:
            await notes_service.update_note(
                file_ref=existing.file_ref,
                content=meeting_ref_update.content,
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Meeting note file not found")
    
    # Update database record (project_id, org_id, attendees, steps)
    update_data = meeting_ref_update.model_dump(exclude_unset=True, exclude={"content"})
    
    meeting_ref = await crud.update_meeting_ref(
        db=db,
        meeting_ref_id=meeting_ref_id,
        project_id=update_data.get("project_id"),
        org_id=update_data.get("org_id"),
        attendees=update_data.get("attendees"),
        past_steps=_steps_to_db_payload(update_data.get("past_steps"))
        if "past_steps" in update_data
        else None,
        next_steps=_steps_to_db_payload(update_data.get("next_steps"))
        if "next_steps" in update_data
        else None,
        update_project_id="project_id" in update_data,
        update_org_id="org_id" in update_data,
        update_attendees="attendees" in update_data,
        update_past_steps="past_steps" in update_data,
        update_next_steps="next_steps" in update_data,
    )
    
    return meeting_ref


@router.delete("/{meeting_ref_id}", status_code=204)
async def delete_meeting_ref(
    meeting_ref_id: int,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_notes_service),
):
    """
    Delete a meeting reference and its associated file.
    """
    # Get existing meeting ref to get file_ref
    existing = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    
    # Delete the file (ignore if not found)
    await notes_service.delete_note(existing.file_ref)
    
    # Delete the database record
    success = await crud.delete_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    
    return None


@router.post("/{meeting_ref_id}/extract", response_model=MeetingAgentOutputResponse)
async def extract_meeting_info(
    meeting_ref_id: int,
    db: AsyncSession = Depends(get_db),
    notes_service: MeetingNotesService = Depends(get_notes_service),
):
    """
    Extract structured information from a meeting note. When AGENT_SERVICE_URL is set, uses agent-service.
    """
    meeting_ref = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not meeting_ref:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    try:
        content = await notes_service.read_note(meeting_ref.file_ref)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting note file not found")

    org_description = ""
    if meeting_ref.org_id:
        org = await crud.get_organization(db=db, organization_id=meeting_ref.org_id)
        if org:
            org_description = read_description_file(org.name, org.description_path) or ""
    project_description = ""
    if meeting_ref.project_id:
        project = await crud.get_project(db=db, project_id=meeting_ref.project_id)
        if project:
            project_description = project.description or ""

    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.extract_meeting(
                content=content,
                organization=org_description or None,
                project=project_description or None,
                attendees=meeting_ref.attendees,
            )
        except httpx.HTTPStatusError as e:
            logger.error("Agent service extract failed: %s", e.response.text)
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        next_steps = data.get("next_steps") or []
        key_points = data.get("key_points") or []
        attendees_list = data.get("attendees") or []
        cleaned_notes = data.get("cleaned_notes", "")
        attendees_str = ""
        for person in attendees_list:
            name = person.get("name", str(person)) if isinstance(person, dict) else str(person)
            last_met = person.get("last_met_date") if isinstance(person, dict) else None
            logger.info("Creating person: %s", name)
            await crud.create_person(
                db=db,
                name=name,
                last_met_date=last_met or datetime.now().isoformat(),
            )
            attendees_str += f"{name}, "
        if next_steps and meeting_ref.project_id:
            steps = [
                Step(what=ns.get("what", ""), who=ns.get("who", "to_be_decided"))
                for ns in next_steps
            ]
            await crud.update_project(
                db=db,
                project_id=meeting_ref.project_id,
                project_update=ProjectEntity(next_steps=steps),
            )
        notes_with_sections = cleaned_notes
        if key_points:
            notes_with_sections += "\n## Key Points\n" + "\n".join([f"- {kp.get('point', '')}" for kp in key_points]) + "\n"
        if next_steps:
            notes_with_sections += "\n## Next Steps\n" + "\n".join([f"- {ns.get('what', '')} (assigned to {ns.get('who', 'to_be_decided')})" for ns in next_steps]) + "\n"
        await notes_service.update_note(
            file_ref=meeting_ref.file_ref,
            content="# Notes updated by AI: " + notes_with_sections + "\n---\n" + "# Original: " + content,
        )
        await crud.update_meeting_ref(
            db=db,
            meeting_ref_id=meeting_ref_id,
            project_id=meeting_ref.project_id,
            org_id=meeting_ref.org_id,
            attendees=attendees_str,
            update_attendees=bool(attendees_list),
        )
        return MeetingAgentOutputResponse(
            meeting_ref_id=meeting_ref_id,
            meeting_id=meeting_ref.meeting_id,
            attendees=attendees_str,
            next_steps=[NextStepResponse(what=ns.get("what", ""), who=ns.get("who", "to_be_decided")) for ns in next_steps],
            key_points=[KeyPointResponse(point=kp.get("point", "")) for kp in key_points],
            notes=cleaned_notes,
        )

    settings = get_settings()
    config_dir = resolve_agent_config_dir(settings.agent_config_dir)
    factory = AgentFactory(config_dir=config_dir)
    agent = factory.create_agent("MeetingAgent")
    context = {"organization": org_description, "project": project_description, "attendees": meeting_ref.attendees}
    try:
        input_data = AgentInput(query=content, context=context)
        agent_response = await agent.execute(input_data=input_data)
    except Exception as e:
        logger.error("MeetingAgent execution failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    logger.info("Agent response: %s", json.dumps(agent_response.__dict__, indent=2, default=str))
    if agent_response.key_points:
        agent_response.cleaned_notes += "\n## Key Points\n" + "\n".join(f"- {kp.point}" for kp in agent_response.key_points) + "\n"
    if agent_response.next_steps:
        agent_response.cleaned_notes += "\n## Next Steps\n" + "\n".join(f"- {ns.what} (assigned to {ns.who})" for ns in agent_response.next_steps) + "\n"
        steps = [Step(what=ns.what, who=ns.who) for ns in agent_response.next_steps]
        await crud.update_project(db=db, project_id=meeting_ref.project_id, project_update=ProjectEntity(next_steps=steps))
    await notes_service.update_note(
        file_ref=meeting_ref.file_ref,
        content="# Notes updated by AI: " + agent_response.cleaned_notes + "\n---\n" + "# Original: " + content,
    )
    attendees_str = ""
    if agent_response.attendees:
        for person in agent_response.attendees:
            logger.info("Creating person: %s", person.name)
            await crud.create_person(
                db=db,
                name=person.name,
                last_met_date=person.last_met_date or datetime.now().isoformat(),
            )
            attendees_str += f"{person.name}, "
    await crud.update_meeting_ref(
        db=db,
        meeting_ref_id=meeting_ref_id,
        project_id=meeting_ref.project_id,
        org_id=meeting_ref.org_id,
        attendees=attendees_str,
        update_attendees=bool(agent_response.attendees),
    )
    return MeetingAgentOutputResponse(
        meeting_ref_id=meeting_ref_id,
        meeting_id=meeting_ref.meeting_id,
        attendees=attendees_str,
        next_steps=[NextStepResponse(what=ns.what, who=ns.who) for ns in agent_response.next_steps],
        key_points=[KeyPointResponse(point=kp.point) for kp in agent_response.key_points],
        notes=agent_response.cleaned_notes,
    )
    
