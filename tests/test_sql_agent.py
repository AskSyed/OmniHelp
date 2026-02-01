"""
Tests for SQL Agent
"""
import pytest
from app.agents.sql_agent import (
    execute_sql_query,
    determine_mcp_tool,
    validate_sql,
    format_sql_results
)
from app.core.config import settings


@pytest.mark.asyncio
async def test_determine_mcp_tool_order_status():
    """Test determining MCP tool for order status query"""
    query = "What is the status of order #123?"
    
    tool_name, args = await determine_mcp_tool(query)
    
    assert tool_name in ["get_order_status", "get_order_details"]
    assert "order_id" in args


@pytest.mark.asyncio
async def test_determine_mcp_tool_customer_orders():
    """Test determining MCP tool for customer orders query"""
    query = "Show me all orders for John Doe"
    
    tool_name, args = await determine_mcp_tool(query)
    
    assert tool_name in ["get_customer_orders_by_name", "get_customer_orders"]


@pytest.mark.asyncio
async def test_determine_mcp_tool_inventory():
    """Test determining MCP tool for inventory query"""
    query = "How many laptops do we have in stock?"
    
    tool_name, args = await determine_mcp_tool(query)
    
    assert tool_name in ["get_product_inventory", "execute_sql"]


def test_validate_sql_select_allowed():
    """Test that SELECT queries are allowed"""
    sql = "SELECT * FROM orders WHERE id = 1"
    
    assert validate_sql(sql) is True


def test_validate_sql_drop_blocked():
    """Test that DROP queries are blocked"""
    sql = "DROP TABLE orders"
    
    assert validate_sql(sql) is False


def test_validate_sql_delete_blocked():
    """Test that DELETE queries are blocked"""
    sql = "DELETE FROM orders WHERE id = 1"
    
    assert validate_sql(sql) is False


def test_validate_sql_insert_blocked():
    """Test that INSERT queries are blocked"""
    sql = "INSERT INTO orders (customer_id, total) VALUES (1, 100)"
    
    assert validate_sql(sql) is False


def test_validate_sql_update_blocked():
    """Test that UPDATE queries are blocked"""
    sql = "UPDATE orders SET status = 'shipped' WHERE id = 1"
    
    assert validate_sql(sql) is False


def test_format_sql_results_empty():
    """Test formatting empty results"""
    results = []
    
    output = format_sql_results(results)
    
    assert "No results found" in output


def test_format_sql_results_with_data():
    """Test formatting results with data"""
    results = [
        {"id": 1, "name": "John", "total": 100.0},
        {"id": 2, "name": "Jane", "total": 200.0}
    ]
    
    output = format_sql_results(results)
    
    assert "Results:" in output
    assert "John" in output
    assert "Jane" in output
    assert "100" in output
    assert "200" in output


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_execute_sql_query_integration():
    """Test SQL agent execution with actual MCP server"""
    from app.services.mcp_client_service import initialize_mcp_client
    
    # Initialize MCP client
    await initialize_mcp_client()
    
    # Create state
    state = {
        "query": "What is the status of order #1?",
        "intent": "order_management",
        "context": "",
        "sources": [],
        "error": ""
    }
    
    # Execute SQL query
    result = await execute_sql_query(state)
    
    assert "context" in result
    assert result["context"] != ""
    assert "sources" in result
    assert len(result["sources"]) > 0
    assert result["error"] == ""


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_execute_sql_query_customer_orders():
    """Test SQL agent with customer orders query"""
    from app.services.mcp_client_service import initialize_mcp_client
    
    await initialize_mcp_client()
    
    state = {
        "query": "Show me all orders",
        "intent": "order_management",
        "context": "",
        "sources": [],
        "error": ""
    }
    
    result = await execute_sql_query(state)
    
    assert "context" in result
    assert result["context"] != ""
    assert "Order" in result["context"] or "No orders" in result["context"]


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_execute_sql_query_inventory():
    """Test SQL agent with inventory query"""
    from app.services.mcp_client_service import initialize_mcp_client
    
    await initialize_mcp_client()
    
    state = {
        "query": "What products are in stock?",
        "intent": "order_management",
        "context": "",
        "sources": [],
        "error": ""
    }
    
    result = await execute_sql_query(state)
    
    assert "context" in result
    assert result["context"] != ""
    assert ("Product" in result["context"] or "Inventory" in result["context"] or 
            "No products" in result["context"])
