"""
Comprehensive tests for core/logging_middleware.py
Tests logging middleware for FastAPI request/response logging
"""
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestLoggingMiddleware:
    """Test LoggingMiddleware class"""

    @patch("core.logging_middleware.logger")
    def test_middleware_logs_request(self, mock_logger):
        """Test middleware logs incoming request"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Verify request was logged
        assert any(
            "Request: GET" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 200

    @patch("core.logging_middleware.logger")
    def test_middleware_logs_response(self, mock_logger):
        """Test middleware logs response"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Verify response was logged
        assert any(
            "Response: 200" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 200

    @patch("core.logging_middleware.logger")
    def test_middleware_logs_processing_time(self, mock_logger):
        """Test middleware logs processing time"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Verify processing time was logged
        assert any("Time:" in str(call) for call in mock_logger.info.call_args_list)
        assert response.status_code == 200

    @patch("core.logging_middleware.logger")
    def test_middleware_logs_request_path(self, mock_logger):
        """Test middleware logs request path"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/path")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test/path")

        # Verify path was logged
        assert any(
            "/test/path" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 200

    @patch("core.logging_middleware.logger")
    def test_middleware_works_with_post_requests(self, mock_logger):
        """Test middleware works with POST requests"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.post("/test")
        async def test_endpoint():
            return {"message": "created"}

        client = TestClient(app)
        response = client.post("/test")

        # Verify POST request was logged
        assert any(
            "Request: POST" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 200

    @patch("core.logging_middleware.logger")
    def test_middleware_logs_different_status_codes(self, mock_logger):
        """Test middleware logs different status codes"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/not-found")
        async def test_endpoint():
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not found")

        client = TestClient(app)
        response = client.get("/not-found")

        # Verify 404 status was logged
        assert any(
            "Response: 404" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 404

    @patch("core.logging_middleware.logger")
    def test_middleware_preserves_response(self, mock_logger):
        """Test middleware preserves original response"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test", "value": 123}

        client = TestClient(app)
        response = client.get("/test")

        # Verify response is preserved
        data = response.json()
        assert data["message"] == "test"
        assert data["value"] == 123


class TestSetupLoggingMiddleware:
    """Test setup_logging_middleware function"""

    @patch("core.logging_middleware.logger")
    def test_setup_adds_middleware(self, mock_logger):
        """Test setup adds middleware to app"""
        from core.logging_middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app)

        # Verify middleware was added (by checking logger was called)
        mock_logger.info.assert_called_with("Logging middleware setup completed")

    @patch("core.logging_middleware.logger")
    def test_setup_logs_completion(self, mock_logger):
        """Test setup logs completion message"""
        from core.logging_middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app)

        # Verify completion was logged
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("setup completed" in call for call in calls)

    @patch("core.logging_middleware.logger")
    def test_middleware_works_after_setup(self, mock_logger):
        """Test middleware works after setup"""
        from core.logging_middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Verify middleware is working
        assert any(
            "Request: GET" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.status_code == 200


class TestLoggingMiddlewareIntegration:
    """Integration tests for logging middleware"""

    @patch("core.logging_middleware.logger")
    def test_middleware_with_multiple_requests(self, mock_logger):
        """Test middleware logs multiple requests"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test1")
        async def test1():
            return {"message": "test1"}

        @app.get("/test2")
        async def test2():
            return {"message": "test2"}

        client = TestClient(app)
        client.get("/test1")
        client.get("/test2")

        # Verify both requests were logged
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("/test1" in call for call in calls)
        assert any("/test2" in call for call in calls)

    @patch("core.logging_middleware.logger")
    def test_middleware_with_query_parameters(self, mock_logger):
        """Test middleware logs requests with query parameters"""
        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint(param: str = "default"):
            return {"param": param}

        client = TestClient(app)
        response = client.get("/test?param=value")

        # Verify request with query params was logged
        assert any(
            "Request: GET" in str(call) for call in mock_logger.info.call_args_list
        )
        assert response.json()["param"] == "value"

    @patch("core.logging_middleware.logger")
    def test_middleware_timing_accuracy(self, mock_logger):
        """Test middleware measures processing time"""
        import asyncio

        from core.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.01)  # Small delay
            return {"message": "slow"}

        client = TestClient(app)
        response = client.get("/slow")

        # Verify timing was logged (should be > 0)
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Time:" in call and "0.0" in call for call in calls)
        assert response.status_code == 200
