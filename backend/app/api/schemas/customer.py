from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    stakeholders: Optional[str] = Field(None, description="Key stakeholders at the customer")
    team: Optional[str] = Field(None, description="Team members working with this customer")
    description: Optional[str] = Field(None, description="Customer strategy and notes")
    related_products: Optional[str] = Field(None, description="Products related to this customer")


class CustomerCreate(CustomerBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Acme Corporation",
                    "stakeholders": "John Doe (CTO), Jane Smith (PM)",
                    "team": "Alice, Bob",
                    "description": "Enterprise customer focused on cloud migration",
                    "related_products": "Platform API, Analytics Dashboard"
                }
            ]
        }
    )


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    stakeholders: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None
    related_products: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "Updated customer strategy notes"
                }
            ]
        }
    )


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    customers: list[CustomerResponse]
    total: int
    skip: int
    limit: int

