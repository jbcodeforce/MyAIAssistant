"""Configuration for LLM Core library."""

import os
from dataclasses import dataclass
from typing import Optional, Literal

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ProviderType = Literal["huggingface"]


# Default base URLs for each provider
DEFAULT_BASE_URLS = {
    "huggingface": None,  # Uses HF Hub API by default, or custom base_url for local
}


def get_hf_token() -> Optional[str]:
    """Get HuggingFace token from environment."""
    return os.getenv("HF_TOKEN")


@dataclass
class LLMConfig:
    """Configuration for LLM client.
    
    Attributes:
        provider: The LLM provider (currently only "huggingface" supported)
        model: The model name to use (HF Hub model ID or local model name)
        api_key: HF_TOKEN for remote HF Hub models (not needed for local servers)
        base_url: Base URL for local inference servers (TGI, vLLM, Ollama, etc.)
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0.0 to 2.0)
        timeout: Request timeout in seconds
        response_format: Optional response format (e.g., {"type": "json_object"})
    """
    provider: ProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 60.0
    response_format: Optional[dict] = None
    
    def get_base_url(self) -> Optional[str]:
        """Get the base URL, using default if not set."""
        if self.base_url:
            return self.base_url
        return DEFAULT_BASE_URLS.get(self.provider)
    
    def validate(self) -> None:
        """Validate the configuration."""
        if self.provider != "huggingface":
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'huggingface' provider.")
        
        if not self.model:
            raise ValueError("Model name is required")
        
        # HuggingFace requires token for remote models (not for local endpoints)
        if self.provider == "huggingface" and not self.base_url and not self.api_key:
            raise ValueError("HF_TOKEN is required for HuggingFace Hub models (set api_key or HF_TOKEN env var)")
        
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
