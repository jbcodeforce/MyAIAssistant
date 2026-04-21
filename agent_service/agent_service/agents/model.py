from typing import List, Optional

from pydantic import BaseModel, Field


class SavePromptRequest(BaseModel):
    """Request body for saving an agent's prompt."""
    prompt: str = Field(..., min_length=1, description="Prompt text to save")