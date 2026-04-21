"""
Configuration management with singleton pattern.

Loading priority (highest to lowest):
1. Environment variables
2. .env file
3. Init kwargs
4. CONFIG_FILE yaml (user overrides) + default app/config.yaml

Usage:
    from app.core.config import get_settings

    settings = get_settings()
    print(settings.database_url)
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

# Default config file shipped with the app
DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"

# Singleton instance
_settings: Optional["Settings"] = None

# Track which config file was loaded for debugging
_loaded_config_file: Optional[str] = None


def _load_yaml_file(path: Path, encoding: str = "utf-8") -> dict[str, Any]:
    """Load a single YAML file if it exists."""
    if not path.exists():
        logger.info(f"Config file not found: {path}")
        return {}
    content = path.read_text(encoding=encoding)
    return yaml.safe_load(content) or {}


class YamlSettingsSource(PydanticBaseSettingsSource):
    """Thin settings source that provides YAML config as lowest-priority layer."""

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        yaml_data = self.settings_cls.load_yaml_data()
        field_value = yaml_data.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value
        return d


class Settings(BaseSettings):
    """Application settings with defaults.
    Load order (first = lowest priority): YAML (default + CONFIG_FILE), init, .env, env vars.
    """

    _yaml_cache: ClassVar[dict[str, Any] | None] = None

    app_name: str = "MyAIAssistant Backend"
    app_version: str = "0.1.1"

    # Database settings (SQLite default for local, PostgreSQL for production)
    # SQLite: sqlite+aiosqlite:///./data/app.db (relative) or sqlite+aiosqlite:////absolute/path
    # PostgreSQL: postgresql+asyncpg://user:pass@host:5432/database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Server bind (when running via `python -m app.main`). For `uvicorn` CLI use --host/--port or set env.
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Optional origin to add to CORS when frontend runs on a custom port (e.g. FRONTEND_ORIGIN=http://localhost:3001).
    frontend_origin: Optional[str] = None


    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None  # None = {CONFIG_FILE parent or cwd}/logs/app_YYYY-MM-DD.log, or path (date appended)
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Meeting notes storage
    notes_root: str = "docs/meetings"  # Root folder for meeting notes

    # Agent configuration directory
    agent_config_dir: Optional[str] = None  # Path to agent config directory (defaults to agent_core/agent_core/agents/config)

    # Agent service (Agno/AgentOS microservice). When set, chat/knowledge/rag are proxied to this URL.
    agent_service_url: Optional[str] = "http://localhost:8100"  # e.g. http://localhost:8100

    # Optional: user identity for UI and future AI tools (e.g. send email)
    user_name: Optional[str] = None  # Display name in UI
    email: Optional[str] = None  # For future AI tools (e.g. sending email)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @classmethod
    def load_yaml_data(cls) -> dict[str, Any]:
        """Load default app/config.yaml and overlay CONFIG_FILE if set. Cached per class."""
        global _loaded_config_file
        if cls._yaml_cache is not None:
            return cls._yaml_cache
        cls._yaml_cache = _load_yaml_file(DEFAULT_CONFIG_FILE)
        _loaded_config_file = str(DEFAULT_CONFIG_FILE)
        logger.info(f"Loaded default config from: {DEFAULT_CONFIG_FILE}")
        user_config_file = os.environ.get("CONFIG_FILE")
        if user_config_file:
            user_config_path = Path(user_config_file)
            if user_config_path.exists():
                user_config = _load_yaml_file(user_config_path)
                cls._yaml_cache.update(user_config)
                _loaded_config_file = str(user_config_path.resolve())
                logger.info(f"Loaded user config from CONFIG_FILE: {_loaded_config_file}")
            else:
                logger.warning(f"CONFIG_FILE specified but not found: {user_config_path}")
        return cls._yaml_cache

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """First = highest priority: env, dotenv, init, YAML (lowest)."""
        return (
            env_settings,
            dotenv_settings,
            init_settings,
            YamlSettingsSource(settings_cls),
            file_secret_settings,
        )

def get_settings() -> Settings:
    """
    Get the singleton Settings instance.
    
    Creates the instance on first call, loading configuration from:
    1. Default app/config.yaml
    2. CONFIG_FILE yaml (if set, overrides defaults)
    3. Environment variables (highest priority)
    
    Returns:
        Settings: The singleton settings instance.
    """
    global _settings
    if _settings is None:
        logger.info("Initializing settings singleton...")
        _settings = Settings()
        logger.info(f"Settings initialized")
    return _settings


def reset_settings() -> None:
    """
    Reset the singleton instance. Useful for testing.
    """
    global _settings, _loaded_config_file
    _settings = None
    _loaded_config_file = None
    Settings._yaml_cache = None


def _log_path_with_date(base_path: Path) -> Path:
    """Build a log file path with the current date: stem_YYYY-MM-DD.suffix."""
    today = datetime.now().strftime("%Y-%m-%d")
    parent = base_path.parent
    stem = base_path.stem
    suffix = base_path.suffix or ""
    return parent / f"{stem}_{today}{suffix}"


def setup_logging() -> None:
    """
    Configure logging based on settings.

    Creates a log file with the execution date in the filename (e.g. app_2025-03-09.log).
    Call this early in application startup.
    """
    settings = get_settings()

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    formatter = logging.Formatter(settings.log_format)

    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Determine log file path: use explicit setting or default to {workspace_or_cwd}/logs/app.log; add date to filename
    log_file_path = settings.log_file
    if log_file_path is None:
        # When CONFIG_FILE is set (e.g. by start_dev_mode.sh), put logs in that directory (workspace), not backend/
        config_file = os.environ.get("CONFIG_FILE")
        if config_file:
            config_path = Path(config_file).resolve()
            if config_path.exists():
                log_root = config_path.parent
            else:
                log_root = Path.cwd()
        else:
            log_root = Path.cwd()
        base_path = log_root / "logs" / "app.log"
    else:
        base_path = Path(log_file_path)
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path
    log_path = _log_path_with_date(base_path)

    # Add file handler (always create log file for persistence)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    logger.info(f"Logging to file: {log_path.resolve()}")


def resolve_agent_config_dir(agent_config_dir: Optional[str]) -> Path:
    """
    Resolve the agent configuration directory path.
    
    Args:
        agent_config_dir: Optional path from settings. If None, uses default.
        
    Returns:
        Resolved absolute path as string.
    """
    if agent_config_dir is None:
        # Default to current hardcoded path relative to workspace root
        # This assumes the workspace root is the current working directory
        return Path.cwd() / "config"
    
    path = Path(agent_config_dir)
    if path.is_absolute():
        return path
    else:
        # Resolve relative to workspace root (current working directory)
        return Path.cwd() / path

def get_config_info() -> dict[str, Any]:
    """
    Get information about the current configuration for debugging.
    
    Returns:
        Dict with config file path and database path.
    """
    settings = get_settings()
    
    # Resolve database path for SQLite, keep URL for PostgreSQL
    resolved_db_path = settings.database_url
    if settings.database_url.startswith("sqlite"):
        # Extract and resolve SQLite file path
        if ":///" in settings.database_url:
            path_part = settings.database_url.split(":///", 1)[1]
            if path_part and path_part != ":memory:":
                db_path = Path(path_part)
                if not db_path.is_absolute():
                    db_path = Path.cwd() / path_part
                resolved_db_path = str(db_path.resolve())
    
    # Resolve log file path if specified
    resolved_log_path = None
    if settings.log_file:
        resolved_log_path = str(Path(settings.log_file).resolve())
    
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "agent_service_url": settings.agent_service_url,
        "notes_root": settings.notes_root,
        "agent_config_dir": settings.agent_config_dir,
        "user_name": settings.user_name,
        "email": settings.email,
        "config_file": _loaded_config_file,
        "database_url": settings.database_url,
        "resolved_database_path": resolved_db_path,
        "log_level": settings.log_level,
        "log_file": settings.log_file,
        "resolved_log_path": resolved_log_path,

    }
