"""
Order data models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OrderItem(BaseModel):
    """Order item model"""
    item_name: str
    quantity: int
    price: float


class OrderCreate(BaseModel):
    """Order creation model"""
    order_id: str
    customer_id: str
    product_name: str
    product_model: Optional[str] = None
    order_date: str
    status: str
    total_amount: float
    items: List[OrderItem] = []


class OrderResponse(BaseModel):
    """Order response model"""
    id: int
    order_id: str
    customer_id: str
    product_name: str
    product_model: Optional[str]
    order_date: str
    status: str
    total_amount: Optional[float]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    """Customer creation model"""
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(BaseModel):
    """Customer response model"""
    id: int
    customer_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

