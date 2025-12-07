from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MyAIAssistant Backend"
    app_version: str = "0.1.0"
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./myaiassistant.db"
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

