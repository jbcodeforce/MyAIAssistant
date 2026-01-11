"""HuggingFace provider implementation using huggingface_hub InferenceClient."""

from typing import Optional, TYPE_CHECKING

from huggingface_hub import InferenceClient, AsyncInferenceClient
from huggingface_hub.inference._generated.types import ChatCompletionOutput

from agent_core.providers.base import LLMProvider
from agent_core.types import Message, LLMResponse, LLMError

if TYPE_CHECKING:
    from agent_core.agents.factory import AgentConfig


def get_hf_token() -> Optional[str]:
    """Get HuggingFace token from environment."""
    import os
    return os.getenv("HF_TOKEN")


class HuggingFaceProvider(LLMProvider):
    """Provider for HuggingFace Hub and local inference servers.
    
    Supports both:
    - Remote HuggingFace Hub models (requires HF_TOKEN)
    - Local inference servers (TGI, vLLM, Ollama) via OpenAI-compatible API
    
    Example (remote):
        config = AgentConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key=os.getenv("HF_TOKEN")
        )
    
    Example (local with Ollama):
        config = AgentConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:11434/v1"
        )
    """
    
    provider_name = "huggingface"
    
    def _get_token(self, config: "AgentConfig") -> Optional[str]:
        """Get HuggingFace token from config or environment."""
        return config.api_key or get_hf_token()
    
    def _is_local_server(self, config: "AgentConfig") -> bool:
        """Check if using a local inference server."""
        return config.base_url is not None
    
    def _parse_response(
        self,
        response: ChatCompletionOutput,
        config: "AgentConfig"
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
        config: "AgentConfig"
    ) -> LLMResponse:
        """Send async chat completion request using HuggingFace AsyncInferenceClient."""
        token = self._get_token(config)
        is_local = self._is_local_server(config)
        
        try:
            # For local servers, use base_url parameter; for remote, use model
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
            
            # Build chat completion kwargs
            chat_kwargs = {
                "messages": [msg.to_dict() for msg in messages],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "stream": False,
            }
            
            # For local servers, pass model name in the request
            if is_local:
                chat_kwargs["model"] = config.model
            
            response = await client.chat_completion(**chat_kwargs)
            
            return self._parse_response(response, config)
            
        except Exception as e:
            # Check for connection errors
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to inference endpoint. Error: {e}",
                    provider=self.provider_name,
                )
            self._handle_error(e)
    
    def chat_sync(
        self,
        messages: list[Message],
        config: "AgentConfig"
    ) -> LLMResponse:
        """Send sync chat completion request using HuggingFace InferenceClient."""
        token = self._get_token(config)
        is_local = self._is_local_server(config)
        
        try:
            # For local servers, use base_url parameter; for remote, use model
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
            
            # Build chat completion kwargs
            chat_kwargs = {
                "messages": [msg.to_dict() for msg in messages],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "stream": False,
            }
            
            # For local servers, pass model name in the request
            if is_local:
                chat_kwargs["model"] = config.model
            
            response = client.chat_completion(**chat_kwargs)
            
            return self._parse_response(response, config)
            
        except Exception as e:
            # Check for connection errors
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise LLMError(
                    message=f"Could not connect to inference endpoint. Error: {e}",
                    provider=self.provider_name,
                )
            self._handle_error(e)
