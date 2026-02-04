"""
Comprehensive tests for core.database module
Tests for DatabaseManager class and database utilities
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, DatabaseManager, get_db


class TestGetDb:
    """Test get_db function"""

    @pytest.mark.asyncio
    async def test_get_db_function(self):
        """Test get_db function returns mock database"""
        result = await get_db()

        assert result == {"mock_db": True}
        assert isinstance(result, dict)


class TestDatabaseManager:
    """Test DatabaseManager class"""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        db_manager = DatabaseManager()

        assert db_manager.engine is None
        assert db_manager.session_factory is None
        assert db_manager.is_initialized is False
        assert db_manager.connection_pool_size == 20
        assert db_manager.max_overflow == 30
        assert db_manager.pool_timeout == 30
        assert db_manager.pool_recycle == 3600
        assert db_manager.echo == False

    def test_database_manager_custom_initialization(self):
        """Test DatabaseManager initialization with custom parameters"""
        db_manager = DatabaseManager(
            connection_pool_size=10,
            max_overflow=15,
            pool_timeout=60,
            pool_recycle=7200,
            echo=True,
        )

        assert db_manager.connection_pool_size == 10
        assert db_manager.max_overflow == 15
        assert db_manager.pool_timeout == 60
        assert db_manager.pool_recycle == 7200
        assert db_manager.echo is True

    @pytest.mark.asyncio
    async def test_initialize_success_mock(self):
        """Test successful database initialization with mocking"""
        db_manager = DatabaseManager()

        # Mock SQLAlchemy components
        with patch("core.database.create_async_engine") as mock_create_engine, patch(
            "core.database.async_sessionmaker"
        ) as mock_sessionmaker:
            # Setup mocks
            mock_engine = AsyncMock()
            mock_create_engine.return_value = mock_engine

            mock_session_factory = MagicMock()
            mock_sessionmaker.return_value = mock_session_factory

            # Mock settings
            mock_settings = MagicMock()
            mock_settings.database_url = "postgresql+asyncpg://user:pass@localhost/db"

            with patch("core.database.settings", mock_settings):
                # Test initialization
                result = await db_manager.initialize()

                assert result is True
                assert db_manager.engine == mock_engine
                assert db_manager.session_factory == mock_session_factory
                assert db_manager.is_initialized is True

                # Verify engine creation
                mock_create_engine.assert_called_once()
                mock_sessionmaker.assert_called_once_with(
                    mock_engine,
                    expire_on_commit=False,
                    class_=AsyncMock().__class__.__bases__[0],  # AsyncSession type
                )

    @pytest.mark.asyncio
    async def test_initialize_failure_mock(self):
        """Test failed database initialization with mocking"""
        db_manager = DatabaseManager()

        # Mock create_async_engine to raise exception
        with patch("core.database.create_async_engine") as mock_create_engine:
            mock_create_engine.side_effect = Exception("Database connection failed")

            # Mock settings
            mock_settings = MagicMock()
            mock_settings.database_url = "postgresql+asyncpg://user:pass@localhost/db"

            with patch("core.database.settings", mock_settings):
                # Test initialization
                result = await db_manager.initialize()

                assert result is False
                assert db_manager.engine is None
                assert db_manager.session_factory is None
                assert db_manager.is_initialized is False

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test successful database close"""
        db_manager = DatabaseManager()

        # Setup mock engine
        mock_engine = AsyncMock()
        db_manager.engine = mock_engine
        db_manager.is_initialized = True

        # Test close
        await db_manager.close()

        # Verify cleanup
        mock_engine.dispose.assert_called_once()
        assert db_manager.engine is None
        assert db_manager.session_factory is None
        assert db_manager.is_initialized is False

    @pytest.mark.asyncio
    async def test_close_no_engine(self):
        """Test database close when no engine exists"""
        db_manager = DatabaseManager()

        # Test close without engine
        await db_manager.close()

        # Should not raise exception
        assert db_manager.engine is None
        assert db_manager.session_factory is None
        assert db_manager.is_initialized is False

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test get_session context manager success"""
        db_manager = DatabaseManager()

        # Setup mock session factory
        mock_session = AsyncMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value = mock_session

        db_manager.session_factory = mock_session_factory
        db_manager.is_initialized = True

        # Test get_session context manager
        async with db_manager.get_session() as session:
            assert session == mock_session

        # Verify session was closed
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_not_initialized(self):
        """Test get_session when database not initialized"""
        db_manager = DatabaseManager()

        # Test get_session without initialization
        with pytest.raises(RuntimeError, match="Database not initialized"):
            async with db_manager.get_session():
                pass

    @pytest.mark.asyncio
    async def test_get_session_with_exception(self):
        """Test get_session context manager with exception"""
        db_manager = DatabaseManager()

        # Setup mock session factory
        mock_session = AsyncMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value = mock_session

        db_manager.session_factory = mock_session_factory
        db_manager.is_initialized = True

        # Test get_session with exception
        with pytest.raises(ValueError):
            async with db_manager.get_session() as session:
                assert session == mock_session
                raise ValueError("Test exception")

        # Verify session was still closed
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test execute_query method success"""
        db_manager = DatabaseManager()

        # Setup mock session and result
        mock_result = MagicMock()
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Mock get_session context manager
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = False

            # Test execute_query
            result = await db_manager.execute_query("SELECT 1")

            assert result == mock_result
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self):
        """Test execute_query method with parameters"""
        db_manager = DatabaseManager()

        # Setup mock session and result
        mock_result = MagicMock()
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Mock get_session context manager
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = False

            # Test execute_query with parameters
            params = {"id": 1, "name": "test"}
            result = await db_manager.execute_query(
                "SELECT * FROM users WHERE id = :id", params
            )

            assert result == mock_result
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_transaction_success(self):
        """Test commit_transaction method success"""
        db_manager = DatabaseManager()

        # Setup mock session
        mock_session = AsyncMock()

        # Mock get_session context manager
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = False

            # Test commit_transaction
            result = await db_manager.commit_transaction(mock_session)

            assert result is True
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_transaction_failure(self):
        """Test commit_transaction method failure"""
        db_manager = DatabaseManager()

        # Setup mock session that raises exception on commit
        mock_session = AsyncMock()
        mock_session.commit.side_effect = Exception("Commit failed")

        # Test commit_transaction
        result = await db_manager.commit_transaction(mock_session)

        assert result is False
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_transaction_success(self):
        """Test rollback_transaction method success"""
        db_manager = DatabaseManager()

        # Setup mock session
        mock_session = AsyncMock()

        # Test rollback_transaction
        result = await db_manager.rollback_transaction(mock_session)

        assert result is True
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_transaction_failure(self):
        """Test rollback_transaction method failure"""
        db_manager = DatabaseManager()

        # Setup mock session that raises exception on rollback
        mock_session = AsyncMock()
        mock_session.rollback.side_effect = Exception("Rollback failed")

        # Test rollback_transaction
        result = await db_manager.rollback_transaction(mock_session)

        assert result is False
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health_check method success"""
        db_manager = DatabaseManager()
        db_manager.is_initialized = True

        # Setup mock session and result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Mock get_session context manager
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = False

            # Test health_check
            result = await db_manager.health_check()

            assert result["status"] == "healthy"
            assert result["database_connected"] is True
            assert "response_time_ms" in result
            assert result["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health_check method when not initialized"""
        db_manager = DatabaseManager()
        db_manager.is_initialized = False

        # Test health_check
        result = await db_manager.health_check()

        assert result["status"] == "unhealthy"
        assert result["database_connected"] is False
        assert result["error"] == "Database not initialized"
        assert result["response_time_ms"] == 0

    @pytest.mark.asyncio
    async def test_health_check_connection_failure(self):
        """Test health_check method with connection failure"""
        db_manager = DatabaseManager()
        db_manager.is_initialized = True

        # Mock get_session to raise exception
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")

            # Test health_check
            result = await db_manager.health_check()

            assert result["status"] == "unhealthy"
            assert result["database_connected"] is False
            assert "Connection failed" in result["error"]
            assert result["response_time_ms"] == 0

    @pytest.mark.asyncio
    async def test_get_connection_info(self):
        """Test get_connection_info method"""
        db_manager = DatabaseManager()

        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.url.drivername = "postgresql+asyncpg"
        mock_engine.url.host = "localhost"
        mock_engine.url.port = 5432
        mock_engine.url.database = "testdb"
        mock_engine.url.username = "testuser"

        db_manager.engine = mock_engine
        db_manager.is_initialized = True

        # Test get_connection_info
        result = db_manager.get_connection_info()

        assert result["driver"] == "postgresql+asyncpg"
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["database"] == "testdb"
        assert result["username"] == "testuser"
        assert result["is_initialized"] is True
        assert result["pool_size"] == 20
        assert result["max_overflow"] == 30

    def test_get_connection_info_not_initialized(self):
        """Test get_connection_info method when not initialized"""
        db_manager = DatabaseManager()

        # Test get_connection_info
        result = db_manager.get_connection_info()

        assert result["driver"] is None
        assert result["host"] is None
        assert result["port"] is None
        assert result["database"] is None
        assert result["username"] is None
        assert result["is_initialized"] is False
        assert result["pool_size"] == 20
        assert result["max_overflow"] == 30

    @pytest.mark.asyncio
    async def test_create_tables_success(self):
        """Test create_tables method success"""
        db_manager = DatabaseManager()

        # Setup mock engine
        mock_engine = AsyncMock()
        db_manager.engine = mock_engine
        db_manager.is_initialized = True

        # Mock Base.metadata.create_all
        with patch("core.database.Base") as mock_base:
            mock_metadata = AsyncMock()
            mock_base.metadata = mock_metadata

            # Test create_tables
            result = await db_manager.create_tables()

            assert result is True
            mock_metadata.create_all.assert_called_once_with(mock_engine)

    @pytest.mark.asyncio
    async def test_create_tables_not_initialized(self):
        """Test create_tables method when not initialized"""
        db_manager = DatabaseManager()

        # Test create_tables
        result = await db_manager.create_tables()

        assert result is False

    @pytest.mark.asyncio
    async def test_drop_tables_success(self):
        """Test drop_tables method success"""
        db_manager = DatabaseManager()

        # Setup mock engine
        mock_engine = AsyncMock()
        db_manager.engine = mock_engine
        db_manager.is_initialized = True

        # Mock Base.metadata.drop_all
        with patch("core.database.Base") as mock_base:
            mock_metadata = AsyncMock()
            mock_base.metadata = mock_metadata

            # Test drop_tables
            result = await db_manager.drop_tables()

            assert result is True
            mock_metadata.drop_all.assert_called_once_with(mock_engine)

    @pytest.mark.asyncio
    async def test_drop_tables_not_initialized(self):
        """Test drop_tables method when not initialized"""
        db_manager = DatabaseManager()

        # Test drop_tables
        result = await db_manager.drop_tables()

        assert result is False


class TestBase:
    """Test Base declarative_base"""

    def test_base_exists(self):
        """Test that Base exists and is callable"""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
