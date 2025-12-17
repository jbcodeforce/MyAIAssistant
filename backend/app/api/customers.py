from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)


router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new customer.
    """
    return await crud.create_customer(db=db, customer=customer)


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of customers with pagination.
    """
    customers, total = await crud.get_customers(db=db, skip=skip, limit=limit)
    return CustomerListResponse(customers=customers, total=total, skip=skip, limit=limit)


@router.get("/search/by-name", response_model=CustomerResponse)
async def get_customer_by_name(
    name: str = Query(..., description="Customer name to search for (case-insensitive)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find a customer by name (case-insensitive exact match).
    """
    customer = await crud.get_customer_by_name(db=db, name=name)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific customer by ID.
    """
    customer = await crud.get_customer(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a customer.
    """
    customer = await crud.update_customer(
        db=db, customer_id=customer_id, customer_update=customer_update
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a customer.
    """
    success = await crud.delete_customer(db=db, customer_id=customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None

