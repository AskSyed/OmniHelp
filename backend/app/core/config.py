"""
Application configuration settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pathlib import Path


# Find the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_TEMPERATURE: float = 0.3
    
    # LangSmith Configuration
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_TRACING_V2: str = "false"
    LANGSMITH_PROJECT: Optional[str] = None
    LANGSMITH_ENDPOINT: Optional[str] = None
    
    # ChromaDB Configuration
    CHROMA_DB_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Embedding Configuration
    EMBEDDING_BATCH_SIZE: int = 100
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "csv"]
    UPLOAD_DIR: str = "./data/documents"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
