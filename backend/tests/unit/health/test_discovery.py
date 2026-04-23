"""
Unit Tests - Endpoint Discovery

Bu modül, EndpointDiscovery sınıfı için unit testler içerir.
"""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.discovery import EndpointDiscovery
from app.health.models import EndpointMetadata


# Test FastAPI app
def create_test_app():
    """Test için FastAPI uygulaması oluşturur."""
    app = FastAPI()

    @app.get("/api/v1/users")
    async def get_users():
        return []

    @app.post("/api/v1/users")
    async def create_user():
        return {}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/auth/login")
    async def login():
        return {}

    return app


class TestEndpointDiscovery:
    """EndpointDiscovery unit testleri."""

    def setup_method(self):
        """Test setup."""
        self.app = create_test_app()
        self.discovery = EndpointDiscovery(self.app)

    @pytest.mark.asyncio
    async def test_discover_all_endpoints(self):
        """Test: Tüm endpoint'ler keşfedilmeli."""
        endpoints = await self.discovery.discover_all_endpoints()

        # En az 4 endpoint olmalı
        assert len(endpoints) >= 4

        # Path'ler kontrol
        paths = [e.path for e in endpoints]
        assert "/api/v1/users" in paths
        assert "/health" in paths
        assert "/api/v1/auth/login" in paths

    @pytest.mark.asyncio
    async def test_discover_methods(self):
        """Test: HTTP methodları doğru keşfedilmeli."""
        endpoints = await self.discovery.discover_all_endpoints()

        # /api/v1/users için hem GET hem POST olmalı
        user_endpoints = [e for e in endpoints if e.path == "/api/v1/users"]
        methods = [e.method for e in user_endpoints]

        assert "GET" in methods
        assert "POST" in methods

    @pytest.mark.asyncio
    async def test_check_critical_endpoint_health(self):
        """Test: /health critical olarak işaretlenmeli."""
        endpoints = await self.discovery.discover_all_endpoints()

        health_endpoint = next(
            (e for e in endpoints if e.path == "/health"),
            None
        )

        assert health_endpoint is not None
        assert health_endpoint.is_critical is True

    @pytest.mark.asyncio
    async def test_check_critical_endpoint_auth(self):
        """Test: /api/v1/auth/* critical olarak işaretlenmeli."""
        endpoints = await self.discovery.discover_all_endpoints()

        auth_endpoint = next(
            (e for e in endpoints if e.path == "/api/v1/auth/login"),
            None
        )

        assert auth_endpoint is not None
        assert auth_endpoint.is_critical is True

    @pytest.mark.asyncio
    async def test_discovered_endpoints_tracked(self):
        """Test: Keşfedilen endpoint'ler tracked olmalı."""
        await self.discovery.discover_all_endpoints()

        assert len(self.discovery.discovered_endpoints) >= 4

    @pytest.mark.asyncio
    async def test_check_new_endpoints(self):
        """Test: Yeni endpoint'ler tespit edilmeli."""
        # İlk keşif
        await self.discovery.discover_all_endpoints()

        # Yeni endpoint ekle
        @self.app.get("/api/v1/new")
        async def new_endpoint():
            return {}

        new_endpoints = await self.discovery.check_new_endpoints()

        # Yeni endpoint bulunmalı
        new_paths = [e.path for e in new_endpoints]
        assert "/api/v1/new" in new_paths

    @pytest.mark.asyncio
    async def test_check_removed_endpoints(self):
        """Test: Silinen endpoint'ler tespit edilmeli."""
        # İlk keşif
        await self.discovery.discover_all_endpoints()

        # Bir endpoint'i discovered_endpoints'e ekle (sonra silinecekmiş gibi)
        self.discovery.discovered_endpoints.add("GET:/api/v1/removed")

        removed = await self.discovery.check_removed_endpoints()

        # Silinen endpoint bulunmalı
        assert "GET:/api/v1/removed" in removed

    def test_check_auth_requirement_no_deps(self):
        """Test: Dependency olmayan endpoint auth gerektirmemeli."""
        route = MagicMock(spec=APIRoute)
        route.dependencies = []
        route.security = None

        requires_auth = self.discovery._check_auth_requirement(route)

        assert requires_auth is False

    def test_check_auth_requirement_with_auth_dep(self):
        """Test: Auth dependency olan endpoint auth gerektirmeli."""
        route = MagicMock(spec=APIRoute)

        # Mock dependency with 'auth' in name
        mock_dep = MagicMock()
        mock_dep.__str__ = MagicMock(return_value="get_current_user_auth")
        route.dependencies = [mock_dep]
        route.security = None

        requires_auth = self.discovery._check_auth_requirement(route)

        assert requires_auth is True

    def test_extract_expected_status_codes_get(self):
        """Test: GET endpoint için varsayılan status codes."""
        route = MagicMock(spec=APIRoute)
        route.status_code = None
        route.methods = {"GET"}

        status_codes = self.discovery._extract_expected_status_codes(route)

        assert 200 in status_codes

    def test_extract_expected_status_codes_post(self):
        """Test: POST endpoint için 201 de eklenmeli."""
        route = MagicMock(spec=APIRoute)
        route.status_code = None
        route.methods = {"POST"}

        status_codes = self.discovery._extract_expected_status_codes(route)

        assert 200 in status_codes
        assert 201 in status_codes

    def test_extract_expected_status_codes_delete(self):
        """Test: DELETE endpoint için 204 de eklenmeli."""
        route = MagicMock(spec=APIRoute)
        route.status_code = None
        route.methods = {"DELETE"}

        status_codes = self.discovery._extract_expected_status_codes(route)

        assert 200 in status_codes
        assert 204 in status_codes


class TestEndpointDiscoveryWithRedis:
    """Redis entegrasyonlu EndpointDiscovery testleri."""

    def setup_method(self):
        """Test setup with mock Redis."""
        self.app = create_test_app()
        self.mock_redis = AsyncMock()
        self.discovery = EndpointDiscovery(self.app, self.mock_redis)

    @pytest.mark.asyncio
    async def test_store_metadata_to_redis(self):
        """Test: Metadata Redis'e kaydedilmeli."""
        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="test_handler"
        )

        await self.discovery._store_metadata(metadata)

        self.mock_redis.hset.assert_called_once()
        self.mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_endpoint_metadata_from_redis(self):
        """Test: Metadata Redis'ten alınmalı."""
        self.mock_redis.hgetall.return_value = {
            b"path": b"/api/v1/test",
            b"method": b"GET",
            b"handler": b"test_handler",
            b"requires_auth": b"False",
            b"is_critical": b"False",
            b"expected_status_codes": b"200"
        }

        metadata = await self.discovery.get_endpoint_metadata("GET", "/api/v1/test")

        assert metadata is not None
        assert metadata.path == "/api/v1/test"
        assert metadata.method == "GET"

    @pytest.mark.asyncio
    async def test_get_endpoint_metadata_not_found(self):
        """Test: Bulunamayan metadata için None döndürmeli."""
        self.mock_redis.hgetall.return_value = {}

        metadata = await self.discovery.get_endpoint_metadata("GET", "/nonexistent")

        assert metadata is None
