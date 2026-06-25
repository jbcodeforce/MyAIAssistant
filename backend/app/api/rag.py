"""RAG API endpoints: load document content and proxy indexing to agent-service."""

from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.crud.knowledge import get_knowledge, get_knowledges, update_knowledge
from app.api.schemas import IndexKnowledgeResponse, IndexAllResponse
from app.api.schemas.knowledge import KnowledgeUpdate
from app.services import agent_service_client
from app.services.document_loader import DocumentLoader

router = APIRouter(prefix="/rag", tags=["rag"])


async def _load_content_for_proxy(uri: str, document_type: str) -> str:
    """Load document content when proxying index to agent-service."""
    loader = DocumentLoader()
    recursive = document_type == "folder"
    try:
        loaded_docs = await loader.load(uri, document_type, recursive=recursive)
    except FileNotFoundError:
        return ""
    if not loaded_docs:
        return ""
    return "\n\n".join(doc.content for doc in loaded_docs)


async def _index_one(db: AsyncSession, knowledge_id: int) -> IndexKnowledgeResponse:
    agent_service_client.require_agent_service_url()
    knowledge = await get_knowledge(db, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    content = await _load_content_for_proxy(knowledge.uri, knowledge.document_type)
    if not content.strip():
        await update_knowledge(db, knowledge_id, KnowledgeUpdate(status="error"))
        return IndexKnowledgeResponse(
            success=False,
            knowledge_id=knowledge_id,
            chunks_indexed=0,
            content_hash=None,
            error="No documents loaded",
        )
    try:
        result = await agent_service_client.rag_index(
            knowledge_id=knowledge.id,
            title=knowledge.title,
            uri=knowledge.uri,
            document_type=knowledge.document_type,
            content=content,
            category=knowledge.category,
            tags=knowledge.tags,
        )
    except httpx.HTTPStatusError as e:
        await update_knowledge(db, knowledge_id, KnowledgeUpdate(status="error"))
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    if result.get("success"):
        now = datetime.now(timezone.utc)
        await update_knowledge(
            db,
            knowledge_id,
            KnowledgeUpdate(
                content_hash=result.get("content_hash"),
                last_fetched_at=now,
                indexed_at=now,
                status="active",
            ),
        )
    else:
        await update_knowledge(db, knowledge_id, KnowledgeUpdate(status="error"))

    return IndexKnowledgeResponse(
        success=result.get("success", False),
        knowledge_id=knowledge_id,
        chunks_indexed=result.get("chunks_indexed", 0),
        content_hash=result.get("content_hash"),
        error=result.get("error"),
    )


@router.post("/index/{knowledge_id}", response_model=IndexKnowledgeResponse)
async def index_knowledge_item(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Index a knowledge item via agent-service (loads content from URI, then proxies)."""
    return await _index_one(db, knowledge_id)


@router.post("/index-all", response_model=IndexAllResponse)
async def index_all_knowledge(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'active')"),
    db: AsyncSession = Depends(get_db),
):
    """Index all knowledge items via agent-service."""
    agent_service_client.require_agent_service_url()
    items, _ = await get_knowledges(db, limit=1000, status=status)
    results = []
    successful = 0
    failed = 0

    for item in items:
        content = await _load_content_for_proxy(item.uri, item.document_type)
        if not content.strip():
            results.append(
                IndexKnowledgeResponse(
                    success=False,
                    knowledge_id=item.id,
                    chunks_indexed=0,
                    content_hash=None,
                    error="No documents loaded",
                )
            )
            failed += 1
            await update_knowledge(db, item.id, KnowledgeUpdate(status="error"))
            continue
        try:
            result = await agent_service_client.rag_index(
                knowledge_id=item.id,
                title=item.title,
                uri=item.uri,
                document_type=item.document_type,
                content=content,
                category=item.category,
                tags=item.tags,
            )
        except Exception:
            result = {"success": False, "error": "Agent service error"}
        r = IndexKnowledgeResponse(
            success=result.get("success", False),
            knowledge_id=item.id,
            chunks_indexed=result.get("chunks_indexed", 0),
            content_hash=result.get("content_hash"),
            error=result.get("error"),
        )
        results.append(r)
        if r.success:
            successful += 1
            now = datetime.now(timezone.utc)
            await update_knowledge(
                db,
                item.id,
                KnowledgeUpdate(
                    content_hash=result.get("content_hash"),
                    last_fetched_at=now,
                    indexed_at=now,
                    status="active",
                ),
            )
        else:
            failed += 1
            await update_knowledge(db, item.id, KnowledgeUpdate(status="error"))

    return IndexAllResponse(
        total_items=len(items),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.delete("/index/{knowledge_id}")
async def remove_knowledge_index(knowledge_id: int):
    """RAG delete is handled by the frontend calling agent-service directly."""
    agent_service_client.require_agent_service_url()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for RAG index removal (DELETE /rag/index/{id} on agent-service)",
    )


@router.post("/search")
async def search_knowledge_post():
    """RAG search is handled by the frontend calling agent-service directly."""
    agent_service_client.require_agent_service_url()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for RAG search",
    )


@router.get("/search")
async def search_knowledge_get():
    """RAG search is handled by the frontend calling agent-service directly."""
    agent_service_client.require_agent_service_url()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for RAG search",
    )


@router.get("/stats")
async def get_rag_stats():
    """RAG stats are handled by the frontend calling agent-service directly."""
    agent_service_client.require_agent_service_url()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for RAG stats",
    )
