"""
Transaction Management Context Manager
ARCHITECTURE FIX: Standardized transaction handling with automatic rollback
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .database import db_manager
from .structured_logger import get_logger

logger = get_logger("transaction_context")


class TransactionError(Exception):
    """Transaction-related errors"""

    pass


@asynccontextmanager
async def transactional_session(
    session: Optional[AsyncSession] = None,
    auto_commit: bool = True,
    isolation_level: Optional[str] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Transaction context manager with automatic commit/rollback

    Args:
        session: Existing session to use (or create new)
        auto_commit: Automatically commit on success
        isolation_level: Transaction isolation level (READ COMMITTED, SERIALIZABLE, etc.)

    Yields:
        AsyncSession: Database session with transaction

    Example:
        async with transactional_session() as session:
            user = User(name="Test")
            session.add(user)
            # Auto-commits on success, auto-rolls back on exception

    Example with existing session:
        async with get_async_session() as session:
            async with transactional_session(session, auto_commit=False) as tx_session:
                # Manual transaction control
                user = User(name="Test")
                tx_session.add(user)
                await tx_session.commit()
    """
    # Use provided session or create new one
    if session is not None:
        # Use existing session (nested transaction)
        async with session.begin_nested():
            try:
                if isolation_level:
                    await session.execute(
                        f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
                    )
                yield session
                if auto_commit:
                    await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rolled back: {e}", exc_info=True)
                raise
    else:
        # Create new session
        if not db_manager._initialized:
            await db_manager.initialize()

        async with db_manager.get_session() as new_session:
            try:
                if isolation_level:
                    await new_session.execute(
                        f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
                    )
                yield new_session
                if auto_commit:
                    await new_session.commit()
            except Exception as e:
                await new_session.rollback()
                logger.error(f"Transaction rolled back: {e}", exc_info=True)
                raise
            finally:
                await new_session.close()


@asynccontextmanager
async def readonly_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Read-only session (no commits)

    Yields:
        AsyncSession: Read-only database session

    Example:
        async with readonly_session() as session:
            users = await session.execute(select(User))
            # No commits, automatic rollback
    """
    if not db_manager._initialized:
        await db_manager.initialize()

    async with db_manager.get_session() as session:
        try:
            # Set read-only mode
            await session.execute("SET TRANSACTION READ ONLY")
            yield session
        except Exception as e:
            logger.error(f"Read-only session error: {e}", exc_info=True)
            raise
        finally:
            # Always rollback for read-only
            await session.rollback()
            await session.close()


class TransactionalRepository:
    """
    Base repository with transaction support

    Example:
        class UserRepository(TransactionalRepository):
            async def create_user(self, user_data: dict) -> User:
                async with self.transaction() as session:
                    user = User(**user_data)
                    session.add(user)
                    return user
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    @asynccontextmanager
    async def transaction(
        self, auto_commit: bool = True, isolation_level: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get transaction context

        Args:
            auto_commit: Automatically commit on success
            isolation_level: Transaction isolation level

        Yields:
            AsyncSession: Database session
        """
        async with transactional_session(
            self.session, auto_commit=auto_commit, isolation_level=isolation_level
        ) as session:
            yield session

    @asynccontextmanager
    async def readonly(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get read-only session

        Yields:
            AsyncSession: Read-only database session
        """
        async with readonly_session() as session:
            yield session


# Decorator for automatic transaction management
def transactional(auto_commit: bool = True, isolation_level: Optional[str] = None):
    """
    Decorator for automatic transaction management

    Args:
        auto_commit: Automatically commit on success
        isolation_level: Transaction isolation level

    Example:
        @transactional()
        async def create_user(user_data: dict):
            async with transactional_session() as session:
                user = User(**user_data)
                session.add(user)
                return user
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with transactional_session(
                auto_commit=auto_commit, isolation_level=isolation_level
            ) as session:
                # Inject session into kwargs if not present
                if "session" not in kwargs:
                    kwargs["session"] = session
                return await func(*args, **kwargs)

        return wrapper

    return decorator
