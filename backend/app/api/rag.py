"""RAG API endpoints for indexing and semantic search."""

from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.db.crud.knowledge import get_knowledge, get_knowledges, update_knowledge
from app.api.schemas import (
    IndexKnowledgeResponse,
    IndexAllResponse,
    SearchResponse,
    RAGStatsResponse,
    SearchRequest,
    SearchResultItem,
)
from app.api.schemas.knowledge import KnowledgeUpdate
from app.services import agent_service_client

router = APIRouter(prefix="/rag", tags=["rag"])

from agent_core.services.rag.service import get_rag_service, RAGService
from agent_core.services.rag.document_loader import DocumentLoader


def get_rag() -> RAGService:
    """Dependency to get the RAG service."""
    return get_rag_service()


async def _load_content_for_proxy(uri: str, document_type: str) -> str:
    """Load document content when proxying index to agent-service."""
    if DocumentLoader is None:
        return ""
    loader = DocumentLoader()
    recursive = document_type == "folder"
    loaded_docs = await loader.load(uri, document_type, recursive=recursive)
    if not loaded_docs:
        return ""
    return "\n\n".join(doc.content for doc in loaded_docs)


@router.post("/index/{knowledge_id}", response_model=IndexKnowledgeResponse)
async def index_knowledge_item(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag),
):
    """
    Index a specific knowledge item. When AGENT_SERVICE_URL is set, content is sent to agent-service.
    """
    knowledge = await get_knowledge(db, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    if get_settings().agent_service_url:
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

    result = await rag.index_knowledge(
        knowledge_id=knowledge.id,
        title=knowledge.title,
        uri=knowledge.uri,
        document_type=knowledge.document_type,
        category=knowledge.category,
        tags=knowledge.tags,
    )
    if result.success:
        now = datetime.now(timezone.utc)
        await update_knowledge(
            db,
            knowledge_id,
            KnowledgeUpdate(
                content_hash=result.content_hash,
                last_fetched_at=now,
                indexed_at=now,
                status="active",
            ),
        )
    else:
        await update_knowledge(db, knowledge_id, KnowledgeUpdate(status="error"))
    return IndexKnowledgeResponse(
        success=result.success,
        knowledge_id=knowledge_id,
        chunks_indexed=result.chunks_indexed,
        content_hash=result.content_hash if result.success else None,
        error=result.error,
    )


@router.post("/index-all", response_model=IndexAllResponse)
async def index_all_knowledge(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'active')"),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag),
):
    """Index all knowledge items. When AGENT_SERVICE_URL is set, each item is proxied to agent-service."""
    items, _ = await get_knowledges(db, limit=1000, status=status)
    results = []
    successful = 0
    failed = 0

    if get_settings().agent_service_url:
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

    for item in items:
        result = await rag.index_knowledge(
            knowledge_id=item.id,
            title=item.title,
            uri=item.uri,
            document_type=item.document_type,
            category=item.category,
            tags=item.tags,
        )
        results.append(
            IndexKnowledgeResponse(
                success=result.success,
                knowledge_id=item.id,
                chunks_indexed=result.chunks_indexed,
                content_hash=result.content_hash if result.success else None,
                error=result.error,
            )
        )
        if result.success:
            successful += 1
            now = datetime.now(timezone.utc)
            await update_knowledge(
                db,
                item.id,
                KnowledgeUpdate(
                    content_hash=result.content_hash,
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
async def remove_knowledge_index(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag),
):
    """Remove a knowledge item from the index. Proxied to agent-service when AGENT_SERVICE_URL is set."""
    knowledge = await get_knowledge(db, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    if get_settings().agent_service_url:
        try:
            await agent_service_client.rag_remove_index(knowledge_id)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}
    success = await rag.remove_knowledge(knowledge_id)
    if success:
        return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}
    raise HTTPException(status_code=500, detail="Failed to remove index")


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    rag: RAGService = Depends(get_rag),
):
    """Semantic search. Proxied to agent-service when AGENT_SERVICE_URL is set."""
    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.rag_search(
                query=request.query,
                n_results=request.n_results,
                category=request.category,
                tags=request.tags,
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        return SearchResponse(
            query=data.get("query", request.query),
            results=[
                SearchResultItem(
                    content=r.get("content", ""),
                    knowledge_id=r.get("knowledge_id", 0),
                    title=r.get("title", ""),
                    uri=r.get("uri", ""),
                    score=r.get("score", 0.0),
                    chunk_index=r.get("chunk_index", i),
                )
                for i, r in enumerate(data.get("results", []))
            ],
            total_results=data.get("total_results", 0),
        )
    results = await rag.search(
        query=request.query,
        n_results=request.n_results,
        category=request.category,
        tags=request.tags,
    )
    return SearchResponse(
        query=request.query,
        results=[
            SearchResultItem(
                content=r.content,
                knowledge_id=r.knowledge_id,
                title=r.title,
                uri=r.uri,
                score=r.score,
                chunk_index=r.chunk_index,
            )
            for r in results
        ],
        total_results=len(results),
    )


@router.get("/search", response_model=SearchResponse)
async def search_knowledge_get(
    q: str = Query(..., min_length=1, description="Search query"),
    n: int = Query(5, ge=1, le=20, description="Number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rag: RAGService = Depends(get_rag),
):
    """GET search. Proxied to agent-service when AGENT_SERVICE_URL is set."""
    if get_settings().agent_service_url:
        try:
            data = await agent_service_client.rag_search_get(q=q, n=n, category=category)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        return SearchResponse(
            query=data.get("query", q),
            results=[
                SearchResultItem(
                    content=r.get("content", ""),
                    knowledge_id=r.get("knowledge_id", 0),
                    title=r.get("title", ""),
                    uri=r.get("uri", ""),
                    score=r.get("score", 0.0),
                    chunk_index=r.get("chunk_index", i),
                )
                for i, r in enumerate(data.get("results", []))
            ],
            total_results=data.get("total_results", 0),
        )
    results = await rag.search(query=q, n_results=n, category=category)
    return SearchResponse(
        query=q,
        results=[
            SearchResultItem(
                content=r.content,
                knowledge_id=r.knowledge_id,
                title=r.title,
                uri=r.uri,
                score=r.score,
                chunk_index=r.chunk_index,
            )
            for r in results
        ],
        total_results=len(results),
    )


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(rag: RAGService = Depends(get_rag)):
    """RAG stats. Proxied to agent-service when AGENT_SERVICE_URL is set."""
    if get_settings().agent_service_url:
        try:
            stats = await agent_service_client.rag_stats()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        return RAGStatsResponse(**stats)
    stats = rag.get_collection_stats()
    return RAGStatsResponse(**stats)

