"""HuggingFace provider implementation using huggingface_hub InferenceClient."""

from typing import Optional

from huggingface_hub import InferenceClient, AsyncInferenceClient
from huggingface_hub.inference._generated.types import ChatCompletionOutput

from agent_core.providers.base import LLMProvider
from agent_core.config import LLMConfig, get_hf_token
from agent_core.types import Message, LLMResponse, LLMError


class HuggingFaceProvider(LLMProvider):
    """Provider for HuggingFace Hub and local inference servers.
    
    Supports both:
    - Remote HuggingFace Hub models (requires HF_TOKEN)
    - Local inference servers (TGI, vLLM, Ollama) via OpenAI-compatible API
    
    Example (remote):
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key=os.getenv("HF_TOKEN")
        )
    
    Example (local):
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
    """
    
    provider_name = "huggingface"
    
    def _get_token(self, config: LLMConfig) -> Optional[str]:
        """Get HuggingFace token from config or environment."""
        return config.api_key or get_hf_token()
    
    def _get_model_or_base_url(self, config: LLMConfig) -> str:
        """Get the model identifier or base URL for the client.
        
        For local servers, returns the base_url.
        For HF Hub, returns the model name.
        """
        if config.base_url:
            return config.base_url
        return config.model
    
    def _parse_response(
        self,
        response: ChatCompletionOutput,
        config: LLMConfig
    ) -> LLMResponse:
        """Parse HuggingFace ChatCompletionOutput to LLMResponse."""
        choice = response.choices[0]
        content = choice.message.content or ""
        
        # Extract usage information if available
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return LLMResponse(
            content=content,
            model=response.model or config.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
        )
    
    def _handle_error(self, error: Exception) -> None:
        """Handle errors from HuggingFace InferenceClient."""
        error_msg = str(error)
        
        # Try to extract status code if available
        status_code = None
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
        
        raise LLMError(
            message=error_msg,
            provider=self.provider_name,
            status_code=status_code,
        )
    
    async def chat_async(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Send async chat completion request using HuggingFace AsyncInferenceClient."""
        token = self._get_token(config)
        model_or_url = self._get_model_or_base_url(config)
        
        try:
            client = AsyncInferenceClient(
                model=model_or_url,
                token=token,
                timeout=config.timeout,
            )
            
            response = await client.chat_completion(
                messages=[msg.to_dict() for msg in messages],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=False,
            )
            
            return self._parse_response(response, config)
            
        except Exception as e:
            # Check for connection errors
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to HuggingFace endpoint. Error: {e}",
                    provider=self.provider_name,
                )
            self._handle_error(e)
    
    def chat_sync(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Send sync chat completion request using HuggingFace InferenceClient."""
        token = self._get_token(config)
        model_or_url = self._get_model_or_base_url(config)
        
        try:
            client = InferenceClient(
                model=model_or_url,
                token=token,
                timeout=config.timeout,
            )
            
            response = client.chat_completion(
                messages=[msg.to_dict() for msg in messages],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=False,
            )
            
            return self._parse_response(response, config)
            
        except Exception as e:
            # Check for connection errors
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to HuggingFace endpoint. Error: {e}",
                    provider=self.provider_name,
                )
            self._handle_error(e)

