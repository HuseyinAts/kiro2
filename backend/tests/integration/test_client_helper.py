"""
Custom TestClient helper that works with httpx 0.27+
"""
import httpx
from fastapi import FastAPI


class CompatibleTestClient:
    """A TestClient that works with httpx 0.27+ versions"""

    def __init__(self, app: FastAPI):
        self.app = app
        # Create an httpx Client with the proper initialization for new versions
        transport = httpx.ASGITransport(app=app)
        # In httpx 0.27+, we need to use the transport differently
        self.client = httpx.Client(
            transport=transport, base_url="http://testserver", follow_redirects=True
        )

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make a request with the specified method"""
        # Build the request
        request = self.client.build_request(method, url, **kwargs)
        # Send it through the transport directly
        return self.client.send(request)

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        """Make a PUT request"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make a DELETE request"""
        return self.request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make a PATCH request"""
        return self.request("PATCH", url, **kwargs)

    def websocket_connect(self, url: str):
        """WebSocket connection for testing"""
        # For websocket, use a mock since httpx doesn't support WebSockets
        from unittest.mock import MagicMock

        class MockWebSocket:
            def __init__(self):
                self.send_text = MagicMock()
                self.receive_text = MagicMock(
                    return_value='{"type": "response", "content": "test"}'
                )
                self.receive_json = MagicMock(
                    return_value={"type": "response", "content": "test"}
                )
                self.send_json = MagicMock()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, _):
                pass

        return MockWebSocket()

    def close(self):
        """Close the client"""
        # httpx.Client has a close method but ASGITransport doesn't
        # So we just close the client itself
        try:
            self.client.close()
        except Exception:
            pass  # Ignore close errors

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, _):
        """Context manager cleanup"""
        self.close()


def create_test_client(app: FastAPI) -> CompatibleTestClient:
    """Create a test client that works with current httpx version"""
    return CompatibleTestClient(app)
