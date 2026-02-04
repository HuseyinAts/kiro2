"""
Database Monitoring Middleware
Database query performance tracking için middleware
Production Health Monitoring entegrasyonu ile
"""

import logging
import time
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.engine.events import event
from sqlalchemy.ext.asyncio import AsyncSession

from .production_health_monitor import record_db_metrics

logger = logging.getLogger(__name__)


class DatabaseMonitoringMiddleware:
    """Database query monitoring middleware"""

    def __init__(self):
        self.active_queries = {}
        self.query_stats = {}

    def setup_sqlalchemy_events(self, engine):
        """SQLAlchemy event listener'larını kur"""

        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, _):
            """Query başlamadan önce"""
            context._query_start_time = time.perf_counter()
            context._query_statement = statement[:100]  # İlk 100 karakter

        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, _):
            """Query tamamlandıktan sonra"""
            if hasattr(context, "_query_start_time"):
                execution_time = time.perf_counter() - context._query_start_time

                # Query type'ını tespit et
                query_type = self._detect_query_type(statement)

                # Rows affected
                rows_affected = cursor.rowcount if hasattr(cursor, "rowcount") else 0

                # Production Health Monitor'a kaydet
                record_db_metrics(
                    query_type=query_type,
                    execution_time=execution_time,
                    rows_affected=rows_affected,
                    success=True,
                )

                # Yavaş query uyarısı
                if execution_time > 1.0:
                    logger.warning(
                        f"Yavaş database query: {query_type} - {execution_time:.3f}s - "
                        f"Statement: {statement[:100]}..."
                    )

        @event.listens_for(engine.sync_engine, "handle_error")
        def handle_error(exception_context):
            """Query hatası durumunda"""
            statement = exception_context.statement
            if statement:
                query_type = self._detect_query_type(statement)

                # Hata kaydı
                record_db_metrics(
                    query_type=query_type,
                    execution_time=0.0,
                    rows_affected=0,
                    success=False,
                )

                logger.error(
                    f"Database query hatası: {query_type} - {exception_context.original_exception}"
                )

    def _detect_query_type(self, statement: str) -> str:
        """SQL statement'tan query type'ını tespit et"""

        if not statement:
            return "unknown"

        statement_upper = statement.strip().upper()

        if statement_upper.startswith("SELECT"):
            return "SELECT"
        if statement_upper.startswith("INSERT"):
            return "INSERT"
        if statement_upper.startswith("UPDATE"):
            return "UPDATE"
        if statement_upper.startswith("DELETE"):
            return "DELETE"
        if statement_upper.startswith("CREATE"):
            return "CREATE"
        if statement_upper.startswith("DROP"):
            return "DROP"
        if statement_upper.startswith("ALTER"):
            return "ALTER"
        if (
            statement_upper.startswith("BEGIN")
            or statement_upper.startswith("COMMIT")
            or statement_upper.startswith("ROLLBACK")
        ):
            return "TRANSACTION"
        return "OTHER"


@asynccontextmanager
async def monitored_db_session(
    session: AsyncSession, operation_name: str = "database_operation"
):
    """Database session monitoring context manager"""

    start_time = time.perf_counter()

    try:
        yield session

        # Başarılı işlem
        execution_time = time.perf_counter() - start_time

        record_db_metrics(
            query_type=operation_name,
            execution_time=execution_time,
            rows_affected=0,  # Session level'da bilinmiyor
            success=True,
        )

    except Exception as e:
        # Hatalı işlem
        execution_time = time.perf_counter() - start_time

        record_db_metrics(
            query_type=operation_name,
            execution_time=execution_time,
            rows_affected=0,
            success=False,
        )

        logger.error(f"Database session hatası ({operation_name}): {e}")
        raise


class AsyncDatabaseMonitor:
    """Async database operations monitoring"""

    def __init__(self):
        self.connection_pool_stats = {}

    async def monitor_connection_pool(self, engine):
        """Connection pool monitoring"""

        try:
            pool = engine.pool

            # Pool statistics
            pool_stats = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }

            self.connection_pool_stats = pool_stats

            # Production Health Monitor'a kaydet
            # Bu bilgiler production_health_monitor.py'da kullanılacak

            return pool_stats

        except Exception as e:
            logger.error(f"Connection pool monitoring hatası: {e}")
            return {}

    async def execute_monitored_query(
        self,
        session: AsyncSession,
        query: str,
        parameters: dict | None = None,
        query_type: str = "SELECT",
    ):
        """Monitored query execution"""

        start_time = time.perf_counter()
        rows_affected = 0
        success = True

        try:
            if parameters:
                result = await session.execute(text(query), parameters)
            else:
                result = await session.execute(text(query))

            # Rows affected
            if hasattr(result, "rowcount"):
                rows_affected = result.rowcount

            return result

        except Exception as e:
            success = False
            logger.error(f"Monitored query hatası: {e}")
            raise

        finally:
            execution_time = time.perf_counter() - start_time

            # Production Health Monitor'a kaydet
            record_db_metrics(
                query_type=query_type,
                execution_time=execution_time,
                rows_affected=rows_affected,
                success=success,
            )


# Global instances
db_monitoring_middleware = DatabaseMonitoringMiddleware()
async_db_monitor = AsyncDatabaseMonitor()


# Decorator for monitoring database operations
def monitor_db_operation(operation_name: str):
    """Database operation monitoring decorator"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception:
                success = False
                raise

            finally:
                execution_time = time.perf_counter() - start_time

                record_db_metrics(
                    query_type=operation_name,
                    execution_time=execution_time,
                    rows_affected=0,
                    success=success,
                )

        return wrapper

    return decorator


# Example usage functions
async def example_monitored_operations():
    """Example of monitored database operations"""

    # Örnek 1: Context manager kullanımı
    # async with monitored_db_session(session, "user_operations") as db:
    #     users = await db.execute(text("SELECT * FROM users"))

    # Örnek 2: Decorator kullanımı
    @monitor_db_operation("user_creation")
    async def create_user(session: AsyncSession, user_data: dict):
        # User creation logic
        pass

    # Örnek 3: Direct monitoring
    # result = await async_db_monitor.execute_monitored_query(
    #     session,
    #     "SELECT COUNT(*) FROM users",
    #     query_type="COUNT"
    # )
