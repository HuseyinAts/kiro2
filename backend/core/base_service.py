"""
Base Service Class Template
Tüm servisler için ortak kalıp ve metodlar
"""

from abc import ABC
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, TypeVar, Union

from sqlalchemy.orm import Session

from core.database import get_db, get_db_session
from core.exceptions import NotFoundError, ServiceError, ValidationError
from core.structured_logger import get_logger

T = TypeVar("T")


class BaseService(ABC):
    """
    Base service sınıfı - tüm servislerin kalıtım alacağı temel sınıf

    Özellikler:
    - Standardized error handling
    - Logging infrastructure
    - Database session management
    - Common validation methods
    - Response format standardization
    """

    def __init__(self, service_name: str | None = None):
        """Service'i başlat"""
        self.service_name = service_name or self.__class__.__name__
        self.logger = get_logger(self.service_name.lower())
        self._initialize_service()

    def _initialize_service(self):
        """Service-specific initialization - subclass'lar override edebilir"""
        self.logger.info(f"{self.service_name} service initialized")

    # ==================== DATABASE MANAGEMENT ====================

    @asynccontextmanager
    async def get_async_session(self):
        """Async database session context manager"""
        async with get_db_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database error in {self.service_name}: {e}")
                raise ServiceError(f"Database operation failed: {e!s}")

    def get_sync_session(self) -> Session:
        """Synchronous database session"""
        return get_db()

    # ==================== ERROR HANDLING ====================

    def handle_service_error(self, operation: str, error: Exception) -> None:
        """Standardized service error handling"""
        self.logger.error(f"Error in {self.service_name}.{operation}: {error}")

        if isinstance(error, (ValidationError, NotFoundError)):
            raise error
        raise ServiceError(f"{operation} failed: {error!s}")

    def validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> None:
        """Validate required fields in data"""
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ]

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def validate_non_empty(self, value: Any, field_name: str) -> None:
        """Validate that a value is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} cannot be empty")

    # ==================== RESPONSE FORMATTING ====================

    def create_success_response(
        self,
        data: Any = None,
        message: str = "Operation completed successfully",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create standardized success response"""
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if meta:
            response["meta"] = meta

        return response

    def create_error_response(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create standardized error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        return response

    # ==================== PAGINATION ====================

    def create_pagination_meta(
        self, total: int, page: int, page_size: int
    ) -> dict[str, Any]:
        """Create pagination metadata"""
        total_pages = max(1, (total + page_size - 1) // page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    # ==================== CACHING ====================

    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key for service operations"""
        key_parts = [self.service_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)

    # ==================== ABSTRACT METHODS ====================

    async def health_check(self) -> dict[str, Any]:
        """Service health check - default implementation"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }


class AsyncBaseService(BaseService):
    """
    Async operations için base service
    """

    def __init__(self, service_name: str | None = None):
        super().__init__(service_name)

    async def execute_with_error_handling(
        self, operation_name: str, operation_func, *args, **kwargs
    ) -> Any:
        """Execute operation with standardized error handling"""
        try:
            self.logger.debug(f"Starting {operation_name}")
            result = await operation_func(*args, **kwargs)
            self.logger.debug(f"Completed {operation_name}")
            return result

        except Exception as e:
            self.handle_service_error(operation_name, e)


class SyncBaseService(BaseService):
    """
    Synchronous operations için base service
    """

    def __init__(self, service_name: str | None = None):
        super().__init__(service_name)

    def execute_with_error_handling(
        self, operation_name: str, operation_func, *args, **kwargs
    ) -> Any:
        """Execute operation with standardized error handling"""
        try:
            self.logger.debug(f"Starting {operation_name}")
            result = operation_func(*args, **kwargs)
            self.logger.debug(f"Completed {operation_name}")
            return result

        except Exception as e:
            self.handle_service_error(operation_name, e)


class DatabaseService(AsyncBaseService):
    """
    Database operations için specialized base service
    """

    async def find_by_id(self, model_class, entity_id: Union[str, int]) -> T | None:
        """Generic find by ID method"""
        async with self.get_async_session() as session:
            result = await session.get(model_class, entity_id)
            if not result:
                raise NotFoundError(
                    f"{model_class.__name__} with ID {entity_id} not found"
                )
            return result

    async def soft_delete(self, entity: T) -> T:
        """Soft delete entity (set is_active = False)"""
        if hasattr(entity, "is_active"):
            entity.is_active = False
            entity.deleted_at = datetime.now()
        return entity

    async def health_check(self) -> dict[str, Any]:
        """Database service health check"""
        try:
            async with self.get_async_session() as session:
                await session.execute("SELECT 1")
                return self.create_success_response(
                    data={"database": "healthy"},
                    message="Database connection successful",
                )
        except Exception as e:
            return self.create_error_response(
                message="Database health check failed", details={"error": str(e)}
            )


# ==================== SERVICE DECORATORS ====================


def service_operation(operation_name: str):
    """Decorator for service operations with automatic error handling and logging"""

    def decorator(func):
        async def async_wrapper(self, *args, **kwargs):
            return await self.execute_with_error_handling(
                operation_name, func, self, *args, **kwargs
            )

        def sync_wrapper(self, *args, **kwargs):
            return self.execute_with_error_handling(
                operation_name, func, self, *args, **kwargs
            )

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validate_input(**validation_rules):
    """Decorator for input validation"""

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Validation logic can be implemented here
            # For now, just call the original function
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
