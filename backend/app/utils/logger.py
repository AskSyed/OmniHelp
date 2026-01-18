"""
Logging configuration
"""
from loguru import logger
import sys
from app.core.config import settings

# Remove default logger
logger.remove()

# Add custom logger
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

logger.add(
    "logs/omnihelp_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

