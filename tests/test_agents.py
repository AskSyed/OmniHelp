"""
Tests for Langgraph agents
"""
import pytest
from app.agents.query_agent import classify_query, QueryState
from app.agents.retrieval_agent import retrieve_context, RetrievalState


@pytest.mark.asyncio
async def test_classify_query():
    """Test query classification"""
    state: QueryState = {
        "query": "What is machine learning?",
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": {}
    }
    
    result = classify_query(state)
    assert "intent" in result
    assert result["intent"] in ["document_search", "metadata_filter", "general"]


@pytest.mark.asyncio
async def test_retrieve_context():
    """Test context retrieval"""
    # This test requires ChromaDB to be initialized with documents
    # Skip if no documents available
    state: RetrievalState = {
        "query": "test query",
        "intent": "document_search",
        "filters": {},
        "query_embedding": [],
        "retrieved_chunks": [],
        "context": "",
        "sources": []
    }
    
    result = retrieve_context(state)
    assert "retrieved_chunks" in result
    assert "context" in result
    assert "sources" in result
