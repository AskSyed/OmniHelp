"""
Order management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger
from app.models.order import OrderCreate, OrderResponse, CustomerCreate, CustomerResponse
from app.services.order_service import (
    create_order,
    get_order,
    get_orders_by_customer,
    create_customer,
    get_customer
)

router = APIRouter()


@router.post("/", response_model=OrderResponse)
async def create_order_endpoint(order: OrderCreate):
    """
    Create a new order
    """
    try:
        result = await create_order(order)
        return result
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(order_id: str):
    """
    Get order by ID
    """
    try:
        order = await get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_id}", response_model=List[OrderResponse])
async def get_customer_orders(customer_id: str):
    """
    Get all orders for a customer
    """
    try:
        orders = await get_orders_by_customer(customer_id)
        return orders
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers", response_model=CustomerResponse)
async def create_customer_endpoint(customer: CustomerCreate):
    """
    Create a new customer
    """
    try:
        result = await create_customer(customer)
        return result
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer_endpoint(customer_id: str):
    """
    Get customer by ID
    """
    try:
        customer = await get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

