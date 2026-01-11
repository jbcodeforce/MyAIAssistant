"""Shared fixtures and utilities for integration tests.

This module provides common configuration and skip markers for tests
that require external services like Ollama.
"""

import os
import pytest
import httpx


# Environment configuration for Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")


def is_ollama_available() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        base = OLLAMA_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str = None) -> bool:
    """Check if the specified model is available in Ollama.
    
    Args:
        model: Model name to check. Defaults to OLLAMA_MODEL env var.
    """
    model = model or OLLAMA_MODEL
    try:
        base = OLLAMA_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            # Check if model exists (with or without tag)
            model_base = model.split(":")[0]
            return any(model_base in name or name in model_base for name in model_names)
        return False
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def get_available_models() -> list[str]:
    """Get list of available models in Ollama."""
    try:
        base = OLLAMA_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m.get("name", "") for m in models]
        return []
    except (httpx.ConnectError, httpx.TimeoutException):
        return []


# Skip markers - evaluated at collection time
requires_ollama = pytest.mark.skipif(
    not is_ollama_available(),
    reason=f"Ollama server not available at {OLLAMA_BASE_URL}"
)

requires_model = pytest.mark.skipif(
    not is_model_available(),
    reason=f"Model {OLLAMA_MODEL} not available in Ollama"
)


@pytest.fixture
def ollama_base_url() -> str:
    """Fixture providing Ollama base URL."""
    return OLLAMA_BASE_URL


@pytest.fixture
def ollama_model() -> str:
    """Fixture providing Ollama model name."""
    return OLLAMA_MODEL
