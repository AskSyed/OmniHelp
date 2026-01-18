"""
Order service - handles order-related database operations
"""
from typing import List, Optional
from loguru import logger
from app.models.order import OrderCreate, OrderResponse, CustomerCreate, CustomerResponse
from app.db.sqlite import get_db_connection


async def create_order(order_data: OrderCreate) -> OrderResponse:
    """Create a new order"""
    async with await get_db_connection() as db:
        # Insert order
        await db.execute("""
            INSERT INTO orders (order_id, customer_id, product_name, product_model, 
                              order_date, status, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_data.order_id,
            order_data.customer_id,
            order_data.product_name,
            order_data.product_model,
            order_data.order_date,
            order_data.status,
            order_data.total_amount
        ))
        
        # Insert order items
        for item in order_data.items:
            await db.execute("""
                INSERT INTO order_items (order_id, item_name, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (
                order_data.order_id,
                item.item_name,
                item.quantity,
                item.price
            ))
        
        await db.commit()
        
        # Fetch created order
        cursor = await db.execute("""
            SELECT * FROM orders WHERE order_id = ?
        """, (order_data.order_id,))
        row = await cursor.fetchone()
        
        return OrderResponse(**dict(row))


async def get_order(order_id: str) -> Optional[OrderResponse]:
    """Get order by ID"""
    async with await get_db_connection() as db:
        db.row_factory = lambda cursor, row: {
            col[0]: row[idx] for idx, col in enumerate(cursor.description)
        }
        cursor = await db.execute("""
            SELECT * FROM orders WHERE order_id = ?
        """, (order_id,))
        row = await cursor.fetchone()
        
        if row:
            return OrderResponse(**row)
        return None


async def get_orders_by_customer(customer_id: str) -> List[OrderResponse]:
    """Get all orders for a customer"""
    async with await get_db_connection() as db:
        db.row_factory = lambda cursor, row: {
            col[0]: row[idx] for idx, col in enumerate(cursor.description)
        }
        cursor = await db.execute("""
            SELECT * FROM orders WHERE customer_id = ? ORDER BY order_date DESC
        """, (customer_id,))
        rows = await cursor.fetchall()
        
        return [OrderResponse(**row) for row in rows]


async def create_customer(customer_data: CustomerCreate) -> CustomerResponse:
    """Create a new customer"""
    async with await get_db_connection() as db:
        await db.execute("""
            INSERT INTO customers (customer_id, name, email, phone)
            VALUES (?, ?, ?, ?)
        """, (
            customer_data.customer_id,
            customer_data.name,
            customer_data.email,
            customer_data.phone
        ))
        
        await db.commit()
        
        # Fetch created customer
        cursor = await db.execute("""
            SELECT * FROM customers WHERE customer_id = ?
        """, (customer_data.customer_id,))
        row = await cursor.fetchone()
        
        return CustomerResponse(**dict(row))


async def get_customer(customer_id: str) -> Optional[CustomerResponse]:
    """Get customer by ID"""
    async with await get_db_connection() as db:
        db.row_factory = lambda cursor, row: {
            col[0]: row[idx] for idx, col in enumerate(cursor.description)
        }
        cursor = await db.execute("""
            SELECT * FROM customers WHERE customer_id = ?
        """, (customer_id,))
        row = await cursor.fetchone()
        
        if row:
            return CustomerResponse(**row)
        return None

