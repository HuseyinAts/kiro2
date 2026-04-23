"""F4: exam_performance — sinav oturumu sahibi / personel kontrolu."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.exam_performance import _assert_exam_session_authorized
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_exam_session_guard_allows_owner() -> None:
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value="user-42"))
    )

    class _CM:
        async def __aenter__(self):
            return mock_db

        async def __aexit__(self, *a):
            return None

    user = AuthenticatedUser(
        id="user-42", username="s", role=UserRole.STUDENT, email=None
    )
    with patch("api.exam_performance.get_db_session_context", return_value=_CM()):
        await _assert_exam_session_authorized("sess-1", user)


@pytest.mark.asyncio
async def test_exam_session_guard_denies_peer() -> None:
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value="other"))
    )

    class _CM:
        async def __aenter__(self):
            return mock_db

        async def __aexit__(self, *a):
            return None

    user = AuthenticatedUser(
        id="user-42", username="s", role=UserRole.STUDENT, email=None
    )
    with patch("api.exam_performance.get_db_session_context", return_value=_CM()):
        with pytest.raises(HTTPException) as ei:
            await _assert_exam_session_authorized("sess-1", user)
        assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_exam_session_guard_allows_teacher_any_session() -> None:
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value="other"))
    )

    class _CM:
        async def __aenter__(self):
            return mock_db

        async def __aexit__(self, *a):
            return None

    user = AuthenticatedUser(
        id="user-42", username="t", role=UserRole.TEACHER, email=None
    )
    with patch("api.exam_performance.get_db_session_context", return_value=_CM()):
        await _assert_exam_session_authorized("sess-1", user)
