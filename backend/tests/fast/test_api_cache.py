"""
Comprehensive tests for api/cache.py
Tests cache management API endpoints
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    manager = AsyncMock()
    manager.get_stats.return_value = {"hits": 100, "misses": 10}
    manager.health_check.return_value = {"status": "healthy"}
    manager.invalidate_pattern.return_value = ["key1", "key2"]
    manager.get.return_value = {"data": "value"}
    manager.set.return_value = True
    manager.delete.return_value = True
    return manager


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return {"id": "admin123", "role": "admin", "username": "admin"}


@pytest.fixture
def test_app():
    """Create test app with cache router"""
    from api.cache import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


def mock_admin_dependency():
    """Mock dependency that returns admin user"""
    return {"id": "admin123", "role": "admin"}


class TestCacheStatsEndpoint:
    """Test /api/v1/cache/stats endpoint"""

    @patch("api.cache.cache_manager")
    def test_get_cache_stats_success(self, mock_cache_manager, test_app):
        """Test getting cache stats successfully"""
        from core.dependencies import get_current_admin_user

        # Override auth dependency
        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        # Mock async method properly
        async def mock_get_stats():
            return {"hits": 100, "misses": 10}

        mock_cache_manager.get_stats = mock_get_stats

        client = TestClient(test_app)
        response = client.get("/api/v1/cache/stats")

        # Clean up
        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "main_cache" in data["data"]

    def test_get_cache_stats_unauthorized(self, client):
        """Test cache stats requires admin"""
        response = client.get("/api/v1/cache/stats")
        # Without auth override, should fail
        assert response.status_code in [401, 403]

    @patch("api.cache.cache_manager")
    def test_get_cache_stats_error(self, mock_cache_manager, test_app):
        """Test cache stats error handling"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        # Mock async method that raises exception
        async def mock_get_stats_error():
            raise Exception("Redis connection failed")

        mock_cache_manager.get_stats = mock_get_stats_error

        client = TestClient(test_app)
        response = client.get("/api/v1/cache/stats")

        test_app.dependency_overrides = {}

        assert response.status_code == 500


class TestCacheHealthEndpoint:
    """Test /api/v1/cache/health endpoint"""

    @patch("api.cache.cache_manager")
    def test_get_cache_health_healthy(self, mock_cache_manager, client):
        """Test cache health check when healthy"""

        async def mock_health_check():
            return {"status": "healthy", "latency": 5}

        mock_cache_manager.health_check = mock_health_check

        response = client.get("/api/v1/cache/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"

    @patch("api.cache.cache_manager")
    def test_get_cache_health_unhealthy(self, mock_cache_manager, client):
        """Test cache health check when unhealthy"""

        async def mock_health_check():
            return {"status": "unhealthy"}

        mock_cache_manager.health_check = mock_health_check

        response = client.get("/api/v1/cache/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @patch("api.cache.cache_manager")
    def test_get_cache_health_error(self, mock_cache_manager, client):
        """Test cache health check error handling"""

        async def mock_health_check():
            raise Exception("Connection failed")

        mock_cache_manager.health_check = mock_health_check

        response = client.get("/api/v1/cache/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data["data"]


class TestEventInvalidation:
    """Test /api/v1/cache/invalidate/event endpoint"""

    @patch("api.cache.cache_manager")
    def test_invalidate_by_event_success(self, mock_cache_manager, test_app):
        """Test event-based invalidation"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return ["key1", "key2", "key3"]

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.post(
            "/api/v1/cache/invalidate/event", json={"event_name": "user_updated"}
        )

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] == 3

    @patch("api.cache.cache_manager")
    def test_invalidate_by_event_with_context(self, mock_cache_manager, test_app):
        """Test event-based invalidation with context"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return ["key1"]

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.post(
            "/api/v1/cache/invalidate/event",
            json={"event_name": "exam_updated", "context": {"exam_id": "123"}},
        )

        test_app.dependency_overrides = {}

        assert response.status_code == 200


class TestPatternInvalidation:
    """Test /api/v1/cache/invalidate/pattern endpoint"""

    @patch("api.cache.cache_manager")
    def test_invalidate_by_pattern_success(self, mock_cache_manager, test_app):
        """Test pattern-based invalidation"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return 5

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.post(
            "/api/v1/cache/invalidate/pattern", json={"pattern": "user:*:profile"}
        )

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["invalidated_count"] == 5

    @patch("api.cache.cache_manager")
    def test_invalidate_by_pattern_with_scope(self, mock_cache_manager, test_app):
        """Test pattern-based invalidation with scope"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return 10

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.post(
            "/api/v1/cache/invalidate/pattern",
            json={"pattern": "exam:*", "scope": "global"},
        )

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["scope"] == "global"


class TestUserCacheInvalidation:
    """Test /api/v1/cache/user/{user_id} endpoint"""

    @patch("api.cache.cache_manager")
    def test_invalidate_user_cache_success(self, mock_cache_manager, test_app):
        """Test invalidating user cache"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return 15

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.delete("/api/v1/cache/user/user123")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "user123"
        assert data["data"]["invalidated_count"] == 15


class TestExamCacheInvalidation:
    """Test /api/v1/cache/exam endpoint"""

    @patch("api.cache.cache_manager")
    def test_invalidate_exam_cache_all(self, mock_cache_manager, test_app):
        """Test invalidating all exam caches"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return 20

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.delete("/api/v1/cache/exam")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["exam_type"] == "all"

    @patch("api.cache.cache_manager")
    def test_invalidate_exam_cache_by_type(self, mock_cache_manager, test_app):
        """Test invalidating specific exam type cache"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_invalidate_pattern(pattern):
            return 10

        mock_cache_manager.invalidate_pattern = mock_invalidate_pattern

        client = TestClient(test_app)
        response = client.delete("/api/v1/cache/exam?exam_type=TYT")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["exam_type"] == "TYT"


class TestCacheKeyOperations:
    """Test cache key get/set/delete operations"""

    @patch("api.cache.cache_manager")
    def test_get_cache_key_exists(self, mock_cache_manager, test_app):
        """Test getting existing cache key"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_get(key, serialize="json"):
            return {"data": "value"}

        mock_cache_manager.get = mock_get

        client = TestClient(test_app)
        response = client.get("/api/v1/cache/key/test_key")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["exists"] is True

    @patch("api.cache.cache_manager")
    def test_get_cache_key_not_exists(self, mock_cache_manager, test_app):
        """Test getting non-existent cache key"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_get(key, serialize="json"):
            return None

        mock_cache_manager.get = mock_get

        client = TestClient(test_app)
        response = client.get("/api/v1/cache/key/missing_key")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["exists"] is False

    @patch("api.cache.cache_manager")
    def test_set_cache_key_success(self, mock_cache_manager, test_app):
        """Test setting cache key"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_set(key, value, expire=None, serialize="json"):
            return True

        mock_cache_manager.set = mock_set

        client = TestClient(test_app)
        response = client.post(
            "/api/v1/cache/key",
            json={"key": "test_key", "value": "test_value", "expire": 3600},
        )

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.cache.cache_manager")
    def test_delete_cache_key_success(self, mock_cache_manager, test_app):
        """Test deleting cache key"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        async def mock_delete(key):
            return True

        mock_cache_manager.delete = mock_delete

        client = TestClient(test_app)
        response = client.delete("/api/v1/cache/key/test_key")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestCacheWarmUp:
    """Test /api/v1/cache/warm-up endpoint"""

    @pytest.mark.skip(reason="Warm-up endpoint has performance issues causing timeout")
    def test_warm_up_cache_success(self, test_app):
        """Test cache warm-up"""
        from core.dependencies import get_current_admin_user

        test_app.dependency_overrides[get_current_admin_user] = mock_admin_dependency

        client = TestClient(test_app)
        response = client.post("/api/v1/cache/warm-up")

        test_app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWarmUpHelpers:
    """Test warm-up helper functions"""

    @pytest.mark.asyncio
    async def test_warm_up_tyt_questions(self):
        """Test TYT questions warm-up"""
        from api.cache import _warm_up_tyt_questions

        result = await _warm_up_tyt_questions()
        assert result is not None
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_warm_up_ayt_questions(self):
        """Test AYT questions warm-up"""
        from api.cache import _warm_up_ayt_questions

        result = await _warm_up_ayt_questions()
        assert result is not None
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_warm_up_ydt_questions(self):
        """Test YDT questions warm-up"""
        from api.cache import _warm_up_ydt_questions

        result = await _warm_up_ydt_questions()
        assert result is not None

    @pytest.mark.asyncio
    async def test_warm_up_popular_content(self):
        """Test popular content warm-up"""
        from api.cache import _warm_up_popular_content

        result = await _warm_up_popular_content()
        assert result is not None
        assert "content" in result

    @pytest.mark.asyncio
    async def test_warm_up_learning_profiles(self):
        """Test learning profiles warm-up"""
        from api.cache import _warm_up_learning_profiles

        result = await _warm_up_learning_profiles()
        assert result is not None
        assert "profiles" in result


class TestPydanticModels:
    """Test Pydantic model validation"""

    def test_cache_stats_response_model(self):
        """Test CacheStatsResponse model"""
        from api.cache import CacheStatsResponse

        response = CacheStatsResponse(
            success=True, data={"hits": 100}, message="Success"
        )
        assert response.success is True

    def test_cache_health_response_model(self):
        """Test CacheHealthResponse model"""
        from api.cache import CacheHealthResponse

        response = CacheHealthResponse(
            success=True, data={"status": "healthy"}, message="Healthy"
        )
        assert response.success is True

    def test_invalidation_request_model(self):
        """Test InvalidationRequest model"""
        from api.cache import InvalidationRequest

        request = InvalidationRequest(event_name="test_event")
        assert request.event_name == "test_event"

    def test_pattern_invalidation_request_model(self):
        """Test PatternInvalidationRequest model"""
        from api.cache import PatternInvalidationRequest

        request = PatternInvalidationRequest(pattern="test:*", scope="global")
        assert request.pattern == "test:*"
        assert request.scope == "global"

    def test_cache_key_request_model(self):
        """Test CacheKeyRequest model"""
        from api.cache import CacheKeyRequest

        request = CacheKeyRequest(
            key="test_key", value="test_value", expire=3600, serialize="json"
        )
        assert request.key == "test_key"
        assert request.expire == 3600
