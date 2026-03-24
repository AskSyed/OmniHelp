"""
Order Management MCP Server
"""
import asyncio
import re
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from sqlalchemy import text
from loguru import logger
import sys

from config import settings
from database import init_database, create_sample_data, get_session

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Initialize server
app = Server("order-management")

# Initialize database
engine = None


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
    dangerous_keywords = ["drop", "truncate", "alter", "create", "grant", "revoke"]
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', sql_lower):
            logger.warning(f"Blocked dangerous SQL keyword: {keyword}")
            return False
    
    # If write operations are disabled, only allow SELECT
    if not settings.ALLOW_WRITE_OPERATIONS:
        if not sql_lower.startswith("select"):
            logger.warning("Write operations are disabled")
            return False
    
    return True


def execute_query(sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Execute SQL query and return results
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        List of result dictionaries
    """
    if not validate_sql(sql):
        raise ValueError("SQL query failed safety validation")
    
    session = get_session(engine)
    try:
        result = session.execute(text(sql), params or {})
        
        # For SELECT queries, fetch results
        if sql.lower().strip().startswith("select"):
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        else:
            # For other queries, commit and return affected rows
            session.commit()
            return [{"affected_rows": result.rowcount}]
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        session.close()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="get_order_status",
            description="Get the status of a specific order by order ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to check"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="get_customer_orders",
            description="Get all orders for a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The customer ID"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_customer_orders_by_name",
            description="Get all orders for a customer by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The customer name to search for"
                    }
                },
                "required": ["customer_name"]
            }
        ),
        Tool(
            name="get_product_inventory",
            description="Get product inventory information",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Optional product name to filter by"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="execute_sql",
            description="Execute a custom SQL SELECT query (read-only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute (SELECT only)"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="get_order_details",
            description="Get detailed information about an order including items and customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to get details for"
                    }
                },
                "required": ["order_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "get_order_status":
            order_id = arguments["order_id"]
            sql = """
                SELECT o.id, o.status, o.total, o.created_at, o.updated_at,
                       c.name as customer_name, c.email as customer_email
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = :order_id
            """
            results = execute_query(sql, {"order_id": order_id})
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No order found with ID {order_id}"
                )]
            
            return [TextContent(
                type="text",
                text=f"Order #{results[0]['id']}\n"
                     f"Status: {results[0]['status']}\n"
                     f"Total: ${results[0]['total']}\n"
                     f"Customer: {results[0]['customer_name']} ({results[0]['customer_email']})\n"
                     f"Created: {results[0]['created_at']}\n"
                     f"Updated: {results[0]['updated_at']}"
            )]
        
        elif name == "get_customer_orders":
            customer_id = arguments.get("customer_id")
            
            if customer_id:
                sql = """
                    SELECT o.id, o.status, o.total, o.created_at,
                           c.name as customer_name
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE c.id = :customer_id
                    ORDER BY o.created_at DESC
                """
                results = execute_query(sql, {"customer_id": customer_id})
            else:
                sql = """
                    SELECT o.id, o.status, o.total, o.created_at,
                           c.name as customer_name
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    ORDER BY o.created_at DESC
                """
                results = execute_query(sql)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No orders found"
                )]
            
            output = "Orders:\n"
            for order in results:
                output += f"- Order #{order['id']}: {order['status']} - ${order['total']} ({order['customer_name']})\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "get_customer_orders_by_name":
            customer_name = arguments["customer_name"]
            sql = """
                SELECT o.id, o.status, o.total, o.created_at,
                       c.name as customer_name, c.email as customer_email
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE c.name LIKE :customer_name
                ORDER BY o.created_at DESC
            """
            results = execute_query(sql, {"customer_name": f"%{customer_name}%"})
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No orders found for customer matching '{customer_name}'"
                )]
            
            output = f"Orders for {results[0]['customer_name']} ({results[0]['customer_email']}):\n"
            for order in results:
                output += f"- Order #{order['id']}: {order['status']} - ${order['total']} (Created: {order['created_at']})\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "get_product_inventory":
            product_name = arguments.get("product_name")
            
            if product_name:
                sql = """
                    SELECT id, name, price, stock, category
                    FROM products
                    WHERE name LIKE :product_name
                    ORDER BY name
                """
                results = execute_query(sql, {"product_name": f"%{product_name}%"})
            else:
                sql = """
                    SELECT id, name, price, stock, category
                    FROM products
                    ORDER BY category, name
                """
                results = execute_query(sql)
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No products found"
                )]
            
            output = "Product Inventory:\n"
            for product in results:
                output += f"- {product['name']} (#{product['id']}): ${product['price']} - {product['stock']} in stock [{product['category']}]\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "execute_sql":
            sql = arguments["sql"]
            results = execute_query(sql)
            
            if not results:
                return [TextContent(type="text", text="Query executed successfully. No results returned.")]
            
            # Format results as a table-like string
            output = "Results:\n"
            if results:
                # Header
                headers = list(results[0].keys())
                output += " | ".join(headers) + "\n"
                output += "-" * (len(" | ".join(headers))) + "\n"
                
                # Rows
                for row in results:
                    output += " | ".join(str(row[h]) for h in headers) + "\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "get_order_details":
            order_id = arguments["order_id"]
            
            # Get order info
            order_sql = """
                SELECT o.id, o.status, o.total, o.created_at, o.updated_at,
                       c.name as customer_name, c.email as customer_email
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = :order_id
            """
            order_results = execute_query(order_sql, {"order_id": order_id})
            
            if not order_results:
                return [TextContent(type="text", text=f"No order found with ID {order_id}")]
            
            order = order_results[0]
            
            # Get order items
            items_sql = """
                SELECT oi.quantity, oi.price, p.name as product_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = :order_id
            """
            items_results = execute_query(items_sql, {"order_id": order_id})
            
            output = f"Order #{order['id']} Details\n"
            output += "=" * 50 + "\n"
            output += f"Customer: {order['customer_name']} ({order['customer_email']})\n"
            output += f"Status: {order['status']}\n"
            output += f"Total: ${order['total']}\n"
            output += f"Created: {order['created_at']}\n"
            output += f"Updated: {order['updated_at']}\n\n"
            output += "Items:\n"
            for item in items_results:
                output += f"- {item['product_name']}: {item['quantity']} x ${item['price']} = ${item['quantity'] * item['price']}\n"
            
            return [TextContent(type="text", text=output)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing tool {name}: {str(e)}"
        )]


async def main():
    """Main entry point"""
    global engine
    
    logger.info("Starting Order Management MCP Server")
    logger.info(f"Database path: {settings.ORDER_DB_PATH}")
    logger.info(f"Write operations: {'enabled' if settings.ALLOW_WRITE_OPERATIONS else 'disabled'}")
    
    # Initialize database
    engine = init_database(settings.ORDER_DB_PATH)
    create_sample_data(engine)
    
    logger.info("MCP Server initialized successfully")
    
    # Run server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
