"""Type definitions for LLM Core library."""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime


MessageRole = Literal["system", "user", "assistant"]


@dataclass
class Message:
    """A chat message."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for API calls."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    raw_response: Optional[dict] = None
    
    @property
    def prompt_tokens(self) -> int:
        """Get prompt token count if available."""
        if self.usage:
            return self.usage.get("prompt_tokens", 0)
        return 0
    
    @property
    def completion_tokens(self) -> int:
        """Get completion token count if available."""
        if self.usage:
            return self.usage.get("completion_tokens", 0)
        return 0
    
    @property
    def total_tokens(self) -> int:
        """Get total token count if available."""
        if self.usage:
            return self.usage.get("total_tokens", 0)
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMError(Exception):
    """Exception raised by LLM operations."""
    message: str
    provider: str
    status_code: Optional[int] = None
    raw_error: Optional[dict] = None
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.provider}] {self.status_code}: {self.message}"
        return f"[{self.provider}] {self.message}"

