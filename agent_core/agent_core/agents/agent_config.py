from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union
from pathlib import Path
import yaml
import os
import httpx
LOCAL_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1337/v1")
LOCAL_MODEL = os.getenv("LOCAL_LLM_MODEL", "lfm2.5-1.2b-thinking-mlx-8bit")
REMOTE_MODEL = os.getenv("HF_REMOTE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")



class AgentConfig(BaseModel):
    """
    Unified configuration for agents, including LLM settings.
    
    This Pydantic model combines agent-specific configuration with LLM configuration,
    providing a single source of truth for agent setup.
    
    Agent-specific attributes:
        name: Agent name (matches directory name in config/)
        description: Human-readable description of the agent
        agent_class: Fully qualified Python class name to instantiate
    
    LLM attributes:
        model: Model name (HF Hub model ID or local model name)
        api_key: HF_TOKEN for remote HF Hub models (not needed for local servers)
        base_url: Base URL for local inference servers (TGI, vLLM, Ollama, etc.)
        llm_url: YAML-only key to override the LLM endpoint per agent; stored as base_url internally.
                 base_url remains supported in YAML for backward compatibility.
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0.0 to 2.0)
        timeout: Request timeout in seconds
        response_format: Optional response format (e.g., {"type": "json_object"})
    
    Extra:
        extra: Additional configuration fields from YAML
    """
    # Agent-specific fields
    name: str = ""
    description: str = ""
    agent_class: Optional[str] = None
    
    # LLM configuration fields (provider is always "huggingface")
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = LOCAL_BASE_URL
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 60.0
    response_format: Optional[dict] = None
    agent_dir: Optional[Path] = None
    sys_prompt: str = "You are a helpful assistant."
    # Extra fields from YAML
    extra: Dict[str, Any] = Field(default_factory=dict)
    provider: str = "huggingface"
    # RAG configuration
    use_rag: bool = False
    rag_top_k: int = 5
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "AgentConfig":
        """
        Load AgentConfig from a YAML file.
        
        Args:
            yaml_path: Path to the agent.yaml file
            
        Returns:
            AgentConfig instance
            
        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Extract known fields (provider is ignored, always "huggingface")
        known_fields = {
            'name', 'description', 'class', 'model', 'provider',
            'api_key', 'base_url', 'llm_url', 'max_tokens', 'temperature',
            'timeout', 'response_format'
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}
        base_url = data.get('llm_url') or data.get('base_url', LOCAL_BASE_URL)
        return cls(
            name=data.get('name', yaml_path.parent.name),
            description=data.get('description', 'A general purpose agent.'),
            agent_class=data.get('class', 'agent_core.agents.base_agent.BaseAgent'),  # None if not specified, resolved by _resolve_agent_class
            model=data.get('model', LOCAL_MODEL),
            provider=data.get('provider', 'huggingface'),
            api_key=data.get('api_key'),
            base_url=base_url,
            max_tokens=int(data.get('max_tokens', 10000)),
            temperature=float(data.get('temperature', 0.7)),
            timeout=float(data.get('timeout', 60.0)),
            response_format=data.get('response_format'),
            use_rag=data.get('use_rag', False),
            rag_top_k=data.get('rag_top_k', 3),
            extra=extra
        )
    
    def get_base_url(self) -> Optional[str]:
        """Get the base URL, using default if not set."""
        return self.base_url
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.model:
            raise ValueError("Model name is required")
        
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
    

def get_available_models() -> list[str]:
    """Get list of available models in local server (OpenAI-compatible /v1/models)."""
    try:
        url = f"{LOCAL_BASE_URL.rstrip('/')}/models"
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json().get("data", [])
            return [m.get("id", "") for m in data if m.get("id")]
        return []
    except (httpx.ConnectError, httpx.TimeoutException):
        return []