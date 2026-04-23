"""
Standard API Response Models - KIRO2 Platform

Tutarli API yanitlari icin Pydantic modelleri.
Tum endpoint'lerde yeniden kullanilabilir.

Usage:
    from api.schemas.error_responses import (
        STANDARD_ERROR_RESPONSES,
        AUTH_RESPONSES,
        APIResponse,
        PaginatedResponse,
        create_success_response,
    )

    @router.get("/items/{id}", responses={**CRUD_RESPONSES})
    async def get_item(id: int):
        return create_success_response(data=item, message="Item retrieved")
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for response data
T = TypeVar("T")


# =============================================================================
# Standard Success Response Wrapper
# =============================================================================


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.

    Provides consistent structure for all API responses:
    - success: Whether the operation succeeded
    - message: Human-readable message
    - data: The actual response payload
    - meta: Optional metadata (request_id, timestamp, etc.)

    Usage:
        return APIResponse(
            success=True,
            message="Items retrieved successfully",
            data=items,
            meta={"total": 100}
        )
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(default="", description="Human-readable message")
    data: T | None = Field(default=None, description="Response payload")
    meta: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": 1, "name": "Example"},
                "meta": {"request_id": "abc-123", "timestamp": "2024-01-15T10:00:00Z"},
            }
        }
    }


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated API response wrapper.

    Extends APIResponse with pagination support.

    Usage:
        return PaginatedResponse(
            success=True,
            data=items,
            pagination=PaginationMeta(page=1, page_size=20, total_items=100, ...)
        )
    """

    success: bool = Field(default=True, description="Whether the operation succeeded")
    message: str = Field(default="", description="Human-readable message")
    data: list[T] = Field(default_factory=list, description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    meta: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Items retrieved successfully",
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False,
                },
                "meta": None,
            }
        }
    }


# =============================================================================
# Helper Functions
# =============================================================================


def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a standard success response.

    Args:
        data: The response payload
        message: Human-readable message
        meta: Optional metadata

    Returns:
        Standard success response dict

    Usage:
        return create_success_response(data=user, message="User created")
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response["meta"] = meta
    return response


def create_error_response(
    message: str,
    error_code: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a standard error response.

    Args:
        message: Error message
        error_code: Optional error code for programmatic handling
        details: Optional error details

    Returns:
        Standard error response dict

    Usage:
        return create_error_response(
            message="User not found",
            error_code="USER_NOT_FOUND",
            details={"user_id": 123}
        )
    """
    response = {
        "success": False,
        "message": message,
        "data": None,
    }
    meta = {}
    if error_code:
        meta["error_code"] = error_code
    if details:
        meta["details"] = details
    if meta:
        response["meta"] = meta
    return response


def create_paginated_response(
    data: list[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Items retrieved successfully",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a standard paginated response.

    Args:
        data: List of items for current page
        page: Current page number (1-indexed)
        page_size: Items per page
        total_items: Total number of items
        message: Human-readable message
        meta: Optional additional metadata

    Returns:
        Standard paginated response dict

    Usage:
        return create_paginated_response(
            data=users,
            page=1,
            page_size=20,
            total_items=100,
        )
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0

    response = {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
    if meta:
        response["meta"] = meta
    return response


# =============================================================================
# Error Response Models
# =============================================================================


class ValidationErrorItem(BaseModel):
    """Dogrulama hatasi detayi"""

    loc: list[str] = Field(..., description="Hata konumu (field path)")
    msg: str = Field(..., description="Hata mesaji")
    type: str = Field(..., description="Hata tipi")


class ErrorResponse(BaseModel):
    """Genel hata yaniti (400 Bad Request)"""

    detail: str = Field(..., description="Hata mesaji")

    model_config = {
        "json_schema_extra": {"example": {"detail": "Gecersiz istek parametresi"}}
    }


class ValidationErrorResponse(BaseModel):
    """422 Dogrulama hatasi yaniti"""

    detail: list[ValidationErrorItem] = Field(..., description="Dogrulama hatalari")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email",
                    }
                ]
            }
        }
    }


class UnauthorizedResponse(BaseModel):
    """401 Yetkilendirme hatasi"""

    detail: str = Field(default="Gecersiz veya suresi dolmus token")

    model_config = {
        "json_schema_extra": {
            "example": {"detail": "Gecersiz veya suresi dolmus token"}
        }
    }


class ForbiddenResponse(BaseModel):
    """403 Erisim engellendi"""

    detail: str = Field(default="Bu islem icin yetkiniz yok")

    model_config = {
        "json_schema_extra": {"example": {"detail": "Bu islem icin yetkiniz yok"}}
    }


class NotFoundResponse(BaseModel):
    """404 Bulunamadi"""

    detail: str = Field(default="Kaynak bulunamadi")

    model_config = {"json_schema_extra": {"example": {"detail": "Kaynak bulunamadi"}}}


class ConflictResponse(BaseModel):
    """409 Conflict - Kaynak zaten mevcut"""

    detail: str = Field(default="Bu kaynak zaten mevcut")

    model_config = {
        "json_schema_extra": {"example": {"detail": "Bu e-posta adresi zaten kayitli"}}
    }


class RateLimitResponse(BaseModel):
    """429 Rate limit asildi"""

    detail: str = Field(default="Istek limiti asildi")
    retry_after: int | None = Field(None, description="Yeniden deneme suresi (saniye)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Istek limiti asildi, lutfen bekleyin",
                "retry_after": 60,
            }
        }
    }


class InternalServerErrorResponse(BaseModel):
    """500 Sunucu hatasi"""

    detail: str = Field(default="Beklenmeyen bir hata olustu")

    model_config = {
        "json_schema_extra": {
            "example": {"detail": "Beklenmeyen bir hata olustu, lutfen tekrar deneyin"}
        }
    }


# Pre-defined responses dict for reuse in endpoints
STANDARD_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Gecersiz istek"},
    401: {"model": UnauthorizedResponse, "description": "Yetkilendirme hatasi"},
    403: {"model": ForbiddenResponse, "description": "Erisim engellendi"},
    404: {"model": NotFoundResponse, "description": "Kaynak bulunamadi"},
    409: {"model": ConflictResponse, "description": "Kaynak zaten mevcut"},
    422: {"model": ValidationErrorResponse, "description": "Dogrulama hatasi"},
    429: {"model": RateLimitResponse, "description": "Istek limiti asildi"},
    500: {"model": InternalServerErrorResponse, "description": "Sunucu hatasi"},
}

# Common response combinations for different endpoint types
AUTH_RESPONSES = {
    401: STANDARD_ERROR_RESPONSES[401],
    403: STANDARD_ERROR_RESPONSES[403],
}

CRUD_RESPONSES = {
    **AUTH_RESPONSES,
    404: STANDARD_ERROR_RESPONSES[404],
    422: STANDARD_ERROR_RESPONSES[422],
}

CREATE_RESPONSES = {
    **AUTH_RESPONSES,
    409: STANDARD_ERROR_RESPONSES[409],
    422: STANDARD_ERROR_RESPONSES[422],
}

LIST_RESPONSES = {
    **AUTH_RESPONSES,
    422: STANDARD_ERROR_RESPONSES[422],
}
