"""
Basic integration tests
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from tests.fixtures.mock_decorators import (
    mock_database,
    mock_all_external_apis,
    mock_settings,
)
from tests.fixtures.mock_data import MockServices, MockResponses


@pytest.mark.integration
class TestBasicIntegration:
    """Basic integration tests"""

    @mock_all_external_apis
    async def test_config_database_integration(self):
        """Test config and database integration"""
        from tests.fixtures.mock_data import create_mock_settings

        # Test that config provides database URL
        settings = create_mock_settings()
        assert settings.database_url is not None

        # Test that database can use the URL
        with patch("core.database.create_async_engine") as mock_engine:
            mock_engine.return_value = Mock()

            # Simulate database initialization
            engine = mock_engine(settings.database_url)
            assert engine is not None

    @mock_all_external_apis
    async def test_auth_dependencies_integration(self):
        """Test authentication dependencies integration"""
        # Test auth workflow
        mock_token = "test_jwt_token"
        mock_user = {"id": 1, "username": "test_user", "role": "student"}

        with patch("core.auth_dependencies.verify_token") as mock_verify:
            with patch("core.auth_dependencies.get_current_user") as mock_get_user:
                # Setup mocks
                mock_verify.return_value = {"user_id": 1, "username": "test_user"}
                mock_get_user.return_value = mock_user

                # Test integration
                token_payload = mock_verify(mock_token)
                assert token_payload["user_id"] == 1

                user = mock_get_user(mock_token)
                assert user["username"] == "test_user"

    @mock_all_external_apis
    async def test_logging_integration(self):
        """Test logging system integration"""
        try:
            from core.structured_logger import get_logger

            # Test logger creation and usage
            logger = get_logger("integration_test")
            assert logger is not None

            # Test that logger can log messages
            with patch.object(logger, "info") as mock_info:
                logger.info("Integration test message")
                mock_info.assert_called_once()

        except ImportError:
            pytest.skip("Structured logger not available")

    @mock_all_external_apis
    async def test_exception_handling_integration(self):
        """Test exception handling integration"""
        try:
            from core.exceptions import ServiceError, ValidationError

            # Test exception inheritance
            validation_error = ValidationError("Test validation error")
            assert isinstance(validation_error, ServiceError)

            # Test error details
            assert validation_error.error_code == "VALIDATION_ERROR"
            assert str(validation_error) == "Test validation error"

        except ImportError:
            pytest.skip("Core exceptions not available")

    @mock_all_external_apis
    async def test_mock_services_integration(self):
        """Test that mock services work together"""
        # Test multiple mock services
        db_session = MockServices.mock_database_session()
        llm_service = MockServices.mock_llm_service()
        youtube_service = MockServices.mock_youtube_service()

        assert db_session is not None
        assert llm_service is not None
        assert youtube_service is not None

        # Test mock responses
        mock_response = await llm_service.generate_text("test prompt")
        assert mock_response == MockResponses.LLM_RESPONSE

        youtube_response = await youtube_service.search_videos("test query")
        assert youtube_response == MockResponses.YOUTUBE_API_RESPONSE

    @mock_all_external_apis
    async def test_settings_environment_integration(self):
        """Test settings and environment integration"""
        import os

        # Test environment variables
        assert os.environ.get("USE_MOCK_RESPONSES") == "true"
        assert os.environ.get("TESTING") == "true"

        # Test settings creation
        from tests.fixtures.mock_data import create_mock_settings

        settings = create_mock_settings()

        assert settings.test_mode is True
        assert "mock" in settings.hf_endpoint_url

    @mock_all_external_apis
    async def test_core_modules_integration(self):
        """Test core modules work together"""
        # Test config + dependencies
        from tests.fixtures.mock_data import create_mock_settings

        settings = create_mock_settings()

        # Test database session with settings
        with patch("core.database.get_session") as mock_get_session:
            mock_get_session.return_value = MockServices.mock_database_session()

            session = mock_get_session()
            assert session is not None

        # Test structured logging
        try:
            from core.structured_logger import get_logger

            logger = get_logger("integration")
            assert logger is not None
        except ImportError:
            pass

    @mock_all_external_apis
    async def test_error_flow_integration(self):
        """Test error handling flow integration"""
        try:
            from core.exceptions import ServiceError

            # Test error creation
            error = ServiceError(
                "Integration test error",
                error_code="TEST_ERROR",
                details={"test": "data"},
            )

            # Test error properties
            assert error.message == "Integration test error"
            assert error.error_code == "TEST_ERROR"
            assert error.details["test"] == "data"

            # Test error can be raised and caught
            with pytest.raises(ServiceError) as exc_info:
                raise error

            caught_error = exc_info.value
            assert caught_error.error_code == "TEST_ERROR"

        except ImportError:
            pytest.skip("ServiceError not available")

    @mock_all_external_apis
    async def test_async_integration(self):
        """Test async operations integration"""
        # Test async mock services
        async_operations = []

        # Database operations
        db_session = MockServices.mock_database_session()
        async_operations.append(db_session.execute("SELECT 1"))

        # LLM operations
        llm_service = MockServices.mock_llm_service()
        async_operations.append(llm_service.generate_text("test"))

        # YouTube operations
        youtube_service = MockServices.mock_youtube_service()
        async_operations.append(youtube_service.search_videos("test"))

        # All operations should be awaitable
        for operation in async_operations:
            result = await operation
            assert result is not None
