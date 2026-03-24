"""
Entry point for Order Management MCP Server with FastMCP
Run with: python -m order_management_mcp
"""
from server_fastmcp import mcp, initialize_server

if __name__ == "__main__":
    # Initialize database
    initialize_server()
    
    # Run FastMCP server (stdio by default)
    mcp.run(transport="sse", port=8001)
