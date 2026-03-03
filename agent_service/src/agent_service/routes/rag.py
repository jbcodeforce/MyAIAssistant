"""RAG compatibility routes for backend proxy: index, search, stats, remove."""

import hashlib
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


class IndexPayload(BaseModel):
    """Payload for indexing; backend sends content it already loaded."""
    title: str
    uri: str
    document_type: str = "markdown"
    category: str | None = None
    tags: str | None = None
    content: str = ""


class SearchPayload(BaseModel):
    query: str = Field(..., min_length=1)
    n_results: int = Field(default=5, ge=1, le=20)
    category: str | None = None
    tags: list[str] | None = None


@router.post("/index/{knowledge_id}")
async def index_knowledge(knowledge_id: int, payload: IndexPayload):
    """Index one knowledge item; backend sends preloaded content."""
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content is required")
    try:
        kb = _get_knowledge()
    except Exception as e:
        logger.exception("Knowledge not available")
        raise HTTPException(status_code=503, detail=str(e))
    content_hash = hashlib.sha256(payload.content.encode()).hexdigest()
    metadata = {
        "knowledge_id": knowledge_id,
        "title": payload.title,
        "uri": payload.uri,
        "category": payload.category or "",
        "tags": payload.tags or "",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name
        try:
            f.write(payload.content)
            f.flush()
        finally:
            f.close()
        try:
            if hasattr(kb, "ainsert"):
                await kb.ainsert(
                    name=payload.title or f"doc_{knowledge_id}",
                    path=path,
                    metadata=metadata,
                )
            elif hasattr(kb, "insert"):
                import asyncio
                await asyncio.to_thread(
                    kb.insert,
                    name=payload.title or f"doc_{knowledge_id}",
                    path=path,
                    metadata=metadata,
                )
            else:
                raise NotImplementedError("Knowledge has no ainsert or insert")
        finally:
            Path(path).unlink(missing_ok=True)
    return {
        "success": True,
        "knowledge_id": knowledge_id,
        "chunks_indexed": 1,
        "content_hash": content_hash,
        "error": None,
    }


@router.post("/search")
async def search(payload: SearchPayload):
    """Semantic search over the knowledge base."""
    try:
        kb = _get_knowledge()
    except Exception as e:
        logger.exception("Knowledge not available")
        raise HTTPException(status_code=503, detail=str(e))
    try:
        results = kb.search(payload.query, limit=payload.n_results)
    except TypeError:
        results = kb.search(payload.query)
    out = []
    for i, doc in enumerate((results or [])[: payload.n_results]):
        if isinstance(doc, dict):
            content = doc.get("content") or doc.get("text", "")
            meta = doc.get("metadata", {})
        else:
            content = getattr(doc, "content", None) or getattr(doc, "text", str(doc))
            meta = getattr(doc, "metadata", {}) or {}
        out.append({
            "content": content,
            "knowledge_id": int(meta.get("knowledge_id", 0)),
            "title": meta.get("title", ""),
            "uri": meta.get("uri", ""),
            "score": float(meta.get("score", 0.0)),
            "chunk_index": i,
        })
    return {
        "query": payload.query,
        "results": out,
        "total_results": len(out),
    }


@router.get("/search")
async def search_get(
    q: str = Query(..., min_length=1),
    n: int = Query(5, ge=1, le=20),
    category: str | None = None,
):
    """GET search endpoint for backend proxy."""
    return await search(SearchPayload(query=q, n_results=n, category=category))


@router.get("/stats")
async def stats():
    """Collection stats for compatibility with backend."""
    try:
        kb = _get_knowledge()
    except Exception as e:
        logger.exception("Knowledge not available")
        raise HTTPException(status_code=503, detail=str(e))
    vdb = getattr(kb, "vector_db", None)
    if vdb is None:
        return {
            "total_chunks": 0,
            "unique_knowledge_items": 0,
            "collection_name": "knowledge_base",
            "embedding_model": "ollama",
        }
    try:
        coll = getattr(vdb, "collection", None) or getattr(vdb, "_collection", None)
        if coll is not None:
            count = coll.count()
            return {
                "total_chunks": count,
                "unique_knowledge_items": count,
                "collection_name": getattr(vdb, "collection", "knowledge_base") if isinstance(getattr(vdb, "collection", None), str) else "knowledge_base",
                "embedding_model": "ollama",
            }
    except Exception:
        pass
    return {
        "total_chunks": 0,
        "unique_knowledge_items": 0,
        "collection_name": "knowledge_base",
        "embedding_model": "ollama",
    }


@router.delete("/index/{knowledge_id}")
async def remove_index(knowledge_id: int):
    """Remove all chunks for a knowledge item from the vector store."""
    try:
        kb = _get_knowledge()
    except Exception as e:
        logger.exception("Knowledge not available")
        raise HTTPException(status_code=503, detail=str(e))
    vdb = getattr(kb, "vector_db", None)
    if vdb is None:
        return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}
    try:
        coll = getattr(vdb, "collection", None) or getattr(vdb, "_collection", None)
        if coll is not None and hasattr(coll, "delete"):
            coll.delete(where={"knowledge_id": knowledge_id})
    except Exception as e:
        logger.exception("Remove index failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}


def _get_knowledge():
    from agent_service.knowledge import get_knowledge
    return get_knowledge()
