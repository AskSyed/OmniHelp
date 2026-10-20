"""
Tests for Langgraph agents
"""
import pytest
from app.agents.query_agent import classify_query, QueryState
from app.agents.retrieval_agent import retrieve_context, RetrievalState

# Calls live OpenAI / MCP services; excluded from the CI unit run
pytestmark = pytest.mark.integration


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
    assert result["intent"] in ["document_search", "metadata_filter", "general", "order_management"]


@pytest.mark.asyncio
async def test_classify_order_query():
    """Test query classification for order management"""
    state: QueryState = {
        "query": "What is the status of order #123?",
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": {}
    }
    
    result = classify_query(state)
    assert "intent" in result
    # Should classify as order_management
    assert result["intent"] == "order_management"


@pytest.mark.asyncio
async def test_classify_customer_order_query():
    """Test query classification for customer orders"""
    state: QueryState = {
        "query": "Show me all orders for John Doe",
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": {}
    }
    
    result = classify_query(state)
    assert "intent" in result
    # Should classify as order_management
    assert result["intent"] == "order_management"


@pytest.mark.asyncio
async def test_classify_inventory_query():
    """Test query classification for inventory"""
    state: QueryState = {
        "query": "How many laptops are in stock?",
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": {}
    }
    
    result = classify_query(state)
    assert "intent" in result
    # Should classify as order_management
    assert result["intent"] == "order_management"


@pytest.mark.asyncio
async def test_classify_document_query():
    """Test query classification for document search"""
    state: QueryState = {
        "query": "What are the benefits of our product?",
        "intent": "document_search",
        "search_strategy": "",
        "reasoning": "",
        "filters": {}
    }
    
    result = classify_query(state)
    assert "intent" in result
    # Should classify as document_search
    assert result["intent"] in ["document_search", "general"]


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
