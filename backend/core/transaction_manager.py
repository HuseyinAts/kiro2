"""
Advanced Transaction Management System
Comprehensive transaction handling for the enhanced database pattern consolidation

Bu dosya gelişmiş transaction management sağlar:
- Nested transaction support (savepoints)
- Transaction isolation levels
- Distributed transaction coordination
- Transaction retry logic
- Deadlock detection ve recovery
- Transaction performance monitoring
- Multi-database transaction support
- Transaction hooks ve callbacks
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    TypeVar,
)

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.exc import TimeoutError as SQLTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncTransaction
from sqlalchemy.sql import text

from .enhanced_database import EnhancedDatabaseManager, enhanced_db_manager
from .error_context import async_error_context
from .error_monitoring import log_error
from .exceptions import DatabaseError, ErrorSeverity, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ==================== TRANSACTION ENUMS ====================


class TransactionIsolationLevel(Enum):
    """Transaction isolation levels"""

    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionStatus(Enum):
    """Transaction status tracking"""

    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TransactionPriority(Enum):
    """Transaction priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


# ==================== TRANSACTION DATA CLASSES ====================


@dataclass
class TransactionConfig:
    """Transaction configuration"""

    isolation_level: TransactionIsolationLevel | None = None
    timeout_seconds: int | None = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_savepoints: bool = True
    enable_deadlock_retry: bool = True
    priority: TransactionPriority = TransactionPriority.NORMAL
    read_only: bool = False

    def __post_init__(self):
        if self.timeout_seconds and self.timeout_seconds <= 0:
            raise ValidationError("Transaction timeout must be positive")
        if self.retry_attempts < 0:
            raise ValidationError("Retry attempts must be non-negative")
        if self.retry_delay < 0:
            raise ValidationError("Retry delay must be non-negative")


@dataclass
class TransactionMetrics:
    """Transaction execution metrics"""

    transaction_id: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: TransactionStatus = TransactionStatus.ACTIVE
    queries_executed: int = 0
    rows_affected: int = 0
    savepoints_created: int = 0
    retry_count: int = 0
    isolation_level: str | None = None
    error_message: str | None = None

    def mark_completed(
        self, status: TransactionStatus, error_message: str | None = None
    ):
        """Mark transaction as completed"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        self.error_message = error_message


@dataclass
class SavepointInfo:
    """Savepoint information"""

    name: str
    created_at: datetime
    transaction_id: str


# ==================== TRANSACTION HOOKS ====================


class TransactionHook(ABC):
    """Abstract base class for transaction hooks"""

    @abstractmethod
    async def before_transaction(
        self, transaction_id: str, config: TransactionConfig
    ) -> None:
        """Called before transaction starts"""

    @abstractmethod
    async def after_commit(
        self, transaction_id: str, metrics: TransactionMetrics
    ) -> None:
        """Called after successful commit"""

    @abstractmethod
    async def after_rollback(
        self, transaction_id: str, metrics: TransactionMetrics, error: Exception
    ) -> None:
        """Called after rollback"""


class LoggingTransactionHook(TransactionHook):
    """Transaction hook that logs transaction events"""

    async def before_transaction(
        self, transaction_id: str, config: TransactionConfig
    ) -> None:
        logger.info(f"Transaction {transaction_id} starting with config: {config}")

    async def after_commit(
        self, transaction_id: str, metrics: TransactionMetrics
    ) -> None:
        logger.info(
            f"Transaction {transaction_id} committed successfully in {metrics.duration_ms:.2f}ms"
        )

    async def after_rollback(
        self, transaction_id: str, metrics: TransactionMetrics, error: Exception
    ) -> None:
        logger.warning(
            f"Transaction {transaction_id} rolled back after {metrics.duration_ms:.2f}ms: {error}"
        )


class MetricsTransactionHook(TransactionHook):
    """Transaction hook that collects metrics"""

    def __init__(self):
        self.transaction_metrics: dict[str, TransactionMetrics] = {}
        self.completed_transactions: list[TransactionMetrics] = []
        self.active_transactions: set[str] = set()

    async def before_transaction(
        self, transaction_id: str, config: TransactionConfig
    ) -> None:
        self.active_transactions.add(transaction_id)

    async def after_commit(
        self, transaction_id: str, metrics: TransactionMetrics
    ) -> None:
        self.active_transactions.discard(transaction_id)
        self.completed_transactions.append(metrics)

        # Keep only last 1000 completed transactions
        if len(self.completed_transactions) > 1000:
            self.completed_transactions = self.completed_transactions[-1000:]

    async def after_rollback(
        self, transaction_id: str, metrics: TransactionMetrics, error: Exception
    ) -> None:
        self.active_transactions.discard(transaction_id)
        self.completed_transactions.append(metrics)

        # Keep only last 1000 completed transactions
        if len(self.completed_transactions) > 1000:
            self.completed_transactions = self.completed_transactions[-1000:]

    def get_stats(self) -> dict[str, Any]:
        """Get transaction statistics"""
        if not self.completed_transactions:
            return {
                "total_transactions": 0,
                "active_transactions": len(self.active_transactions),
                "average_duration_ms": 0,
                "success_rate": 0,
            }

        successful = [
            t
            for t in self.completed_transactions
            if t.status == TransactionStatus.COMMITTED
        ]
        failed = [
            t
            for t in self.completed_transactions
            if t.status in [TransactionStatus.ROLLED_BACK, TransactionStatus.FAILED]
        ]

        durations = [
            t.duration_ms for t in self.completed_transactions if t.duration_ms
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_transactions": len(self.completed_transactions),
            "active_transactions": len(self.active_transactions),
            "successful_transactions": len(successful),
            "failed_transactions": len(failed),
            "success_rate": len(successful) / len(self.completed_transactions)
            if self.completed_transactions
            else 0,
            "average_duration_ms": avg_duration,
            "total_queries": sum(
                t.queries_executed for t in self.completed_transactions
            ),
            "total_rows_affected": sum(
                t.rows_affected for t in self.completed_transactions
            ),
        }


# ==================== TRANSACTION CONTEXT ====================


class TransactionContext:
    """Enhanced transaction context with comprehensive tracking"""

    def __init__(
        self,
        session: AsyncSession,
        transaction: AsyncTransaction,
        config: TransactionConfig,
        transaction_id: str,
    ):
        self.session = session
        self.transaction = transaction
        self.config = config
        self.transaction_id = transaction_id
        self.metrics = TransactionMetrics(
            transaction_id=transaction_id, start_time=datetime.now()
        )
        self.savepoints: dict[str, SavepointInfo] = {}
        self._hooks: list[TransactionHook] = []
        self._is_committed = False
        self._is_rolled_back = False

    def add_hook(self, hook: TransactionHook):
        """Add transaction hook"""
        self._hooks.append(hook)

    async def create_savepoint(self, name: str | None = None) -> str:
        """Create a savepoint"""
        if not self.config.enable_savepoints:
            raise DatabaseError("Savepoints are disabled in transaction configuration")

        savepoint_name = name or f"sp_{uuid.uuid4().hex[:8]}"

        # Sanitize savepoint name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", savepoint_name):
            raise ValidationError(
                f"Invalid savepoint name: must contain only alphanumeric and underscore"
            )

        if savepoint_name in self.savepoints:
            raise ValidationError(f"Savepoint '{savepoint_name}' already exists")

        async with async_error_context(
            operation_name="create_savepoint",
            entity_id=savepoint_name,
            business_operation="savepoint_management",
        ) as ctx:
            try:
                # SQL identifier validation performed above
                await self.session.execute(text(f"SAVEPOINT {savepoint_name}"))

                savepoint_info = SavepointInfo(
                    name=savepoint_name,
                    created_at=datetime.now(),
                    transaction_id=self.transaction_id,
                )

                self.savepoints[savepoint_name] = savepoint_info
                self.metrics.savepoints_created += 1

                ctx.add_annotation(f"Savepoint '{savepoint_name}' created successfully")

                return savepoint_name

            except Exception as e:
                ctx.add_annotation(
                    f"Failed to create savepoint '{savepoint_name}': {e!s}"
                )
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to create savepoint '{savepoint_name}'",
                    operation="create_savepoint",
                    details={"savepoint_name": savepoint_name, "error": str(e)},
                )

    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a specific savepoint"""
        # Validate savepoint name
        if not re.match(r"^[a-zA-Z0-9_]+$", name):
            raise ValidationError(
                f"Invalid savepoint name: must contain only alphanumeric and underscore"
            )

        if name not in self.savepoints:
            raise ValidationError(f"Savepoint '{name}' does not exist")

        async with async_error_context(
            operation_name="rollback_to_savepoint",
            entity_id=name,
            business_operation="savepoint_rollback",
        ) as ctx:
            try:
                # SQL identifier validation performed above
                await self.session.execute(text(f"ROLLBACK TO SAVEPOINT {name}"))

                # Remove savepoints created after this one
                savepoint_time = self.savepoints[name].created_at
                to_remove = [
                    sp_name
                    for sp_name, sp_info in self.savepoints.items()
                    if sp_info.created_at > savepoint_time
                ]

                for sp_name in to_remove:
                    del self.savepoints[sp_name]

                ctx.add_annotation(
                    f"Rolled back to savepoint '{name}', removed {len(to_remove)} later savepoints"
                )

            except Exception as e:
                ctx.add_annotation(f"Failed to rollback to savepoint '{name}': {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to rollback to savepoint '{name}'",
                    operation="rollback_to_savepoint",
                    details={"savepoint_name": name, "error": str(e)},
                )

    async def release_savepoint(self, name: str) -> None:
        """Release a savepoint"""
        # Validate savepoint name
        if not re.match(r"^[a-zA-Z0-9_]+$", name):
            raise ValidationError(
                f"Invalid savepoint name: must contain only alphanumeric and underscore"
            )

        if name not in self.savepoints:
            raise ValidationError(f"Savepoint '{name}' does not exist")

        try:
            # SQL identifier validation performed above
            await self.session.execute(text(f"RELEASE SAVEPOINT {name}"))
            del self.savepoints[name]

        except Exception as e:
            await log_error(e, {}, ErrorSeverity.MEDIUM)
            raise DatabaseError(
                message=f"Failed to release savepoint '{name}'",
                operation="release_savepoint",
                details={"savepoint_name": name, "error": str(e)},
            )

    async def commit(self) -> None:
        """Commit the transaction"""
        if self._is_committed or self._is_rolled_back:
            raise DatabaseError("Transaction is already completed")

        async with async_error_context(
            operation_name="transaction_commit",
            entity_id=self.transaction_id,
            business_operation="transaction_commit",
        ) as ctx:
            try:
                await self.transaction.commit()
                self._is_committed = True

                self.metrics.mark_completed(TransactionStatus.COMMITTED)

                # Execute commit hooks
                for hook in self._hooks:
                    try:
                        await hook.after_commit(self.transaction_id, self.metrics)
                    except Exception as hook_error:
                        logger.error(f"Transaction commit hook failed: {hook_error}")

                ctx.add_annotation(
                    f"Transaction {self.transaction_id} committed successfully"
                )

            except Exception as e:
                ctx.add_annotation(f"Transaction commit failed: {e!s}")
                self.metrics.mark_completed(TransactionStatus.FAILED, str(e))

                # Execute rollback hooks
                for hook in self._hooks:
                    try:
                        await hook.after_rollback(self.transaction_id, self.metrics, e)
                    except Exception as hook_error:
                        logger.error(f"Transaction rollback hook failed: {hook_error}")

                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Transaction {self.transaction_id} commit failed",
                    operation="transaction_commit",
                    details={"transaction_id": self.transaction_id, "error": str(e)},
                )

    async def rollback(self) -> None:
        """Rollback the transaction"""
        if self._is_committed or self._is_rolled_back:
            return  # Already completed

        async with async_error_context(
            operation_name="transaction_rollback",
            entity_id=self.transaction_id,
            business_operation="transaction_rollback",
        ) as ctx:
            try:
                await self.transaction.rollback()
                self._is_rolled_back = True

                self.metrics.mark_completed(TransactionStatus.ROLLED_BACK)

                ctx.add_annotation(
                    f"Transaction {self.transaction_id} rolled back successfully"
                )

            except Exception as e:
                ctx.add_annotation(f"Transaction rollback failed: {e!s}")
                self.metrics.mark_completed(TransactionStatus.FAILED, str(e))
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                # Don't raise exception from rollback - just log it

    def is_active(self) -> bool:
        """Check if transaction is still active"""
        return not (self._is_committed or self._is_rolled_back)


# ==================== TRANSACTION MANAGER ====================


class EnhancedTransactionManager:
    """Enhanced transaction manager with comprehensive features"""

    def __init__(self, db_manager: EnhancedDatabaseManager | None = None):
        self.db_manager = db_manager or enhanced_db_manager
        self.global_hooks: list[TransactionHook] = []
        self.active_transactions: dict[str, TransactionContext] = {}
        self.metrics_hook = MetricsTransactionHook()
        self.logging_hook = LoggingTransactionHook()

        # Add default hooks
        self.add_global_hook(self.metrics_hook)
        self.add_global_hook(self.logging_hook)

    def add_global_hook(self, hook: TransactionHook):
        """Add a global transaction hook"""
        self.global_hooks.append(hook)

    def remove_global_hook(self, hook: TransactionHook):
        """Remove a global transaction hook"""
        if hook in self.global_hooks:
            self.global_hooks.remove(hook)

    @asynccontextmanager
    async def transaction(
        self,
        config: TransactionConfig | None = None,
        session: AsyncSession | None = None,
    ) -> AsyncGenerator[TransactionContext, None]:
        """Create a managed transaction context"""

        transaction_config = config or TransactionConfig()
        transaction_id = str(uuid.uuid4())

        async with async_error_context(
            operation_name="managed_transaction",
            entity_id=transaction_id,
            business_operation="transaction_management",
        ) as ctx:
            ctx.tags.update(
                {
                    "transaction_id": transaction_id,
                    "isolation_level": transaction_config.isolation_level.value
                    if transaction_config.isolation_level
                    else None,
                    "timeout_seconds": str(transaction_config.timeout_seconds)
                    if transaction_config.timeout_seconds
                    else None,
                    "read_only": str(transaction_config.read_only),
                }
            )

            # Execute before_transaction hooks
            for hook in self.global_hooks:
                try:
                    await hook.before_transaction(transaction_id, transaction_config)
                except Exception as hook_error:
                    logger.error(f"Transaction before hook failed: {hook_error}")

            # Get or create session
            if session is None:
                async with self.db_manager.get_session(
                    read_only=transaction_config.read_only,
                    isolation_level=transaction_config.isolation_level.value
                    if transaction_config.isolation_level
                    else None,
                ) as db_session, self._create_transaction_context(
                    db_session, transaction_config, transaction_id, ctx
                ) as tx_ctx:
                    yield tx_ctx
            else:
                async with self._create_transaction_context(
                    session, transaction_config, transaction_id, ctx
                ) as tx_ctx:
                    yield tx_ctx

    @asynccontextmanager
    async def _create_transaction_context(
        self,
        session: AsyncSession,
        config: TransactionConfig,
        transaction_id: str,
        error_ctx,
    ) -> AsyncGenerator[TransactionContext, None]:
        """Create transaction context with proper cleanup"""

        transaction = session.begin()
        await transaction.__aenter__()

        tx_context = TransactionContext(session, transaction, config, transaction_id)

        # Add global hooks to transaction context
        for hook in self.global_hooks:
            tx_context.add_hook(hook)

        # Track active transaction
        self.active_transactions[transaction_id] = tx_context

        try:
            # Set isolation level if specified
            if config.isolation_level:
                await session.execute(
                    text(
                        f"SET TRANSACTION ISOLATION LEVEL {config.isolation_level.value}"
                    )
                )
                tx_context.metrics.isolation_level = config.isolation_level.value

            # Set read-only if specified
            if config.read_only:
                await session.execute(text("SET TRANSACTION READ ONLY"))

            # Set timeout if specified
            if config.timeout_seconds:
                await session.execute(
                    text(f"SET statement_timeout = {config.timeout_seconds * 1000}")
                )

            error_ctx.add_annotation(
                f"Transaction {transaction_id} started successfully"
            )

            yield tx_context

            # Auto-commit if transaction is still active
            if tx_context.is_active():
                await tx_context.commit()

        except Exception as e:
            error_ctx.add_annotation(f"Transaction {transaction_id} failed: {e!s}")

            if tx_context.is_active():
                await tx_context.rollback()

            # Execute rollback hooks
            for hook in self.global_hooks:
                try:
                    await hook.after_rollback(transaction_id, tx_context.metrics, e)
                except Exception as hook_error:
                    logger.error(f"Transaction rollback hook failed: {hook_error}")

            raise

        finally:
            # Clean up
            try:
                await transaction.__aexit__(None, None, None)
            except Exception as cleanup_error:
                logger.error(f"Transaction cleanup failed: {cleanup_error}")

            # Remove from active transactions
            self.active_transactions.pop(transaction_id, None)

    async def execute_with_retry(
        self,
        operation: Callable[[TransactionContext], Awaitable[T]],
        config: TransactionConfig | None = None,
    ) -> T:
        """Execute operation with automatic retry on transient failures"""

        retry_config = config or TransactionConfig()
        last_error = None

        async with async_error_context(
            operation_name="transaction_with_retry",
            business_operation="retry_transaction",
        ) as ctx:
            ctx.tags.update(
                {
                    "max_attempts": str(retry_config.retry_attempts + 1),
                    "retry_delay": str(retry_config.retry_delay),
                }
            )

            for attempt in range(retry_config.retry_attempts + 1):
                try:
                    ctx.add_annotation(
                        f"Transaction attempt {attempt + 1}/{retry_config.retry_attempts + 1}"
                    )

                    async with self.transaction(retry_config) as tx_ctx:
                        tx_ctx.metrics.retry_count = attempt
                        result = await operation(tx_ctx)

                        if attempt > 0:
                            ctx.add_annotation(
                                f"Transaction succeeded on attempt {attempt + 1}"
                            )

                        return result

                except (OperationalError, SQLTimeoutError, IntegrityError) as e:
                    last_error = e

                    # Check if this is a retryable error
                    if (
                        self._is_retryable_error(e)
                        and attempt < retry_config.retry_attempts
                    ):
                        delay = retry_config.retry_delay * (
                            2**attempt
                        )  # Exponential backoff

                        ctx.add_annotation(
                            f"Retryable error on attempt {attempt + 1}, waiting {delay}s"
                        )
                        logger.warning(
                            f"Transaction failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                        )

                        await asyncio.sleep(delay)
                    else:
                        ctx.add_annotation(
                            "Non-retryable error or max attempts reached"
                        )
                        break

                except Exception as e:
                    # Non-retryable error
                    ctx.add_annotation(f"Non-retryable error: {type(e).__name__}")
                    await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                    raise

            # All retries exhausted
            ctx.add_annotation(f"All {retry_config.retry_attempts + 1} attempts failed")
            await log_error(last_error, ctx.to_dict(), ErrorSeverity.HIGH)

            raise DatabaseError(
                message="Transaction failed after all retry attempts",
                operation="transaction_with_retry",
                details={
                    "attempts": retry_config.retry_attempts + 1,
                    "last_error": str(last_error),
                },
            )

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable"""
        error_str = str(error).lower()

        # Common retryable error patterns
        retryable_patterns = [
            "deadlock detected",
            "connection lost",
            "connection reset",
            "timeout",
            "temporary failure",
            "serialization failure",
            "could not serialize access",
        ]

        return any(pattern in error_str for pattern in retryable_patterns)

    async def get_transaction_stats(self) -> dict[str, Any]:
        """Get comprehensive transaction statistics"""
        base_stats = self.metrics_hook.get_stats()

        return {
            **base_stats,
            "active_transactions_count": len(self.active_transactions),
            "active_transaction_ids": list(self.active_transactions.keys()),
            "global_hooks_count": len(self.global_hooks),
        }

    async def kill_transaction(
        self, transaction_id: str, reason: str = "Manual termination"
    ) -> bool:
        """Kill an active transaction (emergency use only)"""

        if transaction_id not in self.active_transactions:
            return False

        tx_context = self.active_transactions[transaction_id]

        async with async_error_context(
            operation_name="kill_transaction",
            entity_id=transaction_id,
            business_operation="transaction_termination",
        ) as ctx:
            ctx.add_annotation(f"Killing transaction {transaction_id}: {reason}")

            try:
                if tx_context.is_active():
                    await tx_context.rollback()

                logger.warning(f"Transaction {transaction_id} was killed: {reason}")
                return True

            except Exception as e:
                ctx.add_annotation(f"Failed to kill transaction: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                return False


# ==================== GLOBAL TRANSACTION MANAGER INSTANCE ====================

# Global transaction manager instance
transaction_manager = EnhancedTransactionManager()


# ==================== UTILITY FUNCTIONS ====================


@asynccontextmanager
async def managed_transaction(
    config: TransactionConfig | None = None,
) -> AsyncGenerator[TransactionContext, None]:
    """Convenience function for managed transactions"""
    async with transaction_manager.transaction(config) as tx_ctx:
        yield tx_ctx


async def execute_with_transaction_retry(
    operation: Callable[[TransactionContext], Awaitable[T]],
    config: TransactionConfig | None = None,
) -> T:
    """Convenience function for retryable transactions"""
    return await transaction_manager.execute_with_retry(operation, config)


async def get_transaction_statistics() -> dict[str, Any]:
    """Get global transaction statistics"""
    return await transaction_manager.get_transaction_stats()


# ==================== DECORATORS ====================


def transactional(config: TransactionConfig | None = None):
    """Decorator to make a function transactional"""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs) -> T:
            async def operation(tx_ctx: TransactionContext) -> T:
                # Inject transaction context if function expects it
                sig = inspect.signature(func)
                if (
                    "tx_ctx" in sig.parameters
                    or "transaction_context" in sig.parameters
                ):
                    kwargs["tx_ctx"] = tx_ctx
                elif "session" in sig.parameters:
                    kwargs["session"] = tx_ctx.session

                return await func(*args, **kwargs)

            return await execute_with_transaction_retry(operation, config)

        return wrapper

    return decorator


def retryable_transaction(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retryable transactional functions"""

    config = TransactionConfig(retry_attempts=max_attempts - 1, retry_delay=delay)
    return transactional(config)
