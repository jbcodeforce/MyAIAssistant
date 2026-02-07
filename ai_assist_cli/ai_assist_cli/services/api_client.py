"""Backend API client for AI Assistant."""

import os
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel, Field


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


class OrganizationCreateRequest(BaseModel):
    """Request model for creating an organization."""
    name: str
    stakeholders: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None
    related_products: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Response model for an organization."""
    id: int
    name: str
    stakeholders: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None
    related_products: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectStep(BaseModel):
    """Step with action and assignee."""
    what: str
    who: str


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = None
    organization_id: Optional[int] = None
    status: str = "Draft"
    tasks: Optional[str] = None
    past_steps: Optional[list[ProjectStep]] = None
    next_steps: Optional[list[ProjectStep]] = None


class ProjectResponse(BaseModel):
    """Response model for a project."""
    id: int
    name: str
    description: Optional[str] = None
    organization_id: Optional[int] = None
    status: Optional[str] = None
    tasks: Optional[str] = None
    past_steps: Optional[list[ProjectStep]] = None
    next_steps: Optional[list[ProjectStep]] = None
    created_at: datetime
    updated_at: datetime


class PersonCreateRequest(BaseModel):
    """Request model for creating a person."""
    name: str
    context: Optional[str] = None
    role: Optional[str] = None
    last_met_date: Optional[datetime] = None
    next_step: Optional[str] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None


class PersonResponse(BaseModel):
    """Response model for a person."""
    id: int
    name: str
    context: Optional[str] = None
    role: Optional[str] = None
    last_met_date: Optional[datetime] = None
    next_step: Optional[str] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class MeetingRefCreateRequest(BaseModel):
    """Request model for creating a meeting reference."""
    meeting_id: str
    project_id: Optional[int] = None
    org_id: Optional[int] = None
    attendees: Optional[str] = None
    content: str = Field(..., min_length=1)


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

    async def create_organization(
        self,
        name: str,
        description: Optional[str] = None,
        stakeholders: Optional[str] = None,
        team: Optional[str] = None,
        related_products: Optional[str] = None,
    ) -> OrganizationResponse:
        """Create a new organization."""
        request = OrganizationCreateRequest(
            name=name,
            description=description,
            stakeholders=stakeholders,
            team=team,
            related_products=related_products,
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/organizations/",
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return OrganizationResponse(**response.json())

    async def get_organization_by_name(self, name: str) -> Optional[OrganizationResponse]:
        """Find an organization by name (case-insensitive exact match)."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/organizations/search/by-name",
                params={"name": name},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return OrganizationResponse(**response.json())

    async def create_project(
        self,
        name: str,
        organization_id: Optional[int] = None,
        description: Optional[str] = None,
        status: str = "Draft",
        tasks: Optional[str] = None,
        past_steps: Optional[list[dict]] = None,
        next_steps: Optional[list[dict]] = None,
    ) -> ProjectResponse:
        """Create a new project."""
        payload = {
            "name": name,
            "organization_id": organization_id,
            "description": description,
            "status": status,
            "tasks": tasks,
        }
        if past_steps is not None:
            payload["past_steps"] = [ProjectStep(**s).model_dump() for s in past_steps]
        if next_steps is not None:
            payload["next_steps"] = [ProjectStep(**s).model_dump() for s in next_steps]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/projects/",
                json={k: v for k, v in payload.items() if v is not None},
            )
            response.raise_for_status()
            return ProjectResponse(**response.json())

    async def create_person(
        self,
        name: str,
        organization_id: Optional[int] = None,
        project_id: Optional[int] = None,
        role: Optional[str] = None,
        context: Optional[str] = None,
        next_step: Optional[str] = None,
    ) -> PersonResponse:
        """Create a new person."""
        request = PersonCreateRequest(
            name=name,
            organization_id=organization_id,
            project_id=project_id,
            role=role,
            context=context,
            next_step=next_step,
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/persons/",
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return PersonResponse(**response.json())

    async def create_meeting_ref(
        self,
        meeting_id: str,
        content: str,
        org_id: Optional[int] = None,
        project_id: Optional[int] = None,
        attendees: Optional[str] = None,
    ) -> dict:
        """Create a new meeting reference (content saved to file system)."""
        request = MeetingRefCreateRequest(
            meeting_id=meeting_id,
            content=content,
            org_id=org_id,
            project_id=project_id,
            attendees=attendees,
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/meeting-refs/",
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return response.json()

