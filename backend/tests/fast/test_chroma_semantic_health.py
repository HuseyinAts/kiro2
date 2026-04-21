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


def test_content_recommendation_health_route():
    from api.v1 import content_recommendation as mod

    app = FastAPI()
    app.include_router(mod.router)
    client = TestClient(app)
    r = client.get("/api/v1/recommendations/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "chromadb_available" in data


def test_duplicate_detection_health_route():
    from api.v1 import duplicate_detection as mod

    app = FastAPI()
    app.include_router(mod.router)
    client = TestClient(app)
    r = client.get("/api/v1/duplicates/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "chromadb_available" in data


def test_clustering_health_route():
    import api.clustering_api as mod

    app = FastAPI()
    app.include_router(mod.router)
    client = TestClient(app)
    r = client.get("/api/v1/clustering/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "chromadb_available" in data
