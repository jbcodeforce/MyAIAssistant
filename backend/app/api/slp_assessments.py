from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.slp_assessment import (
    SLPassessmentCreate,
    SLPassessmentEntity,
    SLPassessmentResponse,
    SLPassessmentListResponse,
)

"""
The API endpoints for the Strategic Life Portfolio assessment.
"""

router = APIRouter(prefix="/slp-assessments", tags=["slp-assessments"])


@router.post("/", response_model=SLPassessmentResponse, status_code=201)
async def create_slp_assessment(
    assessment: SLPassessmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Strategic Life Plan assessment.
    
    All 16 life dimensions are required with their importance and time_spent ratings (0-10).
    """
    return await crud.create_slp_assessment(db=db, assessment=assessment)


@router.get("/", response_model=SLPassessmentListResponse)
async def list_slp_assessments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of SLP assessments with pagination.
    
    Returns assessments sorted by creation date (most recent first).
    """
    assessments, total = await crud.get_slp_assessments(
        db=db,
        skip=skip,
        limit=limit
    )
    return SLPassessmentListResponse(
        assessments=assessments, total=total, skip=skip, limit=limit
    )


@router.get("/{assessment_id}", response_model=SLPassessmentResponse)
async def get_slp_assessment(
    assessment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific SLP assessment by ID.
    """
    assessment = await crud.get_slp_assessment(db=db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="SLP assessment not found")
    return assessment


@router.put("/{assessment_id}", response_model=SLPassessmentResponse)
async def update_slp_assessment(
    assessment_id: int,
    assessment_update: SLPassessmentEntity,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an SLP assessment.
    
    Only provided dimensions will be updated; others remain unchanged.
    """
    assessment = await crud.update_slp_assessment(
        db=db, assessment_id=assessment_id, assessment_update=assessment_update
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="SLP assessment not found")
    return assessment


@router.delete("/{assessment_id}", status_code=204)
async def delete_slp_assessment(
    assessment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an SLP assessment.
    """
    success = await crud.delete_slp_assessment(db=db, assessment_id=assessment_id)
    if not success:
        raise HTTPException(status_code=404, detail="SLP assessment not found")
    return None

