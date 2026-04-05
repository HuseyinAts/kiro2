"""
Unit tests for core/dependencies.py

Tests:
- AuthenticatedUser Pydantic model (validation, repr, immutability)
- get_current_user async dependency (bearer, cookie, blacklist, expiry, missing claims)
- Role-based dependencies (admin, teacher, student)
- verify_token and create_access_token utilities

Standards: AAA pattern, no assert True, no reward hacking.
"""

import datetime
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest

# Ensure backend is on path
backend_dir = str(Path(__file__).parents[2])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ============================================================================
# Module-level secret override so JWT_SECRET matches test tokens everywhere
# ============================================================================
import core.dependencies as _dep_module
from tests.conftest import TEST_JWT_ALGORITHM, TEST_JWT_SECRET, _generate_test_jwt

_ORIGINAL_JWT_SECRET = _dep_module.JWT_SECRET
_ORIGINAL_JWT_ALGORITHM = _dep_module.JWT_ALGORITHM


@pytest.fixture(autouse=True)
def patch_jwt_secret(monkeypatch):
    """Override JWT_SECRET and JWT_ALGORITHM in the module under test."""
    monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)


@pytest.fixture
def mock_jwt_manager():
    """Return a mock JWTManager with is_blacklisted_async returning False."""
    manager = MagicMock()
    manager.is_blacklisted_async = AsyncMock(return_value=False)
    return manager


@pytest.fixture
def patch_jwt_manager(mock_jwt_manager):
    """Patch get_jwt_manager at its definition site (imported inside the function body)."""
    with patch("core.jwt_auth.get_jwt_manager", return_value=mock_jwt_manager):
        yield mock_jwt_manager


# ============================================================================
# Helper: build a FastAPI Request with a Bearer Authorization header
# ============================================================================
def _make_bearer_credentials(token: str):
    from fastapi.security import HTTPAuthorizationCredentials

    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_request_with_cookie(token: str):
    """Create a minimal mock Request whose cookies contain access_token."""
    req = MagicMock()
    req.cookies = {"access_token": token}
    return req


def _make_empty_request():
    req = MagicMock()
    req.cookies = {}
    return req


# ============================================================================
# TestAuthenticatedUserModel
# ============================================================================
class TestAuthenticatedUserModel:
    """Tests for the AuthenticatedUser Pydantic model."""

    def test_valid_int_id_accepted(self):
        """Integer user_id within INT32 range must be accepted as-is."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=42, username="alice", role=UserRole.STUDENT)
        assert user.id == 42
        assert isinstance(user.id, int)

    def test_valid_digit_string_id_converted_to_int(self):
        """Digit-only string IDs should be converted to int."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id="123", username="bob", role=UserRole.TEACHER)
        assert user.id == 123
        assert isinstance(user.id, int)

    def test_non_numeric_string_id_kept_as_string(self):
        """UUID-style string IDs that are non-numeric must be kept as str."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        uid = "a7f3c2d1-uuid"
        user = AuthenticatedUser(id=uid, username="carol", role=UserRole.ADMIN)
        assert user.id == uid
        assert isinstance(user.id, str)

    def test_int_id_overflow_rejected(self):
        """int IDs > 2147483647 (INT32_MAX) should raise ValueError."""
        from pydantic import ValidationError

        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        with pytest.raises(ValidationError):
            AuthenticatedUser(
                id=2_147_483_648, username="overflow", role=UserRole.STUDENT
            )

    def test_digit_string_id_overflow_rejected(self):
        """Digit-string IDs that overflow INT32 should raise ValueError."""
        from pydantic import ValidationError

        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        with pytest.raises(ValidationError):
            AuthenticatedUser(id="9999999999", username="x", role=UserRole.STUDENT)

    def test_invalid_id_type_rejected(self):
        """List or dict as id must raise ValidationError."""
        from pydantic import ValidationError

        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        with pytest.raises(ValidationError):
            AuthenticatedUser(id=[1, 2], username="x", role=UserRole.STUDENT)

    def test_valid_role_enum_accepted(self):
        """Passing a UserRole enum directly must be accepted."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=1, username="u", role=UserRole.ADMIN)
        assert user.role == UserRole.ADMIN

    def test_valid_role_lowercase_string_accepted(self):
        """Lowercase role string 'student' must resolve via _missing_ to UserRole.STUDENT."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=1, username="u", role="student")
        assert user.role == UserRole.STUDENT

    def test_valid_role_uppercase_string_accepted(self):
        """Uppercase role string 'ADMIN' must resolve to UserRole.ADMIN."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=1, username="u", role="ADMIN")
        assert user.role == UserRole.ADMIN

    def test_invalid_role_string_rejected(self):
        """An unrecognised role string must raise ValidationError."""
        from pydantic import ValidationError

        from core.dependencies import AuthenticatedUser

        with pytest.raises(ValidationError):
            AuthenticatedUser(id=1, username="u", role="supervillain")

    def test_repr_masks_email(self):
        """__repr__ must mask email for KVKK compliance."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(
            id=5, username="dana", role=UserRole.STUDENT, email="dana@example.com"
        )
        r = repr(user)
        assert "dana@example.com" not in r
        assert "***@***" in r

    def test_repr_without_email_shows_none(self):
        """__repr__ with no email should show None (not crash)."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(
            id=6, username="eve", role=UserRole.TEACHER, email=None
        )
        r = repr(user)
        assert "***@***" not in r
        assert "None" in r

    def test_frozen_model_prevents_mutation(self):
        """AuthenticatedUser is frozen — attribute assignment must raise."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=7, username="frank", role=UserRole.STUDENT)
        with pytest.raises(
            Exception
        ):  # ValidationError or TypeError depending on pydantic version
            user.role = UserRole.ADMIN  # type: ignore[misc]

    def test_default_permissions_empty_list(self):
        """permissions field should default to empty list."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        user = AuthenticatedUser(id=8, username="g", role=UserRole.STUDENT)
        assert user.permissions == []

    def test_permissions_stored_correctly(self):
        """Explicit permissions list should be stored verbatim."""
        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        perms = ["read:questions", "write:answers"]
        user = AuthenticatedUser(
            id=9, username="h", role=UserRole.TEACHER, permissions=perms
        )
        assert user.permissions == perms


# ============================================================================
# TestGetCurrentUser
# ============================================================================
class TestGetCurrentUser:
    """Tests for the get_current_user async dependency."""

    @pytest.mark.asyncio
    async def test_bearer_token_returns_authenticated_user(self, patch_jwt_manager):
        """Valid Bearer token → AuthenticatedUser with correct fields."""
        from core.dependencies import get_current_user
        from models.enums_db import UserRole

        token = _generate_test_jwt("42", "user@test.com", "student")
        creds = _make_bearer_credentials(token)

        user = await get_current_user(request=_make_empty_request(), credentials=creds)

        assert user.id == 42  # digit string "42" → int
        assert user.username == "user"
        assert user.role == UserRole.STUDENT
        assert user.email == "user@test.com"

    @pytest.mark.asyncio
    async def test_cookie_auth_fallback(self, patch_jwt_manager):
        """No Bearer header → falls back to httpOnly cookie."""
        from core.dependencies import get_current_user
        from models.enums_db import UserRole

        token = _generate_test_jwt("10", "cookie@test.com", "teacher")
        request = _make_request_with_cookie(token)

        user = await get_current_user(request=request, credentials=None)

        assert user.role == UserRole.TEACHER
        assert user.email == "cookie@test.com"

    @pytest.mark.asyncio
    async def test_no_token_raises_401(self, patch_jwt_manager):
        """No Bearer and no cookie → 401 Unauthorized."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=None)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_401(self, mock_jwt_manager):
        """Blacklisted token → 401 with revoked message."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        mock_jwt_manager.is_blacklisted_async = AsyncMock(return_value=True)
        token = _generate_test_jwt("5", "black@test.com", "student")
        creds = _make_bearer_credentials(token)

        with patch("core.jwt_auth.get_jwt_manager", return_value=mock_jwt_manager):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, patch_jwt_manager):
        """Expired token → 401 with 'expired' message."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        # Build token that expired 1 hour ago
        expired_payload = {
            "sub": "99",
            "username": "expired_user",
            "role": "student",
            "email": "exp@test.com",
            "exp": datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
        }
        expired_token = pyjwt.encode(
            expired_payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM
        )
        creds = _make_bearer_credentials(expired_token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_signature_raises_401(self, patch_jwt_manager):
        """Token signed with wrong secret → 401."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        bad_token = pyjwt.encode(
            {"sub": "1", "username": "x", "role": "student", "email": "x@t.com"},
            "WRONG_SECRET",
            algorithm="HS256",
        )
        creds = _make_bearer_credentials(bad_token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_sub_claim_raises_401(self, patch_jwt_manager):
        """Token without 'sub' claim → 401 missing subject."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        payload_no_sub = {
            "username": "nosub",
            "role": "student",
            "email": "nosub@test.com",
        }
        token = pyjwt.encode(
            payload_no_sub, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM
        )
        creds = _make_bearer_credentials(token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401
        assert (
            "subject" in exc_info.value.detail.lower()
            or "missing" in exc_info.value.detail.lower()
        )

    @pytest.mark.asyncio
    async def test_missing_username_claim_raises_401(self, patch_jwt_manager):
        """Token without 'username' claim → 401 missing required claims."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        payload = {
            "sub": "7",
            # username intentionally omitted
            "role": "student",
            "email": "nouser@test.com",
        }
        token = pyjwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)
        creds = _make_bearer_credentials(token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_role_claim_raises_401(self, patch_jwt_manager):
        """Token without 'role' claim → 401 missing required claims."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        payload = {
            "sub": "8",
            "username": "norole",
            # role intentionally omitted
            "email": "norole@test.com",
        }
        token = pyjwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)
        creds = _make_bearer_credentials(token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_user_id_in_payload_raises_401(self, patch_jwt_manager):
        """Token with an unparseable user_id type → 401."""
        from fastapi import HTTPException

        from core.dependencies import get_current_user

        # Pass a list as sub — AuthenticatedUser.validate_id will reject it
        payload = {
            "sub": [1, 2, 3],
            "username": "badid",
            "role": "student",
            "email": "badid@test.com",
        }
        token = pyjwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)
        creds = _make_bearer_credentials(token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=_make_empty_request(), credentials=creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_role_in_token_returns_admin_user(self, patch_jwt_manager):
        """Token with 'admin' role → AuthenticatedUser with ADMIN role."""
        from core.dependencies import get_current_user
        from models.enums_db import UserRole

        token = _generate_test_jwt("100", "admin@test.com", "admin")
        creds = _make_bearer_credentials(token)

        user = await get_current_user(request=_make_empty_request(), credentials=creds)

        assert user.role == UserRole.ADMIN
        assert user.id == 100

    @pytest.mark.asyncio
    async def test_bearer_takes_priority_over_cookie(self, patch_jwt_manager):
        """When both Bearer and cookie present, Bearer token is used."""
        from core.dependencies import get_current_user
        from models.enums_db import UserRole

        bearer_token = _generate_test_jwt("1", "bearer@test.com", "admin")
        cookie_token = _generate_test_jwt("2", "cookie@test.com", "student")

        creds = _make_bearer_credentials(bearer_token)
        request = _make_request_with_cookie(cookie_token)

        user = await get_current_user(request=request, credentials=creds)

        # Should resolve to Bearer user (admin, id=1), NOT cookie user (student, id=2)
        assert user.role == UserRole.ADMIN
        assert user.id == 1


# ============================================================================
# TestRoleBasedDependencies
# ============================================================================
class TestRoleBasedDependencies:
    """Tests for get_current_admin_user, get_current_teacher_user, get_current_student_user."""

    def _make_user(self, role_str: str, user_id: int = 1):
        from core.dependencies import AuthenticatedUser

        return AuthenticatedUser(id=user_id, username="testuser", role=role_str)

    @pytest.mark.asyncio
    async def test_admin_dependency_allows_admin(self):
        """get_current_admin_user must return ADMIN user unchanged."""
        from core.dependencies import get_current_admin_user
        from models.enums_db import UserRole

        admin_user = self._make_user("admin")

        result = await get_current_admin_user(current_user=admin_user)

        assert result is admin_user
        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_admin_dependency_rejects_teacher(self):
        """get_current_admin_user must raise 403 for TEACHER."""
        from fastapi import HTTPException

        from core.dependencies import get_current_admin_user

        teacher_user = self._make_user("teacher")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=teacher_user)

        assert exc_info.value.status_code == 403
        assert "Admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_admin_dependency_rejects_student(self):
        """get_current_admin_user must raise 403 for STUDENT."""
        from fastapi import HTTPException

        from core.dependencies import get_current_admin_user

        student_user = self._make_user("student")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=student_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_dependency_allows_teacher(self):
        """get_current_teacher_user must return TEACHER user."""
        from core.dependencies import get_current_teacher_user
        from models.enums_db import UserRole

        teacher_user = self._make_user("teacher")

        result = await get_current_teacher_user(current_user=teacher_user)

        assert result.role == UserRole.TEACHER

    @pytest.mark.asyncio
    async def test_teacher_dependency_allows_admin(self):
        """get_current_teacher_user must also allow ADMIN."""
        from core.dependencies import get_current_teacher_user
        from models.enums_db import UserRole

        admin_user = self._make_user("admin")

        result = await get_current_teacher_user(current_user=admin_user)

        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_teacher_dependency_rejects_student(self):
        """get_current_teacher_user must raise 403 for STUDENT."""
        from fastapi import HTTPException

        from core.dependencies import get_current_teacher_user

        student_user = self._make_user("student")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_teacher_user(current_user=student_user)

        assert exc_info.value.status_code == 403
        assert "Teacher" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_student_dependency_allows_student(self):
        """get_current_student_user must return STUDENT user."""
        from core.dependencies import get_current_student_user
        from models.enums_db import UserRole

        student_user = self._make_user("student")

        result = await get_current_student_user(current_user=student_user)

        assert result.role == UserRole.STUDENT

    @pytest.mark.asyncio
    async def test_student_dependency_allows_teacher(self):
        """get_current_student_user must also allow TEACHER."""
        from core.dependencies import get_current_student_user
        from models.enums_db import UserRole

        teacher_user = self._make_user("teacher")

        result = await get_current_student_user(current_user=teacher_user)

        assert result.role == UserRole.TEACHER

    @pytest.mark.asyncio
    async def test_student_dependency_allows_admin(self):
        """get_current_student_user must also allow ADMIN."""
        from core.dependencies import get_current_student_user
        from models.enums_db import UserRole

        admin_user = self._make_user("admin")

        result = await get_current_student_user(current_user=admin_user)

        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_student_dependency_rejects_parent(self):
        """get_current_student_user must raise 403 for PARENT."""
        from fastapi import HTTPException

        from core.dependencies import get_current_student_user

        parent_user = self._make_user("parent")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_student_user(current_user=parent_user)

        assert exc_info.value.status_code == 403
        assert "Student" in exc_info.value.detail


# ============================================================================
# TestTokenUtilities
# ============================================================================
class TestTokenUtilities:
    """Tests for verify_token and create_access_token."""

    def test_verify_token_valid_token_returns_payload(self):
        """verify_token with a valid token should return the decoded payload dict."""
        from core.dependencies import verify_token

        payload_in = {"sub": "55", "username": "tester", "role": "student"}
        token = pyjwt.encode(payload_in, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)

        result = verify_token(token)

        assert result["sub"] == "55"
        assert result["username"] == "tester"
        assert result["role"] == "student"

    def test_verify_token_invalid_token_raises_401(self):
        """verify_token with a garbage string should raise HTTPException 401."""
        from fastapi import HTTPException

        from core.dependencies import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.valid.token")

        assert exc_info.value.status_code == 401

    def test_verify_token_wrong_secret_raises_401(self):
        """verify_token with a token signed by wrong secret should raise 401."""
        from fastapi import HTTPException

        from core.dependencies import verify_token

        bad_token = pyjwt.encode(
            {"sub": "1", "username": "x"},
            "WRONG_SECRET_XXXXXX",
            algorithm="HS256",
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(bad_token)

        assert exc_info.value.status_code == 401

    def test_create_access_token_returns_decodable_jwt(self):
        """create_access_token should return a valid JWT decodable with the same secret."""
        from core.dependencies import create_access_token

        data = {"sub": "77", "username": "alice", "role": "student"}
        token = create_access_token(data)

        # Decode without verification to inspect structure quickly
        decoded = pyjwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM])
        assert decoded["sub"] == "77"
        assert decoded["username"] == "alice"
        assert "exp" in decoded

    def test_create_access_token_with_custom_expires_delta(self):
        """Token with expires_delta=5 should expire ~5 minutes from now."""
        from core.dependencies import create_access_token

        data = {"sub": "88", "username": "bob", "role": "admin"}
        token = create_access_token(data, expires_delta=5)

        decoded = pyjwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM])
        exp = decoded["exp"]

        now = datetime.datetime.now(datetime.UTC).timestamp()
        delta_minutes = (exp - now) / 60.0

        # Should be within 4–6 minutes
        assert 4.0 <= delta_minutes <= 6.0, (
            f"Expected ~5 min expiry, got {delta_minutes:.1f} min"
        )

    def test_create_access_token_default_expiry_uses_config(self):
        """Token without expires_delta should use ACCESS_TOKEN_EXPIRE_MINUTES from config."""
        from core.dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

        data = {"sub": "99", "username": "carol", "role": "teacher"}
        token = create_access_token(data)

        decoded = pyjwt.decode(token, TEST_JWT_SECRET, algorithms=[TEST_JWT_ALGORITHM])
        exp = decoded["exp"]

        now = datetime.datetime.now(datetime.UTC).timestamp()
        delta_minutes = (exp - now) / 60.0

        # Allow ±1 minute tolerance around the configured value
        assert (
            ACCESS_TOKEN_EXPIRE_MINUTES - 1
            <= delta_minutes
            <= ACCESS_TOKEN_EXPIRE_MINUTES + 1
        ), (
            f"Expected ~{ACCESS_TOKEN_EXPIRE_MINUTES} min expiry, got {delta_minutes:.1f} min"
        )

    def test_create_access_token_does_not_mutate_input_data(self):
        """create_access_token should not modify the original data dict."""
        from core.dependencies import create_access_token

        original_data = {"sub": "10", "username": "dan", "role": "student"}
        data_copy = original_data.copy()

        create_access_token(original_data)

        assert original_data == data_copy, (
            "Input dict was mutated by create_access_token"
        )
