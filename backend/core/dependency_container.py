"""
Dependency Injection Container
ARCHITECTURE FIX: Replace global singletons with proper DI pattern
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar

from .structured_logger import get_logger

logger = get_logger("dependency_container")

T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container

    Example:
        # Register dependencies
        container = DependencyContainer()
        container.register(DatabaseService, lambda: DatabaseService())
        container.register(CacheService, lambda: CacheService())

        # Resolve dependencies
        db_service = container.resolve(DatabaseService)
        cache_service = container.resolve(CacheService)

    Features:
        - Singleton pattern (lazy initialization)
        - Factory pattern support
        - Automatic dependency resolution
        - Lifecycle management
    """

    def __init__(self):
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Callable] = {}
        self._initialized = False

    def register_singleton(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a singleton dependency (created once, reused)

        Args:
            interface: Interface or class type
            factory: Factory function that creates the instance

        Example:
            container.register_singleton(DatabaseManager, lambda: DatabaseManager())
        """
        self._factories[interface] = factory
        logger.debug(f"Registered singleton: {interface.__name__}")

    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a transient dependency (created every time)

        Args:
            interface: Interface or class type
            factory: Factory function that creates the instance

        Example:
            container.register_transient(EmailService, lambda: EmailService())
        """
        self._transients[interface] = factory
        logger.debug(f"Registered transient: {interface.__name__}")

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register an existing instance

        Args:
            interface: Interface or class type
            instance: Pre-created instance

        Example:
            config = AppConfig()
            container.register_instance(AppConfig, config)
        """
        self._singletons[interface] = instance
        logger.debug(f"Registered instance: {interface.__name__}")

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency

        Args:
            interface: Interface or class type to resolve

        Returns:
            Instance of the requested type

        Raises:
            KeyError: If dependency not registered

        Example:
            db_service = container.resolve(DatabaseService)
        """
        # Check if singleton already created
        if interface in self._singletons:
            return self._singletons[interface]

        # Check if transient
        if interface in self._transients:
            factory = self._transients[interface]
            instance = factory()
            logger.debug(f"Created transient instance: {interface.__name__}")
            return instance

        # Create singleton
        if interface in self._factories:
            factory = self._factories[interface]
            instance = factory()
            self._singletons[interface] = instance
            logger.debug(f"Created singleton instance: {interface.__name__}")
            return instance

        raise KeyError(f"Dependency not registered: {interface.__name__}")

    def resolve_optional(self, interface: Type[T]) -> Optional[T]:
        """
        Resolve a dependency (returns None if not found)

        Args:
            interface: Interface or class type to resolve

        Returns:
            Instance of the requested type or None
        """
        try:
            return self.resolve(interface)
        except KeyError:
            return None

    def clear(self) -> None:
        """Clear all singletons (for testing)"""
        self._singletons.clear()
        logger.debug("Cleared all singleton instances")

    def reset(self) -> None:
        """Reset the container (clear all registrations)"""
        self._factories.clear()
        self._singletons.clear()
        self._transients.clear()
        logger.debug("Reset dependency container")


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """
    Get global dependency container

    Returns:
        Global DependencyContainer instance
    """
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def setup_dependencies():
    """
    Setup application dependencies

    Example:
        from core.dependency_container import setup_dependencies
        setup_dependencies()
    """
    container = get_container()

    # Register core services
    try:
        from .database import db_manager

        container.register_instance(type(db_manager), db_manager)
        logger.info("Registered DatabaseManager")
    except ImportError:
        logger.warning("DatabaseManager not available")

    try:
        from .cache import cache_manager

        container.register_instance(type(cache_manager), cache_manager)
        logger.info("Registered CacheManager")
    except ImportError:
        logger.warning("CacheManager not available")

    try:
        from .config import settings

        container.register_instance(type(settings), settings)
        logger.info("Registered Settings")
    except ImportError:
        logger.warning("Settings not available")

    logger.info("Dependency container setup complete")


# Dependency injection decorators
def inject(dependency_type: Type[T]) -> Callable:
    """
    Decorator to inject dependencies into function parameters

    Args:
        dependency_type: Type to inject

    Example:
        @inject(DatabaseService)
        async def get_users(db_service: DatabaseService):
            return await db_service.get_all_users()
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            container = get_container()
            instance = container.resolve(dependency_type)
            kwargs[func.__code__.co_varnames[0]] = instance
            return await func(*args, **kwargs)

        return wrapper

    return decorator
