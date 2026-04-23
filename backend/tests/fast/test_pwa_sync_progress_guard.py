"""PWA POST /api/v1/sync/progress: body userId must match JWT user (IDOR guard)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.pwa_sync_api import sync_router
from core.dependencies import AuthenticatedUser, get_current_user, get_db
from models.enums_db import UserRole


def _progress_body(user_id: str | int) -> dict:
    return {
        "userId": str(user_id),
        "subject": "matematik",
        "totalQuestions": 1,
        "correctAnswers": 1,
        "studyTime": 5,
        "lastActivity": "2026-01-01T12:00:00Z",
    }


@pytest.fixture
def progress_client() -> TestClient:
    app = FastAPI()
    app.include_router(sync_router)

    async def _user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=1,
            username="u",
            role=UserRole.STUDENT,
            email=None,
        )

    async def _db():
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        yield db

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    return TestClient(app, raise_server_exceptions=True)


def test_sync_progress_user_id_mismatch_403(progress_client: TestClient) -> None:
    r = progress_client.post("/api/v1/sync/progress", json=_progress_body("999"))
    assert r.status_code == 403
    assert "match" in r.json()["detail"].lower()


def test_sync_progress_matching_user_ok(progress_client: TestClient) -> None:
    r = progress_client.post("/api/v1/sync/progress", json=_progress_body(1))
    assert r.status_code == 200
    assert r.json().get("success") is True
