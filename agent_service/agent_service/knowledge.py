"""Singleton Knowledge base for RAG compatibility routes."""

from agent_service.ai_db import create_knowledge, get_embedder

_kb = None


def get_knowledge():
    global _kb
    if _kb is None:
        _kb = create_knowledge("rag", "knowledge_base")
        embedder = get_embedder()
        if hasattr(_kb, "vector_db") and _kb.vector_db is not None:
            if hasattr(_kb.vector_db, "embedder"):
                _kb.vector_db.embedder = embedder
    return _kb
