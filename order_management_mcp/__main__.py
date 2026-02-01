"""
Entry point for Order Management MCP Server
Run with: python -m order_management_mcp
"""
import asyncio
from server import main

if __name__ == "__main__":
    asyncio.run(main())
