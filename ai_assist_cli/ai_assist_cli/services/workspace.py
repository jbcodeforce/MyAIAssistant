"""Workspace management module."""

import os
import json
import shutil
from pathlib import Path
from typing import Any
import typer
from rich.console import Console
import yaml
console = Console()

class WorkspaceManager:
    """Manages AI Assistant workspace structure and configuration."""

    # Global home directory for cross-workspace resources
    GLOBAL_HOME = Path.home() / ".ai_assist"
    
    # Global directory structure (shared across workspaces)
    GLOBAL_DIRS = [
        "agents",
        "tools",
        "skills"
    ]

    # Workspace directory structure (per-workspace)
    WORKSPACE_DIRS = [
        "data/chroma",
        "agents",
        "tools",
        "skills",
        "history",
        "summaries",
        "notes",
    ]

    WORKSPACE_MARKER = ".ai_assist_workspace"
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
        return (self.path / self.WORKSPACE_MARKER).exists()

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
        # Get docker-compose.yml file from git repository
        docker_compose_file = self.path / "docker-compose.yml"
        # Copy the docker-compose.yml into the workspace directory (overwrite if exists)
        from shutil import copyfile
        source_docker_compose = Path(os.getenv("MYAIASSISTANT_DIR")) / "code" / "docker-compose.yml"
        if not source_docker_compose.exists():
            source_docker_compose = Path(os.getenv("MYAIASSISTANT_DIR")) /  "docker-compose.yml"
        if docker_compose_file != source_docker_compose and source_docker_compose.exists():
            # copy from source to workspace
            copyfile(source_docker_compose, docker_compose_file)
        # Write workspace marker with name
        marker_file = self.path / self.WORKSPACE_MARKER
        with open(marker_file, "w") as f:
            json.dump({"name": name}, f, indent=2)

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
        
        # Create default global agents
        cls._create_global_agents()
        
        return created_dirs

    @classmethod
    def _create_global_config(cls):
        """Create global configuration file."""
        config = {
            "version": "1.0",
            # Default LLM settings (can be overridden per workspace)
            "default_llm_provider": "osaurus",
            "default_llm_model": "lfm2.5-1.2b-thinking-mlx-8bit",
            "default_llm_base_url": "http://localhost:1334/v1",
            # Default embedding settings
            "default_embedding_model": "all-MiniLM-L6-v2",
            # Paths to directories
            "agents_dir": str(cls.GLOBAL_HOME / "agents"),
            "tools_dir": str(cls.GLOBAL_HOME / "tools"),
            "skills_dir": str(cls.GLOBAL_HOME / "skills"),
        }
        
        config_file = cls.GLOBAL_HOME / cls.GLOBAL_CONFIG_FILE
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def _create_global_agents(cls):
        """Create default global agent definitions."""
        agents_dir = cls.GLOBAL_HOME / "agents"
        
        # Create default global agent definitions
        agents_dir.mkdir(parents=True, exist_ok=True)
       

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

    def get_workspace_name(self) -> str | None:
        """Read workspace name from marker file."""
        marker_file = self.path / self.WORKSPACE_MARKER
        if not marker_file.exists():
            return None
        try:
            with open(marker_file) as f:
                data = json.load(f)
            return data.get("name")
        except (json.JSONDecodeError, OSError):
            return None

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
                "valid": path.exists() and (path / cls.WORKSPACE_MARKER).exists(),
            })

        return result

