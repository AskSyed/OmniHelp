"""
Text chunking service for document processing
"""
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from app.core.config import settings


class ChunkingService:
    """Service for chunking text documents"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise
    
    def chunk_documents(self, documents: List[str]) -> List[str]:
        """
        Split multiple documents into chunks
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(doc)
            all_chunks.extend(chunks)
        return all_chunks
