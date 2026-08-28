"""F4: analytics GET /student/{student_id} — profil student_id ile uyum."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from api.analytics import _assert_can_read_student_analytics
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_analytics_staff_no_verify() -> None:
    user = AuthenticatedUser(
        id=1, username="t", role=UserRole.TEACHER, email=None
    )
    with patch("api.analytics.verify_student_access", new_callable=AsyncMock) as v:
        await _assert_can_read_student_analytics("any-student", user)
        v.assert_not_called()


@pytest.mark.asyncio
async def test_analytics_self_user_id_no_verify() -> None:
    user = AuthenticatedUser(
        id=42, username="s", role=UserRole.STUDENT, email=None
    )
    with patch("api.analytics.verify_student_access", new_callable=AsyncMock) as v:
        await _assert_can_read_student_analytics("42", user)
        v.assert_not_called()


@pytest.mark.asyncio
async def test_analytics_student_other_id_calls_verify() -> None:
    user = AuthenticatedUser(
        id=42, username="s", role=UserRole.STUDENT, email=None
    )
    mock_db = AsyncMock()

    class _CM:
        async def __aenter__(self):
            return mock_db

        async def __aexit__(self, *a):
            return None

    with patch("api.analytics.get_db_session_context", return_value=_CM()):
        with patch("api.analytics.verify_student_access", new_callable=AsyncMock) as v:
            await _assert_can_read_student_analytics("STU_X", user)
            v.assert_awaited_once_with("STU_X", user, mock_db)


@pytest.mark.asyncio
async def test_analytics_verify_raises_propagates() -> None:
    user = AuthenticatedUser(
        id=42, username="s", role=UserRole.STUDENT, email=None
    )
    mock_db = AsyncMock()

    class _CM:
        async def __aenter__(self):
            return mock_db

        async def __aexit__(self, *a):
            return None

    with patch("api.analytics.get_db_session_context", return_value=_CM()):
        with patch("api.analytics.verify_student_access", new_callable=AsyncMock) as v:
            v.side_effect = HTTPException(status_code=403, detail="no")
            with pytest.raises(HTTPException) as ei:
                await _assert_can_read_student_analytics("STU_PEER", user)
            assert ei.value.status_code == 403
