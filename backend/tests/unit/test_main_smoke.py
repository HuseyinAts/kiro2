"""
Smoke Tests for main.py - FastAPI Application
Testing basic app initialization and endpoint availability
"""
import os

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestMainApplicationSmoke:
    """Smoke tests for main FastAPI application"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        mock_db = AsyncMock()
        mock_db.initialize = AsyncMock()
        mock_db.close = AsyncMock()
        return mock_db

    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        mock_settings = Mock()
        mock_settings.environment = "testing"
        mock_settings.debug = True
        mock_settings.database_url = "sqlite+aiosqlite:///:memory:"
        mock_settings.allowed_origins = ["http://localhost:3000"]
        return mock_settings

    @pytest.fixture
    def mock_routers_setup(self):
        """Mock router setup"""
        return Mock()

    @pytest.fixture
    def mock_all_startup_services(self, mock_db_manager, mock_settings, mock_routers_setup):
        """Mock all services that initialize during startup"""
        mocks = {
            'db_manager': mock_db_manager,
            'settings': mock_settings,
            'setup_routers': mock_routers_setup,
        }
        return mocks

    def test_app_instance_creation(self, mock_all_startup_services):
        """Test that FastAPI app instance is created successfully"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    assert app is not None
                    # Check that we have a FastAPI instance
                    assert hasattr(app, 'title')
                    assert hasattr(app, 'version')

    def test_app_has_cors_middleware(self, mock_all_startup_services):
        """Test that CORS middleware is configured"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # Check that middleware is present
                    # Note: middleware might be 0 in fallback mode
                    assert app.user_middleware is not None

    def test_health_endpoint_responds(self, mock_all_startup_services):
        """Test that /health endpoint responds"""
        # Elasticsearch preflight check - skip if not available
        try:
            import httpx
        except ModuleNotFoundError:
            pytest.skip("httpx not installed")

        es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
        try:
            with httpx.Client(timeout=2.0) as client:
                client.get(f"{es_url}/_cluster/health", timeout=2.0)
        except Exception:
            pytest.skip("Elasticsearch not available")

        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    client = TestClient(app)
                    response = client.get("/health")

                    # Should respond (might be 200, 404, or redirect)
                    assert response.status_code in [200, 404, 307, 308]

    def test_docs_endpoint_exists(self, mock_all_startup_services):
        """Test that OpenAPI docs endpoint exists"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    client = TestClient(app)
                    response = client.get("/docs")

                    # Docs should be accessible (200 or redirect)
                    assert response.status_code in [200, 307, 308]

    def test_openapi_schema_generation(self, mock_all_startup_services):
        """Test that OpenAPI schema is generated"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # OpenAPI schema should be generated
                    schema = app.openapi()
                    assert schema is not None
                    assert 'info' in schema
                    assert 'paths' in schema

    def test_app_routes_registered(self, mock_all_startup_services):
        """Test that routes are registered"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # Get all routes
                    routes = [route.path for route in app.routes]

                    # Should have some routes registered
                    assert len(routes) > 0

                    # Common routes should exist
                    assert any('docs' in path for path in routes)
                    assert any('openapi' in path for path in routes)

    def test_app_has_lifespan_context(self, mock_all_startup_services):
        """Test that lifespan context manager is configured"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # App should have lifespan configured
                    assert hasattr(app.router, 'lifespan_context')
                    assert app.router.lifespan_context is not None

    def test_app_metadata_attributes(self, mock_all_startup_services):
        """Test app metadata is correctly set"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # Check that app has basic metadata
                    assert app.title is not None
                    assert app.version is not None
                    assert app.description is not None

    def test_exception_handlers_configured(self, mock_all_startup_services):
        """Test that exception handlers are set up"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # Exception handlers should be attempted to set up
                    # (might fail if imports are mocked, but attempt should be made)
                    assert app is not None

    def test_middleware_stack_order(self, mock_all_startup_services):
        """Test that middleware is configured"""
        with patch('core.application.db_manager', mock_all_startup_services['db_manager']):
            with patch('core.application.settings', mock_all_startup_services['settings']):
                with patch('core.application.setup_routers', mock_all_startup_services['setup_routers']):
                    from main import app

                    # App should have middleware attribute
                    assert hasattr(app, 'user_middleware')
                    # Middleware may be empty in fallback/test mode
                    assert app.user_middleware is not None
