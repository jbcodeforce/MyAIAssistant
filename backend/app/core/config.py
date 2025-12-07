from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MyAIAssistant Backend"
    app_version: str = "0.1.0"
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./myaiassistant.db"
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # LLM settings
    llm_provider: str = "openai"  # "openai", "anthropic", "ollama"
    llm_model: str = "gpt-4o-mini"  # Model name for the provider
    llm_api_key: Optional[str] = None  # API key (not needed for Ollama)
    llm_base_url: Optional[str] = None  # Custom base URL (for Ollama: http://localhost:11434)
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

