"""Schemas for RAG operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IndexKnowledgeRequest(BaseModel):
    """Request to index a specific knowledge item."""
    knowledge_id: int = Field(..., description="ID of the knowledge item to index")


class IndexKnowledgeResponse(BaseModel):
    """Response from indexing a knowledge item."""
    success: bool
    knowledge_id: int
    chunks_indexed: int
    content_hash: Optional[str] = None
    error: Optional[str] = None


class IndexAllResponse(BaseModel):
    """Response from indexing all knowledge items."""
    total_items: int
    successful: int
    failed: int
    results: list[IndexKnowledgeResponse]


class SearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., min_length=1, description="Search query")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[list[str]] = Field(None, description="Filter by tags")


class SearchResultItem(BaseModel):
    """A single search result."""
    content: str
    knowledge_id: int
    title: str
    uri: str
    score: float = Field(..., description="Relevance score (0-1)")
    chunk_index: int


class SearchResponse(BaseModel):
    """Response from semantic search."""
    query: str
    results: list[SearchResultItem]
    total_results: int


class RAGStatsResponse(BaseModel):
    """Statistics about the RAG vector store."""
    total_chunks: int
    unique_knowledge_items: int
    collection_name: str
    embedding_model: str

