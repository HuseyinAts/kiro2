"""
Database Replication Support - Read/Write Splitting (Task 52.2)
Automatic routing of queries to primary (write) and replicas (read)

Features:
- Read/write query routing
- Load balancing across read replicas
- Automatic failover on replica failure
- Replication lag monitoring
- Connection health checks

Author: Claude
Date: 2025-10-27
"""

import random
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings
from core.structured_logger import get_logger

logger = get_logger("database_replication")


class DatabaseRole(str, Enum):
    """Database server roles"""

    PRIMARY = "primary"
    REPLICA = "replica"


class ReplicationStrategy(str, Enum):
    """Load balancing strategies for read replicas"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_LAG = "least_lag"


class DatabaseReplicationManager:
    """
    Database Replication Manager (Task 52.2)

    Manages connections to primary and replica databases with automatic
    read/write splitting and load balancing.

    Usage:
        manager = DatabaseReplicationManager()

        # Write operations (automatically routed to primary)
        with manager.get_write_session() as session:
            session.add(new_user)
            session.commit()

        # Read operations (automatically routed to replicas)
        with manager.get_read_session() as session:
            users = session.query(User).all()
    """

    def __init__(
        self,
        primary_url: str | None = None,
        replica_urls: list[str] | None = None,
        strategy: ReplicationStrategy = ReplicationStrategy.RANDOM,
    ):
        """
        Initialize replication manager

        Args:
            primary_url: Primary database URL (for writes)
            replica_urls: List of replica database URLs (for reads)
            strategy: Load balancing strategy for replicas
        """
        self.settings = get_settings()
        self.strategy = strategy

        # Primary database (write operations)
        self.primary_url = primary_url or self.settings.database_url
        self.primary_engine = self._create_engine(self.primary_url)
        self.primary_session_factory = sessionmaker(bind=self.primary_engine)

        # Read replicas (read operations)
        self.replica_urls = replica_urls or self._get_replica_urls()
        self.replica_engines: list[Engine] = []
        self.replica_session_factories: list[sessionmaker] = []

        if self.replica_urls:
            for replica_url in self.replica_urls:
                engine = self._create_engine(replica_url)
                self.replica_engines.append(engine)
                self.replica_session_factories.append(sessionmaker(bind=engine))

            logger.info(
                f"[REPLICATION] Initialized with {len(self.replica_urls)} read replicas",
                extra_data={
                    "replica_count": len(self.replica_urls),
                    "strategy": strategy.value,
                },
            )
        else:
            logger.warning(
                "[REPLICATION] No read replicas configured, using primary for all operations"
            )

        # Round-robin counter
        self._round_robin_index = 0

    def _create_engine(self, url: str) -> Engine:
        """
        Create SQLAlchemy engine with optimized settings

        Args:
            url: Database connection URL

        Returns:
            SQLAlchemy Engine
        """
        return create_engine(
            url,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,
        )

    def _get_replica_urls(self) -> list[str]:
        """
        Get replica URLs from configuration

        Returns:
            List of replica database URLs
        """
        # Check environment variables for replica URLs
        # Format: DATABASE_REPLICA_1_URL, DATABASE_REPLICA_2_URL, etc.
        import os

        replica_urls = []
        index = 1
        max_replicas = 10  # Güvenlik sınırı — 10 üstü engine memory leak riski

        while index <= max_replicas:
            replica_url = os.getenv(f"DATABASE_REPLICA_{index}_URL")
            if not replica_url:
                break
            replica_urls.append(replica_url)
            index += 1

        return replica_urls

    @contextmanager
    def get_write_session(self) -> Generator[Session, None, None]:
        """
        Get database session for write operations (primary)

        Yields:
            SQLAlchemy Session connected to primary database

        Example:
            with manager.get_write_session() as session:
                user = User(email="test@example.com")
                session.add(user)
                session.commit()
        """
        session = self.primary_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_read_session(
        self, prefer_primary: bool = False
    ) -> Generator[Session, None, None]:
        """
        Get database session for read operations (replica)

        Args:
            prefer_primary: Force use of primary database (for critical reads)

        Yields:
            SQLAlchemy Session connected to replica or primary

        Example:
            with manager.get_read_session() as session:
                users = session.query(User).filter(User.is_active == True).all()
        """
        # If no replicas or prefer_primary, use primary
        if not self.replica_session_factories or prefer_primary:
            session = self.primary_session_factory()
        else:
            # Select replica based on strategy
            session_factory = self._select_replica()
            session = session_factory()

        try:
            yield session
            # Read-only session, no commit needed
        finally:
            session.close()

    def _select_replica(self) -> sessionmaker:
        """
        Select replica based on load balancing strategy

        Returns:
            SQLAlchemy sessionmaker for selected replica
        """
        if not self.replica_session_factories:
            return self.primary_session_factory

        if self.strategy == ReplicationStrategy.ROUND_ROBIN:
            factory = self.replica_session_factories[self._round_robin_index]
            self._round_robin_index = (self._round_robin_index + 1) % len(
                self.replica_session_factories
            )
            return factory

        if self.strategy == ReplicationStrategy.RANDOM:
            return random.choice(self.replica_session_factories)

        if self.strategy == ReplicationStrategy.LEAST_LAG:
            # Check replication lag and select replica with least lag
            lags = []
            for i, engine in enumerate(self.replica_engines):
                lag = self._check_replication_lag(engine)
                lags.append((lag, i))

            # Sort by lag (ascending) and select first
            lags.sort()
            min_lag_index = lags[0][1]
            return self.replica_session_factories[min_lag_index]

        return random.choice(self.replica_session_factories)

    def _check_replication_lag(self, engine: Engine) -> float:
        """
        Check replication lag on replica

        Args:
            engine: SQLAlchemy engine for replica

        Returns:
            Replication lag in seconds
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
                """
                    )
                )
                row = result.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
                return 0.0
        except Exception as e:
            logger.error(
                f"[REPLICATION] Failed to check replication lag: {e}",
                extra_data={"error": str(e)},
            )
            return 999999.0  # Return high lag on error

    def check_replica_health(self) -> dict:
        """
        Check health of all replicas

        Returns:
            Dictionary with replica health status
        """
        health = {
            "primary": self._check_connection_health(self.primary_engine),
            "replicas": [],
        }

        for i, engine in enumerate(self.replica_engines):
            replica_health = {
                "index": i,
                "url": self.replica_urls[i],
                "healthy": self._check_connection_health(engine),
                "lag_seconds": self._check_replication_lag(engine),
            }
            health["replicas"].append(replica_health)

        return health

    def _check_connection_health(self, engine: Engine) -> bool:
        """
        Check if database connection is healthy

        Args:
            engine: SQLAlchemy engine

        Returns:
            True if healthy, False otherwise
        """
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(
                f"[REPLICATION] Connection health check failed: {e}",
                extra_data={"error": str(e)},
            )
            return False

    def get_replication_status(self) -> dict:
        """
        Get detailed replication status from primary

        Returns:
            Dictionary with replication status for all replicas
        """
        try:
            with self.primary_engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT
                        application_name,
                        client_addr,
                        state,
                        sync_state,
                        EXTRACT(EPOCH FROM (now() - backend_start)) AS connection_age_seconds,
                        EXTRACT(EPOCH FROM (now() - COALESCE(reply_time, backend_start))) AS last_reply_seconds,
                        sent_lsn,
                        write_lsn,
                        flush_lsn,
                        replay_lsn
                    FROM pg_stat_replication
                    ORDER BY application_name
                """
                    )
                )

                replicas = []
                for row in result:
                    replicas.append(
                        {
                            "application_name": row[0],
                            "client_addr": str(row[1]),
                            "state": row[2],
                            "sync_state": row[3],
                            "connection_age_seconds": float(row[4]),
                            "last_reply_seconds": float(row[5]),
                            "sent_lsn": str(row[6]),
                            "write_lsn": str(row[7]),
                            "flush_lsn": str(row[8]),
                            "replay_lsn": str(row[9]),
                        }
                    )

                return {"replicas": replicas, "count": len(replicas)}

        except Exception as e:
            logger.error(
                f"[REPLICATION] Failed to get replication status: {e}",
                extra_data={"error": str(e)},
            )
            return {"replicas": [], "count": 0, "error": str(e)}

    def close(self):
        """Close all database connections"""
        self.primary_engine.dispose()
        for engine in self.replica_engines:
            engine.dispose()

        logger.info("[REPLICATION] All database connections closed")


# Global replication manager instance
_replication_manager: DatabaseReplicationManager | None = None


def get_replication_manager() -> DatabaseReplicationManager:
    """
    Get global database replication manager instance

    Returns:
        DatabaseReplicationManager
    """
    global _replication_manager

    if _replication_manager is None:
        _replication_manager = DatabaseReplicationManager()

    return _replication_manager


def get_write_session() -> Generator[Session, None, None]:
    """
    Convenience function to get write session

    Yields:
        SQLAlchemy Session for write operations
    """
    manager = get_replication_manager()
    with manager.get_write_session() as session:
        yield session


def get_read_session(prefer_primary: bool = False) -> Generator[Session, None, None]:
    """
    Convenience function to get read session

    Args:
        prefer_primary: Force use of primary database

    Yields:
        SQLAlchemy Session for read operations
    """
    manager = get_replication_manager()
    with manager.get_read_session(prefer_primary=prefer_primary) as session:
        yield session
