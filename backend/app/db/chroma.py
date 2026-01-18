"""
ChromaDB vector database client and utilities
"""
import chromadb
from pathlib import Path
from typing import List, Dict, Optional, Any
from loguru import logger
from app.core.config import settings


_client = None
_collection = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create ChromaDB client"""
    global _client
    if _client is None:
        db_path = Path(settings.CHROMA_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(db_path))
        logger.info(f"ChromaDB client initialized at {db_path}")
    return _client


def get_chroma_collection() -> chromadb.Collection:
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
                metadata={"description": "Document embeddings for RAG"}
            )
            logger.info(f"Created new collection: {settings.CHROMA_COLLECTION_NAME}")
    return _collection


def init_chroma_db():
    """Initialize ChromaDB connection"""
    get_chroma_collection()
    logger.info("ChromaDB initialized successfully")


def add_documents(
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    ids: List[str]
):
    """Add documents to ChromaDB collection"""
    collection = get_chroma_collection()
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"Added {len(documents)} documents to ChromaDB")


def query_documents(
    query_embeddings: List[List[float]],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Query documents from ChromaDB"""
    collection = get_chroma_collection()
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where=where,
        where_document=where_document
    )
    return results


def delete_documents(ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
    """Delete documents from ChromaDB"""
    collection = get_chroma_collection()
    collection.delete(ids=ids, where=where)
    logger.info(f"Deleted documents from ChromaDB")


def get_collection_count() -> int:
    """Get total number of documents in collection"""
    collection = get_chroma_collection()
    return collection.count()
