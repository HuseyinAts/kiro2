"""
Retry Utilities - External API Calls
Standart retry logic for external service calls

Features:
- Exponential backoff with jitter
- Configurable retry conditions
- Circuit breaker integration
- Logging and metrics

Usage:
    from core.retry_utils import retry_with_backoff, RetryConfig

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def call_external_api():
        ...

    # Or with custom config:
    config = RetryConfig(
        max_retries=5,
        base_delay=0.5,
        max_delay=30.0,
        exponential_base=2,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )

    @retry_with_backoff(config=config)
    async def call_api():
        ...

Requirements: REQ-1.3
"""

import asyncio
import functools
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from core.structured_logger import get_logger

logger = get_logger(__name__)

# Type variable for generic return type
T = TypeVar("T")

# Default retryable exceptions
DEFAULT_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)


@dataclass
class RetryConfig:
    """
    Retry configuration.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2)
        jitter: Whether to add random jitter to delays (default: True)
        jitter_factor: Maximum jitter as fraction of delay (default: 0.1)
        retryable_exceptions: Tuple of exceptions that trigger retry
        retryable_status_codes: HTTP status codes that trigger retry
        on_retry: Callback function called on each retry (optional)
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS
    retryable_status_codes: set[int] = field(
        default_factory=lambda: {408, 429, 500, 502, 503, 504}
    )
    on_retry: Callable[[int, Exception, float], None] | None = None


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        last_exception: Exception,
        attempts: int,
    ):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """
    Calculate delay for next retry attempt.

    Uses exponential backoff with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    # Exponential backoff
    delay = config.base_delay * (config.exponential_base ** attempt)

    # Cap at max delay
    delay = min(delay, config.max_delay)

    # Add jitter if enabled
    if config.jitter:
        jitter_amount = delay * config.jitter_factor * random.random()
        delay += jitter_amount

    return delay


def is_retryable_exception(
    exception: Exception,
    config: RetryConfig,
) -> bool:
    """
    Check if exception should trigger a retry.

    Args:
        exception: The exception to check
        config: Retry configuration

    Returns:
        True if exception is retryable
    """
    # Check against retryable exceptions
    if isinstance(exception, config.retryable_exceptions):
        return True

    # Check for HTTP status code errors (e.g., aiohttp.ClientResponseError)
    if hasattr(exception, "status"):
        status = exception.status
        if status in config.retryable_status_codes:
            return True

    # Check for response status in nested exceptions
    if hasattr(exception, "response") and hasattr(exception.response, "status"):
        status = exception.response.status
        if status in config.retryable_status_codes:
            return True

    return False


def retry_with_backoff(
    max_retries: int | None = None,
    base_delay: float | None = None,
    config: RetryConfig | None = None,
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum retry attempts (overrides config)
        base_delay: Base delay in seconds (overrides config)
        config: Full retry configuration

    Returns:
        Decorated function

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """
    # Create config if not provided
    if config is None:
        config = RetryConfig()

    # Override config with explicit parameters
    if max_retries is not None:
        config = RetryConfig(
            max_retries=max_retries,
            base_delay=config.base_delay if base_delay is None else base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter,
            jitter_factor=config.jitter_factor,
            retryable_exceptions=config.retryable_exceptions,
            retryable_status_codes=config.retryable_status_codes,
            on_retry=config.on_retry,
        )
    elif base_delay is not None:
        config = RetryConfig(
            max_retries=config.max_retries,
            base_delay=base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter,
            jitter_factor=config.jitter_factor,
            retryable_exceptions=config.retryable_exceptions,
            retryable_status_codes=config.retryable_status_codes,
            on_retry=config.on_retry,
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not is_retryable_exception(e, config):
                        logger.warning(
                            "retry_non_retryable_exception",
                            function=func.__name__,
                            exception_type=type(e).__name__,
                            error_message=str(e),
                        )
                        raise

                    # Check if we have retries left
                    if attempt >= config.max_retries:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            exception_type=type(e).__name__,
                            error_message=str(e),
                        )
                        raise RetryError(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}",
                            last_exception=e,
                            attempts=attempt + 1,
                        )

                    # Calculate delay
                    delay = calculate_delay(attempt, config)

                    logger.info(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=config.max_retries,
                        delay_seconds=round(delay, 2),
                        exception_type=type(e).__name__,
                        error_message=str(e)[:100],  # Truncate long messages
                    )

                    # Call on_retry callback if provided
                    if config.on_retry:
                        config.on_retry(attempt + 1, e, delay)

                    # Wait before retry
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator


def retry_sync_with_backoff(
    max_retries: int | None = None,
    base_delay: float | None = None,
    config: RetryConfig | None = None,
) -> Callable:
    """
    Decorator for retrying sync functions with exponential backoff.

    Same as retry_with_backoff but for synchronous functions.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds
        config: Full retry configuration

    Returns:
        Decorated function
    """
    import time

    # Create config if not provided
    if config is None:
        config = RetryConfig()

    # Override config with explicit parameters
    if max_retries is not None:
        config.max_retries = max_retries
    if base_delay is not None:
        config.base_delay = base_delay

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not is_retryable_exception(e, config):
                        raise

                    # Check if we have retries left
                    if attempt >= config.max_retries:
                        raise RetryError(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}",
                            last_exception=e,
                            attempts=attempt + 1,
                        )

                    # Calculate delay
                    delay = calculate_delay(attempt, config)

                    logger.info(
                        "retry_sync_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        delay_seconds=round(delay, 2),
                    )

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator


# =============================================================================
# Pre-configured retry decorators for common use cases
# =============================================================================


# YouTube API - high retry tolerance
YOUTUBE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0,
    exponential_base=2,
    retryable_status_codes={403, 408, 429, 500, 502, 503, 504},
)

youtube_retry = retry_with_backoff(config=YOUTUBE_RETRY_CONFIG)


# Khan Academy API
KHAN_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2,
)

khan_retry = retry_with_backoff(config=KHAN_RETRY_CONFIG)


# EBA API
EBA_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=15.0,
    exponential_base=2,
)

eba_retry = retry_with_backoff(config=EBA_RETRY_CONFIG)


# LLM API - longer delays, fewer retries
LLM_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=3.0,
    max_delay=30.0,
    exponential_base=2,
    retryable_status_codes={429, 500, 502, 503, 504, 529},  # 529 = Overloaded
)

llm_retry = retry_with_backoff(config=LLM_RETRY_CONFIG)


# Database operations - quick retries
DATABASE_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.1,
    max_delay=2.0,
    exponential_base=2,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
    ),
)

database_retry = retry_with_backoff(config=DATABASE_RETRY_CONFIG)
