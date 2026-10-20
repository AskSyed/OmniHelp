"""
Tests for MCP Client Service
"""
import pytest
from app.services.mcp_client_service import MCPClientService, get_mcp_client
from app.core.config import settings

# Calls live OpenAI / MCP services; excluded from the CI unit run
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client can be initialized"""
    client = MCPClientService()
    await client.initialize()
    
    if settings.MCP_SERVER_ENABLED:
        assert client._initialized is True
    else:
        assert client._initialized is False


@pytest.mark.asyncio
async def test_get_mcp_client_singleton():
    """Test that get_mcp_client returns the same instance"""
    client1 = get_mcp_client()
    client2 = get_mcp_client()
    
    assert client1 is client2


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_mcp_client_connection():
    """Test MCP client can connect to server"""
    client = get_mcp_client()
    await client.initialize()
    await client.connect()
    
    assert client.session is not None
    
    # Check connection
    is_connected = await client.check_connection()
    assert is_connected is True
    
    await client.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_mcp_list_tools():
    """Test listing tools from MCP server"""
    client = get_mcp_client()
    await client.initialize()
    await client.connect()
    
    tools = await client.list_tools()
    
    assert len(tools) > 0
    assert any(tool["name"] == "get_order_status" for tool in tools)
    assert any(tool["name"] == "get_customer_orders" for tool in tools)
    
    await client.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_mcp_call_tool_get_order_status():
    """Test calling get_order_status tool"""
    client = get_mcp_client()
    await client.initialize()
    await client.connect()
    
    result = await client.call_tool("get_order_status", {"order_id": 1})
    
    assert result is not None
    assert isinstance(result, str)
    assert "Order #1" in result or "No order found" in result
    
    await client.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(not settings.MCP_SERVER_ENABLED, reason="MCP server disabled")
async def test_mcp_call_tool_get_product_inventory():
    """Test calling get_product_inventory tool"""
    client = get_mcp_client()
    await client.initialize()
    await client.connect()
    
    result = await client.call_tool("get_product_inventory", {})
    
    assert result is not None
    assert isinstance(result, str)
    assert "Product Inventory" in result or "No products found" in result
    
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_call_tool_without_connection():
    """Test calling tool without connection returns error"""
    client = MCPClientService()
    
    result = await client.call_tool("get_order_status", {"order_id": 1})
    
    assert "Error" in result or "not connected" in result.lower()
