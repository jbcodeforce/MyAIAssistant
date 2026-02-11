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
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, Type
import yaml
from agent_core.agents.agent_config import LOCAL_BASE_URL, LOCAL_MODEL, get_available_models, AgentConfig
from agent_core.agents.base_agent import BaseAgent



logger = logging.getLogger(__name__)

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
        if config_dir is not None and Path(config_dir).exists():
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
                    prompt_path = f"{entry_name}/prompt.md"
                    try:
                        yaml_content = self._load_resource_text(package, yaml_path)
                        prompt_content = self._load_resource_text(package, prompt_path)
                        # Parse YAML content
                        data = yaml.safe_load(yaml_content) or {}
                        
                        # Create AgentConfig from YAML data
                        known_fields = {
                            'name', 'description', 'class', 'model', 'provider',
                            'api_key', 'base_url', 'llm_url', 'max_tokens', 'temperature',
                            'timeout', 'response_format'
                        }
                        extra = {k: v for k, v in data.items() if k not in known_fields}
                        base_url = data.get('llm_url') or data.get('base_url', LOCAL_BASE_URL)
                        agent_name = data.get('name', entry_name)
                        config = AgentConfig(
                            name=agent_name,
                            description=data.get('description', 'A general purpose agent.'),
                            agent_class=data.get('class', 'agent_core.agents.base_agent.BaseAgent'),
                            model=data.get('model', LOCAL_MODEL),
                            provider=data.get('provider', 'huggingface'),
                            api_key=data.get('api_key'),
                            base_url=base_url,
                            max_tokens=int(data.get('max_tokens', 10000)),
                            temperature=float(data.get('temperature', 0.7)),
                            timeout=float(data.get('timeout', 60.0)),
                            response_format=data.get('response_format'),
                            extra=extra,
                            sys_prompt=prompt_content,
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
                    prompt_path = agent_dir / "prompt.md"
                    if prompt_path.exists():
                        _configs[agent_name].sys_prompt = prompt_path.read_text(encoding="utf-8")
                        logger.debug(f"Loaded prompt for agent: {agent_name}")
                    else:
                        logger.debug(f"No prompt found for agent: {agent_name}")
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

    def get_config(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get the AgentConfig for an agent by name.

        Args:
            agent_name: Name of the agent.

        Returns:
            AgentConfig if found, None otherwise.
        """
        return self._configs.get(agent_name)

    
    def create_agent(self, agent_name: Optional[str] = None, **kwargs) -> BaseAgent:
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
        config =  self._configs.get(agent_name)
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


