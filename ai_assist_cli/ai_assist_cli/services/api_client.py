"""Backend API client for AI Assistant."""

import os
from typing import Optional

import httpx
from pydantic import BaseModel


class KnowledgeCreateRequest(BaseModel):
    """Request model for creating a knowledge item."""
    title: str
    description: Optional[str] = None
    document_type: str
    uri: str
    category: Optional[str] = None
    tags: Optional[str] = None
    status: str = "pending"


class KnowledgeResponse(BaseModel):
    """Response model for a knowledge item."""
    id: int
    title: str
    document_type: str
    uri: str
    category: Optional[str] = None
    tags: Optional[str] = None
    status: str
    content_hash: Optional[str] = None


class IndexKnowledgeResponse(BaseModel):
    """Response model for indexing a knowledge item."""
    success: bool
    knowledge_id: int
    chunks_indexed: int
    content_hash: Optional[str] = None
    error: Optional[str] = None


class BackendClient:
    """HTTP client for the AI Assistant backend API."""

    DEFAULT_BASE_URL = "http://localhost:8000/api"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
        """Initialize the backend client.
        
        Args:
            base_url: Backend API base URL. Defaults to AI_ASSIST_BACKEND_URL 
                     env var or http://localhost:8000/api
            timeout: Request timeout in seconds (default 120s for indexing operations)
        """
        self.base_url = (
            base_url 
            or os.getenv("AI_ASSIST_BACKEND_URL") 
            or self.DEFAULT_BASE_URL
        )
        self.timeout = timeout

    async def create_knowledge(
        self,
        title: str,
        uri: str,
        document_type: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> KnowledgeResponse:
        """Create a new knowledge item via the backend API.
        
        Args:
            title: Title of the knowledge item
            uri: URI to the document (file path or URL)
            document_type: Type of document (markdown, website, folder)
            category: Optional category for filtering
            description: Optional description
            tags: Optional comma-separated tags
            
        Returns:
            KnowledgeResponse with the created item details
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        request = KnowledgeCreateRequest(
            title=title,
            uri=uri,
            document_type=document_type,
            category=category,
            description=description,
            tags=tags,
            status="pending",
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/knowledge/",
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return KnowledgeResponse(**response.json())

    async def index_knowledge(self, knowledge_id: int) -> IndexKnowledgeResponse:
        """Trigger indexing for a knowledge item.
        
        Args:
            knowledge_id: ID of the knowledge item to index
            
        Returns:
            IndexKnowledgeResponse with indexing results
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/rag/index/{knowledge_id}",
            )
            response.raise_for_status()
            return IndexKnowledgeResponse(**response.json())

    async def get_knowledge_by_uri(self, uri: str) -> Optional[KnowledgeResponse]:
        """Get a knowledge item by its URI.
        
        Args:
            uri: The document URI to lookup
            
        Returns:
            KnowledgeResponse if found, None otherwise
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/knowledge/by-uri/",
                params={"uri": uri},
            )
            response.raise_for_status()
            data = response.json()
            if data is None:
                return None
            return KnowledgeResponse(**data)

    async def get_rag_stats(self) -> dict:
        """Get RAG vector store statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/rag/stats")
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if the backend is reachable.
        
        Returns:
            True if the backend responds successfully
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code < 500
        except httpx.RequestError:
            return False

