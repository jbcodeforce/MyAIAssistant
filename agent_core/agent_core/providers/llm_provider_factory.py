

from agent_core.providers.huggingface import HuggingFaceProvider
from agent_core.providers.llm_provider_base import LLMProvider

DEFAULT_PROVIDER = "huggingface"

class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(provider_name: str = DEFAULT_PROVIDER) -> LLMProvider:
        """Create a LLM provider based on the provider name."""
        provider_name = provider_name.lower().strip()
        if provider_name == "huggingface":
            return HuggingFaceProvider()
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")