"""
Query API endpoints for RAG queries
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.models.query import QueryRequest, QueryResponse
from app.agents.orchestrator import process_query

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Process a RAG query through the complete workflow
    
    Args:
        request: Query request with query text and optional parameters
        
    Returns:
        Query response with answer, sources, and metadata
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Process query through RAG workflow
        result = await process_query(
            query=request.query,
            n_results=request.n_results,
            filters=request.filters
        )
        
        return QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            metadata=result.get("metadata", {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
