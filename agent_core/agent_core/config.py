"""Configuration for LLM Core library."""

from dataclasses import dataclass
from typing import Optional, Literal


ProviderType = Literal["openai", "anthropic", "ollama"]


# Default base URLs for each provider
DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "ollama": "http://localhost:11434",
}


@dataclass
class LLMConfig:
    """Configuration for LLM client.
    
    Attributes:
        provider: The LLM provider ("openai", "anthropic", "ollama")
        model: The model name to use
        api_key: API key for the provider (not needed for Ollama)
        base_url: Custom base URL (uses provider default if not set)
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0.0 to 1.0)
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
    
    def get_base_url(self) -> str:
        """Get the base URL, using default if not set."""
        if self.base_url:
            return self.base_url
        return DEFAULT_BASE_URLS.get(self.provider, "")
    
    def validate(self) -> None:
        """Validate the configuration."""
        if self.provider not in ("openai", "anthropic", "ollama"):
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        if not self.model:
            raise ValueError("Model name is required")
        
        if self.provider in ("openai", "anthropic") and not self.api_key:
            raise ValueError(f"API key is required for {self.provider}")
        
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

