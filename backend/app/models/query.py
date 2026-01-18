"""
Query and response models
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    n_results: int = 5
    filters: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    sources: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
