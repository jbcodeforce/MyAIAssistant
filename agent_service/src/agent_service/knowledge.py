"""Agno Knowledge + Chroma + embedder for RAG."""

import logging
import os
from pathlib import Path

from agno.knowledge import Knowledge
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.reader.text_reader import TextReader
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType
from agno.db.sqlite.sqlite import SqliteDb
from agent_service.config import get_chroma_path

logger = logging.getLogger("agent_service.knowledge")


def get_embedder():
    """Ollama embedder; set OLLAMA_BASE_URL and embedder model id if needed."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("KNOWLEDGE_EMBEDDER_MODEL", "nomic-embed-text")
    return OllamaEmbedder(id=model)


def build_knowledge() -> Knowledge:
    """Build the main knowledge base for RAG (Chroma + Ollama embedder)."""
    chroma_path = get_chroma_path()
    logger.info("Building knowledge base: chroma_path=%s", chroma_path)
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("KNOWLEDGE_EMBEDDER_MODEL", "nomic-embed-text")
    logger.info("Creating Ollama embedder: base_url=%s model=%s", base_url, model)
    logger.info("Creating ChromaDb (may block on first connection)...")
    kb = Knowledge(
        name="knowledge_base",
        vector_db=ChromaDb(
            name="knowledge_base",
            collection="knowledge_base",
            path=chroma_path,
            persistent_client=True,
            search_type=SearchType.hybrid,
            hybrid_rrf_k=60,
            embedder=get_embedder(),
        ),
        max_results=5,
    )
    logger.info("Knowledge base ready")
    return kb


# Lazy singleton for use by agents
_knowledge: Knowledge | None = None


def get_knowledge() -> Knowledge:
    global _knowledge
    if _knowledge is None:
        _knowledge = build_knowledge()
    return _knowledge
