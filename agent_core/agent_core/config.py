"""Configuration utilities for Agent Core library."""

import os
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


# Re-export AgentConfig as the unified configuration class
# This maintains backward compatibility for imports from config module
from agent_core.agents.factory import AgentConfig  # noqa: E402, F401
