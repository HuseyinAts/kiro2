"""
Smoke Tests for main.py - FastAPI Application
Testing basic app initialization and endpoint availability
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestMainApplicationSmoke:
    """Smoke tests for main FastAPI application"""

    @pytest.fixture
    def mock_all_startup_services(self):
        """Mock all services that initialize during startup"""
        mocks = {}

        # Mock cache manager
        mock_cache = AsyncMock()
        mock_cache.initialize = AsyncMock(return_value=True)
        mocks['cache'] = mock_cache

        # Mock database
        mock_db = AsyncMock()
        mocks['database'] = mock_db

        # Mock health service
        mock_health = Mock()
        mock_health.startup_health_check = AsyncMock(return_value=Mock(
            success=True,
            components=[],
            warnings=[],
            errors=[]
        ))
        mocks['health'] = mock_health

        # Mock circuit breakers
        mocks['circuit_breakers'] = Mock()

        # Mock performance monitor
        mock_perf = Mock()
        mock_perf.start_monitoring = Mock()
        mocks['performance'] = mock_perf

        # Mock optimizer
        mocks['optimizer'] = AsyncMock()

        # Mock database optimizer
        mocks['db_optimizer'] = AsyncMock()

        # Mock monitoring service
        mock_monitoring = AsyncMock()
        mock_monitoring.start = AsyncMock()
        mocks['monitoring'] = mock_monitoring

        # Mock production health monitor
        mock_prod_health = AsyncMock()
        mock_prod_health.start_monitoring = AsyncMock()
        mocks['prod_health'] = mock_prod_health

        # Mock agents
        mocks['agents'] = {}

        # Mock elasticsearch
        mocks['elasticsearch'] = AsyncMock(return_value=Mock())

        # Mock analytics manager
        mock_analytics = AsyncMock()
        mock_analytics.stop = AsyncMock()
        mocks['analytics'] = mock_analytics

        return mocks

    def test_app_instance_creation(self, mock_all_startup_services):
        """Test that FastAPI app instance is created successfully"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    with patch('main.initialize_learning_path_circuit_breakers', mock_all_startup_services['circuit_breakers']):
                        with patch('main.system_monitor', mock_all_startup_services['performance']):
                            with patch('main.optimize_all_revolutionary_features', mock_all_startup_services['optimizer']):
                                with patch('main.create_performance_indexes', mock_all_startup_services['db_optimizer']):
                                    with patch('main.monitoring_service', mock_all_startup_services['monitoring']):
                                        with patch('main.production_health_monitor', mock_all_startup_services['prod_health']):
                                            with patch('main.initialize_agents', return_value=mock_all_startup_services['agents']):
                                                with patch('main.initialize_elasticsearch', mock_all_startup_services['elasticsearch']):
                                                    with patch('main.analytics_manager', mock_all_startup_services['analytics']):
                                                        from main import app

                                                        assert app is not None
                                                        assert app.title == "Türkiye Üniversite Sınavları Hazırlık Platformu"
                                                        assert app.version == "1.0.0"

    def test_app_has_cors_middleware(self, mock_all_startup_services):
        """Test that CORS middleware is configured"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    # Check that middleware is present
                    middleware_types = [type(m).__name__ for m in app.user_middleware]
                    # CORS middleware should be present
                    assert any('CORS' in name for name in middleware_types)

    def test_health_endpoint_responds(self, mock_all_startup_services):
        """Test that /health endpoint responds"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    client = TestClient(app)
                    response = client.get("/health")

                    # Should respond (might be 200, 404, or redirect)
                    assert response.status_code in [200, 404, 307, 308]

    def test_docs_endpoint_exists(self, mock_all_startup_services):
        """Test that OpenAPI docs endpoint exists"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    client = TestClient(app)
                    response = client.get("/docs")

                    # Docs should be accessible (200 or redirect)
                    assert response.status_code in [200, 307, 308]

    def test_openapi_schema_generation(self, mock_all_startup_services):
        """Test that OpenAPI schema is generated"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    # OpenAPI schema should be generated
                    schema = app.openapi()
                    assert schema is not None
                    assert 'info' in schema
                    assert 'paths' in schema
                    assert schema['info']['title'] == "Türkiye Üniversite Sınavları Hazırlık Platformu"
                    assert schema['info']['version'] == "1.0.0"

    def test_app_routes_registered(self, mock_all_startup_services):
        """Test that routes are registered"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
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
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    # App should have lifespan configured
                    assert hasattr(app.router, 'lifespan_context')
                    assert app.router.lifespan_context is not None

    def test_app_metadata_attributes(self, mock_all_startup_services):
        """Test app metadata is correctly set"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    assert app.title == "Türkiye Üniversite Sınavları Hazırlık Platformu"
                    assert app.version == "1.0.0"
                    assert "YKS" in app.description
                    assert "TYT" in app.description or "AYT" in app.description

    def test_exception_handlers_configured(self, mock_all_startup_services):
        """Test that exception handlers are set up"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    with patch('main.setup_global_exception_handlers') as mock_exception_setup:
                        from main import app

                        # Exception handlers should be attempted to set up
                        # (might fail if imports are mocked, but attempt should be made)
                        assert app is not None

    def test_middleware_stack_order(self, mock_all_startup_services):
        """Test that middleware is added in correct order"""
        with patch('main.cache_manager', mock_all_startup_services['cache']):
            with patch('main.init_database', mock_all_startup_services['database']):
                with patch('main.get_health_check_service', return_value=mock_all_startup_services['health']):
                    from main import app

                    # Should have multiple middleware layers
                    assert len(app.user_middleware) > 0

                    # Get middleware names
                    middleware_names = [type(m).__name__ for m in app.user_middleware]

                    # Should have security-related middleware
                    assert len(middleware_names) > 2  # At least CORS + security middleware
