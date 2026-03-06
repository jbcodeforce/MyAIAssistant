"""
Agent factory for creating agents from predefined agents and user defined agents.
Scans a configuration directory for agent definitions 
"""
import importlib
from importlib.resources import as_file, files
from pathlib import Path
import os
import yaml
from typing import Optional, Type
from typing_extensions import Dict, List
from agno.agent import Agent, RemoteAgent
from agent_service.agents.agent_config import AgentConfig, get_llm_model, get_llm_base_url
from agent_service.agents.chat import get_chat_agent
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class AgentConfigReference(BaseModel):
    """
    To support lazy creation of agent 
    """
    agent_name: str
    path_to_config: Path
    default : bool = True

class AgentFactory():
    """
    Agent factory for the agent service.
    """
    def __init__(self):
        #self._config_references =  self._load_agents_ref_from_config_dir(config_dir)
        self._configs: Dict[str, AgentConfig] = {}  # Lazy loading
        self._config_dir = os.getenv("AGENT_CONFIG_DIR", "agent_service/agents/config")
        self._config_references = self._load_agent_references()

    def list_agents(self) ->List[Agent | RemoteAgent]:
        chat_agent = get_chat_agent()
        return [chat_agent]
    
    def get_agent_name_list(self) -> List[str]:
        return list(self._config_references.keys())
        
    # ----------------- Private
    def _load_agent_references(self) -> Dict[str, AgentConfigReference]:
        agent_references: Dict[str, AgentConfigReference] = {}
        # first load default agents from package resources
        package = "agent_service.agents.config"
        target_dir = files(package)
        for entry in target_dir.iterdir():
            with as_file(entry) as path:
                agent_references[entry.name] = AgentConfigReference(
                    agent_name=entry.name,
                    path_to_config=path,
                    default=True)
        return agent_references
    
    def get_or_create_agent(self, agent_name: str) -> Agent | RemoteAgent:
        if agent_name is None or agent_name == "":
            agent_name = "MainAgent"
        if agent_name in self._config_references:
            ref = self._config_references[agent_name]
            agent_config = self._load_agent_config_from_resource(ref)


            agent_cls = self._import_class(agent_config.agent_class)
            constructor_kwargs = {
                'config': agent_config
            }
            ai_agent = agent_cls(**constructor_kwargs)
            return ai_agent.get_agent()
        else:
            raise ValueError(f"Agent {agent_name} not found")


    def _load_agent_config_from_resource(self, config_ref :  AgentConfigReference) -> AgentConfig:

        yaml_path = config_ref.path_to_config / "agent.yaml"
        prompt_path = config_ref.path_to_config / "prompt.md"
        
        yaml_content = self._load_resource_text(yaml_path)
        prompt_content = self._load_resource_text(prompt_path)
        # Parse YAML content
        data = yaml.safe_load(yaml_content) or {}
        
        # Create AgentConfig from YAML data
        known_fields = {
            'name', 'description', 'class', 'model', 'provider',
            'api_key', 'base_url', 'llm_url', 'max_tokens', 'temperature',
            'timeout', 'response_format', 'use_rag', 'rag_top_k',
            'tools', 'tool_choice'
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}
        base_url = data.get('llm_url') or data.get('base_url', get_llm_base_url())
        agent_name = data.get('name', config_ref.agent_name)
        config = AgentConfig(
            name=agent_name,
            description=data.get('description', 'A general purpose agent.'),
            agent_class=data.get('class', 'agent_service.agent_router.AgentRouter'),
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
            sys_prompt=prompt_content,
            agent_dir=config_ref.path_to_config
        )
        
        return config

    def _load_resource_text(self, resource_path: Path) -> str:
        """
        Load text content from a package resource.
        
        Args:
            package: Package name (e.g., "agent_service.agents.config")
            resource_path: Path to resource within package (e.g., "GeneralAgent/agent.yaml")
            
        Returns:
            Text content of the resource
            
        Raises:
            FileNotFoundError: If resource doesn't exist
        """
        resource_path = Path(resource_path)
        if resource_path.exists():
            return resource_path.read_text(encoding="utf-8")
        else:
            return "You are a helpful assistant."


    def _import_class(self, fully_qualified_name: str) -> Type:
        """
        Dynamically import a class from its fully qualified name.
        
        Args:
            fully_qualified_name: Full module path and class name
                                 (e.g., 'agent_core.agents.base_agent.BaseAgent')
            
        Returns:
            The imported class
            
        Raises:
            ImportError: If module cannot be imported
            AttributeError: If class doesn't exist in module
        """
        # Split into module path and class name
        parts = fully_qualified_name.rsplit('.', 1)
        if len(parts) != 2:
            raise ImportError(
                f"Invalid fully qualified class name: {fully_qualified_name}. "
                f"Expected format: 'module.path.ClassName'"
            )
        
        module_path, class_name = parts
        
        # Import the module
        module = importlib.import_module(module_path)
        
        # Get the class from the module
        return getattr(module, class_name)

# Singleton instance
_factory: Optional[AgentFactory] = None

def get_or_create_agent_factory() -> AgentFactory:
    """
    Get or create the global agent factory instance.
    
    Args:
        config_dir: Optional config directory path
        
    Returns:
        AgentFactory instance
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory


def reset_agent_factory() -> None:
    """Reset the global factory instance. Useful for testing."""
    global _factory
    _factory = None


