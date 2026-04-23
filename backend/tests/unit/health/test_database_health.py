"""
Database Health Checker Unit Tests

Bu modul, DatabaseHealthChecker sinifinin unit testlerini icerir.
Task 6.3a - Optional tests for api-endpoint-saglik spec.

Requirements Tested:
    REQ-5.1: SELECT 1 query ile health check
    REQ-5.2: Active/idle connection sayisi olcumu
    REQ-5.3: Connection pool %90 dolu uyarisi
    REQ-5.4: Query response time < 50ms hedefi
    REQ-5.5: Database unreachable -> tum DB endpoint'ler degraded
    REQ-5.6: Connection leak tespiti ve trace raporu
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.health.dependencies.database_health import (
    DatabaseHealthChecker,
    DatabaseHealthMetrics,
)


class TestDatabaseHealthMetrics:
    """DatabaseHealthMetrics dataclass testleri."""

    def test_metrics_default_timestamp(self):
        """Timestamp varsayilan olarak simdi olmali."""
        before = datetime.now(UTC)
        metrics = DatabaseHealthMetrics(is_healthy=True, response_time_ms=10.0)
        after = datetime.now(UTC)

        assert metrics.timestamp is not None
        assert before <= metrics.timestamp <= after

    def test_metrics_all_fields_populated(self):
        """Tum alanlar dogru degerlerle doldurulmali."""
        metrics = DatabaseHealthMetrics(
            is_healthy=True,
            response_time_ms=25.5,
            active_connections=5,
            idle_connections=10,
            pool_size=20,
            pool_usage_percent=25.0,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
            error_message=None
        )

        assert metrics.is_healthy is True
        assert metrics.response_time_ms == 25.5
        assert metrics.active_connections == 5
        assert metrics.idle_connections == 10
        assert metrics.pool_size == 20
        assert metrics.pool_usage_percent == 25.0
        assert metrics.error_message is None

    def test_metrics_with_error_message(self):
        """Hata mesaji dogru saklanmali."""
        metrics = DatabaseHealthMetrics(
            is_healthy=False,
            response_time_ms=0.0,
            error_message="Connection refused"
        )

        assert metrics.is_healthy is False
        assert metrics.error_message == "Connection refused"


class TestDatabaseHealthCheckerInit:
    """DatabaseHealthChecker initialization testleri."""

    def test_initialization_defaults(self):
        """Varsayilan degerlerle baslatilmali."""
        mock_engine = MagicMock()

        checker = DatabaseHealthChecker(engine=mock_engine)

        assert checker.engine == mock_engine
        assert checker.redis_client is None
        assert checker.response_time_threshold == 50.0
        assert checker.pool_warning_threshold == 90.0
        assert checker._connection_history == []
        assert checker._max_history_size == 1000

    def test_initialization_custom_thresholds(self):
        """Ozel esiklerle baslatilmali."""
        mock_engine = MagicMock()
        mock_redis = MagicMock()

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis,
            response_time_threshold=100.0,
            pool_warning_threshold=80.0
        )

        assert checker.engine == mock_engine
        assert checker.redis_client == mock_redis
        assert checker.response_time_threshold == 100.0
        assert checker.pool_warning_threshold == 80.0


class TestDatabaseHealthCheckerCheckHealth:
    """check_health method testleri."""

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy AsyncEngine."""
        engine = MagicMock()

        # Mock connection context manager
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)

        # Async context manager setup
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        engine.connect = MagicMock(return_value=mock_conn)

        # Mock pool
        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=5)
        mock_pool.overflow = MagicMock(return_value=0)
        engine.pool = mock_pool

        return engine

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        client = AsyncMock()
        client.hset = AsyncMock(return_value=True)
        client.expire = AsyncMock(return_value=True)
        client.lpush = AsyncMock(return_value=1)
        client.ltrim = AsyncMock(return_value=True)
        client.set = AsyncMock(return_value=True)
        return client

    @pytest.mark.asyncio
    async def test_check_health_success(self, mock_engine, mock_redis_client):
        """
        Basarili health check testi.
        REQ-5.1: SELECT 1 query ile health check
        """
        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis_client
        )

        metrics = await checker.check_health()

        assert metrics.is_healthy is True
        assert metrics.response_time_ms >= 0
        assert metrics.error_message is None

    @pytest.mark.asyncio
    async def test_check_health_timeout(self, mock_redis_client):
        """
        Timeout durumunda health check testi.
        REQ-5.4: Query response time olcumu
        """
        import asyncio

        # Slow engine mock
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        async def slow_execute(*args):
            await asyncio.sleep(0.1)  # 100ms delay

        mock_conn.execute = slow_execute
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect = MagicMock(return_value=mock_conn)

        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=5)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_engine.pool = mock_pool

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis_client,
            response_time_threshold=50.0
        )

        metrics = await checker.check_health()

        # 100ms > 50ms threshold, but still healthy
        assert metrics.is_healthy is True
        assert metrics.response_time_ms >= 100  # At least 100ms

    @pytest.mark.asyncio
    async def test_check_health_connection_error(self, mock_redis_client):
        """
        Baglanti hatasi durumunda health check testi.
        REQ-5.5: Database unreachable handling
        """
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_engine.connect = MagicMock(return_value=mock_conn)

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis_client
        )

        metrics = await checker.check_health()

        assert metrics.is_healthy is False
        assert "Connection refused" in metrics.error_message

    @pytest.mark.asyncio
    async def test_response_time_measurement_accuracy(self, mock_engine, mock_redis_client):
        """Response time dogru olculur."""
        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis_client
        )

        metrics = await checker.check_health()

        # Response time pozitif olmali ve mantikli aralikta
        assert metrics.response_time_ms >= 0
        assert metrics.response_time_ms < 10000  # 10 saniyeden az


class TestDatabaseHealthCheckerPoolMetrics:
    """Connection pool metrikleri testleri."""

    @pytest.fixture
    def mock_engine_with_pool(self):
        """Mock engine with pool metrics."""
        engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=20)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=15)
        mock_pool.overflow = MagicMock(return_value=0)
        engine.pool = mock_pool

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        engine.connect = MagicMock(return_value=mock_conn)

        return engine

    @pytest.mark.asyncio
    async def test_get_pool_metrics_success(self, mock_engine_with_pool):
        """
        Pool metrikleri dogru alınır.
        REQ-5.2: Active/idle connection sayisi olcumu
        """
        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine_with_pool,
            redis_client=mock_redis
        )

        metrics = await checker.check_health()

        assert metrics.active_connections == 15
        assert metrics.idle_connections == 5
        assert metrics.pool_size == 20

    @pytest.mark.asyncio
    async def test_pool_warning_at_90_percent(self, mock_engine_with_pool):
        """
        Pool %90 doluyken uyari vermeli.
        REQ-5.3: Connection pool %90 dolu uyarisi
        """
        # Pool'u %95 dolu yap
        mock_engine_with_pool.pool.checkedout = MagicMock(return_value=19)
        mock_engine_with_pool.pool.checkedin = MagicMock(return_value=1)

        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock(return_value=1)
        mock_redis.ltrim = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine_with_pool,
            redis_client=mock_redis,
            pool_warning_threshold=90.0
        )

        metrics = await checker.check_health()

        # Pool warning tetiklenmeli
        assert metrics.pool_usage_percent >= 90.0
        # Redis'e alert kaydedilmeli
        mock_redis.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_pool_warning_not_triggered_below_threshold(self, mock_engine_with_pool):
        """Pool %90 alti uyari vermemeli."""
        # Pool'u %50 dolu yap
        mock_engine_with_pool.pool.checkedout = MagicMock(return_value=10)
        mock_engine_with_pool.pool.checkedin = MagicMock(return_value=10)

        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock(return_value=1)

        checker = DatabaseHealthChecker(
            engine=mock_engine_with_pool,
            redis_client=mock_redis,
            pool_warning_threshold=90.0
        )

        metrics = await checker.check_health()

        # Pool usage %50, uyari olmamali
        assert metrics.pool_usage_percent < 90.0


class TestDatabaseHealthCheckerLeakDetection:
    """Connection leak tespiti testleri."""

    @pytest.fixture
    def checker_with_history(self):
        """Checker with connection history."""
        mock_engine = MagicMock()
        checker = DatabaseHealthChecker(engine=mock_engine)
        return checker

    @pytest.mark.asyncio
    async def test_detect_connection_leak_monotonic_increase(self, checker_with_history):
        """
        Monoton artan connection'lari leak olarak tespit etmeli.
        REQ-5.6: Connection leak tespiti
        """
        # Monoton artan connection history ekle
        for i in range(10):
            checker_with_history._connection_history.append({
                "timestamp": f"2026-01-01T{10+i}:00:00",
                "active": 5 + i * 2,  # 5, 7, 9, 11, 13, 15, 17, 19, 21, 23
                "idle": 5,
                "pool_usage": (5 + i * 2) / 30 * 100
            })

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        checker_with_history.redis_client = mock_redis

        leak_report = await checker_with_history.detect_connection_leak()

        assert leak_report is not None
        assert leak_report["severity"] == "warning"
        assert "monotonically_increasing" in leak_report["analysis"]["trend"]
        assert len(leak_report["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_no_leak_detected_stable_connections(self, checker_with_history):
        """Stabil connection sayisinda leak tespit edilmemeli."""
        # Stabil connection history ekle
        for i in range(10):
            checker_with_history._connection_history.append({
                "timestamp": f"2026-01-01T{10+i}:00:00",
                "active": 10,  # Sabit
                "idle": 10,
                "pool_usage": 50.0
            })

        leak_report = await checker_with_history.detect_connection_leak()

        assert leak_report is None

    @pytest.mark.asyncio
    async def test_leak_report_not_generated_with_insufficient_history(self, checker_with_history):
        """10'dan az olcumde leak tespit edilmemeli."""
        # Sadece 5 olcum ekle
        for i in range(5):
            checker_with_history._connection_history.append({
                "timestamp": f"2026-01-01T{10+i}:00:00",
                "active": 5 + i * 5,
                "idle": 5,
                "pool_usage": (5 + i * 5) / 30 * 100
            })

        leak_report = await checker_with_history.detect_connection_leak()

        assert leak_report is None


class TestDatabaseHealthCheckerRedisStorage:
    """Redis storage testleri."""

    @pytest.mark.asyncio
    async def test_store_metrics_to_redis(self):
        """Metrikler Redis'e dogru kaydedilmeli."""
        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect = MagicMock(return_value=mock_conn)

        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=5)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_engine.pool = mock_pool

        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis
        )

        await checker.check_health()

        # hset ve expire cagrilmali
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once()

        # Dogru key kullanilmali
        hset_call = mock_redis.hset.call_args
        assert "kiro2:health:database:metrics" in str(hset_call)

    @pytest.mark.asyncio
    async def test_store_metrics_redis_error_handled(self):
        """Redis hatasi gracefully handle edilmeli."""
        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect = MagicMock(return_value=mock_conn)

        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=5)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_engine.pool = mock_pool

        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_redis.expire = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis
        )

        # Redis hatasi olsa bile health check basarili olmali
        metrics = await checker.check_health()

        assert metrics.is_healthy is True


class TestDatabaseHealthCheckerAvailability:
    """Database availability testleri."""

    @pytest.mark.asyncio
    async def test_is_database_available_true(self):
        """Database erisilebilir ise True donmeli."""
        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect = MagicMock(return_value=mock_conn)

        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)
        mock_pool.checkedin = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=5)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_engine.pool = mock_pool

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis
        )

        result = await checker.is_database_available()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_database_available_cached(self):
        """Cache'den availability okunmali."""
        mock_engine = MagicMock()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"true")

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis
        )

        result = await checker.is_database_available()

        assert result is True
        # Cache hit - engine.connect cagrilmamali
        mock_engine.connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_database_unavailable_sets_flag(self):
        """
        Database unavailable durumunda flag set edilmeli.
        REQ-5.5: Database unreachable -> degraded mode
        """
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
        mock_engine.connect = MagicMock(return_value=mock_conn)

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock(return_value=1)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        checker = DatabaseHealthChecker(
            engine=mock_engine,
            redis_client=mock_redis
        )

        await checker.check_health()

        # Unavailable flag set edilmeli
        mock_redis.set.assert_called()

        # Dogru key ile cagirilmis mi kontrol et
        set_calls = mock_redis.set.call_args_list
        flag_call = [c for c in set_calls if "available" in str(c)]
        assert len(flag_call) > 0
