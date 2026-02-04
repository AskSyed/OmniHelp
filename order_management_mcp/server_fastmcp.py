"""
Order Management MCP Server using FastMCP
Simplified implementation with stdio transport
"""
import re
from typing import Any, Dict, List
from sqlalchemy import text
from loguru import logger
import sys

from fastmcp import FastMCP
from config import settings
from database import init_database, create_sample_data, get_session

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Initialize FastMCP server
mcp = FastMCP("Order Management")

# Initialize database
engine = None


def validate_sql(sql: str) -> bool:
    """Validate SQL query for safety"""
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
    """Execute SQL query and return results"""
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


# Define MCP Tools using FastMCP decorators

@mcp.tool()
def get_order_status(order_id: int) -> str:
    """
    Get the status of a specific order by order ID
    
    Args:
        order_id: The order ID to check
    """
    try:
        sql = """
            SELECT o.id, o.status, o.total, o.created_at, o.updated_at,
                   c.name as customer_name, c.email as customer_email
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = :order_id
        """
        results = execute_query(sql, {"order_id": order_id})
        
        if not results:
            return f"No order found with ID {order_id}"
        
        order = results[0]
        return (f"Order #{order['id']}\n"
                f"Status: {order['status']}\n"
                f"Total: ${order['total']}\n"
                f"Customer: {order['customer_name']} ({order['customer_email']})\n"
                f"Created: {order['created_at']}\n"
                f"Updated: {order['updated_at']}")
    
    except Exception as e:
        logger.error(f"Error in get_order_status: {e}")
        return f"Error getting order status: {str(e)}"


@mcp.tool()
def get_customer_orders(customer_id: int = None) -> str:
    """
    Get all orders for a specific customer, or all orders if no customer_id provided
    
    Args:
        customer_id: Optional customer ID to filter by
    """
    try:
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
            return "No orders found"
        
        output = "Orders:\n"
        for order in results:
            output += f"- Order #{order['id']}: {order['status']} - ${order['total']} ({order['customer_name']})\n"
        
        return output
    
    except Exception as e:
        logger.error(f"Error in get_customer_orders: {e}")
        return f"Error getting customer orders: {str(e)}"


@mcp.tool()
def get_customer_orders_by_name(customer_name: str) -> str:
    """
    Get all orders for a customer by name (supports partial matching)
    
    Args:
        customer_name: The customer name to search for
    """
    try:
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
            return f"No orders found for customer matching '{customer_name}'"
        
        output = f"Orders for {results[0]['customer_name']} ({results[0]['customer_email']}):\n"
        for order in results:
            output += f"- Order #{order['id']}: {order['status']} - ${order['total']} (Created: {order['created_at']})\n"
        
        return output
    
    except Exception as e:
        logger.error(f"Error in get_customer_orders_by_name: {e}")
        return f"Error getting orders by name: {str(e)}"


@mcp.tool()
def get_product_inventory(product_name: str = None) -> str:
    """
    Get product inventory information
    
    Args:
        product_name: Optional product name to filter by (supports partial matching)
    """
    try:
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
            return "No products found"
        
        output = "Product Inventory:\n"
        for product in results:
            output += f"- {product['name']} (#{product['id']}): ${product['price']} - {product['stock']} in stock [{product['category']}]\n"
        
        return output
    
    except Exception as e:
        logger.error(f"Error in get_product_inventory: {e}")
        return f"Error getting product inventory: {str(e)}"


@mcp.tool()
def get_order_details(order_id: int) -> str:
    """
    Get detailed information about an order including items and customer
    
    Args:
        order_id: The order ID to get details for
    """
    try:
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
            return f"No order found with ID {order_id}"
        
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
        
        return output
    
    except Exception as e:
        logger.error(f"Error in get_order_details: {e}")
        return f"Error getting order details: {str(e)}"


@mcp.tool()
def execute_sql(sql: str) -> str:
    """
    Execute a custom SQL SELECT query (read-only)
    
    Args:
        sql: The SQL query to execute (SELECT only)
    """
    try:
        results = execute_query(sql)
        
        if not results:
            return "Query executed successfully. No results returned."
        
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
        
        return output
    
    except Exception as e:
        logger.error(f"Error in execute_sql: {e}")
        return f"Error executing SQL: {str(e)}"


# Server initialization and startup
def initialize_server():
    """Initialize database"""
    global engine
    
    logger.info("Initializing Order Management MCP Server")
    logger.info(f"Database path: {settings.ORDER_DB_PATH}")
    logger.info(f"Write operations: {'enabled' if settings.ALLOW_WRITE_OPERATIONS else 'disabled'}")
    
    # Initialize database
    engine = init_database(settings.ORDER_DB_PATH)
    create_sample_data(engine)
    
    logger.info("MCP Server initialized successfully")


if __name__ == "__main__":
    # Initialize database
    initialize_server()
    
    # Run FastMCP server
    mcp.run(transport="sse", port=8001)
