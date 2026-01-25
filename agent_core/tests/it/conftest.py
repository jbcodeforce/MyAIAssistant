"""Shared fixtures and utilities for integration tests.

This module provides common configuration and skip markers for tests
that require external services like Ollama.
"""

import os
import pytest
import httpx


# Environment configuration for Ollama
LOCAL_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
REMOTE_MODEL = os.getenv("HF_REMOTE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

def is_local_server_available() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        base = LOCAL_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str = None) -> bool:
    """Check if the specified model is available in Ollama.
    
    Args:
        model: Model name to check. Defaults to OLLAMA_MODEL env var.
    """
    model = model or LOCAL_MODEL
    try:
        base = LOCAL_BASE_URL.replace("/v1", "")
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
        base = LOCAL_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m.get("name", "") for m in models]
        return []
    except (httpx.ConnectError, httpx.TimeoutException):
        return []


# Skip markers - evaluated at collection time
requires_ollama = pytest.mark.skipif(
    not is_local_server_available(),
    reason=f"Ollama server not available at {LOCAL_BASE_URL}"
)

requires_model = pytest.mark.skipif(
    not is_model_available(),
    reason=f"Model {LOCAL_MODEL} not available in Ollama"
)


@pytest.fixture
def ollama_base_url() -> str:
    """Fixture providing Ollama base URL."""
    return LOCAL_BASE_URL


@pytest.fixture
def ollama_model() -> str:
    """Fixture providing Ollama model name."""
    return LOCAL_MODEL
