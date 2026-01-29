import logging
import json
from typing import Optional
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
    PersonResponse,
    NextStepResponse,
    KeyPointResponse,
)
from app.services.meeting_notes import MeetingNotesService, get_meeting_notes_service
from app.api.schemas.project import ProjectEntity, Step
from app.core.config import get_settings, resolve_agent_config_dir
from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.base_agent import AgentInput
from agent_core.agents.meeting_agent import MeetingAgentResponse

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/meeting-refs", tags=["meeting-refs"])


def get_notes_service() -> MeetingNotesService:
    """Dependency for meeting notes service."""
    return get_meeting_notes_service()


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
    
    # Update database record (project_id, org_id, and attendees)
    update_data = meeting_ref_update.model_dump(exclude_unset=True, exclude={"content"})
    
    meeting_ref = await crud.update_meeting_ref(
        db=db,
        meeting_ref_id=meeting_ref_id,
        project_id=update_data.get("project_id"),
        org_id=update_data.get("org_id"),
        attendees=update_data.get("attendees"),
        update_project_id="project_id" in update_data,
        update_org_id="org_id" in update_data,
        update_attendees="attendees" in update_data,
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
    Extract structured information from a meeting note using the MeetingAgent.
    
    Uses AI to extract:
    - Persons present at the meeting
    - Key discussion points
    - Actionable next steps with assignees
    """
    # Load meeting metadata from database
    meeting_ref = await crud.get_meeting_ref(db=db, meeting_ref_id=meeting_ref_id)
    if not meeting_ref:
        raise HTTPException(status_code=404, detail="Meeting reference not found")
    
    # Read meeting content from file system
    try:
        content = await notes_service.read_note(meeting_ref.file_ref)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting note file not found")
    
    org_description = ""
    if meeting_ref.org_id:
        org = await crud.get_organization(db=db, organization_id=meeting_ref.org_id)
        if org:
            org_description = org.description
    project_description = ""
    if meeting_ref.project_id:
        project = await crud.get_project(db=db, project_id=meeting_ref.project_id)
        if project:
            project_description = project.description

    # Get agent config directory from settings
    settings = get_settings()
    config_dir = resolve_agent_config_dir(settings.agent_config_dir)
    
    # Create MeetingAgent using AgentFactory with settings overrides
    factory = AgentFactory(config_dir=config_dir)
    agent = factory.create_agent(
        "MeetingAgent"
    )
    
    # Build context with meeting metadata
    context = {
        "organization": org_description,
        "project": project_description,
        "attendees": meeting_ref.attendees
    }
    
    # Execute the agent
    try:
        input = AgentInput(query=content, context=context)
        agent_response: MeetingAgentResponse = await agent.execute(input_data=input)
    except Exception as e:
        logger.error(f"MeetingAgent execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    logger.info(f"Agent response: {json.dumps(agent_response.__dict__, indent=2, default=str)}")
    if agent_response.key_points is not None:
        agent_response.cleaned_notes += "\n## Key Points\n"
        agent_response.cleaned_notes += "\n".join([f"- {kp.point}" for kp in agent_response.key_points])
        agent_response.cleaned_notes += "\n"

    if agent_response.next_steps is not None:
        agent_response.cleaned_notes += "\n## Next Steps\n"
        agent_response.cleaned_notes += "\n".join([f"- {ns.what} (assigned to {ns.who})" for ns in agent_response.next_steps])
        agent_response.cleaned_notes += "\n"
        # Convert NextStep objects from agent to Step objects for ProjectEntity
        steps = [Step(what=ns.what, who=ns.who) for ns in agent_response.next_steps]
        await crud.update_project(
            db=db,
            project_id=meeting_ref.project_id,
            project_update=ProjectEntity(next_steps=steps)
        )

    await notes_service.update_note(
            file_ref=meeting_ref.file_ref,
            content="# Notes updated by AI: " + agent_response.cleaned_notes + "\n---\n" + "# Original: " + content
        )
    
    # Convert list of Person objects to comma-separated string for database storage
    attendees_str = ""
    if agent_response.attendees is not None:
        for person in agent_response.attendees:
            logger.info(f"Creating person: {person.name}")
            await crud.create_person(
                db=db,
                name=person.name,
                last_met_date=person.last_met_date if person.last_met_date else datetime.now().isoformat()
            )
            attendees_str += f"{person.name}, "
    await crud.update_meeting_ref(
        db=db,
        meeting_ref_id=meeting_ref_id,
        project_id=meeting_ref.project_id,
        org_id=meeting_ref.org_id,
        attendees=attendees_str,
        update_attendees=agent_response.attendees is not None,
    )
    # Convert agent output to API response
  
    return MeetingAgentOutputResponse(
        meeting_ref_id=meeting_ref_id,
        meeting_id=meeting_ref.meeting_id,
        attendees=attendees_str,
        next_steps=[
            NextStepResponse(what=ns.what, who=ns.who)
            for ns in agent_response.next_steps
        ],
        key_points=[
            KeyPointResponse(point=kp.point)
            for kp in agent_response.key_points
        ],
        notes=agent_response.cleaned_notes,
    )
    
