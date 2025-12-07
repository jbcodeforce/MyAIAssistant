import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# Default config file shipped with the app
DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


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
            return {}
        encoding = self.config.get("env_file_encoding", "utf-8")
        content = path.read_text(encoding=encoding)
        return yaml.safe_load(content) or {}

    def _load_yaml_data(self) -> dict[str, Any]:
        if self._yaml_data is not None:
            return self._yaml_data

        # Start with default config
        self._yaml_data = self._load_yaml_file(DEFAULT_CONFIG_FILE)

        # Overlay user config if CONFIG_FILE is set
        user_config_file = os.environ.get("CONFIG_FILE")
        if user_config_file:
            user_config = self._load_yaml_file(Path(user_config_file))
            self._yaml_data.update(user_config)

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
    llm_provider: str = "ollama"  # "openai", "anthropic", "ollama"
    llm_model: str = "gpt-oss:20b"  # Model name for the provider
    llm_api_key: Optional[str] = None  # API key (not needed for Ollama)
    llm_base_url: Optional[str] = "http://localhost:11434"  # Custom base URL
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


settings = Settings()

