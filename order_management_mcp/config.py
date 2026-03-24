"""
Configuration for Order Management MCP Server
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


# Find the order_management_mcp directory
MCP_DIR = Path(__file__).parent
ENV_FILE = MCP_DIR / ".env"


class Settings(BaseSettings):
    """MCP Server settings"""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Server Configuration
    MCP_PORT: int = 8001
    MCP_HOST: str = "localhost"
    
    # Database Configuration
    ORDER_DB_PATH: str = "./data/orders.db"
    
    # Security Configuration
    ALLOW_WRITE_OPERATIONS: bool = False  # Read-only by default


settings = Settings()
