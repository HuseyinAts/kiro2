"""PWA sync IDOR guards: progress userId + exam session ownership."""

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


def _exam_body(session_id: str = "ex1") -> dict:
    return {
        "session_id": session_id,
        "questions": [],
        "answers": {},
        "start_time": "2026-01-01T12:00:00Z",
        "end_time": None,
        "score": None,
        "completed": False,
    }


def test_sync_exam_sessions_other_owner_403() -> None:
    app = FastAPI()
    app.include_router(sync_router)

    async def _user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=1, username="u", role=UserRole.STUDENT, email=None
        )

    async def _db():
        db = MagicMock()
        r_owner = MagicMock()
        r_owner.scalar_one_or_none.return_value = "999"
        db.execute = AsyncMock(return_value=r_owner)
        db.commit = AsyncMock()
        yield db

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    client = TestClient(app, raise_server_exceptions=True)
    r = client.post("/api/v1/sync/exam-sessions", json=_exam_body())
    assert r.status_code == 403
    assert "another user" in r.json()["detail"].lower()


def test_sync_exam_sessions_new_session_ok() -> None:
    app = FastAPI()
    app.include_router(sync_router)

    async def _user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=1, username="u", role=UserRole.STUDENT, email=None
        )

    async def _db():
        db = MagicMock()
        r0 = MagicMock()
        r0.scalar_one_or_none.return_value = None
        r_rest = MagicMock()
        db.execute = AsyncMock(side_effect=[r0, r_rest])
        db.commit = AsyncMock()
        yield db

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = _db
    client = TestClient(app, raise_server_exceptions=True)
    r = client.post("/api/v1/sync/exam-sessions", json=_exam_body())
    assert r.status_code == 200
    assert r.json().get("success") is True
