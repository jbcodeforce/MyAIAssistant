"""Schemas for chat functionality."""

from typing import Optional, Literal

from pydantic import BaseModel, Field


# Valid query intents for routing
QueryIntentType = Literal[
    "knowledge_search",
    "task_planning",
    "task_status",
    "data_query",
    "general_chat",
    "code_help",
    "unclear"
]


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
    context: Optional[dict] = Field(None, description="Additional context may be needed for routing to agent")
    rag_query: Optional[str] = Field(None, description="Custom query for RAG search")
    n_results: int = Field(default=5, ge=1, le=10, description="Number of RAG results to use")
    force_intent: Optional[QueryIntentType] = Field(
        None,
        description="Override automatic classification with specific intent"
    )

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
