from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SettingsBase(BaseModel):
    llm_provider: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Provider of the LLM to use (e.g., openai, anthropic, ollama)"
    )
    llm_name: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Name of the LLM to use (e.g., gpt-4, claude-3, ollama/llama2)"
    )
    llm_api_endpoint: Optional[str] = Field(
        None, 
        max_length=2048, 
        description="API endpoint URL for the LLM service"
    )
    api_key: Optional[str] = Field(
        None, 
        max_length=500, 
        description="API key for authenticating with the LLM service"
    )
    default_temperature: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=2.0, 
        description="Default temperature for LLM responses (0.0-2.0)"
    )
    chunk_size: Optional[int] = Field(
        None, 
        ge=100, 
        le=10000, 
        description="Size of text chunks for RAG indexing"
    )
    overlap: Optional[int] = Field(
        None, 
        ge=0, 
        le=1000, 
        description="Overlap between text chunks for RAG indexing"
    )
    min_chunk_size: Optional[int] = Field(
        None, 
        ge=10, 
        le=5000, 
        description="Minimum size for text chunks"
    )


class SettingsCreate(SettingsBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "llm_name": "gpt-4",
                    "llm_api_endpoint": "https://api.openai.com/v1",
                    "api_key": "sk-...",
                    "default_temperature": 0.7,
                    "chunk_size": 1000,
                    "overlap": 200,
                    "min_chunk_size": 100
                }
            ]
        }
    )


class SettingsUpdate(SettingsBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "llm_name": "claude-3-sonnet",
                    "default_temperature": 0.5
                },
                {
                    "chunk_size": 1500,
                    "overlap": 300
                }
            ]
        }
    )


class SettingsResponse(SettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsResponseSafe(BaseModel):
    """Settings response without sensitive fields like api_key."""
    id: int
    llm_provider: Optional[str] = None
    llm_name: Optional[str] = None
    llm_api_endpoint: Optional[str] = None
    default_temperature: Optional[float] = None
    chunk_size: Optional[int] = None
    overlap: Optional[int] = None
    min_chunk_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

