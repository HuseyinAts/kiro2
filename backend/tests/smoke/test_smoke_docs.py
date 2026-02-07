"""
ST-03: Smoke tests for API documentation endpoints.

Tests:
- Swagger UI availability
- OpenAPI JSON validity
- Endpoint count verification
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import pytest  # noqa: E402
import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402


@pytest.mark.asyncio
async def test_docs_returns_html():
    """ST-03-01: Swagger docs endpoint returns HTML."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/docs")

        assert response.status_code == 200, \
            f"Docs endpoint failed: {response.status_code}"

        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type.lower(), \
            f"Expected HTML content-type, got: {content_type}"

        # Verify it's actually Swagger UI HTML
        html_content = response.text
        assert len(html_content) > 100, "HTML content too short"
        assert "swagger" in html_content.lower() or "openapi" in html_content.lower(), \
            "HTML should contain Swagger/OpenAPI references"


@pytest.mark.asyncio
async def test_openapi_json_valid():
    """ST-03-02: OpenAPI JSON is valid and contains paths."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/openapi.json")

        assert response.status_code == 200, \
            f"OpenAPI endpoint failed: {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), "OpenAPI spec must be a JSON object"

        # Verify required OpenAPI fields
        assert "openapi" in data, "OpenAPI spec must have 'openapi' version field"
        assert "paths" in data, "OpenAPI spec must have 'paths' field"
        assert "info" in data, "OpenAPI spec must have 'info' field"

        # Verify version format
        openapi_version = data["openapi"]
        assert openapi_version.startswith("3."), \
            f"Expected OpenAPI 3.x, got: {openapi_version}"


@pytest.mark.asyncio
async def test_openapi_has_endpoints():
    """ST-03-03: OpenAPI spec contains 50+ endpoints."""
    from main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/openapi.json")
        data = response.json()

        paths = data.get("paths", {})
        assert isinstance(paths, dict), "Paths must be a dictionary"

        path_count = len(paths)
        assert path_count > 50, \
            f"Expected 50+ endpoints, got {path_count}. KIRO2 has 115+ routers."

        # Verify we have API endpoints
        api_paths = [p for p in paths.keys() if p.startswith("/api")]
        assert len(api_paths) > 10, \
            f"Expected 10+ API endpoints, got {len(api_paths)}"

        # Verify health endpoints are documented
        health_paths = [p for p in paths.keys() if "health" in p]
        assert len(health_paths) > 0, "Health endpoints should be documented"
