from typing import Optional

from pydantic import BaseModel, Field


class AgentConfigResponse(BaseModel):
    """Read-only agent config for API responses. Excludes secrets and large fields."""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Human-readable description of the agent")
    model: Optional[str] = Field(None, description="LLM model name")
    agent_class: Optional[str] = Field(None, description="Fully qualified agent class name")
    temperature: Optional[float] = Field(None, description="Sampling temperature (0.0 to 2.0)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in the response")
