"""
Database models and initialization for Order Management System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path
from loguru import logger

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String)
    
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, shipped, delivered, cancelled
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price at time of order
    
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


def init_database(db_path: str):
    """
    Initialize database and create tables
    
    Args:
        db_path: Path to SQLite database file
    """
    # Create data directory if it doesn't exist
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    logger.info(f"Database initialized at {db_path}")
    
    return engine


def create_sample_data(engine):
    """Create sample data for testing"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if data already exists
        if session.query(Customer).count() > 0:
            logger.info("Sample data already exists, skipping creation")
            return
        
        # Create customers
        customers = [
            Customer(name="John Doe", email="john.doe@example.com"),
            Customer(name="Jane Smith", email="jane.smith@example.com"),
            Customer(name="Bob Johnson", email="bob.johnson@example.com"),
        ]
        session.add_all(customers)
        session.flush()
        
        # Create products
        products = [
            Product(name="Laptop", price=999.99, stock=50, category="Electronics"),
            Product(name="Mouse", price=29.99, stock=200, category="Electronics"),
            Product(name="Keyboard", price=79.99, stock=150, category="Electronics"),
            Product(name="Monitor", price=299.99, stock=75, category="Electronics"),
            Product(name="Desk Chair", price=199.99, stock=30, category="Furniture"),
            Product(name="Desk", price=399.99, stock=20, category="Furniture"),
        ]
        session.add_all(products)
        session.flush()
        
        # Create orders
        orders = [
            Order(customer_id=customers[0].id, status="delivered", total=1029.98),
            Order(customer_id=customers[0].id, status="shipped", total=299.99),
            Order(customer_id=customers[1].id, status="processing", total=679.97),
            Order(customer_id=customers[2].id, status="pending", total=599.98),
        ]
        session.add_all(orders)
        session.flush()
        
        # Create order items
        order_items = [
            # Order 1: Laptop + Mouse
            OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=1, price=999.99),
            OrderItem(order_id=orders[0].id, product_id=products[1].id, quantity=1, price=29.99),
            # Order 2: Monitor
            OrderItem(order_id=orders[1].id, product_id=products[3].id, quantity=1, price=299.99),
            # Order 3: Keyboard + Mouse + Monitor
            OrderItem(order_id=orders[2].id, product_id=products[2].id, quantity=1, price=79.99),
            OrderItem(order_id=orders[2].id, product_id=products[1].id, quantity=2, price=29.99),
            OrderItem(order_id=orders[2].id, product_id=products[3].id, quantity=2, price=299.99),
            # Order 4: Desk + Desk Chair
            OrderItem(order_id=orders[3].id, product_id=products[5].id, quantity=1, price=399.99),
            OrderItem(order_id=orders[3].id, product_id=products[4].id, quantity=1, price=199.99),
        ]
        session.add_all(order_items)
        
        session.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample data: {e}")
        raise
    finally:
        session.close()


def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()
