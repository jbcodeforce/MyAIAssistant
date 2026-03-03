"""Configuration from environment."""

import os
from pathlib import Path


def get_llm_base_url() -> str:
    return os.getenv("LOCAL_LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/v1"


def get_llm_model() -> str:
    return os.getenv("LOCAL_LLM_MODEL", "llama3.2")


def get_chroma_path() -> str:
    return os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma")


def get_agent_config_path() -> str | None:
    return os.environ.get("AGENT_CONFIG_DIR")
