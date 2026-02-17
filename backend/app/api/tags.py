"""Tags API: list of existing tags used across todos and knowledge."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=dict)
async def list_tags(
    include_knowledge: bool = Query(True, description="Include tags from knowledge items"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return distinct tag values from Todo and optionally Knowledge.
    Tags are comma-separated in the DB; they are split, trimmed, and deduplicated.
    """
    tags = await crud.get_distinct_tags(db=db, include_knowledge=include_knowledge)
    return {"tags": tags}
