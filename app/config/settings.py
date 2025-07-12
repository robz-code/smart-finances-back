import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationInfo


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: Optional[str] = "sqlite:///./smart_finances.db"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str]
    
    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings() 