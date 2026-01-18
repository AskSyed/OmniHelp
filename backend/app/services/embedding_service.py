"""
Embedding generation service
"""
from typing import List
from langchain_openai import OpenAIEmbeddings
from loguru import logger
from app.core.config import settings


class EmbeddingService:
    """Service for generating document embeddings"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Generate embeddings in batches for efficiency
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                logger.debug(f"Generated embeddings for batch {i//self.batch_size + 1}")
            
            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a single query
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.embeddings.embed_query(query)
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
