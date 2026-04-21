from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
import yaml
import os
import httpx

def get_llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/v1"


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", "llama3.2")

def get_vstore_path() -> str:
    return os.getenv("VS_DB_URL", os.getenv("VSTORE_PERSIST_DIRECTORY", "data/vs.db"))

def get_llm_api_key() -> str:
    return os.getenv("LLM_API_KEY", "no-key")

def get_agent_config_path() -> str | None:
    return os.environ.get("AGENT_CONFIG_DIR")

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
    agent_class: str = "agent_service.agents.base_ai_agent.AIAgent"
    
    # LLM configuration fields (provider is always "huggingface")
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = get_llm_base_url()
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 60.0
    response_format: Optional[dict] = None
    agent_dir: Optional[Path] = None
    sys_prompt: str = "You are a helpful assistant."
    knowledge_name: str = "default"
    # RAG configuration
    use_rag: bool = False
    rag_category: str = "default"
    rag_top_k: int = 5
    tools: Optional[List[Union[str, dict]]] = None
    tool_choice: str = "auto"
    tool_prompt: Optional[str] = None
    reasoning: bool = True

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
            'name', 'description', 'agent_class', 'model', 
            'api_key', 'base_url', 'llm_url', 'max_tokens', 'temperature',
            'timeout', 'response_format', 'tools', 'tool_choice', 'tool_prompt',
            'reasoning',
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}
        base_url = data.get('llm_url') or data.get('base_url', get_llm_base_url())
        return cls(
            name=data.get('name', yaml_path.parent.name),
            description=data.get('description', 'A general purpose agent.'),
            agent_class=data.get('agent_class', 'agent_core.agents.base_agent.BaseAgent'),  # None if not specified, resolved by _resolve_agent_class
            model=data.get('model', get_llm_model()),
            api_key=data.get('api_key'),
            base_url=base_url,
            max_tokens=int(data.get('max_tokens', 10000)),
            temperature=float(data.get('temperature', 0.7)),
            timeout=float(data.get('timeout', 60.0)),
            response_format=data.get('response_format'),
            use_rag=data.get('use_rag', False),
            rag_top_k=data.get('rag_top_k', 3),
            tools=data.get('tools'),
            tool_choice=data.get('tool_choice', 'auto'),
            tool_prompt=data.get('tool_prompt'),
            reasoning=data.get('reasoning', True),
            agent_dir=yaml_path.parent
        )
    
    
