from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from enum import Enum
from datetime import datetime
from pydantic import Field, ConfigDict

from app.schema.baseapp_schema import (
    BaseAppSchema
)
from app.config.constants import SchemaDescriptions


class DemoStatus(str, Enum):
    """Allowed demo status values."""
    CREATED = "created"
    UPDATING = "updating" 
    UPDATED = "updated"
    DELETING = "deleting"
    DELETED = "deleted"


class StatusSchema(BaseAppSchema):
    """Represents the current status of an entity."""

    status: DemoStatus = Field(..., description=SchemaDescriptions.DEMO_STATUS_DESCRIPTION)
    is_active: bool = True


class DemoCreateSchema(BaseAppSchema):
    """Schema for creating a new demo."""

    name: str = Field(..., min_length=1, max_length=200)
    logo: Optional[str] = Field(default=None, description="Logo image file")  # Will be set after file upload

class DemoUpdateSchema(BaseAppSchema):
    """Schema for updating an existing demo."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    logo: Optional[str] = Field(default=None, description="Logo image file")  # Will be set after file upload



class DemoStatusUpdateSchema(BaseAppSchema):
    """Schema for updating demo status and error messages."""

    status: DemoStatus = Field(..., description=SchemaDescriptions.DEMO_STATUS_DESCRIPTION)
    error_message: Optional[str] = Field(default=None, description="Technical error message for debugging")
    error_user_message: Optional[str] = Field(default=None, description="User-friendly error message for display")



class DemoIsActiveUpdateSchema(BaseAppSchema):
    """Schema for updating demo is_active status."""

    is_active: bool = Field(default=True, description="Whether the demo is active")


class DemoListParamsSchema(BaseAppSchema):
    """Schema for demo list API parameters."""

    # Pagination parameters
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=100, description="Number of items to return")
    
    # Ordering parameters
    order_by: str = Field(default="-created_at", description="Field to order by. Prefix with '-' for descending order")
    
    # Search parameter
    search: Optional[str] = Field(default=None, description="Search query string to filter results")
    
    # Filters parameter (list of filter dicts as JSON strings)
    filters: Optional[List[str]] = Field(default=None, description="List of filter dicts as JSON strings")


class DemoReadSchema(BaseAppSchema):
    """Schema for reading demo details."""

    demo_id: UUID = Field(..., description="Demo ID")
    name: str = Field(..., description="Demo name")
    logo: Optional[str] = Field(default=None, description="Logo image file")
    
    # Include fields from other schemas directly
    created_at: datetime = Field(..., description="Created at")
    updated_at: Optional[datetime] = Field(default=None, description="Updated at")
    deleted_at: Optional[datetime] = Field(default=None, description="Deleted at")
    deleted_by: Optional[UUID] = Field(default=None, description="Deleted by")
    status: DemoStatus = Field(..., description=SchemaDescriptions.DEMO_STATUS_DESCRIPTION)
    is_active: bool = Field(default=True, description="Whether the demo is active")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")