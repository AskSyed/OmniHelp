# Order Management MCP Server

An MCP (Model Context Protocol) server that exposes order management system functionality through a standardized interface.

## Overview

This server provides tools to query and interact with an order management database, including:
- Order status tracking
- Customer order history
- Product inventory management
- Custom SQL queries (read-only by default)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

## Running the Server

Run the MCP server using:

```bash
python -m order_management_mcp
```

Or directly:

```bash
python server.py
```

The server will:
1. Initialize a SQLite database at `./data/orders.db`
2. Create sample data if the database is empty
3. Start the MCP server on stdio (standard MCP protocol)

## Database Schema

### Tables

- **customers**: Customer information (id, name, email, created_at)
- **products**: Product catalog (id, name, price, stock, category)
- **orders**: Order records (id, customer_id, status, total, created_at, updated_at)
- **order_items**: Line items for orders (id, order_id, product_id, quantity, price)

### Sample Data

The server automatically creates sample data including:
- 3 customers
- 6 products (laptops, monitors, keyboards, etc.)
- 4 orders with various statuses
- Multiple order items per order

## Available Tools

### 1. get_order_status
Get the status of a specific order by ID.

**Parameters:**
- `order_id` (integer, required): The order ID to check

**Example:**
```json
{
  "order_id": 1
}
```

### 2. get_customer_orders
Get all orders for a specific customer.

**Parameters:**
- `customer_id` (integer, optional): The customer ID

**Example:**
```json
{
  "customer_id": 1
}
```

### 3. get_customer_orders_by_name
Get all orders for a customer by name (supports partial matching).

**Parameters:**
- `customer_name` (string, required): The customer name to search for

**Example:**
```json
{
  "customer_name": "John"
}
```

### 4. get_product_inventory
Get product inventory information.

**Parameters:**
- `product_name` (string, optional): Optional product name to filter by

**Example:**
```json
{
  "product_name": "Laptop"
}
```

### 5. get_order_details
Get detailed information about an order including items and customer.

**Parameters:**
- `order_id` (integer, required): The order ID to get details for

**Example:**
```json
{
  "order_id": 1
}
```

### 6. execute_sql
Execute a custom SQL SELECT query (read-only).

**Parameters:**
- `sql` (string, required): The SQL query to execute

**Example:**
```json
{
  "sql": "SELECT * FROM products WHERE stock > 100"
}
```

## Security

- **Read-only by default**: Only SELECT queries are allowed unless `ALLOW_WRITE_OPERATIONS=true`
- **SQL injection protection**: Queries are validated before execution
- **Dangerous operations blocked**: DROP, TRUNCATE, ALTER, etc. are prohibited

## Configuration

Environment variables (in `.env` file):

```bash
# Server settings
MCP_PORT=8001
MCP_HOST=localhost

# Database settings
ORDER_DB_PATH=./data/orders.db

# Security settings
ALLOW_WRITE_OPERATIONS=false  # Enable write operations (UPDATE, INSERT, DELETE)
```

## Example Queries

### Check order status
```
"What is the status of order #1?"
```

### Customer order history
```
"Show me all orders for John Doe"
```

### Inventory check
```
"How many laptops do we have in stock?"
```

### Custom query
```
"Show me all orders with status 'shipped'"
```

## Integration

This MCP server is designed to work with the OmniHelp RAG application backend, which acts as an MCP client. The backend routes order-related queries to this server through the SQL Agent.

## Troubleshooting

### Database not found
The database is created automatically on first run. If you see errors, ensure the `./data/` directory is writable.

### Port already in use
If running as a network server (future enhancement), change the `MCP_PORT` in `.env`.

### Permission errors
Ensure the process has write permissions to the `./data/` directory for database creation.

## Development

To modify the database schema:
1. Edit `database.py`
2. Delete the existing `./data/orders.db` file
3. Restart the server to recreate the database

To add new tools:
1. Add tool definition in `list_tools()` function
2. Add handler in `call_tool()` function
3. Update this README with the new tool documentation
