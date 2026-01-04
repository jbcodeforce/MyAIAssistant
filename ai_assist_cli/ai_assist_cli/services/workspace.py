"""Workspace management module."""

import json
import shutil
from pathlib import Path
from typing import Any

import yaml


class WorkspaceManager:
    """Manages AI Assistant workspace structure and configuration."""

    # Global home directory for cross-workspace resources
    GLOBAL_HOME = Path.home() / ".ai_assist"
    
    # Global directory structure (shared across workspaces)
    GLOBAL_DIRS = [
        "prompts",
        "agents",
        "tools",
        "models",
        "cache",
    ]

    # Workspace directory structure (per-workspace)
    WORKSPACE_DIRS = [
        "data/chroma",
        "data/db",
        "prompts",
        "tools",
        "history",
        "summaries",
        "notes",
    ]

    CONFIG_FILE = "config.yaml"
    GLOBAL_CONFIG_FILE = "config.yaml"
    WORKSPACE_REGISTRY_FILE = Path.home() / ".ai_assist" / "workspaces.json"

    def __init__(self, path: Path):
        """Initialize workspace manager.
        
        Args:
            path: Path to the workspace root directory.
        """
        self.path = path.resolve()

    def is_initialized(self) -> bool:
        """Check if workspace is initialized."""
        config_file = self.path / self.CONFIG_FILE
        return config_file.exists()

    def initialize(self, name: str) -> list[Path]:
        """Initialize workspace structure.
        
        Args:
            name: Workspace name.
            
        Returns:
            List of created directories.
        """
        created_dirs = []

        # Initialize global home directory first (if not exists)
        self._initialize_global_home()

        # Create workspace directory structure
        for dir_name in self.WORKSPACE_DIRS:
            dir_path = self.path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)

        # Create configuration file
        self._create_default_config(name)

        # Create default prompt templates
        self._create_default_prompts()

        # Register workspace
        self._register_workspace(name)

        return created_dirs

    @classmethod
    def _initialize_global_home(cls) -> list[Path]:
        """Initialize the global ~/.ai_assist directory structure.
        
        Creates directories for cross-workspace resources like shared prompts,
        agents, tools, and models.
        
        Returns:
            List of created directories.
        """
        created_dirs = []
        
        # Create global home directory
        cls.GLOBAL_HOME.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for dir_name in cls.GLOBAL_DIRS:
            dir_path = cls.GLOBAL_HOME / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
        
        # Create global config if not exists
        global_config = cls.GLOBAL_HOME / cls.GLOBAL_CONFIG_FILE
        if not global_config.exists():
            cls._create_global_config()
        
        # Create default global prompts
        cls._create_global_prompts()
        
        # Create default global agents
        cls._create_global_agents()
        
        return created_dirs

    @classmethod
    def _create_global_config(cls):
        """Create global configuration file."""
        config = {
            "version": "1.0",
            # Default LLM settings (can be overridden per workspace)
            "default_llm_provider": "ollama",
            "default_llm_model": "gpt-oss:20b",
            "default_llm_base_url": "http://localhost:11434",
            # Default embedding settings
            "default_embedding_model": "all-MiniLM-L6-v2",
            # Paths
            "prompts_dir": str(cls.GLOBAL_HOME / "prompts"),
            "agents_dir": str(cls.GLOBAL_HOME / "agents"),
            "tools_dir": str(cls.GLOBAL_HOME / "tools"),
            "models_dir": str(cls.GLOBAL_HOME / "models"),
            "cache_dir": str(cls.GLOBAL_HOME / "cache"),
        }
        
        config_file = cls.GLOBAL_HOME / cls.GLOBAL_CONFIG_FILE
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def _create_global_prompts(cls):
        """Create default global prompt templates."""
        prompts_dir = cls.GLOBAL_HOME / "prompts"
        
        # Base system prompt
        base_system = prompts_dir / "base_system.md"
        if not base_system.exists():
            base_system.write_text(
                """You are a helpful AI assistant.

Core principles:
1. Be accurate and truthful
2. Acknowledge uncertainty when appropriate
3. Provide concise, actionable responses
4. Respect user privacy and data
"""
            )
        
        # Coding assistant prompt
        coding_prompt = prompts_dir / "coding_assistant.md"
        if not coding_prompt.exists():
            coding_prompt.write_text(
                """You are an expert software engineer and coding assistant.

When helping with code:
1. Write clean, maintainable code following best practices
2. Include appropriate error handling
3. Add comments for complex logic
4. Consider edge cases and performance
5. Suggest tests when appropriate
"""
            )
        
        # Research assistant prompt
        research_prompt = prompts_dir / "research_assistant.md"
        if not research_prompt.exists():
            research_prompt.write_text(
                """You are a research assistant with expertise in information synthesis.

When researching topics:
1. Provide balanced perspectives on complex issues
2. Cite sources when available
3. Distinguish between facts and opinions
4. Highlight areas of uncertainty or debate
5. Suggest related topics for further exploration
"""
            )

    @classmethod
    def _create_global_agents(cls):
        """Create default global agent definitions."""
        agents_dir = cls.GLOBAL_HOME / "agents"
        
        # Default assistant agent
        assistant_agent = agents_dir / "assistant.yaml"
        if not assistant_agent.exists():
            agent_config = {
                "name": "assistant",
                "description": "General-purpose AI assistant",
                "system_prompt": "base_system.md",
                "tools": [],
                "temperature": 0.7,
                "max_tokens": 2048,
            }
            with open(assistant_agent, "w") as f:
                yaml.dump(agent_config, f, default_flow_style=False)
        
        # Coding agent
        coding_agent = agents_dir / "coder.yaml"
        if not coding_agent.exists():
            agent_config = {
                "name": "coder",
                "description": "Software development assistant",
                "system_prompt": "coding_assistant.md",
                "tools": ["file_reader", "code_executor"],
                "temperature": 0.3,
                "max_tokens": 4096,
            }
            with open(coding_agent, "w") as f:
                yaml.dump(agent_config, f, default_flow_style=False)
        
        # Research agent
        research_agent = agents_dir / "researcher.yaml"
        if not research_agent.exists():
            agent_config = {
                "name": "researcher",
                "description": "Research and information synthesis assistant",
                "system_prompt": "research_assistant.md",
                "tools": ["web_search", "document_reader"],
                "temperature": 0.5,
                "max_tokens": 4096,
            }
            with open(research_agent, "w") as f:
                yaml.dump(agent_config, f, default_flow_style=False)

    @classmethod
    def get_global_home(cls) -> Path:
        """Get the global home directory path."""
        return cls.GLOBAL_HOME

    @classmethod
    def is_global_initialized(cls) -> bool:
        """Check if global home directory is initialized."""
        return (cls.GLOBAL_HOME / cls.GLOBAL_CONFIG_FILE).exists()

    @classmethod
    def load_global_config(cls) -> dict[str, Any]:
        """Load global configuration."""
        config_file = cls.GLOBAL_HOME / cls.GLOBAL_CONFIG_FILE
        if not config_file.exists():
            return {}
        
        with open(config_file) as f:
            return yaml.safe_load(f) or {}

    def _create_default_config(self, name: str):
        """Create default configuration file."""
        config = {
            "name": name,
            "version": "1.0",
            # Database settings
            "database_path": "data/db/assistant.db",
            "database_url": f"postgresql+asyncpg://postgres:postgres@{name}:5432/biz_assistant",
            # LLM settings
            "llm_provider": "ollama",
            "llm_model": "gpt-oss:20b",
            "llm_api_key": None,
            "llm_base_url": "http://localhost:11434",
            "llm_max_tokens": 2048,
            "llm_temperature": 0.1,
            # RAG settings
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            # Paths
            "prompts_dir": "prompts",
            "tools_dir": "tools",
            "history_dir": "history",
            "summaries_dir": "summaries",
            "notes_dir": "notes",
        }

        config_file = self.path / self.CONFIG_FILE
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def _create_default_prompts(self):
        """Create default prompt templates."""
        prompts_dir = self.path / "prompts"

        # System prompt
        system_prompt = prompts_dir / "system.md"
        system_prompt.write_text(
            """You are a helpful AI assistant with access to a knowledge base.

When answering questions:
1. Use the provided context when relevant
2. Be concise and accurate
3. If you don't know something, say so
4. Cite sources when available
"""
        )

        # RAG prompt
        rag_prompt = prompts_dir / "rag.md"
        rag_prompt.write_text(
            """Use the following context to answer the question.

Context:
{context}

Question: {question}

Answer based on the context provided. If the context doesn't contain relevant information, say so.
"""
        )

    def _register_workspace(self, name: str):
        """Register workspace in global registry."""
        registry_file = self.WORKSPACE_REGISTRY_FILE
        registry_file.parent.mkdir(parents=True, exist_ok=True)

        workspaces = []
        if registry_file.exists():
            with open(registry_file) as f:
                workspaces = json.load(f)

        # Update or add workspace
        workspace_entry = {
            "name": name,
            "path": str(self.path),
        }

        # Remove existing entry with same path
        workspaces = [w for w in workspaces if w["path"] != str(self.path)]
        workspaces.append(workspace_entry)

        with open(registry_file, "w") as f:
            json.dump(workspaces, f, indent=2)

    def load_config(self) -> dict[str, Any]:
        """Load workspace configuration."""
        config_file = self.path / self.CONFIG_FILE
        if not config_file.exists():
            return {}

        with open(config_file) as f:
            return yaml.safe_load(f) or {}

    def set_config(self, key: str, value: Any):
        """Set a configuration value."""
        config = self.load_config()
        
        # Handle nested keys (e.g., "llm.model")
        keys = key.split(".")
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

        config_file = self.path / self.CONFIG_FILE
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def clean(self) -> int:
        """Clean workspace data (history, summaries, cache).
        
        Returns:
            Number of items cleaned.
        """
        cleaned = 0
        dirs_to_clean = ["history", "summaries"]

        for dir_name in dirs_to_clean:
            dir_path = self.path / dir_name
            if dir_path.exists():
                for item in dir_path.iterdir():
                    if item.is_file():
                        item.unlink()
                        cleaned += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        cleaned += 1

        return cleaned

    @classmethod
    def list_known_workspaces(cls) -> list[dict[str, Any]]:
        """List all registered workspaces."""
        registry_file = cls.WORKSPACE_REGISTRY_FILE
        if not registry_file.exists():
            return []

        with open(registry_file) as f:
            workspaces = json.load(f)

        # Validate each workspace
        result = []
        for ws in workspaces:
            path = Path(ws["path"])
            result.append({
                "name": ws["name"],
                "path": ws["path"],
                "valid": path.exists() and (path / cls.CONFIG_FILE).exists(),
            })

        return result

