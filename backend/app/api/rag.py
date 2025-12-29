"""RAG API endpoints for indexing and semantic search."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.rag.service import get_rag_service, RAGService
from app.api.schemas.knowledge import KnowledgeUpdate
from app.api.schemas.rag import (
    IndexKnowledgeResponse,
    IndexAllResponse,
    SearchRequest,
    SearchResultItem,
    SearchResponse,
    RAGStatsResponse,
)


router = APIRouter(prefix="/rag", tags=["rag"])


def get_rag() -> RAGService:
    """Dependency to get the RAG service."""
    return get_rag_service()


@router.post("/index/{knowledge_id}", response_model=IndexKnowledgeResponse)
async def index_knowledge_item(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag)
):
    """
    Index a specific knowledge item into the vector store.
    
    This loads the document, splits it into chunks, computes embeddings,
    and stores them in ChromaDB for semantic search.
    """
    # Get the knowledge item
    knowledge = await crud.get_knowledge(db, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    # Index the document or folder  
    result = await rag.index_knowledge(
        knowledge_id=knowledge.id,
        title=knowledge.title,
        uri=knowledge.uri,
        document_type=knowledge.document_type,
        category=knowledge.category,
        tags=knowledge.tags
    )
    
    # Update the knowledge item with indexing results
    if result.success:
        now = datetime.now(timezone.utc)
        await crud.update_knowledge(
            db,
            knowledge_id,
            KnowledgeUpdate(
                content_hash=result.content_hash,
                last_fetched_at=now,
                indexed_at=now,
                status="active"
            )
        )
    else:
        await crud.update_knowledge(
            db,
            knowledge_id,
            KnowledgeUpdate(status="error")
        )
    
    return IndexKnowledgeResponse(
        success=result.success,
        knowledge_id=knowledge_id,
        chunks_indexed=result.chunks_indexed,
        content_hash=result.content_hash if result.success else None,
        error=result.error
    )


@router.post("/index-all", response_model=IndexAllResponse)
async def index_all_knowledge(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'active')"),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag)
):
    """
    Index all knowledge items (or filtered by status) into the vector store.
    
    This is useful for initial setup or reindexing after changes.
    """
    # Get all knowledge items
    items, total = await crud.get_knowledges(db, limit=1000, status=status)
    
    results = []
    successful = 0
    failed = 0
    
    for item in items:
        result = await rag.index_knowledge(
            knowledge_id=item.id,
            title=item.title,
            uri=item.uri,
            document_type=item.document_type,
            category=item.category,
            tags=item.tags
        )
        
        response = IndexKnowledgeResponse(
            success=result.success,
            knowledge_id=item.id,
            chunks_indexed=result.chunks_indexed,
            content_hash=result.content_hash if result.success else None,
            error=result.error
        )
        results.append(response)
        
        # Update knowledge item status
        if result.success:
            successful += 1
            now = datetime.now(timezone.utc)
            await crud.update_knowledge(
                db,
                item.id,
                KnowledgeUpdate(
                    content_hash=result.content_hash,
                    last_fetched_at=now,
                    indexed_at=now,
                    status="active"
                )
            )
        else:
            failed += 1
            await crud.update_knowledge(
                db,
                item.id,
                KnowledgeUpdate(status="error")
            )
    
    return IndexAllResponse(
        total_items=len(items),
        successful=successful,
        failed=failed,
        results=results
    )


@router.delete("/index/{knowledge_id}")
async def remove_knowledge_index(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag)
):
    """
    Remove a knowledge item from the vector store index.
    
    This removes all chunks associated with the knowledge item.
    """
    # Verify the knowledge item exists
    knowledge = await crud.get_knowledge(db, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    success = await rag.remove_knowledge(knowledge_id)
    
    if success:
        return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to remove index")


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    rag: RAGService = Depends(get_rag)
):
    """
    Perform semantic search on the knowledge base.
    
    Returns the most relevant chunks based on the query.
    """
    results = await rag.search(
        query=request.query,
        n_results=request.n_results,
        category=request.category,
        tags=request.tags
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
                chunk_index=r.chunk_index
            )
            for r in results
        ],
        total_results=len(results)
    )


@router.get("/search", response_model=SearchResponse)
async def search_knowledge_get(
    q: str = Query(..., min_length=1, description="Search query"),
    n: int = Query(5, ge=1, le=20, description="Number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rag: RAGService = Depends(get_rag)
):
    """
    Perform semantic search on the knowledge base (GET endpoint).
    
    This is a convenience endpoint for simple searches.
    """
    results = await rag.search(
        query=q,
        n_results=n,
        category=category
    )
    
    return SearchResponse(
        query=q,
        results=[
            SearchResultItem(
                content=r.content,
                knowledge_id=r.knowledge_id,
                title=r.title,
                uri=r.uri,
                score=r.score,
                chunk_index=r.chunk_index
            )
            for r in results
        ],
        total_results=len(results)
    )


@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    rag: RAGService = Depends(get_rag)
):
    """
    Get statistics about the RAG vector store.
    
    Returns information about indexed chunks and knowledge items.
    """
    stats = rag.get_collection_stats()
    return RAGStatsResponse(**stats)

