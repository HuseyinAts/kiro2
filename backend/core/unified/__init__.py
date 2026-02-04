"""
KIRO2 Unified Core Systems
Consolidated modules for better maintainability
"""

from .auth_system import UnifiedAuthManager, get_auth_manager

# Convenience imports for common use cases
from .cache_system import UnifiedCacheManager, get_cache_manager
from .database_system import UnifiedDatabaseManager, get_db_manager, get_db_session
from .security_system import UnifiedSecurityManager, get_security_manager

__all__ = [
    # Core managers
    "UnifiedCacheManager",
    "UnifiedAuthManager",
    "UnifiedDatabaseManager",
    "UnifiedSecurityManager",
    # Convenience functions
    "get_cache_manager",
    "get_auth_manager",
    "get_db_manager",
    "get_db_session",
    "get_security_manager",
]
