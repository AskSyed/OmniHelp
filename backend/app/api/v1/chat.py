"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from app.agents.orchestrator import route_query

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    conversation_id: str = None


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    intent: str
    route_to: str
    sources: list = []
    error: str = None


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Main chat endpoint - routes queries to appropriate agents
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Received query: {request.query}")
        
        result = await route_query(request.query)
        
        return ChatResponse(
            answer=result.get("answer", ""),
            intent=result.get("intent", "unknown"),
            route_to=result.get("route_to", "unknown"),
            sources=result.get("sources", []),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Error in chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

