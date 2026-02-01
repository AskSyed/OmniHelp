"""
SQL Agent - Handles order management queries via MCP server
"""
import json
import re
from typing import TypedDict, List, Dict, Any
from langchain_openai import ChatOpenAI
from langsmith import traceable
from loguru import logger
from app.core.config import settings
from app.services.mcp_client_service import get_mcp_client


class SqlAgentState(TypedDict):
    """State for SQL agent"""
    query: str
    sql_query: str
    sql_results: List[Dict]
    formatted_context: str
    context: str  # Unified context field for orchestrator
    sources: List[str]  # Unified sources field
    error: str


@traceable(name="execute_sql_query")
async def execute_sql_query(state: dict) -> dict:
    """
    Main entry point for SQL agent - routes order management queries to MCP server
    
    Args:
        state: Current state with query
        
    Returns:
        Updated state with SQL results and formatted context
    """
    query = state["query"]
    
    try:
        logger.info(f"SQL Agent processing query: {query}")
        
        # Determine which MCP tool to use based on the query
        tool_name, tool_args = await determine_mcp_tool(query)
        
        logger.info(f"Using MCP tool: {tool_name} with args: {tool_args}")
        
        # Call the MCP server
        mcp_client = get_mcp_client()
        
        if not mcp_client.session:
            logger.warning("MCP client not connected, attempting to connect...")
            await mcp_client.connect()
        
        result_text = await mcp_client.call_tool(tool_name, tool_args)
        
        # Store results in state
        state["formatted_context"] = result_text
        state["context"] = result_text  # Unified field for generation agent
        state["sql_results"] = [{"result": result_text}]
        state["sources"] = ["Order Management System"]
        state["error"] = ""
        
        logger.info(f"SQL Agent completed successfully")
        
    except Exception as e:
        logger.error(f"Error in SQL agent: {e}")
        error_msg = f"I encountered an error accessing the order management system: {str(e)}"
        state["formatted_context"] = error_msg
        state["context"] = error_msg
        state["sql_results"] = []
        state["sources"] = []
        state["error"] = str(e)
    
    return state


async def determine_mcp_tool(query: str) -> tuple[str, Dict[str, Any]]:
    """
    Determine which MCP tool to use based on the query
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (tool_name, arguments)
    """
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    analysis_prompt = f"""
    Analyze the following query and determine which order management tool to use.
    
    Query: "{query}"
    
    Available tools:
    1. get_order_status - Get status of a specific order by ID
       Args: {{"order_id": <integer>}}
    
    2. get_customer_orders_by_name - Get all orders for a customer by name
       Args: {{"customer_name": "<string>"}}
    
    3. get_customer_orders - Get all orders (optionally for a specific customer ID)
       Args: {{"customer_id": <integer>}} or {{}}
    
    4. get_product_inventory - Get product inventory information
       Args: {{"product_name": "<string>"}} or {{}}
    
    5. get_order_details - Get detailed information about an order
       Args: {{"order_id": <integer>}}
    
    6. execute_sql - Execute a custom SQL SELECT query
       Args: {{"sql": "<SQL query>"}}
    
    Extract any relevant IDs, names, or parameters from the query.
    
    Respond ONLY with valid JSON in this format:
    {{
        "tool": "<tool_name>",
        "arguments": {{...}}
    }}
    """
    
    try:
        response = llm.invoke(analysis_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        logger.debug(f"Tool determination response: {response_text}")
        
        # Parse JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()
        
        result = json.loads(json_str)
        tool_name = result.get("tool", "execute_sql")
        arguments = result.get("arguments", {})
        
        return tool_name, arguments
        
    except Exception as e:
        logger.error(f"Error determining MCP tool: {e}")
        # Fallback: try to extract order ID from query
        order_id_match = re.search(r'#?(\d+)', query)
        if order_id_match and ("order" in query.lower() or "status" in query.lower()):
            return "get_order_status", {"order_id": int(order_id_match.group(1))}
        
        # Default to listing all orders
        return "get_customer_orders", {}


@traceable(name="translate_query_to_sql")
async def translate_query_to_sql(query: str) -> str:
    """
    Translate natural language query to SQL using LLM
    
    Args:
        query: Natural language query
        
    Returns:
        SQL query string
    """
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    schema_info = """
    Database Schema:
    
    customers (id INTEGER, name TEXT, email TEXT, created_at DATETIME)
    products (id INTEGER, name TEXT, price REAL, stock INTEGER, category TEXT)
    orders (id INTEGER, customer_id INTEGER, status TEXT, total REAL, created_at DATETIME, updated_at DATETIME)
    order_items (id INTEGER, order_id INTEGER, product_id INTEGER, quantity INTEGER, price REAL)
    
    Relationships:
    - orders.customer_id → customers.id
    - order_items.order_id → orders.id
    - order_items.product_id → products.id
    """
    
    sql_prompt = f"""
    Convert the following natural language query to SQL.
    
    {schema_info}
    
    Query: "{query}"
    
    Generate a SELECT query only. Do not include any explanations, just the SQL query.
    """
    
    try:
        response = llm.invoke(sql_prompt)
        sql = response.content if hasattr(response, "content") else str(response)
        
        # Clean up the SQL
        sql = sql.strip()
        # Remove markdown code blocks if present
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        logger.info(f"Generated SQL: {sql}")
        return sql
        
    except Exception as e:
        logger.error(f"Error translating query to SQL: {e}")
        raise


def validate_sql(sql: str) -> bool:
    """
    Validate SQL query for safety
    
    Args:
        sql: SQL query string
        
    Returns:
        True if safe, False otherwise
    """
    sql_lower = sql.lower().strip()
    
    # Check for dangerous operations
    dangerous_keywords = ["drop", "truncate", "alter", "create", "grant", "revoke", "delete", "insert", "update"]
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', sql_lower):
            logger.warning(f"Blocked dangerous SQL keyword: {keyword}")
            return False
    
    # Only allow SELECT queries
    if not sql_lower.startswith("select"):
        logger.warning("Only SELECT queries are allowed")
        return False
    
    return True


def format_sql_results(results: List[Dict[str, Any]]) -> str:
    """
    Format SQL results into human-readable text
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Formatted text
    """
    if not results:
        return "No results found."
    
    output = "Results:\n\n"
    
    # Format as a table
    if results:
        headers = list(results[0].keys())
        
        # Header row
        output += " | ".join(headers) + "\n"
        output += "-" * (len(" | ".join(headers)) + 10) + "\n"
        
        # Data rows
        for row in results:
            output += " | ".join(str(row.get(h, "")) for h in headers) + "\n"
    
    return output
