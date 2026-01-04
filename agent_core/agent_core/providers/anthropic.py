"""Anthropic provider implementation."""

import httpx

from agent_core.providers.base import LLMProvider
from agent_core.config import LLMConfig
from agent_core.types import Message, LLMResponse, LLMError


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic API (Claude models)."""
    
    provider_name = "anthropic"
    ANTHROPIC_VERSION = "2023-06-01"
    
    def _build_request_body(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> dict:
        """Build the request body for Anthropic API.
        
        Anthropic uses a different format: system message is separate,
        and messages alternate between user and assistant.
        """
        system_content = ""
        api_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        body = {
            "model": config.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        
        if system_content:
            body["system"] = system_content
        
        return body
    
    def _build_headers(self, config: LLMConfig) -> dict:
        """Build headers for Anthropic API."""
        return {
            "x-api-key": config.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
    
    def _parse_response(self, data: dict, config: LLMConfig) -> LLMResponse:
        """Parse Anthropic API response."""
        content = data["content"][0]["text"]
        usage = data.get("usage")
        
        # Normalize usage format to match OpenAI
        normalized_usage = None
        if usage:
            normalized_usage = {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            }
        
        return LLMResponse(
            content=content,
            model=data.get("model", config.model),
            provider=self.provider_name,
            usage=normalized_usage,
            finish_reason=data.get("stop_reason"),
            raw_response=data,
        )
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error response from Anthropic API."""
        try:
            error_data = response.json()
            message = error_data.get("error", {}).get("message", response.text)
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
        """Send async chat completion request to Anthropic."""
        if not config.api_key:
            raise LLMError(
                message="API key is required for Anthropic",
                provider=self.provider_name,
            )
        
        url = f"{config.get_base_url()}/messages"
        headers = self._build_headers(config)
        body = self._build_request_body(messages, config)
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return self._parse_response(response.json(), config)
    
    def chat_sync(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Send sync chat completion request to Anthropic."""
        if not config.api_key:
            raise LLMError(
                message="API key is required for Anthropic",
                provider=self.provider_name,
            )
        
        url = f"{config.get_base_url()}/messages"
        headers = self._build_headers(config)
        body = self._build_request_body(messages, config)
        
        with httpx.Client(timeout=config.timeout) as client:
            response = client.post(url, headers=headers, json=body)
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return self._parse_response(response.json(), config)

