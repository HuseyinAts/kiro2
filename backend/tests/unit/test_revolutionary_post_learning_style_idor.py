"""F4: POST /revolutionary-features/learning-style/detect/{student_id} must enforce verify."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.dependencies import AuthenticatedUser, get_current_user, get_db
from main import app
from models.enums_db import UserRole


def _student_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="stu-owner-1",
        username="t",
        email="t@t.com",
        role=UserRole.STUDENT,
    )


async def _override_db():
    """verify_student_access mocked — session kullanılmaz."""
    yield None  # type: ignore[misc, unused-ignore]


def test_post_detect_awaited_verify_and_403_on_forbidden() -> None:
    with (
        patch(
            "api.revolutionary_features.verify_student_access",
            new_callable=AsyncMock,
        ) as vmock,
        patch(
            "api.revolutionary_features.revolutionary_features_service.detect_hybrid_learning_style",
            new_callable=AsyncMock,
        ) as dmock,
    ):
        dmock.return_value = SimpleNamespace(foo=1, __dict__={"foo": 1})
        vmock.return_value = True
        app.dependency_overrides[get_current_user] = _student_user
        app.dependency_overrides[get_db] = _override_db

        try:
            c = TestClient(app)
            r = c.post(
                "/api/v1/revolutionary-features/learning-style/detect/OTHER",
                json={"behavioral_data": {}},
            )
            assert r.status_code == 200, r.text
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)

        vmock.assert_awaited()
        dmock.assert_awaited()

    with patch(
        "api.revolutionary_features.verify_student_access",
        new_callable=AsyncMock,
    ) as vmock2:
        vmock2.side_effect = HTTPException(status_code=403, detail="no")

        app.dependency_overrides[get_current_user] = _student_user
        app.dependency_overrides[get_db] = _override_db
        try:
            c2 = TestClient(app)
            r2 = c2.post(
                "/api/v1/revolutionary-features/learning-style/detect/OTHER",
                json={"behavioral_data": {}},
            )
            assert r2.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)
