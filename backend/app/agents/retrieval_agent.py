"""
Retrieval Agent - Performs vector search and retrieves relevant context
"""
from typing import TypedDict, List, Dict, Any
from loguru import logger
from app.services.embedding_service import EmbeddingService
from app.db.chroma import query_documents


class RetrievalState(TypedDict):
    """State for retrieval agent"""
    query: str
    intent: str
    filters: dict
    query_embedding: List[float]
    retrieved_chunks: List[Dict[str, Any]]
    context: str
    sources: List[str]


def retrieve_context(state: dict) -> dict:
    """
    Retrieve relevant context from ChromaDB
    
    Args:
        state: Current retrieval state
        
    Returns:
        Updated state with retrieved chunks and context
    """
    query = state["query"]
    filters = state.get("filters", {})
    n_results = 5
    
    try:
        # Generate query embedding
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.generate_query_embedding(query)
        state["query_embedding"] = query_embedding
        
        # Prepare where clause for metadata filtering
        where_clause = None
        if filters and "source" in filters:
            where_clause = {"source": filters["source"]}
        
        # Query ChromaDB
        results = query_documents(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        # Extract documents, metadatas, and distances
        documents = results.get("documents", [])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [])[0] if results.get("metadatas") else []
        distances = results.get("distances", [])[0] if results.get("distances") else []
        ids = results.get("ids", [])[0] if results.get("ids") else []
        
        # Combine into retrieved chunks
        retrieved_chunks = []
        sources = set()
        
        for i, doc in enumerate(documents):
            chunk_data = {
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "id": ids[i] if i < len(ids) else None
            }
            retrieved_chunks.append(chunk_data)
            
            # Collect unique sources
            if metadatas and i < len(metadatas):
                source = metadatas[i].get("source", "unknown")
                sources.add(source)
        
        # Build context string
        context_parts = []
        for chunk in retrieved_chunks:
            context_parts.append(chunk["content"])
        
        context = "\n\n".join(context_parts)
        
        state["retrieved_chunks"] = retrieved_chunks
        state["context"] = context
        state["sources"] = list(sources)
        
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks from {len(sources)} sources")
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        state["retrieved_chunks"] = []
        state["context"] = ""
        state["sources"] = []
    
    return state
