"""RAG (Retrieval-Augmented Generation) module for knowledge base processing."""

from agent_core.services.rag.service import RAGService
from agent_core.services.rag.document_loader import DocumentLoader
from agent_core.services.rag.document_processor import DocumentProcessor
from agent_core.services.rag.vector_store import VectorStore
from agent_core.services.rag.models import (
    KnowledgeItem,
    KnowledgeChunk,
    SearchResults,
    SearchResult,
    IndexingResult,
)

__all__ = [
    "RAGService",
    "DocumentLoader",
    "DocumentProcessor",
    "VectorStore",
    "KnowledgeItem",
    "KnowledgeChunk",
    "SearchResults",
    "SearchResult",
    "IndexingResult",
]

