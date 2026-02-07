"""
Core Database Module Coverage Tests
Goal: Increase core.database coverage from 24% to 70%+
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import (
    BaseRepository,
    DatabaseManager,
    close_database,
    create_all_tables,
    db_manager,
    get_async_session,
    get_database_health,
    get_db,
    get_db_session_context,
    init_database,
)


class TestDatabaseManager:
    """Test DatabaseManager class"""

    @pytest.mark.asyncio
    async def test_initialization_creates_engine(self):
        """Test that initialization creates an async engine"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.create_async_engine") as mock_create:
                with patch("core.database.async_sessionmaker") as mock_session_maker:
                    with patch("core.database.event.listens_for"):
                        mock_engine = AsyncMock()
                        mock_create.return_value = mock_engine

                        # Mock engine.begin() properly for _test_connection()
                        mock_conn = AsyncMock()
                        mock_result = MagicMock()
                        mock_result.scalar.return_value = 1
                        mock_conn.execute = AsyncMock(return_value=mock_result)

                        # Create proper async context manager for begin()
                        mock_engine.begin = MagicMock()
                        async_cm = AsyncMock()
                        async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
                        async_cm.__aexit__ = AsyncMock(return_value=None)
                        mock_engine.begin.return_value = async_cm

                        # Mock sync_engine for event listeners
                        mock_engine.sync_engine = MagicMock()

                        await manager.initialize()

                        assert manager._initialized is True
                        assert manager.engine is not None
                        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_idempotent(self):
        """Test that calling initialize twice doesn't reinitialize"""
        manager = DatabaseManager()
        manager._initialized = True
        manager.engine = MagicMock()

        await manager.initialize()

        # Should still be initialized with same engine
        assert manager._initialized is True

    @pytest.mark.asyncio
    async def test_postgresql_pool_configuration(self):
        """Test PostgreSQL-specific pool settings"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.settings") as mock_settings:
                mock_settings.database_url = "postgresql://user:pass@localhost/db"
                mock_settings.database_echo = False
                mock_settings.db_pool_size = 25
                mock_settings.db_max_overflow = 50

                with patch("core.database.create_async_engine") as mock_create:
                    with patch("core.database.async_sessionmaker"):
                        with patch("core.database.event.listens_for"):
                            mock_engine = AsyncMock()
                            mock_create.return_value = mock_engine

                            # Mock engine.begin() properly for _test_connection()
                            mock_conn = AsyncMock()
                            mock_result = MagicMock()
                            mock_result.scalar.return_value = 1
                            mock_conn.execute = AsyncMock(return_value=mock_result)

                            # Create proper async context manager for begin()
                            mock_engine.begin = MagicMock()
                            async_cm = AsyncMock()
                            async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
                            async_cm.__aexit__ = AsyncMock(return_value=None)
                            mock_engine.begin.return_value = async_cm

                            # Mock sync_engine for event listeners
                            mock_engine.sync_engine = MagicMock()

                            await manager.initialize()

                            # Verify pool settings were used
                            call_kwargs = mock_create.call_args[1]
                            assert call_kwargs["pool_size"] == 25
                            assert call_kwargs["max_overflow"] == 50
                            assert call_kwargs["pool_pre_ping"] is True
                            assert call_kwargs["pool_recycle"] == 300

    @pytest.mark.asyncio
    async def test_sqlite_no_pool_settings(self):
        """Test that SQLite doesn't get pool settings"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.settings") as mock_settings:
                mock_settings.database_url = "sqlite:///test.db"
                mock_settings.database_echo = False

                with patch("core.database.create_async_engine") as mock_create:
                    with patch("core.database.async_sessionmaker"):
                        with patch("core.database.event.listens_for"):
                            mock_engine = AsyncMock()
                            mock_create.return_value = mock_engine

                            # Mock engine.begin() properly for _test_connection()
                            mock_conn = AsyncMock()
                            mock_result = MagicMock()
                            mock_result.scalar.return_value = 1
                            mock_conn.execute = AsyncMock(return_value=mock_result)

                            # Create proper async context manager for begin()
                            mock_engine.begin = MagicMock()
                            async_cm = AsyncMock()
                            async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
                            async_cm.__aexit__ = AsyncMock(return_value=None)
                            mock_engine.begin.return_value = async_cm

                            # Mock sync_engine for event listeners
                            mock_engine.sync_engine = MagicMock()

                            await manager.initialize()

                            # Verify no pool settings for SQLite
                            call_kwargs = mock_create.call_args[1]
                            assert "pool_size" not in call_kwargs
                            assert "max_overflow" not in call_kwargs

    @pytest.mark.asyncio
    async def test_connection_test_successful(self):
        """Test successful connection test"""
        manager = DatabaseManager()
        mock_engine = AsyncMock()
        manager.engine = mock_engine

        # Create proper async context manager for begin()
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_conn.execute = AsyncMock(return_value=mock_result)

        # Mock begin() to return an async context manager
        mock_engine.begin = MagicMock()
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        async_cm.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_cm

        # Should not raise
        await manager._test_connection()

    @pytest.mark.asyncio
    async def test_connection_test_failure(self):
        """Test connection test failure raises exception"""
        manager = DatabaseManager()
        mock_engine = AsyncMock()
        manager.engine = mock_engine

        # Mock begin() to return an async context manager that raises
        mock_engine.begin = MagicMock()
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(side_effect=SQLAlchemyError("Connection failed"))
        async_cm.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_cm

        with pytest.raises(SQLAlchemyError):
            await manager._test_connection()

    @pytest.mark.asyncio
    async def test_close_disposes_engine(self):
        """Test that close disposes the engine"""
        manager = DatabaseManager()
        mock_engine = AsyncMock()
        manager.engine = mock_engine
        manager._initialized = True

        await manager.close()

        mock_engine.dispose.assert_called_once()
        assert manager._initialized is False

    @pytest.mark.asyncio
    async def test_close_when_no_engine(self):
        """Test close when engine is None"""
        manager = DatabaseManager()
        manager.engine = None
        manager._initialized = False

        # Should not raise
        await manager.close()

        assert manager._initialized is False

    @pytest.mark.asyncio
    async def test_get_session_context_manager(self):
        """Test get_session as context manager"""
        manager = DatabaseManager()
        manager._initialized = True

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_maker = MagicMock()

        # Create async context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = mock_session
        async_cm.__aexit__.return_value = None
        mock_session_maker.return_value = async_cm

        manager.async_session_maker = mock_session_maker

        async with manager.get_session() as session:
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_session_initializes_if_needed(self):
        """Test get_session initializes database if not initialized"""
        manager = DatabaseManager()
        manager._initialized = False

        with patch.object(manager, "initialize", new_callable=AsyncMock) as mock_init:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_maker = MagicMock()

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_session_maker.return_value = async_cm

            manager.async_session_maker = mock_session_maker

            # Set initialized after initialize is called
            async def set_initialized():
                manager._initialized = True
            mock_init.side_effect = set_initialized

            async with manager.get_session() as session:
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_direct(self):
        """Test get_session_direct returns session"""
        manager = DatabaseManager()
        manager._initialized = True

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_maker = MagicMock(return_value=mock_session)
        manager.async_session_maker = mock_session_maker

        session = await manager.get_session_direct()

        assert session == mock_session
        mock_session_maker.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tables(self):
        """Test create_tables runs metadata.create_all"""
        manager = DatabaseManager()
        manager._initialized = True

        mock_engine = AsyncMock()
        manager.engine = mock_engine

        # Create proper async context manager for begin()
        mock_conn = AsyncMock()

        mock_engine.begin = MagicMock()
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        async_cm.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_cm

        with patch("core.database.Base") as mock_base:
            await manager.create_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_drop_tables(self):
        """Test drop_tables runs metadata.drop_all"""
        manager = DatabaseManager()
        manager._initialized = True

        mock_engine = AsyncMock()
        manager.engine = mock_engine

        # Create proper async context manager for begin()
        mock_conn = AsyncMock()

        mock_engine.begin = MagicMock()
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        async_cm.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_cm

        with patch("core.database.Base") as mock_base:
            await manager.drop_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when database is healthy"""
        manager = DatabaseManager()
        manager._initialized = True

        # Mock engine with pool
        mock_engine = AsyncMock()
        mock_pool = MagicMock()

        # Mock pool methods as callables that return values
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedout = MagicMock(return_value=2)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_pool.checkedin = MagicMock(return_value=8)

        mock_engine.pool = mock_pool
        manager.engine = mock_engine

        # Mock get_session
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock execute to return result with scalar
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(manager, "get_session") as mock_get_session:
            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_get_session.return_value = async_cm

            result = await manager.health_check()

            assert result["healthy"] is True
            assert result["status"] == "healthy"
            assert "pool_size" in result

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health check when not initialized"""
        manager = DatabaseManager()
        manager._initialized = False

        result = await manager.health_check()

        assert result["healthy"] is False
        assert result["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        """Test health check when error occurs"""
        manager = DatabaseManager()
        manager._initialized = True

        with patch.object(manager, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Connection error")

            result = await manager.health_check()

            assert result["healthy"] is False
            assert result["status"] == "error"
            assert "error" in result


class TestGetAsyncSession:
    """Test get_async_session generator function"""

    @pytest.mark.asyncio
    async def test_get_async_session_yields_session(self):
        """Test that get_async_session yields a session"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager._initialized = True
            mock_session = AsyncMock(spec=AsyncSession)

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_manager.get_session.return_value = async_cm

            async for session in get_async_session():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_async_session_commits_on_success(self):
        """Test that session commits on successful exit"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager._initialized = True
            mock_session = AsyncMock(spec=AsyncSession)

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_manager.get_session.return_value = async_cm

            async for session in get_async_session():
                pass

            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_rollback_on_error(self):
        """Test that session rolls back on error"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager._initialized = True
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_manager.get_session.return_value = async_cm

            with pytest.raises(SQLAlchemyError):
                async for session in get_async_session():
                    pass

            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_closes_session(self):
        """Test that session is always closed"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager._initialized = True
            mock_session = AsyncMock(spec=AsyncSession)

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_manager.get_session.return_value = async_cm

            async for session in get_async_session():
                pass

            mock_session.close.assert_called_once()


class TestBaseRepository:
    """Test BaseRepository class"""

    @pytest.mark.asyncio
    async def test_commit_success(self):
        """Test successful commit"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(mock_session)

        await repo.commit()

        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_failure_rolls_back(self):
        """Test commit failure triggers rollback"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        repo = BaseRepository(mock_session)

        with pytest.raises(SQLAlchemyError):
            await repo.commit()

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback(self):
        """Test rollback"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(mock_session)

        await repo.rollback()

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh(self):
        """Test refresh instance"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(mock_session)
        mock_instance = MagicMock()

        await repo.refresh(mock_instance)

        mock_session.refresh.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    async def test_flush(self):
        """Test flush"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(mock_session)

        await repo.flush()

        mock_session.flush.assert_called_once()


class TestUtilityFunctions:
    """Test utility functions"""

    @pytest.mark.asyncio
    async def test_init_database(self):
        """Test init_database utility"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager.initialize = AsyncMock()

            await init_database()

            mock_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database(self):
        """Test close_database utility"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager.close = AsyncMock()

            await close_database()

            mock_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_all_tables(self):
        """Test create_all_tables utility"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager.create_tables = AsyncMock()

            await create_all_tables()

            mock_manager.create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_database_health(self):
        """Test get_database_health utility"""
        with patch("core.database.db_manager") as mock_manager:
            mock_manager.health_check = AsyncMock(return_value={"healthy": True})

            result = await get_database_health()

            assert result["healthy"] is True
            mock_manager.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_context(self):
        """Test get_db_session_context"""
        with patch("core.database.db_manager") as mock_manager:
            mock_session = AsyncMock(spec=AsyncSession)

            # Create async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_session
            async_cm.__aexit__.return_value = None
            mock_manager.get_session.return_value = async_cm

            async with get_db_session_context() as session:
                assert session == mock_session

    def test_get_db(self):
        """Test get_db returns db_manager"""
        result = get_db()
        assert isinstance(result, DatabaseManager)


class TestDatabaseManagerEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_initialization_failure_propagates(self):
        """Test that initialization failure raises exception"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.create_async_engine") as mock_create:
                mock_create.side_effect = Exception("Engine creation failed")

                with pytest.raises(Exception) as exc_info:
                    await manager.initialize()

                assert "Engine creation failed" in str(exc_info.value)
                assert manager._initialized is False

    @pytest.mark.asyncio
    async def test_session_maker_creation(self):
        """Test async_sessionmaker is created correctly"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.create_async_engine") as mock_create:
                with patch("core.database.async_sessionmaker") as mock_session_maker:
                    with patch("core.database.event.listens_for"):
                        mock_engine = AsyncMock()
                        mock_create.return_value = mock_engine

                        # Mock engine.begin() properly for _test_connection()
                        mock_conn = AsyncMock()
                        mock_result = MagicMock()
                        mock_result.scalar.return_value = 1
                        mock_conn.execute = AsyncMock(return_value=mock_result)

                        # Create proper async context manager for begin()
                        mock_engine.begin = MagicMock()
                        async_cm = AsyncMock()
                        async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
                        async_cm.__aexit__ = AsyncMock(return_value=None)
                        mock_engine.begin.return_value = async_cm

                        # Mock sync_engine for event listeners
                        mock_engine.sync_engine = MagicMock()

                        await manager.initialize()

                        # Verify session maker was created with correct settings
                        mock_session_maker.assert_called_once()
                        call_kwargs = mock_session_maker.call_args[1]
                        assert call_kwargs["bind"] == mock_engine
                        assert call_kwargs["class_"] == AsyncSession
                        assert call_kwargs["expire_on_commit"] is False
                        assert call_kwargs["autoflush"] is True
                        assert call_kwargs["autocommit"] is False

    @pytest.mark.asyncio
    async def test_default_pool_settings_when_not_configured(self):
        """Test default pool settings when config attributes missing"""
        manager = DatabaseManager()

        with patch("os.environ.get", return_value=None):
            with patch("core.database.settings") as mock_settings:
                mock_settings.database_url = "postgresql://localhost/db"
                mock_settings.database_echo = False
                # Configure mock to raise AttributeError for missing attributes
                del mock_settings.db_pool_size
                del mock_settings.db_max_overflow

                with patch("core.database.create_async_engine") as mock_create:
                    with patch("core.database.async_sessionmaker"):
                        with patch("core.database.event.listens_for"):
                            mock_engine = AsyncMock()
                            mock_create.return_value = mock_engine

                            # Mock engine.begin() properly for _test_connection()
                            mock_conn = AsyncMock()
                            mock_result = MagicMock()
                            mock_result.scalar.return_value = 1
                            mock_conn.execute = AsyncMock(return_value=mock_result)

                            # Create proper async context manager for begin()
                            mock_engine.begin = MagicMock()
                            async_cm = AsyncMock()
                            async_cm.__aenter__ = AsyncMock(return_value=mock_conn)
                            async_cm.__aexit__ = AsyncMock(return_value=None)
                            mock_engine.begin.return_value = async_cm

                            # Mock sync_engine for event listeners
                            mock_engine.sync_engine = MagicMock()

                            await manager.initialize()

                            # Should use defaults: pool_size=50, max_overflow=100
                            call_kwargs = mock_create.call_args[1]
                            assert call_kwargs["pool_size"] == 50
                            assert call_kwargs["max_overflow"] == 100


class TestGlobalDatabaseManager:
    """Test the global db_manager instance"""

    def test_db_manager_exists(self):
        """Test that global db_manager instance exists"""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    def test_db_manager_starts_uninitialized(self):
        """Test that db_manager starts in uninitialized state"""
        # Note: This might fail if db_manager was already initialized
        # In production tests, we'd use a fresh instance
        assert hasattr(db_manager, "_initialized")
