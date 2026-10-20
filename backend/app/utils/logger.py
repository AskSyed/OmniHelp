"""
Logging configuration
"""
from loguru import logger
import sys
from pathlib import Path
from app.core.config import settings

# Remove default logger
logger.remove()

# Defaults for fields set per request by RequestContextMiddleware
logger.configure(extra={"request_id": "-", "trace_id": "-"})

# Add console logger
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {extra[request_id]} | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

# Add file logger
log_file = Path(settings.LOG_FILE)
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_file),
    rotation="1 day",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | request_id={extra[request_id]} trace_id={extra[trace_id]} | {name}:{function} - {message}",
    compression="zip"
)
