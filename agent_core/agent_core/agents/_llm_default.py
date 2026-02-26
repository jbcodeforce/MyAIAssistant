"""Default HuggingFace InferenceClient adapter and protocol for optional LLM client injection.

This module provides the default LLM path used by BaseAgent when no client is injected,
and the protocol that injected clients must implement.
"""

import os
from typing import AsyncIterator, Optional, Protocol, runtime_checkable, List, Union
import json

from huggingface_hub import InferenceClient, AsyncInferenceClient
from huggingface_hub.inference._generated.types import ChatCompletionOutput, ChatCompletionInputToolCall

from agent_core.types import LLMResponse, LLMError, ToolCall, Message
from agent_core.agents.agent_config import AgentConfig


def _get_hf_token(config: AgentConfig) -> Optional[str]:
    """Get HuggingFace token from config or environment."""
    return config.api_key or os.getenv("HF_TOKEN")


def _is_local_server(config: AgentConfig) -> bool:
    """Check if using a local inference server."""
    return config.base_url is not None


def _parse_response(response: ChatCompletionOutput, config: AgentConfig) -> LLMResponse:
    """Parse HuggingFace ChatCompletionOutput to LLMResponse."""
    choice = response.choices[0]
    content = choice.message.content or ""

    usage = None
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    
    tool_calls: Optional[List[ToolCall]] = None
    if choice.message.tool_calls:
        tool_calls = []
        for tc in choice.message.tool_calls:
            if isinstance(tc, ChatCompletionInputToolCall):
                tool_calls.append(ToolCall(
                    id=tc.id,
                    function_name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

    return LLMResponse(
        content=content,
        model=response.model or config.model,
        provider="huggingface",
        usage=usage,
        finish_reason=choice.finish_reason,
        raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        tool_calls=tool_calls
    )


def _normalize_messages(messages: list[dict]) -> list[dict]:
    """Ensure messages are list of dicts with role and content."""
    results = []
    for m in messages:
        if isinstance(m, Message):
            results.append({"role": m.role, "content": m.content})
        else:
            results.append(m)
        
    return results


def _normalize_tools(tools: List[dict]) -> List[dict]:
    """Ensure tools match OpenAI/HF chat completion format: type=function, function.name, function.parameters (JSON Schema)."""
    normalized = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        if "function" in t:
            fn = t["function"]
            if not isinstance(fn, dict) or "name" not in fn:
                continue
            name = fn["name"]
            params = fn.get("parameters")
            if params is None or not isinstance(params, dict):
                params = {"type": "object", "properties": {}}
            description = fn.get("description")
        else:
            name = t.get("name")
            if not name:
                continue
            params = t.get("parameters")
            if params is None or not isinstance(params, dict):
                params = {"type": "object", "properties": {}}
            description = t.get("description")
        out = {"type": "function", "function": {"name": name, "parameters": params}}
        if description is not None:
            out["function"]["description"] = description
        normalized.append(out)
    return normalized


@runtime_checkable
class LLMCallable(Protocol):
    """Protocol for an optional LLM client injected into BaseAgent.

    Agents can pass any object that implements chat_async (and optionally chat_sync)
    to use a different backend than the default HuggingFace InferenceClient.
    """

    async def chat_async(
        self,
        messages: list[dict],
        config: AgentConfig,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> LLMResponse:
        """Send a chat completion request asynchronously."""
        ...

    def chat_sync(
        self,
        messages: list[dict],
        config: AgentConfig,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> LLMResponse:
        """Send a chat completion request synchronously."""
        ...

    def chat_async_stream(
        self, messages: list[dict], config: AgentConfig
    ) -> AsyncIterator[str]:
        """Optional: stream chat completion tokens asynchronously. Yields content chunks."""
        ...


class DefaultHFAdapter:
    """Default adapter that uses HuggingFace InferenceClient for local and remote inference.

    Accepts list[dict] messages (role, content) and uses AgentConfig for model, base_url, etc.
    """

    async def chat_async(
        self,
        messages: list[dict],
        config: AgentConfig,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> LLMResponse:
        """Send async chat completion using AsyncInferenceClient."""
        token = _get_hf_token(config)
        is_local = _is_local_server(config)
        msgs = _normalize_messages(messages)

        chat_kwargs = {
            "messages": msgs,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": False,
        }
        if is_local:
            chat_kwargs["model"] = config.model
        if config.response_format:
            chat_kwargs["response_format"] = config.response_format
        if tools:
            chat_kwargs["tools"] = _normalize_tools(tools)
            if getattr(config, "tool_prompt", None):
                chat_kwargs["tool_prompt"] = config.tool_prompt
        if tool_choice:
            chat_kwargs["tool_choice"] = tool_choice

        try:
            if is_local:
                client = AsyncInferenceClient(
                    base_url=config.base_url,
                    token=token,
                    timeout=config.timeout,
                )
            else:
                client = AsyncInferenceClient(
                    model=config.model,
                    token=token,
                    timeout=config.timeout,
                )
            response = await client.chat_completion(**chat_kwargs)
            return _parse_response(response, config)
        except Exception as e:
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to inference endpoint. Error: {e}",
                    provider="huggingface",
                )
            _raise_llm_error(e)

    async def chat_async_stream(
        self,
        messages: list[dict],
        config: AgentConfig,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> AsyncIterator[str]:
        """Stream async chat completion; yields content chunks (token deltas)."""
        token = _get_hf_token(config)
        is_local = _is_local_server(config)
        msgs = _normalize_messages(messages)

        chat_kwargs = {
            "messages": msgs,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }
        if is_local:
            chat_kwargs["model"] = config.model
        if config.response_format:
            chat_kwargs["response_format"] = config.response_format
        if tools:
            chat_kwargs["tools"] = _normalize_tools(tools)
            if getattr(config, "tool_prompt", None):
                chat_kwargs["tool_prompt"] = config.tool_prompt
        if tool_choice:
            chat_kwargs["tool_choice"] = tool_choice

        try:
            if is_local:
                client = AsyncInferenceClient(
                    base_url=config.base_url,
                    token=token,
                    timeout=config.timeout,
                )
            else:
                client = AsyncInferenceClient(
                    model=config.model,
                    token=token,
                    timeout=config.timeout,
                )
            stream = await client.chat_completion(**chat_kwargs)
            if stream is None:
                return
            async for chunk in stream:
                content = None
                if chunk.choices and len(chunk.choices) > 0:
                    delta = getattr(chunk.choices[0], "delta", None)
                    if delta is not None:
                        content = getattr(delta, "content", None)
                if content:
                    yield content
        except Exception as e:
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to inference endpoint. Error: {e}",
                    provider="huggingface",
                )
            _raise_llm_error(e)

    def chat_sync(
        self,
        messages: list[dict],
        config: AgentConfig,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> LLMResponse:
        """Send sync chat completion using InferenceClient."""
        token = _get_hf_token(config)
        is_local = _is_local_server(config)
        msgs = _normalize_messages(messages)

        chat_kwargs = {
            "messages": msgs,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": False,
        }
        if is_local:
            chat_kwargs["model"] = config.model
        if config.response_format:
            chat_kwargs["response_format"] = config.response_format
        if tools:
            chat_kwargs["tools"] = _normalize_tools(tools)
            if getattr(config, "tool_prompt", None):
                chat_kwargs["tool_prompt"] = config.tool_prompt
        if tool_choice:
            chat_kwargs["tool_choice"] = tool_choice

        try:
            if is_local:
                client = InferenceClient(
                    base_url=config.base_url,
                    token=token,
                    timeout=config.timeout,
                )
            else:
                client = InferenceClient(
                    model=config.model,
                    token=token,
                    timeout=config.timeout,
                )
            response = client.chat_completion(**chat_kwargs)
            return _parse_response(response, config)
        except Exception as e:
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to inference endpoint. Error: {e}",
                    provider="huggingface",
                )
            _raise_llm_error(e)


def _raise_llm_error(error: Exception) -> None:
    """Map exception to LLMError and raise."""
    error_msg = str(error)
    status_code = None
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        status_code = error.response.status_code
    raise LLMError(
        message=error_msg,
        provider="huggingface",
        status_code=status_code,
    )
