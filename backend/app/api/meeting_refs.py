from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.meeting_ref import (
    MeetingRefCreate,
    MeetingRefUpdate,
    MeetingRefResponse,
    MeetingRefListResponse,
)
from app.services.meeting_notes import MeetingNotesService, get_meeting_notes_service


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
    
    # Update database record (project_id and org_id only)
    update_data = meeting_ref_update.model_dump(exclude_unset=True, exclude={"content"})
    
    meeting_ref = await crud.update_meeting_ref(
        db=db,
        meeting_ref_id=meeting_ref_id,
        project_id=update_data.get("project_id"),
        org_id=update_data.get("org_id"),
        update_project_id="project_id" in update_data,
        update_org_id="org_id" in update_data,
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
