"""F4: parent_social_api — veli rolü + onaylı parent_child (IDOR önleme)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.parent_social_api import _require_parent_linked_student
from core.dependencies import AuthenticatedUser, UserRole


@pytest.mark.asyncio
async def test_require_parent_rejects_non_parent() -> None:
    db = AsyncMock()
    user = AuthenticatedUser(
        id=1, username="s", role=UserRole.STUDENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await _require_parent_linked_student(db, user, "child-1")
    assert ei.value.status_code == 403
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_require_parent_rejects_unapproved_child() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(first=MagicMock(return_value=None))
    )
    user = AuthenticatedUser(
        id=10, username="p", role=UserRole.PARENT, email=None
    )
    with pytest.raises(HTTPException) as ei:
        await _require_parent_linked_student(db, user, "child-99")
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_require_parent_allows_linked_child() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(first=MagicMock(return_value=(1,)))
    )
    user = AuthenticatedUser(
        id=10, username="p", role=UserRole.PARENT, email=None
    )
    await _require_parent_linked_student(db, user, "child-1")
    db.execute.assert_awaited_once()
