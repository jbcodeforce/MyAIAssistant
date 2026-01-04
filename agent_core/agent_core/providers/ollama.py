"""Ollama provider implementation."""

import httpx

from agent_core.providers.base import LLMProvider
from agent_core.config import LLMConfig
from agent_core.types import Message, LLMResponse, LLMError


class OllamaProvider(LLMProvider):
    """Provider for Ollama API (local LLM models)."""
    
    provider_name = "ollama"
    
    def _build_request_body(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> dict:
        """Build the request body for Ollama API."""
        body = {
            "model": config.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
            "options": {
                "num_predict": config.max_tokens,
                "temperature": config.temperature,
            },
        }
        
        if config.response_format and config.response_format.get("type") == "json_object":
            body["format"] = "json"
        
        return body
    
    def _parse_response(self, data: dict, config: LLMConfig) -> LLMResponse:
        """Parse Ollama API response."""
        content = data["message"]["content"]
        
        # Ollama provides different usage metrics
        usage = None
        if "prompt_eval_count" in data or "eval_count" in data:
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }
        
        return LLMResponse(
            content=content,
            model=data.get("model", config.model),
            provider=self.provider_name,
            usage=usage,
            finish_reason=data.get("done_reason"),
            raw_response=data,
        )
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error response from Ollama API."""
        try:
            error_data = response.json()
            message = error_data.get("error", response.text)
        except Exception:
            message = response.text
        
        raise LLMError(
            message=message,
            provider=self.provider_name,
            status_code=response.status_code,
            raw_error=error_data if 'error_data' in dir() else None,
        )
    
    async def chat_async(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Send async chat completion request to Ollama."""
        url = f"{config.get_base_url()}/api/chat"
        body = self._build_request_body(messages, config)
        
        # Ollama may need longer timeout for large models
        timeout = max(config.timeout, 120.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=body)
            except httpx.ConnectError:
                raise LLMError(
                    message="Could not connect to Ollama. Is it running?",
                    provider=self.provider_name,
                )
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return self._parse_response(response.json(), config)
    
    def chat_sync(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Send sync chat completion request to Ollama."""
        url = f"{config.get_base_url()}/api/chat"
        body = self._build_request_body(messages, config)
        
        timeout = max(config.timeout, 120.0)
        
        with httpx.Client(timeout=timeout) as client:
            try:
                response = client.post(url, json=body)
            except httpx.ConnectError:
                raise LLMError(
                    message="Could not connect to Ollama. Is it running?",
                    provider=self.provider_name,
                )
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return self._parse_response(response.json(), config)

