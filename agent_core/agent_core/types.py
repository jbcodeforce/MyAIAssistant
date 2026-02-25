from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
import json


MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    """Represents a call to a tool."""
    id: str
    function_name: str
    arguments: Dict[str, Any]


@dataclass
class ToolOutput:
    """Represents the output of a tool."""
    tool_call_id: str
    output: str


@dataclass
class Message:
    """A chat message."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for API calls."""
        msg_dict = {"role": self.role}
        if self.content is not None:
            msg_dict["content"] = self.content
        if self.tool_calls is not None:
            msg_calls = []
            for tc in self.tool_calls:
                msg_calls.append({
                    "id": tc.id,
                    "function": {
                        "name": tc.function_name,
                        "arguments": json.dumps(tc.arguments)
                    }
                })
            msg_dict["tool_calls"] = msg_calls
        if self.tool_call_id is not None:
            msg_dict["tool_call_id"] = self.tool_call_id
        return msg_dict


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: Optional[str]
    model: str
    provider: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    raw_response: Optional[dict] = None
    tool_calls: Optional[List[ToolCall]] = None
    
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

