"""Data models for RAG system components."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


@dataclass
class KnowledgeItem:
    """Represents a knowledge base item."""
    
    knowledge_id: int
    title: str
    uri: str
    category: Optional[str] = None
    tags: Optional[str] = None


@dataclass
class KnowledgeChunk:
    """Represents a text chunk from a knowledge item."""
    
    content: str
    knowledge_id: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class SearchResults:
    """Container for search results with metadata."""
    
    documents: List[str]
    metadata: List[Dict[str, Any]]
    distances: List[float]
    error: Optional[str] = None
    
    @classmethod
    def from_chroma(cls, chroma_results: Dict) -> "SearchResults":
        """Create SearchResults from ChromaDB query results."""
        return cls(
            documents=(
                chroma_results["documents"][0] if chroma_results["documents"] else []
            ),
            metadata=(
                chroma_results["metadatas"][0] if chroma_results["metadatas"] else []
            ),
            distances=(
                chroma_results["distances"][0] if chroma_results["distances"] else []
            ),
        )
    
    @classmethod
    def empty(cls, error_msg: str) -> "SearchResults":
        """Create empty results with error message."""
        return cls(documents=[], metadata=[], distances=[], error=error_msg)
    
    def is_empty(self) -> bool:
        """Check if results are empty."""
        return len(self.documents) == 0


class SearchResult(BaseModel):
    """A search result from the vector store."""
    content: str
    knowledge_id: int
    title: str
    uri: str
    score: float
    chunk_index: int


class IndexingResult(BaseModel):
    """Result of indexing a knowledge item."""
    success: bool
    chunks_indexed: int
    content_hash: str
    error: Optional[str] = None
