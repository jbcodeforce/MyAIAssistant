from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeListResponse
)


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/", response_model=KnowledgeResponse, status_code=201)
async def create_knowledge(
    knowledge: KnowledgeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new knowledge item.
    """
    return await crud.create_knowledge(db=db, knowledge=knowledge)


@router.get("/", response_model=KnowledgeListResponse)
async def list_knowledge(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    document_type: Optional[str] = Query(None, description="Filter by document type (markdown, website)"),
    status: Optional[str] = Query(None, description="Filter by status (active, pending, error, archived)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of knowledge items with optional filtering.
    """
    items, total = await crud.get_knowledges(
        db=db,
        skip=skip,
        limit=limit,
        document_type=document_type,
        status=status
    )
    return KnowledgeListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific knowledge item by ID.
    """
    knowledge = await crud.get_knowledge(db=db, knowledge_id=knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return knowledge


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: int,
    knowledge_update: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a knowledge item.
    """
    knowledge = await crud.update_knowledge(
        db=db,
        knowledge_id=knowledge_id,
        knowledge_update=knowledge_update
    )
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return knowledge


@router.delete("/{knowledge_id}", status_code=204)
async def delete_knowledge(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a knowledge item.
    """
    success = await crud.delete_knowledge(db=db, knowledge_id=knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return None

