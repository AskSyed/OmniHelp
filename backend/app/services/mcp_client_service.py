"""
MCP Client Service for communicating with Order Management MCP Server via SSE
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from loguru import logger
import httpx

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError:
    logger.warning("MCP client library not installed. MCP functionality will be disabled.")
    ClientSession = None
    sse_client = None

from app.core.config import settings


class MCPClientService:
    """Service for interacting with MCP servers via SSE"""
    
    def __init__(self):
        self.session: Optional[Any] = None
        self.server_url: Optional[str] = None
        self._sse_context = None
        self._read_stream = None
        self._write_stream = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the MCP client connection"""
        if not settings.MCP_SERVER_ENABLED:
            logger.info("MCP server integration is disabled")
            return
        
        if ClientSession is None:
            logger.warning("MCP client not available. Install 'mcp' package.")
            return
        
        try:
            # Set up SSE endpoint URL
            self.server_url = f"http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}/sse"
            
            logger.info(f"MCP client initialized with SSE endpoint: {self.server_url}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing MCP client: {e}")
            self._initialized = False
    
    async def connect(self):
        """Connect to the MCP server via SSE"""
        if not self._initialized or not settings.MCP_SERVER_ENABLED:
            return
        
        try:
            # Create SSE client connection
            self._sse_context = sse_client(self.server_url)
            self._read_stream, self._write_stream = await self._sse_context.__aenter__()
            
            # Create session
            self.session = ClientSession(self._read_stream, self._write_stream)
            await self.session.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            logger.info(f"Connected to MCP server via SSE at {self.server_url}")
            
        except Exception as e:
            logger.error(f"Error connecting to MCP server at {self.server_url}")
            logger.error(f"Make sure the MCP server is running: python -m order_management_mcp.server_fastmcp")
            logger.error(f"Error details: {e}")
            self.session = None
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None
            
            if self._sse_context:
                await self._sse_context.__aexit__(None, None, None)
                self._sse_context = None
                self._read_stream = None
                self._write_stream = None
            
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server
        
        Returns:
            List of tool definitions
        """
        if not self.session:
            logger.warning("MCP session not initialized")
            return []
        
        try:
            tools_response = await self.session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in tools_response.tools
            ]
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool response as string
        """
        if not self.session:
            logger.warning("MCP session not initialized")
            return "Error: MCP server not connected"
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text content from response
            if result and hasattr(result, 'content') and result.content:
                # Concatenate all text content
                text_parts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_parts.append(content.text)
                
                response = "\n".join(text_parts)
                logger.info(f"MCP tool response: {response[:200]}...")
                return response
            
            return "No response from MCP server"
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"
    
    async def check_connection(self) -> bool:
        """
        Check if the MCP server connection is healthy
        
        Returns:
            True if connected, False otherwise
        """
        if not self.session:
            return False
        
        try:
            # Try to list tools as a health check
            await self.list_tools()
            return True
        except Exception as e:
            logger.error(f"MCP connection check failed: {e}")
            return False
    
    @asynccontextmanager
    async def get_session(self):
        """
        Context manager for MCP session
        
        Usage:
            async with mcp_client.get_session():
                result = await mcp_client.call_tool("tool_name", {...})
        """
        if not self.session:
            await self.connect()
        
        try:
            yield self
        finally:
            # Keep connection alive for reuse
            pass


# Global MCP client instance
_mcp_client: Optional[MCPClientService] = None


def get_mcp_client() -> MCPClientService:
    """
    Get the global MCP client instance
    
    Returns:
        MCPClientService instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClientService()
    return _mcp_client


async def initialize_mcp_client():
    """Initialize the global MCP client"""
    client = get_mcp_client()
    await client.initialize()
    if client._initialized:
        await client.connect()


async def shutdown_mcp_client():
    """Shutdown the global MCP client"""
    client = get_mcp_client()
    await client.disconnect()
