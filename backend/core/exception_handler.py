"""
Centralized Exception Handling
ARCHITECTURE FIX: Standardized exception handling across the application
"""

import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Type

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from .structured_logger import get_logger

logger = get_logger("exception_handler")


class ErrorCode(Enum):
    """Application error codes"""

    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    CONFLICT = 1003
    UNAUTHORIZED = 1004
    FORBIDDEN = 1005

    # Database errors (2000-2999)
    DATABASE_ERROR = 2000
    TRANSACTION_ERROR = 2001
    CONSTRAINT_VIOLATION = 2002
    CONNECTION_ERROR = 2003

    # Business logic errors (3000-3999)
    BUSINESS_LOGIC_ERROR = 3000
    INVALID_STATE = 3001
    OPERATION_NOT_ALLOWED = 3002

    # External service errors (4000-4999)
    EXTERNAL_SERVICE_ERROR = 4000
    API_ERROR = 4001
    TIMEOUT_ERROR = 4002

    # Authentication/Authorization errors (5000-5999)
    AUTHENTICATION_ERROR = 5000
    TOKEN_EXPIRED = 5001
    INVALID_CREDENTIALS = 5002
    INSUFFICIENT_PERMISSIONS = 5003


class AppException(Exception):
    """
    Base application exception

    Example:
        raise AppException(
            message="User not found",
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={"user_id": "123"}
        )
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "success": False,
            "error": {
                "message": self.message,
                "code": self.error_code.value,
                "type": self.error_code.name,
                "details": self.details,
            },
        }


class ValidationException(AppException):
    """Validation error exception"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)},
        )


class ConflictException(AppException):
    """Resource conflict exception"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    """Forbidden access exception"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class DatabaseException(AppException):
    """Database operation exception"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceException(AppException):
    """External service error exception"""

    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"{service} error: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {"service": service},
        )


# Exception handler mapping
EXCEPTION_HANDLERS: Dict[Type[Exception], int] = {
    ValueError: status.HTTP_400_BAD_REQUEST,
    KeyError: status.HTTP_404_NOT_FOUND,
    PermissionError: status.HTTP_403_FORBIDDEN,
    TimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
}


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for AppException

    Args:
        request: FastAPI request
        exc: AppException instance

    Returns:
        JSONResponse with error details
    """
    logger.error(
        f"Application error: {exc.message}",
        extra_data={
            "error_code": exc.error_code.name,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handler for validation exceptions

    Args:
        request: FastAPI request
        exc: Validation exception

    Returns:
        JSONResponse with validation error
    """
    logger.warning(
        f"Validation error: {str(exc)}",
        extra_data={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "message": "Validation error",
                "code": ErrorCode.VALIDATION_ERROR.value,
                "type": ErrorCode.VALIDATION_ERROR.name,
                "details": {"errors": str(exc)},
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for generic exceptions

    Args:
        request: FastAPI request
        exc: Exception instance

    Returns:
        JSONResponse with error details
    """
    # Get status code from mapping or default to 500
    status_code = EXCEPTION_HANDLERS.get(
        type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    # Log with full traceback
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra_data={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    # Don't expose internal errors in production
    from .config import settings

    if settings.environment == "production":
        message = "Internal server error"
        details = {}
    else:
        message = str(exc)
        details = {"type": type(exc).__name__}

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "message": message,
                "code": ErrorCode.UNKNOWN_ERROR.value,
                "type": ErrorCode.UNKNOWN_ERROR.name,
                "details": details,
            },
        },
    )


def setup_exception_handlers(app):
    """
    Setup exception handlers for FastAPI app

    Args:
        app: FastAPI application instance

    Example:
        from fastapi import FastAPI
        from core.exception_handler import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)
    """
    # Register custom exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationException, app_exception_handler)
    app.add_exception_handler(NotFoundException, app_exception_handler)
    app.add_exception_handler(DatabaseException, app_exception_handler)

    # Register generic exception handler
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
