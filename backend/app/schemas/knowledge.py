from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class KnowledgeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the knowledge item")
    description: Optional[str] = Field(None, description="Description of the knowledge item")
    document_type: str = Field(..., description="Document type: markdown, website")
    uri: str = Field(..., max_length=2048, description="URI reference (file path or URL)")
    status: str = Field(default="active", description="Status: active, pending, error, archived")


class KnowledgeCreate(KnowledgeBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Project Documentation",
                    "description": "Main documentation for the project",
                    "document_type": "markdown",
                    "uri": "file:///docs/README.md",
                    "status": "active"
                },
                {
                    "title": "API Reference",
                    "description": "External API documentation",
                    "document_type": "website",
                    "uri": "https://api.example.com/docs",
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
    status: Optional[str] = None
    content_hash: Optional[str] = Field(None, max_length=64)
    last_fetched_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "archived"
                },
                {
                    "content_hash": "abc123...",
                    "last_fetched_at": "2025-12-07T10:00:00"
                }
            ]
        }
    )


class KnowledgeResponse(KnowledgeBase):
    id: int
    content_hash: Optional[str] = None
    referenced_at: datetime
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeResponse]
    total: int
    skip: int
    limit: int

