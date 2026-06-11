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
        from fastapi.exception_handlers import (
            http_exception_handler,
            request_validation_exception_handler,
        )
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException

        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        if isinstance(exc, RequestValidationError):
            return await request_validation_exception_handler(request, exc)

        return JSONResponse(
            status_code=500,
            content={"detail": "Dahili sunucu hatasi"},
        )

    @_app.get("/test-unhandled-error")
    async def unhandled_error():
        raise RuntimeError("Internal secret: DB password is hunter2")

    @_app.get("/test-http-error")
    async def http_error():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")

    @_app.get("/test-validation-error")
    async def validation_error():
        from fastapi.exceptions import RequestValidationError
        raise RequestValidationError(errors=[])

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
async def test_http_exception_passes_through(app):
    """HTTPException should return its actual status code and detail."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-http-error")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


@pytest.mark.asyncio
async def test_validation_error_passes_through(app):
    """RequestValidationError should return 422 status code."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-validation-error")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_normal_endpoint_not_affected(app):
    """Normal endpoints should work fine with the handler installed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-ok")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
