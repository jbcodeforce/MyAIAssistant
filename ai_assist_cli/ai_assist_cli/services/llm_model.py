"""Shared OpenAI-compatible model factory for Agno agents."""

from __future__ import annotations

from agno.models.openai.like import OpenAILike

from ai_assist_cli.services.llm_env import get_llm_api_key, get_llm_base_url, get_llm_model


def build_openai_like_model(*, temperature: float = 0.2) -> OpenAILike:
    """OpenAI-compatible chat model (Ollama, vLLM, OpenAI, etc.)."""
    return OpenAILike(
        id=get_llm_model(),
        base_url=get_llm_base_url(),
        api_key=get_llm_api_key(),
        temperature=temperature,
    )
