# Core modülleri
"""
KIRO2 Core Module Exports

Temel modüller ve fonksiyonlar bu dosyadan export edilir.
Import hataları önlemek için lazy loading kullanılır.
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import Settings, settings, get_settings
    from .database import db_manager, get_async_session, Base
    from .auth import AuthService
    from .application import create_app
    from .exceptions import (
        ServiceError,
        ValidationError,
        AuthorizationError,
        NotFoundError,
        DatabaseError,
        ExternalServiceError,
        ConfigurationError,
    )

# Export list - kullanım: from core import settings
__all__ = [
    # Config
    "Settings",
    "settings",
    "get_settings",
    # Database
    "db_manager",
    "get_async_session",
    "Base",
    # Auth
    "AuthService",
    # Application
    "create_app",
    # Exceptions
    "ServiceError",
    "ValidationError",
    "AuthorizationError",
    "NotFoundError",
    "DatabaseError",
    "ExternalServiceError",
    "ConfigurationError",
]


def __getattr__(name: str):
    """
    Lazy loading for core modules.

    Bu fonksiyon circular import sorunlarını önler.
    Modüller sadece ihtiyaç duyulduğunda yüklenir.
    """
    # Config exports
    if name in ("Settings", "settings", "get_settings"):
        from .config import Settings, settings, get_settings
        mapping = {
            "Settings": Settings,
            "settings": settings,
            "get_settings": get_settings,
        }
        return mapping[name]

    # Database exports
    if name in ("db_manager", "get_async_session", "Base"):
        from .database import db_manager, get_async_session
        try:
            from models.base import Base
        except ImportError:
            from sqlalchemy.orm import declarative_base
            Base = declarative_base()
        mapping = {
            "db_manager": db_manager,
            "get_async_session": get_async_session,
            "Base": Base,
        }
        return mapping[name]

    # Auth exports
    if name == "AuthService":
        from .auth import AuthService
        return AuthService

    # Application exports
    if name == "create_app":
        from .application import create_app
        return create_app

    # Exception exports
    if name in (
        "ServiceError",
        "ValidationError",
        "AuthorizationError",
        "NotFoundError",
        "DatabaseError",
        "ExternalServiceError",
        "ConfigurationError",
    ):
        from .exceptions import (
            ServiceError,
            ValidationError,
            AuthorizationError,
            NotFoundError,
            DatabaseError,
            ExternalServiceError,
            ConfigurationError,
        )
        exceptions = {
            "ServiceError": ServiceError,
            "ValidationError": ValidationError,
            "AuthorizationError": AuthorizationError,
            "NotFoundError": NotFoundError,
            "DatabaseError": DatabaseError,
            "ExternalServiceError": ExternalServiceError,
            "ConfigurationError": ConfigurationError,
        }
        return exceptions[name]

    raise AttributeError(f"module 'core' has no attribute '{name}'")
