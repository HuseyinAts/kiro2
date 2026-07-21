"""
Resilience & Retry Utilities
Includes poison-protected database retries.
"""

import asyncio
import functools
import logging
import os

from sqlalchemy.exc import SQLAlchemyError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_none,
)

logger = logging.getLogger(__name__)

def db_retry(fn_or_max_attempts=None, *, max_attempts=3, wait_seconds=1):
    """
    Database retry decorator.
    
    Guarantees rollback before retry to prevent PendingRollbackError (Session Poisoning).
    If a testing environment is detected (TESTING=true or SQLite DATABASE_URL), wait is set to 0.
    """
    if fn_or_max_attempts is None:
        return lambda fn: db_retry(fn, max_attempts=max_attempts, wait_seconds=wait_seconds)

    if callable(fn_or_max_attempts):
        func = fn_or_max_attempts

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if testing environment
            is_testing = (
                os.environ.get("TESTING") == "true"
                or "sqlite" in os.environ.get("DATABASE_URL", "").lower()
            )
            wait_strategy = wait_none() if is_testing else wait_fixed(wait_seconds)

            retrier = AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_strategy,
                retry=retry_if_exception_type(SQLAlchemyError),
                reraise=True
            )

            # Identify the database session
            session = None
            # 1. Check if args[0] (self) has a 'db' attribute
            if args and hasattr(args[0], "db"):
                session = args[0].db
            # 2. Check if any arg is a session
            if not session:
                for arg in args:
                    if hasattr(arg, "commit") and hasattr(arg, "rollback"):
                        session = arg
                        break
            # 3. Check kwargs
            if not session:
                for val in kwargs.values():
                    if hasattr(val, "commit") and hasattr(val, "rollback"):
                        session = val
                        break

            async def attempt():
                try:
                    return await func(*args, **kwargs)
                except SQLAlchemyError as e:
                    if session:
                        logger.warning(
                            f"Database error occurred during {func.__name__}: {e!s}. "
                            "Performing rollback before retry."
                        )
                        try:
                            # rollback might be a coroutine (AsyncSession) or a sync method
                            res = session.rollback()
                            if asyncio.iscoroutine(res):
                                await res
                        except Exception as rollback_err:
                            logger.error(f"Failed to rollback database session: {rollback_err!s}")
                    raise

            async for state in retrier:
                with state:
                    return await attempt()
        return wrapper
    return lambda fn: db_retry(fn, max_attempts=fn_or_max_attempts, wait_seconds=wait_seconds)
