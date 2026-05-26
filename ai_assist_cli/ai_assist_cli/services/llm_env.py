"""Minimal LLM env reads for Agno OpenAILike (aligned with agent_service defaults)."""

from __future__ import annotations

import os


def get_llm_base_url() -> str:
    """OpenAI-compatible base URL (e.g. Ollama http://127.0.0.1:11434/v1)."""
    return os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/v1"


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", "llama3.2")


def get_llm_api_key() -> str:
    return os.getenv("LLM_API_KEY", "no-key")
