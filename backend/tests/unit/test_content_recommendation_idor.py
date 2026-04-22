"""F4: recommendation body user_id must match caller (unless staff)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.v1.content_recommendation import _authorized_target_user_id
from core.dependencies import AuthenticatedUser
from models.enums_db import UserRole


def _user(
    user_id: str, role: UserRole = UserRole.STUDENT
) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user_id,
        username="u",
        role=role,
        email=None,
    )


def test_self_allowed():
    u = _user("stu-1")
    assert _authorized_target_user_id("stu-1", u) == "stu-1"


def test_mismatch_student_forbidden():
    u = _user("stu-1", UserRole.STUDENT)
    with pytest.raises(HTTPException) as e:
        _authorized_target_user_id("other-9", u)
    assert e.value.status_code == 403


def test_admin_may_target_other():
    u = _user("admin-1", UserRole.ADMIN)
    assert _authorized_target_user_id("stu-2", u) == "stu-2"
