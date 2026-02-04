"""
Unified API Response Models
Standardized response structures for consistent API communication
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from fastapi import status
from pydantic import BaseModel, ConfigDict, Field, computed_field

T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Response status types"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorType(str, Enum):
    """Error classification types"""

    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    DATABASE_ERROR = "database_error"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    MAINTENANCE_ERROR = "maintenance_error"


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    page: int = Field(description="Current page number", ge=1)
    page_size: int = Field(description="Items per page", ge=1, le=1000)
    total_items: int = Field(description="Total number of items", ge=0)

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages based on total_items and page_size"""
        if self.total_items == 0:
            return 0
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @computed_field
    @property
    def has_next(self) -> bool:
        """Whether there is a next page"""
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        """Whether there is a previous page"""
        return self.page > 1


class ResponseMeta(BaseModel):
    """Response metadata"""

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
    request_id: str | None = Field(None, description="Unique request identifier")
    api_version: str = Field(default="v1", description="API version")
    processing_time_ms: float | None = Field(
        None, description="Processing time in milliseconds"
    )
    server_info: dict[str, Any] | None = Field(None, description="Server information")


class ErrorDetail(BaseModel):
    """Detailed error information"""

    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    field: str | None = Field(None, description="Field name for validation errors")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class ValidationErrorDetail(ErrorDetail):
    """Validation-specific error details"""

    field: str = Field(description="Field that failed validation")
    rejected_value: Any = Field(description="Value that was rejected")
    constraint: str | None = Field(
        None, description="Validation constraint that failed"
    )


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response format
    Generic response container that can hold any data type
    """

    success: bool = Field(description="Whether the request was successful")
    status: ResponseStatus = Field(description="Response status")
    message: str = Field(description="Human-readable status message")
    data: T | None = Field(None, description="Response data")
    errors: list[ErrorDetail] | None = Field(None, description="List of errors")
    meta: ResponseMeta = Field(
        default_factory=ResponseMeta, description="Response metadata"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "success": True,
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"example": "data"},
                "errors": None,
                "meta": {
                    "timestamp": "2025-01-25T10:30:00Z",
                    "request_id": "req_123456789",
                    "api_version": "v1",
                    "processing_time_ms": 150.5,
                },
            }
        },
    )


class PaginatedResponse(APIResponse[T]):
    """
    Paginated API response format
    Extends APIResponse with pagination metadata
    """

    pagination: PaginationMeta | None = Field(None, description="Pagination metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "status": "success",
                "message": "Data retrieved successfully",
                "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_previous": False,
                },
                "meta": {"timestamp": "2025-01-25T10:30:00Z", "api_version": "v1"},
            }
        }
    )


class SuccessResponse(APIResponse[T]):
    """Success response with predefined success status"""

    success: Literal[True] = Field(default=True)
    status: Literal[ResponseStatus.SUCCESS] = Field(default=ResponseStatus.SUCCESS)


class ErrorResponse(APIResponse[None]):
    """Error response with predefined error status"""

    success: Literal[False] = Field(default=False)
    status: Literal[ResponseStatus.ERROR] = Field(default=ResponseStatus.ERROR)
    data: Literal[None] = Field(default=None)
    errors: list[ErrorDetail] = Field(description="List of errors")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""

    errors: list[ValidationErrorDetail] = Field(description="Validation errors")


# Pre-defined response types for common scenarios
class EmptySuccessResponse(SuccessResponse[None]):
    """Success response with no data"""

    data: Literal[None] = Field(default=None)


class MessageResponse(SuccessResponse[dict[str, str]]):
    """Success response with only a message"""


class HealthCheckResponse(SuccessResponse[dict[str, Any]]):
    """Health check response format"""


class ListResponse(SuccessResponse[list[T]]):
    """Response containing a list of items"""


class PaginatedListResponse(PaginatedResponse[list[T]]):
    """Paginated list response"""


class CreateResponse(SuccessResponse[T]):
    """Response for create operations"""


class UpdateResponse(SuccessResponse[T]):
    """Response for update operations"""


class DeleteResponse(EmptySuccessResponse):
    """Response for delete operations"""


# HTTP Status Code Mappings
STATUS_CODE_MAPPING = {
    # Success responses
    ResponseStatus.SUCCESS: {
        "default": status.HTTP_200_OK,
        "created": status.HTTP_201_CREATED,
        "accepted": status.HTTP_202_ACCEPTED,
        "no_content": status.HTTP_204_NO_CONTENT,
    },
    # Error responses
    ResponseStatus.ERROR: {
        ErrorType.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorType.AUTHENTICATION_ERROR: status.HTTP_401_UNAUTHORIZED,
        ErrorType.AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
        ErrorType.NOT_FOUND_ERROR: status.HTTP_404_NOT_FOUND,
        ErrorType.BUSINESS_LOGIC_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorType.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
        ErrorType.DATABASE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorType.RATE_LIMIT_ERROR: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorType.MAINTENANCE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorType.INTERNAL_SERVER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        "default": status.HTTP_500_INTERNAL_SERVER_ERROR,
    },
    # Warning responses
    ResponseStatus.WARNING: {"default": status.HTTP_200_OK},
    # Info responses
    ResponseStatus.INFO: {"default": status.HTTP_200_OK},
}


def get_status_code(
    response_status: ResponseStatus,
    error_type: ErrorType | None = None,
    operation_type: str | None = None,
) -> int:
    """Get appropriate HTTP status code based on response status and type"""

    status_mapping = STATUS_CODE_MAPPING.get(response_status, {})

    if error_type:
        return status_mapping.get(
            error_type,
            status_mapping.get("default", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )

    if operation_type:
        return status_mapping.get(
            operation_type, status_mapping.get("default", status.HTTP_200_OK)
        )

    return status_mapping.get("default", status.HTTP_200_OK)


# Response Builder Classes
class ResponseBuilder:
    """Builder class for creating standardized responses"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder state"""
        self._success = True
        self._status = ResponseStatus.SUCCESS
        self._message = ""
        self._data = None
        self._errors = None
        self._meta = ResponseMeta()
        self._pagination = None
        return self

    def success(
        self, message: str = "Operation completed successfully"
    ) -> "ResponseBuilder":
        """Set success response"""
        self._success = True
        self._status = ResponseStatus.SUCCESS
        self._message = message
        return self

    def error(self, message: str = "An error occurred") -> "ResponseBuilder":
        """Set error response"""
        self._success = False
        self._status = ResponseStatus.ERROR
        self._message = message
        return self

    def warning(self, message: str = "Warning occurred") -> "ResponseBuilder":
        """Set warning response"""
        self._success = True
        self._status = ResponseStatus.WARNING
        self._message = message
        return self

    def info(self, message: str = "Information") -> "ResponseBuilder":
        """Set info response"""
        self._success = True
        self._status = ResponseStatus.INFO
        self._message = message
        return self

    def with_data(self, data: Any) -> "ResponseBuilder":
        """Set response data"""
        self._data = data
        return self

    def with_errors(self, errors: list[ErrorDetail]) -> "ResponseBuilder":
        """Set response errors"""
        self._errors = errors
        return self

    def with_pagination(
        self, page: int, page_size: int, total_items: int
    ) -> "ResponseBuilder":
        """Set pagination metadata"""
        self._pagination = PaginationMeta(
            page=page, page_size=page_size, total_items=total_items
        )
        return self

    def with_meta(self, **meta_data) -> "ResponseBuilder":
        """Add metadata"""
        for key, value in meta_data.items():
            if hasattr(self._meta, key):
                setattr(self._meta, key, value)
        return self

    def build(self) -> APIResponse:
        """Build the final response"""
        if self._pagination:
            response = PaginatedResponse(
                success=self._success,
                status=self._status,
                message=self._message,
                data=self._data,
                errors=self._errors,
                meta=self._meta,
                pagination=self._pagination,
            )
        else:
            response = APIResponse(
                success=self._success,
                status=self._status,
                message=self._message,
                data=self._data,
                errors=self._errors,
                meta=self._meta,
            )

        return response


# Convenience functions
def success_response(
    data: Any = None, message: str = "Operation completed successfully", **meta_data
) -> APIResponse:
    """Create success response"""
    return (
        ResponseBuilder()
        .success(message)
        .with_data(data)
        .with_meta(**meta_data)
        .build()
    )


def error_response(
    message: str = "An error occurred",
    errors: list[ErrorDetail] | None = None,
    **meta_data,
) -> APIResponse:
    """Create error response"""
    return (
        ResponseBuilder()
        .error(message)
        .with_errors(errors or [])
        .with_meta(**meta_data)
        .build()
    )


def paginated_response(
    data: list[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Data retrieved successfully",
    **meta_data,
) -> PaginatedResponse:
    """Create paginated response"""
    return (
        ResponseBuilder()
        .success(message)
        .with_data(data)
        .with_pagination(page, page_size, total_items)
        .with_meta(**meta_data)
        .build()
    )


def validation_error_response(
    validation_errors: list[ValidationErrorDetail], message: str = "Validation failed"
) -> ValidationErrorResponse:
    """Create validation error response"""
    return ValidationErrorResponse(message=message, errors=validation_errors)


# Turkish language support
TURKISH_MESSAGES = {
    "success": "İşlem başarıyla tamamlandı",
    "error": "Bir hata oluştu",
    "warning": "Uyarı oluştu",
    "info": "Bilgi",
    "validation_error": "Veri doğrulama hatası",
    "not_found": "İstenen kaynak bulunamadı",
    "unauthorized": "Yetkilendirme gerekli",
    "forbidden": "Bu işlem için yetkiniz bulunmamaktadır",
    "internal_error": "Sunucu iç hatası",
    "data_retrieved": "Veriler başarıyla getirildi",
    "data_created": "Veri başarıyla oluşturuldu",
    "data_updated": "Veri başarıyla güncellendi",
    "data_deleted": "Veri başarıyla silindi",
}


def turkish_success_response(
    data: Any = None,
    message_key: str = "success",
    custom_message: str | None = None,
    **meta_data,
) -> APIResponse:
    """Create success response with Turkish message"""
    message = custom_message or TURKISH_MESSAGES.get(
        message_key, TURKISH_MESSAGES["success"]
    )
    return success_response(data=data, message=message, **meta_data)


def turkish_error_response(
    message_key: str = "error",
    custom_message: str | None = None,
    errors: list[ErrorDetail] | None = None,
    **meta_data,
) -> APIResponse:
    """Create error response with Turkish message"""
    message = custom_message or TURKISH_MESSAGES.get(
        message_key, TURKISH_MESSAGES["error"]
    )
    return error_response(message=message, errors=errors, **meta_data)
