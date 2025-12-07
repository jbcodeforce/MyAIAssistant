"""Schemas for chat functionality."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatMessageInput(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., pattern="^(user|assistant)$", description="Role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    """Request to chat about a todo task."""
    message: str = Field(..., min_length=1, max_length=4000, description="User's message")
    conversation_history: list[ChatMessageInput] = Field(
        default=[],
        description="Previous messages in the conversation"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    rag_query: Optional[str] = Field(None, description="Custom query for RAG search")


class ContextItem(BaseModel):
    """A piece of context retrieved from the knowledge base."""
    title: str
    uri: str
    score: float
    snippet: str


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    message: str = Field(..., description="Assistant's response")
    context_used: list[ContextItem] = Field(
        default=[],
        description="Knowledge base context used for the response"
    )
    model: str = Field(..., description="LLM model used")
    provider: str = Field(..., description="LLM provider used")


class ChatConfigResponse(BaseModel):
    """Current chat configuration."""
    provider: str
    model: str
    max_tokens: int
    temperature: float
    rag_enabled: bool

