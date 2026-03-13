"""Base Pydantic models for API responses and pagination."""

from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List, Optional, Any
from datetime import datetime

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    success: bool = False
    message: str
    detail: Optional[Any] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = True
    data: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
