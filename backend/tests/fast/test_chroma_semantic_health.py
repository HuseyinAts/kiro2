"""Chroma semantic search health — plan J10 smoke (router only)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_semantic_search_health_route():
    from api.v1 import semantic_search as mod

    app = FastAPI()
    app.include_router(mod.router)
    client = TestClient(app)
    r = client.get("/api/v1/search/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "chromadb_available" in data
