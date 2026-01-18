"""
ChromaDB vector database initialization and utilities
"""
import chromadb
from pathlib import Path
from loguru import logger
from app.core.config import settings


_client = None
_collection = None


def get_chroma_client():
    """Get or create ChromaDB client"""
    global _client
    if _client is None:
        db_path = Path(settings.CHROMA_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(db_path))
        logger.info(f"ChromaDB client initialized at {db_path}")
    return _client


def get_chroma_collection():
    """Get or create ChromaDB collection"""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        try:
            _collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
            logger.info(f"Retrieved existing collection: {settings.CHROMA_COLLECTION_NAME}")
        except Exception:
            _collection = client.create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Product manuals and documentation"}
            )
            logger.info(f"Created new collection: {settings.CHROMA_COLLECTION_NAME}")
    return _collection


def init_chroma_db():
    """Initialize ChromaDB"""
    get_chroma_collection()
    logger.info("ChromaDB initialized successfully")

