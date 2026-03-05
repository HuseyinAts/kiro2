"""
Unit tests for core/jwt_auth.py.

Tests target (no DB, no Redis):
- JWTManager.__init__: default field values
- JWTManager._enforce_memory_limit: TTL eviction + capacity eviction
- JWTManager._cleanup_stale_device_attempts: age-based cleanup
- JWTManager.blacklist_token + _is_blacklisted: in-memory round-trip
- JWTManager.create_access_token / create_refresh_token: valid JWT output
- JWTManager.verify_token: valid and invalid token paths
- JWTManager.check_rate_limit: window semantics
- JWTManager._get_default_permissions: role-to-permission mapping
- JWTManager._get_blacklist_key: key prefix format
- JWTManager._extract_jti_and_ttl: JTI extraction from real token
- TokenType / UserRole enums: value correctness
"""
import sys
import time

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from core.jwt_auth import (
    JWTManager,
    TokenPayload,
    TokenType,
    UserRole,
)


# ==================== Fixtures ====================


@pytest.fixture()
def manager() -> JWTManager:
    """Fresh JWTManager with predictable settings (no Redis)."""
    with patch("core.jwt_auth.get_settings") as mock_settings:
        cfg = mock_settings.return_value
        cfg.jwt_secret_key = "test-secret-key-for-unit-tests-only"
        cfg.jwt_algorithm = "HS256"
        cfg.jwt_access_token_expire_minutes = 30
        cfg.jwt_refresh_token_expire_days = 7
        cfg.redis_url = "redis://localhost:6379/0"
        m = JWTManager()
    return m


# ==================== Enum value correctness ====================


class TestTokenTypeEnum:
    """TokenType enum must have stable string values."""

    def test_access_value(self) -> None:
        assert TokenType.ACCESS.value == "access"

    def test_refresh_value(self) -> None:
        assert TokenType.REFRESH.value == "refresh"

    def test_reset_password_value(self) -> None:
        assert TokenType.RESET_PASSWORD.value == "reset_password"

    def test_email_verification_value(self) -> None:
        assert TokenType.EMAIL_VERIFICATION.value == "email_verification"


class TestUserRoleEnum:
    """UserRole enum must expose all five expected roles."""

    def test_student_value(self) -> None:
        assert UserRole.STUDENT.value == "student"

    def test_teacher_value(self) -> None:
        assert UserRole.TEACHER.value == "teacher"

    def test_parent_value(self) -> None:
        assert UserRole.PARENT.value == "parent"

    def test_admin_value(self) -> None:
        assert UserRole.ADMIN.value == "admin"

    def test_super_admin_value(self) -> None:
        assert UserRole.SUPER_ADMIN.value == "super_admin"

    def test_five_roles_total(self) -> None:
        assert len(UserRole) == 5


# ==================== JWTManager.__init__ ====================


class TestJWTManagerInit:
    """Verify constructor sets sensible defaults."""

    def test_blacklisted_tokens_starts_empty(self, manager: JWTManager) -> None:
        assert manager.blacklisted_tokens == {}

    def test_device_attempts_starts_empty(self, manager: JWTManager) -> None:
        assert manager.device_attempts == {}

    def test_redis_not_connected_by_default(self, manager: JWTManager) -> None:
        assert manager._redis is None
        assert manager._redis_available is False

    def test_max_memory_blacklist_constant(self, manager: JWTManager) -> None:
        assert manager.MAX_MEMORY_BLACKLIST == 10_000

    def test_blacklist_prefix_constant(self, manager: JWTManager) -> None:
        assert manager.BLACKLIST_PREFIX == "jwt:blacklist:"

    def test_secret_key_set(self, manager: JWTManager) -> None:
        assert manager.secret_key == "test-secret-key-for-unit-tests-only"

    def test_algorithm_set(self, manager: JWTManager) -> None:
        assert manager.algorithm == "HS256"

    def test_access_token_expiry_minutes(self, manager: JWTManager) -> None:
        assert manager.access_token_expire_minutes == 30

    def test_refresh_token_expiry_days(self, manager: JWTManager) -> None:
        assert manager.refresh_token_expire_days == 7


# ==================== _get_blacklist_key ====================


class TestGetBlacklistKey:
    """Key must include prefix and identifier."""

    def test_key_has_correct_prefix(self, manager: JWTManager) -> None:
        key = manager._get_blacklist_key("abc123")
        assert key.startswith("jwt:blacklist:")

    def test_key_contains_identifier(self, manager: JWTManager) -> None:
        identifier = "unique-jti-value"
        key = manager._get_blacklist_key(identifier)
        assert identifier in key

    def test_key_is_deterministic(self, manager: JWTManager) -> None:
        k1 = manager._get_blacklist_key("jti-xyz")
        k2 = manager._get_blacklist_key("jti-xyz")
        assert k1 == k2


# ==================== _enforce_memory_limit ====================


class TestEnforceMemoryLimit:
    """Eviction must keep blacklisted_tokens bounded."""

    def test_no_eviction_below_limit(self, manager: JWTManager) -> None:
        # Fill to MAX - 1; no eviction should happen.
        for i in range(manager.MAX_MEMORY_BLACKLIST - 1):
            manager.blacklisted_tokens[f"token_{i}"] = time.time()
        manager._enforce_memory_limit()
        # Count should be unchanged (below limit).
        assert len(manager.blacklisted_tokens) == manager.MAX_MEMORY_BLACKLIST - 1

    def test_old_entries_evicted_first(self, manager: JWTManager) -> None:
        # Add MAX entries: half very old (>24h), half recent.
        old_ts = time.time() - 90_000  # ~25 hours ago
        recent_ts = time.time()

        half = manager.MAX_MEMORY_BLACKLIST // 2
        for i in range(half):
            manager.blacklisted_tokens[f"old_{i}"] = old_ts
        for i in range(manager.MAX_MEMORY_BLACKLIST - half):
            manager.blacklisted_tokens[f"new_{i}"] = recent_ts

        # Now we are at exactly MAX — trigger limit check.
        manager._enforce_memory_limit()

        # All old entries should have been removed.
        remaining = set(manager.blacklisted_tokens.keys())
        old_keys_remaining = {k for k in remaining if k.startswith("old_")}
        assert len(old_keys_remaining) == 0

    def test_capacity_eviction_removes_oldest_20_percent(
        self, manager: JWTManager
    ) -> None:
        # Fill to MAX with fresh timestamps (none expired), oldest first.
        base_ts = time.time() - 1000
        for i in range(manager.MAX_MEMORY_BLACKLIST):
            manager.blacklisted_tokens[f"t_{i:06d}"] = base_ts + i

        count_before = len(manager.blacklisted_tokens)
        manager._enforce_memory_limit()
        count_after = len(manager.blacklisted_tokens)

        evict_count = manager.MAX_MEMORY_BLACKLIST // 5
        expected_after = count_before - evict_count
        assert count_after == expected_after

    def test_limit_not_exceeded_after_eviction(self, manager: JWTManager) -> None:
        base_ts = time.time() - 500
        for i in range(manager.MAX_MEMORY_BLACKLIST):
            manager.blacklisted_tokens[f"t_{i}"] = base_ts + i
        manager._enforce_memory_limit()
        assert len(manager.blacklisted_tokens) < manager.MAX_MEMORY_BLACKLIST


# ==================== _cleanup_stale_device_attempts ====================


class TestCleanupStaleDeviceAttempts:
    """Stale entries (>120 min) must be removed when dict >= 100 entries."""

    def test_no_cleanup_below_100_entries(self, manager: JWTManager) -> None:
        # 50 stale entries — cleanup should NOT run (threshold is 100).
        old_start = datetime.now(UTC) - timedelta(minutes=200)
        for i in range(50):
            manager.device_attempts[f"device_{i}"] = {
                "attempts": 3,
                "window_start": old_start,
            }
        manager._cleanup_stale_device_attempts()
        # Entries should still be there (threshold not met).
        assert len(manager.device_attempts) == 50

    def test_stale_entries_removed_above_threshold(self, manager: JWTManager) -> None:
        old_start = datetime.now(UTC) - timedelta(minutes=200)
        recent_start = datetime.now(UTC) - timedelta(minutes=10)

        # Add 60 stale + 60 recent = 120 total → exceeds threshold of 100.
        for i in range(60):
            manager.device_attempts[f"old_{i}"] = {
                "attempts": 1,
                "window_start": old_start,
            }
        for i in range(60):
            manager.device_attempts[f"recent_{i}"] = {
                "attempts": 1,
                "window_start": recent_start,
            }

        manager._cleanup_stale_device_attempts()

        # All stale entries should be gone.
        remaining = set(manager.device_attempts.keys())
        stale_remaining = {k for k in remaining if k.startswith("old_")}
        assert len(stale_remaining) == 0

    def test_recent_entries_kept_after_cleanup(self, manager: JWTManager) -> None:
        old_start = datetime.now(UTC) - timedelta(minutes=200)
        recent_start = datetime.now(UTC) - timedelta(minutes=5)

        for i in range(80):
            manager.device_attempts[f"old_{i}"] = {
                "attempts": 1,
                "window_start": old_start,
            }
        for i in range(40):
            manager.device_attempts[f"recent_{i}"] = {
                "attempts": 1,
                "window_start": recent_start,
            }

        manager._cleanup_stale_device_attempts()

        remaining = set(manager.device_attempts.keys())
        recent_remaining = {k for k in remaining if k.startswith("recent_")}
        assert len(recent_remaining) == 40


# ==================== blacklist_token + _is_blacklisted ====================


class TestTokenBlacklisting:
    """In-memory blacklist round-trip."""

    def test_blacklisted_token_detected(self, manager: JWTManager) -> None:
        token = manager.create_access_token("u1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)
        assert manager._is_blacklisted(token) is True

    def test_non_blacklisted_token_not_detected(self, manager: JWTManager) -> None:
        token = manager.create_access_token("u1", "u@test.com", UserRole.STUDENT)
        assert manager._is_blacklisted(token) is False

    def test_blacklist_stores_jti_not_full_token(self, manager: JWTManager) -> None:
        token = manager.create_access_token("u1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)
        # The stored key should be the JTI (short string), not the JWT itself.
        stored_keys = list(manager.blacklisted_tokens.keys())
        assert len(stored_keys) == 1
        assert len(stored_keys[0]) < len(token)

    def test_blacklist_records_timestamp(self, manager: JWTManager) -> None:
        before = time.time()
        token = manager.create_access_token("u1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)
        after = time.time()

        ts = list(manager.blacklisted_tokens.values())[0]
        assert before <= ts <= after

    def test_blacklisted_token_raises_401_on_verify(
        self, manager: JWTManager
    ) -> None:
        token = manager.create_access_token("u1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        assert exc_info.value.status_code == 401

    def test_multiple_tokens_independently_blacklisted(
        self, manager: JWTManager
    ) -> None:
        token_a = manager.create_access_token("u1", "a@test.com", UserRole.STUDENT)
        token_b = manager.create_access_token("u2", "b@test.com", UserRole.TEACHER)
        manager.blacklist_token(token_a)

        assert manager._is_blacklisted(token_a) is True
        assert manager._is_blacklisted(token_b) is False


# ==================== create_access_token ====================


class TestCreateAccessToken:
    """Access token must encode correct claims."""

    def test_returns_non_empty_string(self, manager: JWTManager) -> None:
        token = manager.create_access_token("123", "user@test.com", UserRole.STUDENT)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_jwt_parts(self, manager: JWTManager) -> None:
        token = manager.create_access_token("123", "user@test.com", UserRole.STUDENT)
        parts = token.split(".")
        assert len(parts) == 3

    def test_sub_claim_is_user_id(self, manager: JWTManager) -> None:
        token = manager.create_access_token("42", "user@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["sub"] == "42"

    def test_email_claim_correct(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "test@kiro2.com", UserRole.TEACHER)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["email"] == "test@kiro2.com"

    def test_type_is_access(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.ACCESS.value

    def test_role_claim_matches_input(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.ADMIN)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["role"] == UserRole.ADMIN.value

    def test_jti_is_present_and_non_empty(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    def test_jti_is_unique_per_token(self, manager: JWTManager) -> None:
        t1 = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        t2 = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        p1 = pyjwt.decode(t1, manager.secret_key, algorithms=[manager.algorithm])
        p2 = pyjwt.decode(t2, manager.secret_key, algorithms=[manager.algorithm])
        assert p1["jti"] != p2["jti"]

    def test_device_id_included_when_provided(self, manager: JWTManager) -> None:
        token = manager.create_access_token(
            "1", "u@test.com", UserRole.STUDENT, device_id="device-abc"
        )
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["device_id"] == "device-abc"

    @pytest.mark.parametrize("role", list(UserRole))
    def test_token_created_for_all_roles(
        self, manager: JWTManager, role: UserRole
    ) -> None:
        token = manager.create_access_token("1", "u@test.com", role)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["role"] == role.value


# ==================== create_refresh_token ====================


class TestCreateRefreshToken:
    """Refresh token must encode correct type claim."""

    def test_type_is_refresh(self, manager: JWTManager) -> None:
        token = manager.create_refresh_token("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.REFRESH.value

    def test_sub_claim_correct(self, manager: JWTManager) -> None:
        token = manager.create_refresh_token("99", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["sub"] == "99"


# ==================== verify_token ====================


class TestVerifyToken:
    """verify_token must validate claims and raise on bad input."""

    def test_valid_access_token_returns_payload(self, manager: JWTManager) -> None:
        token = manager.create_access_token("7", "v@test.com", UserRole.TEACHER)
        result = manager.verify_token(token, TokenType.ACCESS)
        assert isinstance(result, TokenPayload)
        assert result.sub == "7"
        assert result.email == "v@test.com"
        assert result.role == UserRole.TEACHER

    def test_payload_type_field_is_token_type(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        result = manager.verify_token(token)
        assert result.type == TokenType.ACCESS

    def test_garbage_token_raises_401(self, manager: JWTManager) -> None:
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_wrong_token_type_raises_401(self, manager: JWTManager) -> None:
        # Create ACCESS token, then verify as REFRESH → should fail.
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token, TokenType.REFRESH)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self, manager: JWTManager) -> None:
        expired_payload = {
            "sub": "1",
            "email": "u@test.com",
            "role": UserRole.STUDENT.value,
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "type": TokenType.ACCESS.value,
            "jti": "some-jti",
            "permissions": [],
        }
        expired_token = pyjwt.encode(
            expired_payload, manager.secret_key, algorithm=manager.algorithm
        )
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(expired_token)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_401(self, manager: JWTManager) -> None:
        token = pyjwt.encode(
            {
                "sub": "1",
                "email": "u@test.com",
                "role": "student",
                "type": "access",
                "jti": "jti-x",
                "exp": datetime.now(UTC) + timedelta(hours=1),
                "iat": datetime.now(UTC),
                "permissions": [],
            },
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        assert exc_info.value.status_code == 401


# ==================== _get_default_permissions ====================


class TestGetDefaultPermissions:
    """Each role must receive a distinct, non-empty permission set."""

    def test_student_can_take_exam(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.STUDENT)
        assert "exam:take" in perms

    def test_teacher_can_create_exam(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.TEACHER)
        assert "exam:create" in perms

    def test_parent_can_view_child(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.PARENT)
        assert "child:view" in perms

    def test_admin_can_manage_users(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.ADMIN)
        assert "user:manage" in perms

    def test_super_admin_has_wildcard(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.SUPER_ADMIN)
        assert "*" in perms

    def test_student_cannot_manage_users(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions(UserRole.STUDENT)
        assert "user:manage" not in perms

    def test_unknown_role_returns_empty_list(self, manager: JWTManager) -> None:
        perms = manager._get_default_permissions("nonexistent_role")  # type: ignore[arg-type]
        assert perms == []

    @pytest.mark.parametrize("role", list(UserRole))
    def test_all_roles_return_list(
        self, manager: JWTManager, role: UserRole
    ) -> None:
        perms = manager._get_default_permissions(role)
        assert isinstance(perms, list)


# ==================== check_rate_limit ====================


class TestCheckRateLimit:
    """Rate limiter must allow first N attempts and block subsequent ones."""

    def test_first_attempt_allowed(self, manager: JWTManager) -> None:
        assert manager.check_rate_limit("device-1", max_attempts=5) is True

    def test_attempts_within_limit_allowed(self, manager: JWTManager) -> None:
        identifier = "dev-rate-1"
        for _ in range(4):
            result = manager.check_rate_limit(
                identifier, max_attempts=5, window_minutes=15
            )
            assert result is True

    def test_attempt_beyond_limit_blocked(self, manager: JWTManager) -> None:
        identifier = "dev-rate-2"
        # Exhaust the limit (5 attempts).
        for _ in range(5):
            manager.check_rate_limit(identifier, max_attempts=5, window_minutes=15)
        # 6th attempt must be blocked.
        result = manager.check_rate_limit(
            identifier, max_attempts=5, window_minutes=15
        )
        assert result is False

    def test_different_identifiers_are_independent(
        self, manager: JWTManager
    ) -> None:
        identifier_a = "dev-rate-a"
        identifier_b = "dev-rate-b"
        for _ in range(5):
            manager.check_rate_limit(identifier_a, max_attempts=5)
        # Exhaust A's limit; B is untouched.
        manager.check_rate_limit(identifier_a, max_attempts=5)  # blocked
        result_b = manager.check_rate_limit(identifier_b, max_attempts=5)
        assert result_b is True

    def test_window_reset_allows_new_attempts(self, manager: JWTManager) -> None:
        identifier = "dev-rate-3"
        for _ in range(5):
            manager.check_rate_limit(identifier, max_attempts=5, window_minutes=15)
        # Manually backdate the window start to simulate expiry.
        manager.device_attempts[identifier]["window_start"] = (
            datetime.now(UTC) - timedelta(minutes=20)
        )
        # Next attempt should start a fresh window.
        result = manager.check_rate_limit(
            identifier, max_attempts=5, window_minutes=15
        )
        assert result is True


# ==================== _extract_jti_and_ttl ====================


class TestExtractJtiAndTtl:
    """JTI extraction must work for valid and invalid tokens."""

    def test_valid_token_returns_jti(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        jti, ttl = manager._extract_jti_and_ttl(token)
        assert jti is not None
        assert len(jti) > 0

    def test_valid_token_returns_positive_ttl(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        _, ttl = manager._extract_jti_and_ttl(token)
        assert ttl > 0

    def test_garbage_token_returns_hash_fallback(
        self, manager: JWTManager
    ) -> None:
        jti, ttl = manager._extract_jti_and_ttl("not.a.jwt")
        # Fallback: SHA-256 hex = 64 chars
        assert jti is not None
        assert len(jti) == 64
        assert ttl == 86400


# ==================== hash_password + verify_password ====================


class TestPasswordHashing:
    """Password hashing must be bcrypt and round-trip correctly."""

    def test_hash_is_not_plaintext(self, manager: JWTManager) -> None:
        hashed = manager.hash_password("MyPass1!")
        assert hashed != "MyPass1!"

    def test_verify_correct_password(self, manager: JWTManager) -> None:
        hashed = manager.hash_password("MyPass1!")
        assert manager.verify_password("MyPass1!", hashed) is True

    def test_verify_wrong_password(self, manager: JWTManager) -> None:
        hashed = manager.hash_password("MyPass1!")
        assert manager.verify_password("WrongPass!", hashed) is False

    def test_two_hashes_of_same_password_differ(self, manager: JWTManager) -> None:
        # bcrypt uses random salt → same input yields different hashes.
        h1 = manager.hash_password("SamePass1!")
        h2 = manager.hash_password("SamePass1!")
        assert h1 != h2


# ==================== create_token_pair ====================


class TestCreateTokenPair:
    """create_token_pair must return both tokens with correct metadata."""

    def test_returns_jwt_tokens_model(self, manager: JWTManager) -> None:
        from core.jwt_auth import JWTTokens  # noqa: PLC0415
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        assert isinstance(result, JWTTokens)

    def test_access_token_present(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        assert len(result.access_token) > 0

    def test_refresh_token_present(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        assert len(result.refresh_token) > 0

    def test_token_type_is_bearer(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        assert result.token_type == "bearer"

    def test_expires_in_matches_config(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        expected = manager.access_token_expire_minutes * 60
        assert result.expires_in == expected

    def test_refresh_expires_in_matches_config(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        expected = manager.refresh_token_expire_days * 24 * 60 * 60
        assert result.refresh_expires_in == expected

    def test_access_and_refresh_tokens_differ(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        assert result.access_token != result.refresh_token

    def test_access_token_has_access_type(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            result.access_token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.ACCESS.value

    def test_refresh_token_has_refresh_type(self, manager: JWTManager) -> None:
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            result.refresh_token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.REFRESH.value

    def test_default_permissions_included_when_none_passed(
        self, manager: JWTManager
    ) -> None:
        # When no custom permissions are given, default role permissions are used.
        result = manager.create_token_pair("1", "u@test.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            result.access_token, manager.secret_key, algorithms=[manager.algorithm]
        )
        default_perms = manager._get_default_permissions(UserRole.STUDENT)
        assert payload["permissions"] == default_perms


# ==================== create_password_reset_token ====================


class TestCreatePasswordResetToken:
    """Password reset token must carry correct type claim."""

    def test_returns_non_empty_string(self, manager: JWTManager) -> None:
        token = manager.create_password_reset_token("1", "u@test.com")
        assert isinstance(token, str) and len(token) > 0

    def test_token_type_is_reset_password(self, manager: JWTManager) -> None:
        token = manager.create_password_reset_token("1", "u@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.RESET_PASSWORD.value

    def test_sub_claim_correct(self, manager: JWTManager) -> None:
        token = manager.create_password_reset_token("55", "reset@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["sub"] == "55"

    def test_email_claim_correct(self, manager: JWTManager) -> None:
        token = manager.create_password_reset_token("1", "reset@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["email"] == "reset@test.com"

    def test_jti_present(self, manager: JWTManager) -> None:
        token = manager.create_password_reset_token("1", "u@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert "jti" in payload and len(payload["jti"]) > 0


# ==================== create_email_verification_token ====================


class TestCreateEmailVerificationToken:
    """Email verification token must carry correct type claim."""

    def test_returns_non_empty_string(self, manager: JWTManager) -> None:
        token = manager.create_email_verification_token("1", "u@test.com")
        assert isinstance(token, str) and len(token) > 0

    def test_token_type_is_email_verification(self, manager: JWTManager) -> None:
        token = manager.create_email_verification_token("1", "u@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["type"] == TokenType.EMAIL_VERIFICATION.value

    def test_sub_and_email_correct(self, manager: JWTManager) -> None:
        token = manager.create_email_verification_token("77", "verify@test.com")
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["sub"] == "77"
        assert payload["email"] == "verify@test.com"


# ==================== verify_token — missing sub/email path ====================


class TestVerifyTokenEdgeCases:
    """Cover lines 199-203 (missing sub/email) and 208-212 (bad role)."""

    def _make_raw_token(
        self,
        manager: JWTManager,
        overrides: dict,
    ) -> str:
        """Build a raw JWT without going through create_access_token validation."""
        base = {
            "sub": "1",
            "email": "u@test.com",
            "role": UserRole.STUDENT.value,
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": TokenType.ACCESS.value,
            "jti": "jti-test",
            "permissions": [],
        }
        base.update(overrides)
        return pyjwt.encode(base, manager.secret_key, algorithm=manager.algorithm)

    def test_missing_sub_raises_401(self, manager: JWTManager) -> None:
        token = self._make_raw_token(manager, {"sub": ""})
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        assert exc_info.value.status_code == 401

    def test_missing_email_raises_401(self, manager: JWTManager) -> None:
        token = self._make_raw_token(manager, {"email": ""})
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        assert exc_info.value.status_code == 401

    def test_invalid_role_raises_401(self, manager: JWTManager) -> None:
        token = self._make_raw_token(manager, {"role": "invalid_role_xyz"})
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        assert exc_info.value.status_code == 401

    def test_valid_token_no_type_check_passes(self, manager: JWTManager) -> None:
        token = self._make_raw_token(manager, {})
        result = manager.verify_token(token)  # No token_type filter
        assert result.sub == "1"


# ==================== username param in create_access_token ====================


class TestCreateAccessTokenUsername:
    """Username param is optional; defaults to email prefix."""

    def test_username_defaults_to_email_prefix(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "alice@kiro2.com", UserRole.STUDENT)
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["username"] == "alice"

    def test_explicit_username_overrides_default(self, manager: JWTManager) -> None:
        token = manager.create_access_token(
            "1", "alice@kiro2.com", UserRole.STUDENT, username="alicias_custom"
        )
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["username"] == "alicias_custom"

    def test_explicit_permissions_skip_default_lookup(
        self, manager: JWTManager
    ) -> None:
        custom_perms = ["special:perm"]
        token = manager.create_access_token(
            "1", "u@test.com", UserRole.STUDENT, permissions=custom_perms
        )
        payload = pyjwt.decode(
            token, manager.secret_key, algorithms=[manager.algorithm]
        )
        assert payload["permissions"] == custom_perms


# ==================== Module-level auth helpers ====================


def _make_token_payload(
    role: UserRole = UserRole.STUDENT,
    permissions: list[str] | None = None,
    sub: str = "1",
    email: str = "u@test.com",
) -> TokenPayload:
    """Build a TokenPayload without going through JWTManager."""
    from datetime import UTC, datetime, timedelta  # noqa: PLC0415
    return TokenPayload(
        sub=sub,
        email=email,
        role=role,
        exp=datetime.now(UTC) + timedelta(hours=1),
        iat=datetime.now(UTC),
        type=TokenType.ACCESS,
        jti="test-jti",
        permissions=permissions if permissions is not None else [],
    )


class TestRequireRole:
    """require_role must allow matching roles and raise 403 otherwise."""

    @pytest.mark.asyncio
    async def test_matching_role_returns_user(self) -> None:
        from core.jwt_auth import require_role  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.ADMIN)
        result = await require_role([UserRole.ADMIN], user)
        assert result is user

    @pytest.mark.asyncio
    async def test_non_matching_role_raises_403(self) -> None:
        from core.jwt_auth import require_role  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.STUDENT)
        with pytest.raises(HTTPException) as exc_info:
            await require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN], user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_super_admin_allowed_when_in_list(self) -> None:
        from core.jwt_auth import require_role  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.SUPER_ADMIN)
        result = await require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN], user)
        assert result is user

    @pytest.mark.asyncio
    async def test_error_message_includes_required_roles(self) -> None:
        from core.jwt_auth import require_role  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.STUDENT)
        with pytest.raises(HTTPException) as exc_info:
            await require_role([UserRole.ADMIN], user)
        assert "admin" in exc_info.value.detail


class TestRequirePermission:
    """require_permission must enforce per-permission access."""

    @pytest.mark.asyncio
    async def test_user_with_permission_passes(self) -> None:
        from core.jwt_auth import require_permission  # noqa: PLC0415
        user = _make_token_payload(permissions=["exam:create"])
        result = await require_permission("exam:create", user)
        assert result is user

    @pytest.mark.asyncio
    async def test_user_without_permission_raises_403(self) -> None:
        from core.jwt_auth import require_permission  # noqa: PLC0415
        user = _make_token_payload(permissions=["exam:take"])
        with pytest.raises(HTTPException) as exc_info:
            await require_permission("exam:create", user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_super_admin_bypasses_permission_check(self) -> None:
        from core.jwt_auth import require_permission  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.SUPER_ADMIN, permissions=["*"])
        result = await require_permission("any:secret:action", user)
        assert result is user

    @pytest.mark.asyncio
    async def test_wildcard_permission_grants_access(self) -> None:
        from core.jwt_auth import require_permission  # noqa: PLC0415
        # Even a student-role user with explicit "*" perm should pass.
        user = _make_token_payload(role=UserRole.STUDENT, permissions=["*"])
        result = await require_permission("exam:create", user)
        assert result is user

    @pytest.mark.asyncio
    async def test_error_detail_includes_required_permission(self) -> None:
        from core.jwt_auth import require_permission  # noqa: PLC0415
        user = _make_token_payload(permissions=[])
        with pytest.raises(HTTPException) as exc_info:
            await require_permission("reports:admin", user)
        assert "reports:admin" in exc_info.value.detail


class TestRequireAdmin:
    """require_admin must allow ADMIN/SUPER_ADMIN only."""

    @pytest.mark.asyncio
    async def test_admin_passes(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.ADMIN)
        result = await require_admin(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_super_admin_passes(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.SUPER_ADMIN)
        result = await require_admin(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_student_raises_403(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.STUDENT)
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_raises_403(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.TEACHER)
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_raises_403(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.PARENT)
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_error_detail_mentions_admin(self) -> None:
        from core.jwt_auth import require_admin  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.STUDENT)
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert "admin" in exc_info.value.detail.lower()


class TestGetCurrentActiveUser:
    """get_current_active_user must pass the user through."""

    @pytest.mark.asyncio
    async def test_returns_same_user(self) -> None:
        from core.jwt_auth import get_current_active_user  # noqa: PLC0415
        user = _make_token_payload(role=UserRole.STUDENT)
        result = await get_current_active_user(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_works_for_all_roles(self) -> None:
        from core.jwt_auth import get_current_active_user  # noqa: PLC0415
        for role in UserRole:
            user = _make_token_payload(role=role)
            result = await get_current_active_user(user)
            assert result.role == role
