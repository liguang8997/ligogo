from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    data: T | None = None
    message: str = "success"


class ErrorResponse(BaseModel):
    code: int = 400
    data: None = None
    message: str = "error"
    error: str = ""


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class PaginatedData(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
