from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class KnowledgeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the knowledge item")
    description: Optional[str] = Field(None, description="Description of the knowledge item")
    document_type: str = Field(..., description="Document type: markdown, website")
    uri: str = Field(..., max_length=2048, description="URI reference (file path or URL)")
    category: Optional[str] = Field(None, max_length=100, description="Category for classification")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags for flexible querying")
    status: str = Field(default="active", description="Status: active, pending, error, archived")

    @field_validator('tags')
    @classmethod
    def normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags: trim whitespace, lowercase, remove duplicates."""
        if not v:
            return v
        tags = [tag.strip().lower() for tag in v.split(',') if tag.strip()]
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        return ','.join(unique_tags) if unique_tags else None


class KnowledgeCreate(KnowledgeBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Project Documentation",
                    "description": "Main documentation for the project",
                    "document_type": "markdown",
                    "uri": "file:///docs/README.md",
                    "category": "Documentation",
                    "tags": "python,backend,api",
                    "status": "active"
                },
                {
                    "title": "API Reference",
                    "description": "External API documentation",
                    "document_type": "website",
                    "uri": "https://api.example.com/docs",
                    "category": "Reference",
                    "tags": "api,rest,external",
                    "status": "active"
                }
            ]
        }
    )


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = None
    uri: Optional[str] = Field(None, max_length=2048)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    content_hash: Optional[str] = Field(None, max_length=64)
    last_fetched_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None

    @field_validator('tags')
    @classmethod
    def normalize_tags(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tags: trim whitespace, lowercase, remove duplicates."""
        if not v:
            return v
        tags = [tag.strip().lower() for tag in v.split(',') if tag.strip()]
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        return ','.join(unique_tags) if unique_tags else None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": "Documentation",
                    "tags": "updated,reviewed"
                },
                {
                    "status": "archived"
                }
            ]
        }
    )


class KnowledgeResponse(KnowledgeBase):
    id: int
    content_hash: Optional[str] = None
    referenced_at: datetime
    last_fetched_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeResponse]
    total: int
    skip: int
    limit: int

