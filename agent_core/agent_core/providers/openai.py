"""OpenAI provider implementation."""

import httpx

from agent_core.providers.base import LLMProvider
from agent_core.config import LLMConfig
from agent_core.types import Message, LLMResponse, LLMError


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API (GPT-4, GPT-3.5, etc.)."""
    
    provider_name = "openai"
    
    def _build_request_body(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> dict:
        """Build the request body for OpenAI API."""
        body = {
            "model": config.model,
            "messages": [msg.to_dict() for msg in messages],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        
        if config.response_format:
            body["response_format"] = config.response_format
        
        return body
    
    def _build_headers(self, config: LLMConfig) -> dict:
        """Build headers for OpenAI API."""
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
    
    def _parse_response(self, data: dict, config: LLMConfig) -> LLMResponse:
        """Parse OpenAI API response."""
        choice = data["choices"][0]
        usage = data.get("usage")
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", config.model),
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error response from OpenAI API."""
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
        """Send async chat completion request to OpenAI."""
        if not config.api_key:
            raise LLMError(
                message="API key is required for OpenAI",
                provider=self.provider_name,
            )
        
        url = f"{config.get_base_url()}/chat/completions"
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
        """Send sync chat completion request to OpenAI."""
        if not config.api_key:
            raise LLMError(
                message="API key is required for OpenAI",
                provider=self.provider_name,
            )
        
        url = f"{config.get_base_url()}/chat/completions"
        headers = self._build_headers(config)
        body = self._build_request_body(messages, config)
        
        with httpx.Client(timeout=config.timeout) as client:
            response = client.post(url, headers=headers, json=body)
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return self._parse_response(response.json(), config)

