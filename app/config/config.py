from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from app.config.baseapp_config import BaseAppConfig


class Config(BaseAppConfig):
    """Application-specific settings extending BaseAppConfig."""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False, 
        extra="ignore"
    )

    # Additional fields, if any, can be added similarly
    STATUS: str = Field(default="active", env="STATUS")  # Example additional field

@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()

config = get_config()
