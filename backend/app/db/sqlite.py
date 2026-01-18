"""
SQLite database initialization and utilities
"""
import aiosqlite
from pathlib import Path
from loguru import logger
from app.core.config import settings


async def get_db_connection():
    """Get async SQLite database connection"""
    db_path = Path(settings.SQLITE_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return await aiosqlite.connect(str(db_path))


async def init_sqlite_db():
    """Initialize SQLite database with required tables"""
    async with await get_db_connection() as db:
        # Orders table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_model TEXT,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                total_amount REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Order items table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)
        
        # Customers table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        logger.info("SQLite database initialized successfully")


async def close_db_connection(db):
    """Close database connection"""
    await db.close()

