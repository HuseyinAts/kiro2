"""Tests for global catch-all exception handler in application.py."""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    """Create a minimal test app with the same handler pattern."""
    _app = FastAPI()

    # Same handler as in core/application.py
    @_app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Dahili sunucu hatasi"},
        )

    @_app.get("/test-unhandled-error")
    async def unhandled_error():
        raise RuntimeError("Internal secret: DB password is hunter2")

    @_app.get("/test-ok")
    async def ok_endpoint():
        return {"status": "online"}

    return _app


@pytest.mark.asyncio
async def test_unhandled_exception_returns_generic_500(app):
    """Unhandled exceptions should NOT leak internal details."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-unhandled-error")

    assert response.status_code == 500
    # Verify no internal details leaked
    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text


@pytest.mark.asyncio
async def test_normal_endpoint_not_affected(app):
    """Normal endpoints should work fine with the handler installed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-ok")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
