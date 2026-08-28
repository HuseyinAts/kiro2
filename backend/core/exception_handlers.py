"""
Global Exception Handlers
Standardized exception handling for consistent error responses
"""

import logging

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    AuthorizationError,
    BusinessLogicError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
    ServiceError,
)
from .exceptions import ValidationError as CustomValidationError
from .response_models import (
    TURKISH_MESSAGES,
    ErrorDetail,
    ErrorType,
    ResponseBuilder,
    ValidationErrorDetail,
)
from .unified_config import get_unified_config

logger = logging.getLogger(__name__)


class ExceptionHandlers:
    """
    Centralized exception handlers for standardized error responses
    """

    def __init__(self, turkish_messages: bool = True):
        self.config = get_unified_config()
        self.turkish_messages = turkish_messages

    # ==================== FASTAPI BUILT-IN EXCEPTIONS ====================

    async def http_exception_handler(
        self, request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTPException"""

        error_type = self._get_error_type_from_status_code(exc.status_code)

        error_detail = ErrorDetail(
            code=error_type.value,
            message=str(exc.detail),
            details=getattr(exc, "details", None),
        )

        message = self._get_localized_error_message(exc.status_code, str(exc.detail))

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True), status_code=exc.status_code
        )

    async def validation_exception_handler(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI validation errors"""

        validation_errors = []

        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error.get("loc", []))

            validation_error = ValidationErrorDetail(
                code=ErrorType.VALIDATION_ERROR.value,
                message=error.get("msg", "Validation error"),
                field=field_path,
                rejected_value=error.get("input"),
                constraint=error.get("type"),
            )
            validation_errors.append(validation_error)

        message = self._get_message("validation_error")

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors(validation_errors)
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    async def pydantic_validation_exception_handler(
        self, request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors"""

        validation_errors = []

        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error.get("loc", []))

            validation_error = ValidationErrorDetail(
                code=ErrorType.VALIDATION_ERROR.value,
                message=error.get("msg", "Validation error"),
                field=field_path,
                rejected_value=error.get("input"),
                constraint=error.get("type"),
            )
            validation_errors.append(validation_error)

        message = self._get_message("validation_error")

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors(validation_errors)
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # ==================== CUSTOM EXCEPTIONS ====================

    async def service_exception_handler(
        self, request: Request, exc: ServiceError
    ) -> JSONResponse:
        """Handle custom ServiceError exceptions"""

        error_detail = ErrorDetail(
            code=exc.error_code, message=exc.message, details=exc.details
        )

        # Map to appropriate HTTP status
        status_mapping = {
            "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
            "NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
            "DATABASE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
            "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
            "BUSINESS_LOGIC_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }

        http_status = status_mapping.get(
            exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        message = (
            exc.message
            if self._is_turkish_text(exc.message)
            else self._get_message("error")
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        # `jsonable_encoder` ZORUNLU: `.dict()` `meta.timestamp`'i ham `datetime`
        # olarak birakiyor ve `JSONResponse` duz `json.dumps` kullandigi icin
        # "Object of type datetime is not JSON serializable" ile PATLIYOR.
        # Handler patlayinca istek generic catch-all'a duser -> 500. Yani bu
        # metot kaydedilse bile dogru kodu URETEMIYORDU (S252'de olculdu; bu
        # modulun depoda hic cagirani olmamasinin sebebi de bu olabilir).
        return JSONResponse(
            content=jsonable_encoder(response_data, exclude_none=True),
            status_code=http_status,
        )

    async def validation_error_handler(
        self, request: Request, exc: CustomValidationError
    ) -> JSONResponse:
        """Handle custom ValidationError"""

        validation_error = ValidationErrorDetail(
            code=ErrorType.VALIDATION_ERROR.value,
            message=exc.message,
            field=getattr(exc, "field", None),
            rejected_value=None,
            details=exc.details,
        )

        message = (
            exc.message
            if self._is_turkish_text(exc.message)
            else self._get_message("validation_error")
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([validation_error])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    async def not_found_error_handler(
        self, request: Request, exc: NotFoundError
    ) -> JSONResponse:
        """Handle custom NotFoundError"""

        error_detail = ErrorDetail(
            code=ErrorType.NOT_FOUND_ERROR.value,
            message=exc.message,
            details=exc.details,
        )

        message = (
            exc.message
            if self._is_turkish_text(exc.message)
            else self._get_message("not_found")
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    async def authorization_error_handler(
        self, request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        """Handle custom AuthorizationError"""

        error_detail = ErrorDetail(
            code=ErrorType.AUTHORIZATION_ERROR.value, message=exc.message
        )

        message = (
            exc.message
            if self._is_turkish_text(exc.message)
            else self._get_message("forbidden")
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    async def database_error_handler(
        self, request: Request, exc: DatabaseError
    ) -> JSONResponse:
        """Handle custom DatabaseError"""

        error_detail = ErrorDetail(
            code=ErrorType.DATABASE_ERROR.value,
            message="Database operation failed"
            if not self.config.debug
            else exc.message,
            details=exc.details if self.config.debug else None,
        )

        message = (
            self._get_message("database_error")
            if self.turkish_messages
            else "Database error occurred"
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    async def business_logic_error_handler(
        self, request: Request, exc: BusinessLogicError
    ) -> JSONResponse:
        """Handle custom BusinessLogicError"""

        error_detail = ErrorDetail(
            code=ErrorType.BUSINESS_LOGIC_ERROR.value,
            message=exc.message,
            details=exc.details,
        )

        message = (
            exc.message
            if self._is_turkish_text(exc.message)
            else self._get_message("business_error")
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    async def external_service_error_handler(
        self, request: Request, exc: ExternalServiceError
    ) -> JSONResponse:
        """Handle custom ExternalServiceError"""

        error_detail = ErrorDetail(
            code=ErrorType.EXTERNAL_SERVICE_ERROR.value,
            message="External service error" if not self.config.debug else exc.message,
            details=exc.details if self.config.debug else None,
        )

        message = (
            self._get_message("external_service_error")
            if self.turkish_messages
            else "External service error"
        )

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    # ==================== GENERAL EXCEPTION HANDLER ====================

    async def general_exception_handler(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exceptions"""

        # Log the full exception
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "request_url": str(request.url),
                "request_method": request.method,
            },
            exc_info=True,
        )

        # Create error detail
        # SECURITY: Never expose stack traces in API responses (even in debug mode)
        # Tracebacks are logged via exc_info=True above
        if self.config.debug:
            error_message = str(exc)
            error_details = {
                "exception_type": type(exc).__name__,
                # Traceback logged server-side only, not exposed to client
            }
        else:
            error_message = "Internal server error"
            error_details = None

        error_detail = ErrorDetail(
            code=ErrorType.INTERNAL_SERVER_ERROR.value,
            message=error_message,
            details=error_details,
        )

        message = self._get_message("internal_error")

        response_data = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=getattr(request.state, "request_id", None),
                api_version=self.config.app_version,
            )
            .build()
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # ==================== HELPER METHODS ====================

    def _get_error_type_from_status_code(self, status_code: int) -> ErrorType:
        """Map HTTP status code to ErrorType"""
        mapping = {
            400: ErrorType.VALIDATION_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.AUTHORIZATION_ERROR,
            404: ErrorType.NOT_FOUND_ERROR,
            422: ErrorType.BUSINESS_LOGIC_ERROR,
            429: ErrorType.RATE_LIMIT_ERROR,
            500: ErrorType.INTERNAL_SERVER_ERROR,
            502: ErrorType.EXTERNAL_SERVICE_ERROR,
            503: ErrorType.MAINTENANCE_ERROR,
        }
        return mapping.get(status_code, ErrorType.INTERNAL_SERVER_ERROR)

    def _get_message(self, key: str) -> str:
        """Get localized message"""
        if not self.turkish_messages:
            # English messages
            english_messages = {
                "error": "An error occurred",
                "validation_error": "Validation failed",
                "not_found": "Resource not found",
                "forbidden": "Access forbidden",
                "unauthorized": "Authentication required",
                "internal_error": "Internal server error",
                "database_error": "Database error",
                "external_service_error": "External service error",
                "business_error": "Business logic error",
            }
            return english_messages.get(key, "Error occurred")

        return TURKISH_MESSAGES.get(key, "Bir hata oluştu")

    def _get_localized_error_message(self, status_code: int, detail: str) -> str:
        """Get appropriate localized error message"""

        # If detail already contains Turkish characters, use it
        if self._is_turkish_text(detail):
            return detail

        # Map status codes to message keys
        message_mapping = {
            400: "validation_error",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            422: "validation_error",
            429: "rate_limit_exceeded",
            500: "internal_error",
            502: "external_service_error",
            503: "service_unavailable",
        }

        message_key = message_mapping.get(status_code, "error")
        return self._get_message(message_key)

    def _is_turkish_text(self, text: str) -> bool:
        """Check if text contains Turkish characters"""
        turkish_chars = "çğıöşüÇĞIİÖŞÜ"
        return any(char in text for char in turkish_chars)


def setup_exception_handlers(app, turkish_messages: bool = True):
    """Setup all exception handlers for the FastAPI app"""

    handlers = ExceptionHandlers(turkish_messages=turkish_messages)

    # FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, handlers.http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, handlers.http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, handlers.validation_exception_handler
    )
    app.add_exception_handler(
        PydanticValidationError, handlers.pydantic_validation_exception_handler
    )

    # Custom exceptions
    app.add_exception_handler(ServiceError, handlers.service_exception_handler)
    app.add_exception_handler(CustomValidationError, handlers.validation_error_handler)
    app.add_exception_handler(NotFoundError, handlers.not_found_error_handler)
    app.add_exception_handler(AuthorizationError, handlers.authorization_error_handler)
    app.add_exception_handler(DatabaseError, handlers.database_error_handler)
    app.add_exception_handler(BusinessLogicError, handlers.business_logic_error_handler)
    app.add_exception_handler(
        ExternalServiceError, handlers.external_service_error_handler
    )

    # General exception handler (catch-all)
    app.add_exception_handler(Exception, handlers.general_exception_handler)

    return handlers


# Extended Turkish messages
TURKISH_MESSAGES.update(
    {
        "database_error": "Veritabanı hatası oluştu",
        "external_service_error": "Harici servis hatası",
        "business_error": "İş kuralı hatası",
        "rate_limit_exceeded": "İstek limiti aşıldı",
        "service_unavailable": "Servis kullanılamıyor",
        "timeout_error": "İşlem zaman aşımına uğradı",
        "configuration_error": "Konfigürasyon hatası",
    }
)
