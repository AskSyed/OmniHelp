"""
Shared dependencies for FastAPI
"""
from functools import lru_cache
from app.core.config import Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
