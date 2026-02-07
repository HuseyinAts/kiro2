"""
Health Integration Tests Configuration

Bu dosya, health integration testleri icin pytest yapilandirmasi saglar.
"""

import sys
import os

# Backend path'i ekle
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def test_app():
    """Basit test uygulamasi."""
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture
async def async_client(test_app):
    """Async HTTP client fixture."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
