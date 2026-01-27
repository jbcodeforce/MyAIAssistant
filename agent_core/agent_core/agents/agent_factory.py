"""Agent factory for creating agents from configuration.

This module provides a factory pattern for creating agent instances
based on YAML configuration files in the config directory.

AgentConfig is the unified configuration class that includes both
agent-specific settings and LLM configuration.
"""

import importlib
import importlib.resources
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, Type, TYPE_CHECKING
import yaml
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent_core.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

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
    base_url: Optional[str] = "http://localhost:11434/v1"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 60.0
    response_format: Optional[dict] = None
    agent_dir: Optional[Path] = None
    # Extra fields from YAML
    extra: Dict[str, Any] = Field(default_factory=dict)
    provider: str = "huggingface",
    # RAG configuration
    use_rag: bool = False,
    rag_top_k: int = 5,
    rag_category: str = None
    
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
            'name', 'description', 'class', 'model','provider',
            'api_key', 'base_url', 'max_tokens', 'temperature',
            'timeout', 'response_format'
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(
            name=data.get('name', yaml_path.parent.name),
            description=data.get('description', 'A general purpose agent.'),
            agent_class=data.get('class', 'agent_core.agents.base_agent.BaseAgent'),  # None if not specified, resolved by _resolve_agent_class
            model=data.get('model', 'mistral:7b-instruct'),
            provider=data.get('provider', 'huggingface'),
            api_key=data.get('api_key'),
            base_url=data.get('base_url','http://localhost:11434/v1'),
            max_tokens=int(data.get('max_tokens', 10000)),
            temperature=float(data.get('temperature', 0.7)),
            timeout=float(data.get('timeout', 60.0)),
            response_format=data.get('response_format'),
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
    


# Import BaseAgent here to avoid circular imports
def _get_base_agent():
    from agent_core.agents.base_agent import BaseAgent
    return BaseAgent


class AgentFactory:
    """
    Factory for creating agent instances from configuration.
    
    Scans a configuration directory for agent definitions and creates
    agent instances with injected configuration and prompts.
    
    Example:
        factory = AgentFactory(config_dir="path/to/config/directory")
        
        # List available agents
        print(factory.list_agents())  # ['QueryClassifier', 'GeneralAgent', ...]
        
        # Create an agent (uses BaseAgent when class is omitted)
        agent = factory.create_agent("GeneralAgent")
        
        # Get config
        config = factory.get_config("QueryClassifier")
    """
    
    # Registry mapping class names to agent classes
    _class_registry: Dict[str, Type] = {}
    
    # Special marker for resource-based agents
    RESOURCE_MARKER = Path("__resource__")
    
    def __init__(self, config_dir: str = None, load_defaults: bool = True):
        """
        Initialize the agent factory.
        
        Args:
            config_dir: Directory containing agent configurations.
                       If None, only default agents from package resources are loaded.
            load_defaults: Whether to load default agents from package resources.
                          Defaults to True.
        """
        self._configs: Dict[str, AgentConfig] = {}
        
        # Step 1: Load default agents from package resources
        if load_defaults:
            default_agents = self._load_default_agents_from_resources()
            self._configs.update(default_agents)
            logger.debug(f"Loaded {len(default_agents)} default agents from package resources")
        
        # Step 2: Load user-defined agents from config_dir (override defaults if same name)
        if config_dir is not None:
            user_agents = self._discover_agents(Path(config_dir))
            # User agents override defaults
            self._configs.update(user_agents)
            logger.debug(f"Loaded {len(user_agents)} user agents from {config_dir}")
    
    def _load_resource_text(self, package: str, resource_path: str) -> str:
        """
        Load text content from a package resource.
        
        Args:
            package: Package name (e.g., "agent_core.agents.config")
            resource_path: Path to resource within package (e.g., "GeneralAgent/agent.yaml")
            
        Returns:
            Text content of the resource
            
        Raises:
            FileNotFoundError: If resource doesn't exist
        """
        try:
            config_files = importlib.resources.files(package)
            resource_file = config_files / resource_path
            return resource_file.read_text(encoding="utf-8")
        except (FileNotFoundError, ModuleNotFoundError, AttributeError) as e:
            raise FileNotFoundError(f"Resource not found: {package}/{resource_path}") from e
    
    def _list_resource_directory(self, package: str, directory: str = "") -> list[str]:
        """
        List entries in a package resource directory.
        
        Args:
            package: Package name (e.g., "agent_core.agents.config")
            directory: Subdirectory path (empty string for root)
            
        Returns:
            List of entry names (files and directories)
        """
        try:
            config_files = importlib.resources.files(package)
            if directory:
                target_dir = config_files / directory
            else:
                target_dir = config_files
            
            entries = []
            for entry in target_dir.iterdir():
                entries.append(entry.name)
            return entries
        except (FileNotFoundError, ModuleNotFoundError, AttributeError) as e:
            logger.warning(f"Could not list resource directory {package}/{directory}: {e}")
            return []
    
    def _load_default_agents_from_resources(self) -> Dict[str, AgentConfig]:
        """
        Load default agent configurations from package resources.
        
        Returns:
            Dictionary mapping agent names to AgentConfig instances
        """
        default_agents: Dict[str, AgentConfig] = {}
        package = "agent_core.agents.config"
        
        try:
            # List all entries in the config package
            entries = self._list_resource_directory(package)
            
            for entry_name in entries:
                # Skip hidden files and __pycache__
                if entry_name.startswith('_') or entry_name.startswith('.'):
                    continue
                
                # Check if it's a directory (agent folder)
                try:
                    config_files = importlib.resources.files(package)
                    entry_path = config_files / entry_name
                    
                    # Try to access agent.yaml to verify it's an agent directory
                    yaml_path = f"{entry_name}/agent.yaml"
                    try:
                        yaml_content = self._load_resource_text(package, yaml_path)
                        
                        # Parse YAML content
                        data = yaml.safe_load(yaml_content) or {}
                        
                        # Create AgentConfig from YAML data
                        known_fields = {
                            'name', 'description', 'class', 'model', 'provider',
                            'api_key', 'base_url', 'max_tokens', 'temperature',
                            'timeout', 'response_format'
                        }
                        extra = {k: v for k, v in data.items() if k not in known_fields}
                        
                        agent_name = data.get('name', entry_name)
                        config = AgentConfig(
                            name=agent_name,
                            description=data.get('description', 'A general purpose agent.'),
                            agent_class=data.get('class', 'agent_core.agents.base_agent.BaseAgent'),
                            model=data.get('model', 'mistral:7b-instruct'),
                            provider=data.get('provider', 'huggingface'),
                            api_key=data.get('api_key'),
                            base_url=data.get('base_url', 'http://localhost:11434/v1'),
                            max_tokens=int(data.get('max_tokens', 10000)),
                            temperature=float(data.get('temperature', 0.7)),
                            timeout=float(data.get('timeout', 60.0)),
                            response_format=data.get('response_format'),
                            extra=extra,
                            agent_dir=self.RESOURCE_MARKER  # Mark as resource-based
                        )
                        
                        # Store resource path in extra for prompt loading
                        config.extra['_resource_package'] = package
                        config.extra['_resource_path'] = entry_name
                        
                        default_agents[agent_name] = config
                        logger.debug(f"Loaded default agent from resources: {agent_name}")
                        
                    except FileNotFoundError:
                        # Not an agent directory, skip
                        continue
                        
                except Exception as e:
                    logger.warning(f"Failed to process resource entry {entry_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to load default agents from resources: {e}")
        
        return default_agents
    
    def _discover_agents(self, config_dir: Path) -> Dict[str, AgentConfig]:
        """Scan config directory and load all agent configurations."""
        _configs: Dict[str, AgentConfig] = {}  
        if not config_dir.exists():
            logger.warning(f"Config directory not found: {config_dir}")
            return
        
        for agent_dir in config_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            
            agent_name = agent_dir.name
            
            # Skip __pycache__ and hidden directories
            if agent_name.startswith('_') or agent_name.startswith('.'):
                continue
            
            # Load agent.yaml
            yaml_path = agent_dir / "agent.yaml"
            if yaml_path.exists():
                try:
                    _configs[agent_name] = AgentConfig.from_yaml(yaml_path)
                    _configs[agent_name].agent_dir = agent_dir
                    logger.debug(f"Loaded config for agent: {agent_name}")
                except Exception as e:
                    logger.error(f"Failed to load config for {agent_name}: {e}")
        return _configs
            
    
    def list_agents(self) -> list[str]:
        """
        List all available agent names.
        
        Returns:
            List of agent names found in config directory
        """
        return list(self._configs.keys())

    
    def get_agent_map(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentConfig if found, None otherwise
        """
        return self._configs.get(agent_name)
    
    def create_agent(self, agent_name: Optional[str] = None, **kwargs) -> "BaseAgent":
        """
        Create an agent instance by name.
        
        Args:
            agent_name: Name of the agent to create
            **kwargs: Additional arguments to pass to the agent constructor
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent name is unknown
        """
        if agent_name is None or agent_name == "":
            agent_name = "GeneralAgent"
        config = self.get_agent_map(agent_name)
        if config is None:
            raise ValueError(f"Unknown agent: {agent_name}")
        # Resolve agent class
        agent_cls = self._resolve_agent_class(config.agent_class)
        
        # Build constructor arguments from AgentConfig
        # provider is always "huggingface"
        constructor_kwargs = {
            'config': config,
            **kwargs
        }
        agent = agent_cls(**constructor_kwargs)
        agent.agent_type = agent_name
        return agent
    
    def _resolve_agent_class(self, class_name: Optional[str]) -> Type:
        """
        Resolve a fully qualified class name to an actual agent class.
        
        Args:
            class_name: Fully qualified class name (e.g., 'agent_core.agents.base_agent.BaseAgent'),
                       or None for default BaseAgent
            
        Returns:
            Agent class type
            
        Raises:
            ValueError: If class cannot be imported or is not a BaseAgent subclass
        """
        BaseAgent = _get_base_agent()
        
        if class_name is None:
            # Return BaseAgent as default (generic agent)
            return BaseAgent
        
        # Check class registry first (for manually registered classes)
        if class_name in self._class_registry:
            return self._class_registry[class_name]
        
        # Dynamic import using fully qualified class name
        try:
            agent_cls = self._import_class(class_name)
            
            # Validate it's a BaseAgent subclass
            if not issubclass(agent_cls, BaseAgent):
                raise ValueError(
                    f"Class {class_name} is not a subclass of BaseAgent"
                )
            
            return agent_cls
            
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import agent class '{class_name}': {e}")
    
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
    
    @classmethod
    def register_class(cls, name: str, agent_class: Type) -> None:
        """
        Register a custom agent class by name.
        
        This allows using a short name instead of fully qualified name.
        
        Args:
            name: Name to register the class under (can be short or fully qualified)
            agent_class: The agent class to register
        """
        cls._class_registry[name] = agent_class
        logger.info(f"Registered agent class: {name}")


# Singleton instance
_factory: Optional[AgentFactory] = None


def get_agent_factory(config_dir: Path = None) -> AgentFactory:
    """
    Get or create the global agent factory instance.
    
    Args:
        config_dir: Optional config directory path
        
    Returns:
        AgentFactory instance
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory(config_dir=config_dir)
    return _factory


def reset_agent_factory() -> None:
    """Reset the global factory instance. Useful for testing."""
    global _factory
    _factory = None
