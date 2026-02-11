"""Shared fixtures and utilities for integration tests.

This module provides common configuration and skip markers for tests
that require a local LLM server (e.g. Osaurus).
"""

import os
import pytest
import httpx

from agent_core.agents.agent_config import LOCAL_BASE_URL, LOCAL_MODEL, get_available_models

def is_local_server_available() -> bool:
    """Check if local server is running and accessible."""
    try:
         model_names = get_available_models()
         return len(model_names) > 0
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str = None) -> bool:
    """Check if the specified model is available in local server.
    
    Args:
        model: Model name to check. Defaults to LOCAL_LLM_MODEL env var.
    """
    model = model or LOCAL_MODEL
    try:
        model_names = get_available_models()
        model_base = model.split(":")[0]
        return any(model_base in name or name in model_base for name in model_names)
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Skip markers - evaluated at collection time
requires_local_server = pytest.mark.skipif(
    not is_local_server_available(),
    reason=f"Local LLM server not available at {LOCAL_BASE_URL}"
)

requires_local_model = pytest.mark.skipif(
    not is_model_available(),
    reason=f"Model {LOCAL_MODEL} not available in local LLM server"
)


@pytest.fixture
def local_llm_base_url() -> str:
    """Fixture providing local LLM base URL."""
    return LOCAL_BASE_URL


@pytest.fixture
def local_llm_model() -> str:
    """Fixture providing local LLM model name."""
    return LOCAL_MODEL
