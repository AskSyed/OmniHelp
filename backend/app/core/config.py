"""
Application configuration settings
"""
from pydantic import SecretStr, model_validator
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
    LANGSMITH_TRACING_V2: str = "true"
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
    
    # MCP Server Configuration
    MCP_SERVER_HOST: str = "localhost"
    MCP_SERVER_PORT: int = 8001
    MCP_SERVER_ENABLED: bool = True

    # Authentication (JWT bearer tokens). Off for local dev; turn on per environment.
    AUTH_ENABLED: bool = False
    JWT_SECRET: Optional[SecretStr] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "omnihelp-auth"
    JWT_AUDIENCE: str = "omnihelp-api"

    # Redis for the shared cache and rate limits. Unset = in-process fallback (one replica only).
    REDIS_URL: Optional[str] = None
    QUERY_CACHE_TTL_SECONDS: int = 300  # 0 disables the query cache
    RATE_LIMIT_PER_MINUTE: int = 60  # 0 disables rate limiting

    # OpenTelemetry tracing
    OTEL_SERVICE_NAME: str = "omnihelp-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None  # e.g. http://localhost:4318
    OTEL_CONSOLE_EXPORT: bool = False

    @model_validator(mode="after")
    def check_auth_secret(self) -> "Settings":
        """Fail fast at startup instead of running with auth on and no signing key"""
        if self.AUTH_ENABLED and not self.JWT_SECRET:
            raise ValueError("JWT_SECRET must be set when AUTH_ENABLED=true")
        return self


settings = Settings()
