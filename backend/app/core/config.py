"""
Configuration management with singleton pattern.

Loading priority (highest to lowest):
1. Environment variables
2. .env file
3. CONFIG_FILE yaml (user overrides)
4. Default app/config.yaml

Usage:
    from app.core.config import get_settings
    
    settings = get_settings()
    print(settings.database_url)
"""

import os
from pathlib import Path
from typing import Any, Optional

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


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A settings source that loads configuration from YAML files.
    
    Loads in order (later values override earlier):
    1. Default app/config.yaml (shipped with the app)
    2. User config from CONFIG_FILE environment variable (optional)
    """

    _yaml_data: dict[str, Any] | None = None

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        """Load a single YAML file if it exists."""
        if not path.exists():
            logger.debug(f"Config file not found: {path}")
            return {}
        encoding = self.config.get("env_file_encoding", "utf-8")
        content = path.read_text(encoding=encoding)
        return yaml.safe_load(content) or {}

    def _load_yaml_data(self) -> dict[str, Any]:
        global _loaded_config_file
        if self._yaml_data is not None:
            return self._yaml_data

        # Start with default config
        self._yaml_data = self._load_yaml_file(DEFAULT_CONFIG_FILE)
        _loaded_config_file = str(DEFAULT_CONFIG_FILE)
        logger.debug(f"Loaded default config from: {DEFAULT_CONFIG_FILE}")

        # Overlay user config if CONFIG_FILE is set
        user_config_file = os.environ.get("CONFIG_FILE")
        if user_config_file:
            user_config_path = Path(user_config_file)
            if user_config_path.exists():
                user_config = self._load_yaml_file(user_config_path)
                self._yaml_data.update(user_config)
                _loaded_config_file = str(user_config_path.resolve())
                logger.info(f"Loaded user config from CONFIG_FILE: {_loaded_config_file}")
            else:
                logger.warning(f"CONFIG_FILE specified but not found: {str(user_config_path)}")
              
        return self._yaml_data

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        yaml_data = self._load_yaml_data()
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
    """Application settings with defaults."""
    
    app_name: str = "MyAIAssistant Backend"
    app_version: str = "0.1.0"

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./myaiassistant.db"

    # Knowledge base settings
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "knowledge_base"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM settings
    llm_provider: str = "ollama"
    llm_model: str = "gpt-oss:20b"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = "http://localhost:11434"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1
    chunk_size: int = 1000
    overlap: int = 200
    min_chunk_size: int = 100

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None  # None = console only, or path like "./logs/app.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # This method is called by Pydantic when instantiating the Settings class,
    # typically the first time get_settings() is invoked.
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Priority (highest to lowest):
        # 1. init_settings (values passed to constructor)
        # 2. env_settings (environment variables)
        # 3. dotenv_settings (.env file)
        # 4. yaml_settings (app/config.yaml defaults + CONFIG_FILE user overrides)
        # 5. file_secret_settings (secrets directory)
        logger.debug(f"Settings customise sources: {settings_cls}")
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
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
        logger.info(f"Settings initialized - database: {_settings.database_url}")
        logger.info(f"Settings initialized - chroma: {_settings.chroma_persist_directory}")
    return _settings


def reset_settings() -> None:
    """
    Reset the singleton instance. Useful for testing.
    """
    global _settings, _loaded_config_file
    _settings = None
    _loaded_config_file = None
    # Also reset the yaml cache in the source class
    YamlConfigSettingsSource._yaml_data = None


def setup_logging() -> None:
    """
    Configure logging based on settings.
    
    Creates file handler if log_file is specified, otherwise logs to console.
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
    
    # Add file handler if log_file is specified
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_path.resolve()}")


def get_config_info() -> dict[str, Any]:
    """
    Get information about the current configuration for debugging.
    
    Returns:
        Dict with config file path, database path, and vector store path.
    """
    settings = get_settings()
    
    # Resolve the actual database path from the URL
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        # Extract path from sqlite URL: sqlite+aiosqlite:///./path.db
        db_path = db_url.split("///")[-1]
        resolved_db_path = str(Path(db_path).resolve())
    else:
        resolved_db_path = db_url
    
    # Resolve chroma directory
    resolved_chroma_path = str(Path(settings.chroma_persist_directory).resolve())
    
    # Resolve log file path if specified
    resolved_log_path = None
    if settings.log_file:
        resolved_log_path = str(Path(settings.log_file).resolve())
    
    return {
        "config_file": _loaded_config_file,
        "database_url": settings.database_url,
        "resolved_database_path": resolved_db_path,
        "chroma_persist_directory": settings.chroma_persist_directory,
        "resolved_chroma_path": resolved_chroma_path,
        "chroma_collection_name": settings.chroma_collection_name,
        "log_level": settings.log_level,
        "log_file": settings.log_file,
        "resolved_log_path": resolved_log_path,
    }
