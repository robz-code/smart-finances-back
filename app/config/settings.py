from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Smart Finances"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "sqlite:///./smart_finances.db"

    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    JWT_SECRET_KEY: str = ""

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = []

    # Security settings
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
