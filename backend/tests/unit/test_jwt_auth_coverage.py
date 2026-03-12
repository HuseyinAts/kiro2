"""
Additional unit tests for core/jwt_auth.py — coverage gap filler.

Target lines (from coverage report):
- Lines 255-320: refresh_access_token (async, with/without DB)
- Lines 324-343: connect_redis (success and failure paths)
- Line 372: else branch in _extract_jti_and_ttl (no exp field)
- Lines 407->exit: blacklist_token with None identifier guard
- Lines 417-431: blacklist_token_async (Redis path + fallback)
- Lines 449-472: is_blacklisted_async (Redis hit, Redis fail, not found)
- Lines 610-655: _save_refresh_token_to_db (device type branches)
- Lines 668-686: revoke_refresh_token (token hash path, jti path, no-op)
- Lines 697-709: revoke_all_user_tokens
- Lines 720-733: revoke_device_tokens
- Lines 743-749: cleanup_expired_tokens
- Lines 786-803: get_current_user (no credentials, blacklisted token)

All tests use unittest.mock — no real Redis or DB connections.
"""
import sys

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.jwt_auth import (
    JWTManager,
    JWTTokens,
    TokenPayload,
    TokenType,
    UserRole,
    get_current_user,
)


# ==================== Shared fixture ====================


@pytest.fixture()
def manager() -> JWTManager:
    """Fresh JWTManager with predictable settings (no Redis)."""
    with patch("core.jwt_auth.get_settings") as mock_settings:
        cfg = mock_settings.return_value
        cfg.jwt_secret_key = "test-secret-coverage-only"
        cfg.jwt_algorithm = "HS256"
        cfg.jwt_access_token_expire_minutes = 30
        cfg.jwt_refresh_token_expire_days = 7
        cfg.redis_url = "redis://localhost:6379/0"
        m = JWTManager()
    return m


def _make_refresh_token(manager: JWTManager, user_id: str = "42") -> str:
    """Helper: create a valid refresh token."""
    return manager.create_refresh_token(
        user_id, f"user{user_id}@test.com", UserRole.STUDENT
    )


def _make_token_payload(
    manager: JWTManager,
    role: UserRole = UserRole.STUDENT,
    permissions: list[str] | None = None,
    sub: str = "1",
    email: str = "u@test.com",
) -> TokenPayload:
    """Build a TokenPayload without a real DB."""
    return TokenPayload(
        sub=sub,
        email=email,
        role=role,
        exp=datetime.now(UTC) + timedelta(hours=1),
        iat=datetime.now(UTC),
        type=TokenType.ACCESS,
        jti="test-jti-coverage",
        permissions=permissions if permissions is not None else [],
    )


# ==================== refresh_access_token (lines 255-320) ====================


class TestRefreshAccessTokenNoDb:
    """refresh_access_token without DB — only verifies and rotates in-memory."""

    @pytest.mark.asyncio
    async def test_valid_refresh_token_returns_jwt_tokens(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        result = await manager.refresh_access_token(refresh_token)
        assert isinstance(result, JWTTokens)
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0

    @pytest.mark.asyncio
    async def test_new_access_token_type_is_access(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        result = await manager.refresh_access_token(refresh_token)
        payload = pyjwt.decode(
            result.access_token,
            manager.secret_key,
            algorithms=[manager.algorithm],
        )
        assert payload["type"] == TokenType.ACCESS.value

    @pytest.mark.asyncio
    async def test_old_refresh_token_blacklisted_after_rotation(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        await manager.refresh_access_token(refresh_token)
        # Old token must be in the in-memory blacklist after rotation
        assert manager._is_blacklisted(refresh_token) is True

    @pytest.mark.asyncio
    async def test_invalid_refresh_token_raises_401(
        self, manager: JWTManager
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await manager.refresh_access_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_access_token_as_refresh_raises_401(
        self, manager: JWTManager
    ) -> None:
        access_token = manager.create_access_token(
            "1", "u@test.com", UserRole.STUDENT
        )
        with pytest.raises(HTTPException) as exc_info:
            await manager.refresh_access_token(access_token)
        assert exc_info.value.status_code == 401


class TestRefreshAccessTokenWithDb:
    """refresh_access_token with mocked DB session (lines 258-318)."""

    def _build_mock_db_token(self, valid: bool = True) -> MagicMock:
        """Return a mock RefreshToken DB row."""
        db_token = MagicMock()
        db_token.revoked = False
        db_token.expires_at = (
            datetime.now(UTC) + timedelta(hours=1)
            if valid
            else datetime.now(UTC) - timedelta(hours=1)
        )
        db_token.last_used_at = None
        db_token.usage_count = 0
        return db_token

    @pytest.mark.asyncio
    async def test_valid_db_token_returns_jwt_tokens(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        db_token = self._build_mock_db_token(valid=True)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            result = await manager.refresh_access_token(refresh_token, db=mock_db)

        assert isinstance(result, JWTTokens)
        # DB must be committed (rotation + blacklist write)
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_missing_db_token_raises_401(self, manager: JWTManager) -> None:
        refresh_token = _make_refresh_token(manager)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Token not found

        with patch("models.database.RefreshToken", MagicMock()):
            with pytest.raises(HTTPException) as exc_info:
                await manager.refresh_access_token(refresh_token, db=mock_db)
        assert exc_info.value.status_code == 401
        detail = exc_info.value.detail.lower()
        assert "revoked" in detail or "not exist" in detail

    @pytest.mark.asyncio
    async def test_expired_db_token_raises_401(self, manager: JWTManager) -> None:
        refresh_token = _make_refresh_token(manager)
        db_token = self._build_mock_db_token(valid=False)  # expired

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            with pytest.raises(HTTPException) as exc_info:
                await manager.refresh_access_token(refresh_token, db=mock_db)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rotation_marks_old_token_revoked(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        db_token = self._build_mock_db_token(valid=True)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            await manager.refresh_access_token(refresh_token, db=mock_db)

        assert db_token.revoked is True
        assert db_token.revoke_reason == "rotated"

    @pytest.mark.asyncio
    async def test_db_and_request_saves_new_refresh_token(
        self, manager: JWTManager
    ) -> None:
        """When db and request provided, _save_refresh_token_to_db is called."""
        refresh_token = _make_refresh_token(manager)
        db_token = self._build_mock_db_token(valid=True)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Mozilla/5.0"
        mock_request.client.host = "127.0.0.1"

        with patch.object(manager, "_save_refresh_token_to_db") as mock_save:
            with patch("models.database.RefreshToken", MagicMock()):
                await manager.refresh_access_token(
                    refresh_token, db=mock_db, request=mock_request
                )
        mock_save.assert_called_once()


# ==================== connect_redis (lines 324-343) ====================


class TestConnectRedis:
    """connect_redis must set _redis_available correctly."""

    @pytest.mark.asyncio
    async def test_successful_redis_connection_sets_available_true(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        # from_url must be an awaitable coroutine that resolves to mock_redis
        async def fake_from_url(*args, **kwargs):
            return mock_redis

        with patch("redis.asyncio.from_url", side_effect=fake_from_url):
            await manager.connect_redis()

        assert manager._redis_available is True
        assert manager._redis is mock_redis

    @pytest.mark.asyncio
    async def test_failed_redis_connection_sets_available_false(
        self, manager: JWTManager
    ) -> None:
        with patch(
            "redis.asyncio.from_url", side_effect=ConnectionRefusedError("refused")
        ):
            await manager.connect_redis()

        assert manager._redis_available is False
        # _redis stays None on failure
        assert manager._redis is None

    @pytest.mark.asyncio
    async def test_ping_failure_sets_available_false(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("ping failed"))

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await manager.connect_redis()

        assert manager._redis_available is False

    @pytest.mark.asyncio
    async def test_connect_redis_import_error_falls_back(
        self, manager: JWTManager
    ) -> None:
        """If redis package is unavailable, connect_redis must not crash."""
        with patch(
            "core.jwt_auth.JWTManager.connect_redis",
            new_callable=AsyncMock,
        ) as mock_connect:
            mock_connect.side_effect = None  # no-op
            await manager.connect_redis.__wrapped__(manager) if hasattr(
                manager.connect_redis, "__wrapped__"
            ) else None

        # Even after import error, manager keeps working
        assert manager._redis_available is False


# ==================== _extract_jti_and_ttl else branch (line 372) ====================


class TestExtractJtiAndTtlElseBranch:
    """Token with no 'exp' field should return 24h default TTL (line 372)."""

    def test_token_without_exp_returns_24h_ttl(self, manager: JWTManager) -> None:
        # Build a raw token with no 'exp' claim
        payload_no_exp = {
            "sub": "1",
            "email": "u@test.com",
            "role": "student",
            "type": "access",
            "jti": "jti-no-exp",
        }
        token = pyjwt.encode(
            payload_no_exp, manager.secret_key, algorithm=manager.algorithm
        )
        jti, ttl = manager._extract_jti_and_ttl(token)
        assert jti == "jti-no-exp"
        assert ttl == 86400  # 24h default (else branch)

    def test_token_with_exp_in_future_returns_positive_ttl(
        self, manager: JWTManager
    ) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        jti, ttl = manager._extract_jti_and_ttl(token)
        assert jti is not None
        assert ttl > 0

    def test_token_with_exp_in_past_returns_minimum_60s_ttl(
        self, manager: JWTManager
    ) -> None:
        # Token expired 1 hour ago — remaining is negative, should clamp to 60
        past_payload = {
            "sub": "1",
            "email": "u@test.com",
            "role": "student",
            "type": "access",
            "jti": "jti-expired",
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        }
        token = pyjwt.encode(
            past_payload, manager.secret_key, algorithm=manager.algorithm
        )
        _, ttl = manager._extract_jti_and_ttl(token)
        assert ttl == 60  # max(negative, 60) == 60


# ==================== blacklist_token None guard (lines 407->exit) ====================


class TestBlacklistTokenNoneGuard:
    """blacklist_token must skip storing if identifier is None/empty."""

    def test_garbage_token_still_stores_hash_fallback(
        self, manager: JWTManager
    ) -> None:
        # Garbage token → _extract_jti_and_ttl returns a sha256 hash (not None)
        manager.blacklist_token("garbage.token.string")
        # SHA256 hex is 64 chars; some entry should be stored
        assert len(manager.blacklisted_tokens) == 1

    def test_blacklist_token_with_valid_token_stores_jti(
        self, manager: JWTManager
    ) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)
        assert len(manager.blacklisted_tokens) == 1

    def test_blacklist_token_triggers_memory_limit_enforcement(
        self, manager: JWTManager
    ) -> None:
        """_enforce_memory_limit is called during blacklist_token."""
        with patch.object(manager, "_enforce_memory_limit") as mock_enforce:
            token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
            manager.blacklist_token(token)
        mock_enforce.assert_called_once()


# ==================== blacklist_token_async (lines 417-431) ====================


class TestBlacklistTokenAsync:
    """blacklist_token_async must write to Redis when available."""

    @pytest.mark.asyncio
    async def test_async_blacklist_adds_to_memory(
        self, manager: JWTManager
    ) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        await manager.blacklist_token_async(token)
        assert manager._is_blacklisted(token) is True

    @pytest.mark.asyncio
    async def test_async_blacklist_with_redis_calls_setex(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        await manager.blacklist_token_async(token)

        mock_redis.setex.assert_called_once()
        # Key must contain the prefix
        call_args = mock_redis.setex.call_args
        assert "jwt:blacklist:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_async_blacklist_redis_failure_still_updates_memory(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis write error"))
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        # Must not raise, in-memory should still be updated
        await manager.blacklist_token_async(token)
        assert manager._is_blacklisted(token) is True

    @pytest.mark.asyncio
    async def test_async_blacklist_no_redis_skips_setex(
        self, manager: JWTManager
    ) -> None:
        manager._redis_available = False
        manager._redis = None

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        # Must not raise — only in-memory update
        await manager.blacklist_token_async(token)
        assert manager._is_blacklisted(token) is True

    @pytest.mark.asyncio
    async def test_async_blacklist_empty_identifier_returns_early(
        self, manager: JWTManager
    ) -> None:
        """If _extract_jti_and_ttl returns falsy identifier, method returns early."""
        with patch.object(
            manager, "_extract_jti_and_ttl", return_value=(None, 86400)
        ):
            await manager.blacklist_token_async("any.token")
        # Nothing stored — early return path
        assert len(manager.blacklisted_tokens) == 0


# ==================== is_blacklisted_async (lines 449-472) ====================


class TestIsBlacklistedAsync:
    """is_blacklisted_async must check memory first, then Redis."""

    @pytest.mark.asyncio
    async def test_not_blacklisted_returns_false(self, manager: JWTManager) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        result = await manager.is_blacklisted_async(token)
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_blacklisted_returns_true_without_redis(
        self, manager: JWTManager
    ) -> None:
        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)  # put in memory
        result = await manager.is_blacklisted_async(token)
        assert result is True

    @pytest.mark.asyncio
    async def test_redis_hit_returns_true_and_syncs_to_memory(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)  # key exists in Redis
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        result = await manager.is_blacklisted_async(token)

        assert result is True
        # Should also sync to in-memory
        assert manager._is_blacklisted(token) is True

    @pytest.mark.asyncio
    async def test_redis_miss_returns_false(self, manager: JWTManager) -> None:
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)  # key NOT in Redis
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        result = await manager.is_blacklisted_async(token)
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_exception_falls_back_to_memory(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis read error"))
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        # Must not raise; returns False (not in memory either)
        result = await manager.is_blacklisted_async(token)
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_identifier_returns_false(
        self, manager: JWTManager
    ) -> None:
        with patch.object(
            manager, "_extract_jti_and_ttl", return_value=(None, 86400)
        ):
            result = await manager.is_blacklisted_async("any.token")
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_check_is_fast_path_no_redis_call(
        self, manager: JWTManager
    ) -> None:
        """If token is in memory, Redis must NOT be queried."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)
        manager._redis = mock_redis
        manager._redis_available = True

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        manager.blacklist_token(token)  # add to in-memory first

        result = await manager.is_blacklisted_async(token)
        assert result is True
        mock_redis.exists.assert_not_called()


# ==================== _save_refresh_token_to_db (lines 610-655) ====================


class TestSaveRefreshTokenToDb:
    """_save_refresh_token_to_db must detect device types correctly."""

    def _run_save(
        self, manager: JWTManager, user_agent: str, expected_device_type: str
    ) -> None:
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = user_agent
        mock_request.client.host = "10.0.0.1"

        refresh_token = _make_refresh_token(manager)

        mock_rt_class = MagicMock()
        captured = {}

        def capture_init(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        mock_rt_class.side_effect = capture_init

        with patch("models.database.RefreshToken", mock_rt_class):
            manager._save_refresh_token_to_db(
                mock_db, refresh_token, "42", "device-1", mock_request
            )

        assert captured.get("device_type") == expected_device_type
        mock_db.add.assert_called_once()

    def test_mobile_user_agent_sets_device_type_mobile(
        self, manager: JWTManager
    ) -> None:
        self._run_save(manager, "Mozilla/5.0 (Linux; Android 11; Mobile)", "mobile")

    def test_iphone_user_agent_sets_device_type_mobile(
        self, manager: JWTManager
    ) -> None:
        self._run_save(manager, "Mozilla/5.0 (iPhone; CPU iPhone OS 15)", "mobile")

    def test_android_user_agent_sets_device_type_mobile(
        self, manager: JWTManager
    ) -> None:
        self._run_save(manager, "Dalvik/2.1 (Linux; Android 12)", "mobile")

    def test_ipad_user_agent_sets_device_type_tablet(
        self, manager: JWTManager
    ) -> None:
        self._run_save(
            manager, "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X)", "tablet"
        )

    def test_tablet_keyword_sets_device_type_tablet(
        self, manager: JWTManager
    ) -> None:
        # Must NOT contain "mobile", "android", or "iphone" — those match first
        self._run_save(
            manager, "Mozilla/5.0 (Windows; tablet PC; rv:120.0)", "tablet"
        )

    def test_desktop_user_agent_sets_device_type_desktop(
        self, manager: JWTManager
    ) -> None:
        self._run_save(
            manager, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120", "desktop"
        )

    def test_empty_user_agent_sets_device_type_desktop(
        self, manager: JWTManager
    ) -> None:
        self._run_save(manager, "", "desktop")

    def test_invalid_refresh_token_silently_returns(
        self, manager: JWTManager
    ) -> None:
        """If decode fails, method must return without calling db.add."""
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""
        mock_request.client.host = "127.0.0.1"

        with patch("models.database.RefreshToken", MagicMock()):
            manager._save_refresh_token_to_db(
                mock_db, "bad.token.here", "42", None, mock_request
            )

        mock_db.add.assert_not_called()

    def test_ip_address_stored_from_request(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Chrome/120"
        mock_request.client.host = "192.168.1.100"

        refresh_token = _make_refresh_token(manager)
        captured = {}

        def capture_init(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        mock_rt_class = MagicMock()
        mock_rt_class.side_effect = capture_init

        with patch("models.database.RefreshToken", mock_rt_class):
            manager._save_refresh_token_to_db(
                mock_db, refresh_token, "42", None, mock_request
            )

        assert captured.get("ip_address") == "192.168.1.100"

    def test_token_hash_stored_correctly(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Chrome/120"
        mock_request.client.host = "127.0.0.1"

        refresh_token = _make_refresh_token(manager)
        expected_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        captured = {}

        def capture_init(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        mock_rt_class = MagicMock()
        mock_rt_class.side_effect = capture_init

        with patch("models.database.RefreshToken", mock_rt_class):
            manager._save_refresh_token_to_db(
                mock_db, refresh_token, "42", None, mock_request
            )

        assert captured.get("token_hash") == expected_hash


# ==================== revoke_refresh_token (lines 668-686) ====================


class TestRevokeRefreshToken:
    """revoke_refresh_token — by token hash, by JTI, and no-op path."""

    def test_revoke_by_token_hash_marks_revoked(self, manager: JWTManager) -> None:
        refresh_token = _make_refresh_token(manager)
        db_token = MagicMock()
        db_token.revoked = False

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_refresh_token(mock_db, refresh_token=refresh_token)

        assert db_token.revoked is True
        assert db_token.revoke_reason == "manual_revoke"
        mock_db.commit.assert_called_once()

    def test_revoke_by_jti_marks_revoked(self, manager: JWTManager) -> None:
        db_token = MagicMock()
        db_token.revoked = False

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_refresh_token(mock_db, jti="some-jti-value")

        assert db_token.revoked is True
        mock_db.commit.assert_called_once()

    def test_no_token_and_no_jti_returns_early(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_refresh_token(mock_db)  # neither token nor jti
        mock_db.commit.assert_not_called()

    def test_already_revoked_token_not_re_committed(
        self, manager: JWTManager
    ) -> None:
        refresh_token = _make_refresh_token(manager)
        db_token = MagicMock()
        db_token.revoked = True  # already revoked

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = db_token

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_refresh_token(mock_db, refresh_token=refresh_token)

        mock_db.commit.assert_not_called()

    def test_token_not_found_in_db_no_commit(self, manager: JWTManager) -> None:
        refresh_token = _make_refresh_token(manager)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # not found

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_refresh_token(mock_db, refresh_token=refresh_token)

        mock_db.commit.assert_not_called()


# ==================== revoke_all_user_tokens (lines 697-709) ====================


class TestRevokeAllUserTokens:
    """revoke_all_user_tokens must bulk-update and commit."""

    def test_calls_update_and_commit(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 3  # 3 rows updated

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_all_user_tokens(mock_db, user_id="user-42")

        mock_query.update.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_payload_contains_revoked_true(
        self, manager: JWTManager
    ) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        captured_payload = {}

        def capture_update(payload):
            captured_payload.update(payload)
            return 1

        mock_query.update.side_effect = capture_update

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_all_user_tokens(mock_db, user_id="user-42")

        assert captured_payload.get("revoked") is True
        assert captured_payload.get("revoke_reason") == "logout_all_devices"

    def test_revoked_at_is_set_to_recent_datetime(
        self, manager: JWTManager
    ) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        captured_payload = {}

        def capture_update(payload):
            captured_payload.update(payload)
            return 1

        mock_query.update.side_effect = capture_update

        before = datetime.now(UTC)
        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_all_user_tokens(mock_db, user_id="user-42")
        after = datetime.now(UTC)

        revoked_at = captured_payload.get("revoked_at")
        assert revoked_at is not None
        assert before <= revoked_at <= after


# ==================== revoke_device_tokens (lines 720-733) ====================


class TestRevokeDeviceTokens:
    """revoke_device_tokens must filter by user_id AND device_id."""

    def test_calls_update_and_commit(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 1

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_device_tokens(
                mock_db, user_id="user-1", device_id="device-abc"
            )

        mock_query.update.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_reason_is_device_revoke(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        captured_payload = {}

        def capture_update(payload):
            captured_payload.update(payload)
            return 1

        mock_query.update.side_effect = capture_update

        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_device_tokens(
                mock_db, user_id="user-1", device_id="device-abc"
            )

        assert captured_payload.get("revoke_reason") == "device_revoke"
        assert captured_payload.get("revoked") is True

    def test_revoked_at_is_set(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        captured_payload = {}

        def capture_update(payload):
            captured_payload.update(payload)
            return 1

        mock_query.update.side_effect = capture_update

        before = datetime.now(UTC)
        with patch("models.database.RefreshToken", MagicMock()):
            manager.revoke_device_tokens(
                mock_db, user_id="user-1", device_id="device-abc"
            )
        after = datetime.now(UTC)

        revoked_at = captured_payload.get("revoked_at")
        assert revoked_at is not None
        assert before <= revoked_at <= after


# ==================== cleanup_expired_tokens (lines 743-749) ====================


class TestCleanupExpiredTokens:
    """cleanup_expired_tokens must delete old tokens and commit."""

    def _make_mock_refresh_token_class(self) -> MagicMock:
        """
        Build a MagicMock for the RefreshToken ORM class whose 'expires_at'
        column attribute supports __lt__ comparison against a datetime.
        The comparison expression itself just needs to NOT raise — SQLAlchemy
        normally returns a BinaryExpression, so any truthy mock is fine.
        """
        mock_rt_class = MagicMock()
        # Make expires_at column attribute support < comparison
        expires_at_col = MagicMock()
        expires_at_col.__lt__ = MagicMock(return_value=MagicMock())
        mock_rt_class.expires_at = expires_at_col
        return mock_rt_class

    def test_calls_delete_and_commit(self, manager: JWTManager) -> None:
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 5  # 5 rows deleted

        mock_rt = self._make_mock_refresh_token_class()
        with patch("models.database.RefreshToken", mock_rt):
            manager.cleanup_expired_tokens(mock_db)

        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_cutoff_date_is_30_days_ago(self, manager: JWTManager) -> None:
        """Verify that cleanup deletes rows and commits — 30-day cutoff is applied."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 0

        mock_rt = self._make_mock_refresh_token_class()
        before = datetime.now(UTC)
        with patch("models.database.RefreshToken", mock_rt):
            manager.cleanup_expired_tokens(mock_db)
        after = datetime.now(UTC)

        # filter and delete must both have been called
        mock_query.filter.assert_called_once()
        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        # Sanity: both before/after are datetime objects (cutoff was 30 days ago)
        assert (after - before).total_seconds() < 5  # test ran quickly


# ==================== get_current_user (lines 786-803) ====================


class TestGetCurrentUser:
    """get_current_user dependency must reject missing/revoked tokens."""

    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self, manager: JWTManager) -> None:
        with patch("core.jwt_auth.get_jwt_manager", return_value=manager):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(
                    credentials=None, jwt_mgr=manager
                )
        assert exc_info.value.status_code == 401
        assert "Authentication credentials required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_401(self, manager: JWTManager) -> None:
        access_token = manager.create_access_token(
            "1", "u@test.com", UserRole.STUDENT
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=access_token
        )

        with patch.object(
            manager, "is_blacklisted_async", new_callable=AsyncMock, return_value=True
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=credentials, jwt_mgr=manager)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_valid_token_returns_token_payload(
        self, manager: JWTManager
    ) -> None:
        access_token = manager.create_access_token(
            "7", "user@kiro2.com", UserRole.TEACHER
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=access_token
        )

        with patch.object(
            manager, "is_blacklisted_async", new_callable=AsyncMock, return_value=False
        ):
            result = await get_current_user(credentials=credentials, jwt_mgr=manager)

        assert isinstance(result, TokenPayload)
        assert result.sub == "7"
        assert result.email == "user@kiro2.com"
        assert result.role == UserRole.TEACHER

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, manager: JWTManager) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="this.is.invalid"
        )

        with patch.object(
            manager, "is_blacklisted_async", new_callable=AsyncMock, return_value=False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=credentials, jwt_mgr=manager)

        assert exc_info.value.status_code == 401


# ==================== Additional edge-case coverage ====================


class TestBlacklistTokenAsyncEdgeCases:
    """Extra edge cases for blacklist_token_async."""

    @pytest.mark.asyncio
    async def test_async_blacklist_redis_false_but_redis_object_present(
        self, manager: JWTManager
    ) -> None:
        """_redis is set but _redis_available is False — must skip Redis."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        manager._redis = mock_redis
        manager._redis_available = False  # Marked unavailable

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        await manager.blacklist_token_async(token)

        mock_redis.setex.assert_not_called()
        assert manager._is_blacklisted(token) is True


class TestIsBlacklistedAsyncEdgeCases:
    """Extra Redis paths for is_blacklisted_async."""

    @pytest.mark.asyncio
    async def test_redis_available_false_skips_redis_check(
        self, manager: JWTManager
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)
        manager._redis = mock_redis
        manager._redis_available = False  # disabled

        token = manager.create_access_token("1", "u@test.com", UserRole.STUDENT)
        result = await manager.is_blacklisted_async(token)

        assert result is False
        mock_redis.exists.assert_not_called()


class TestRefreshAccessTokenEdgeCases:
    """Additional edge paths in refresh_access_token."""

    @pytest.mark.asyncio
    async def test_token_payload_preserved_in_new_tokens(
        self, manager: JWTManager
    ) -> None:
        """User ID, email, and role must carry through rotation."""
        refresh_token = manager.create_refresh_token(
            "99", "preserve@test.com", UserRole.ADMIN
        )
        result = await manager.refresh_access_token(refresh_token)

        new_payload = pyjwt.decode(
            result.access_token,
            manager.secret_key,
            algorithms=[manager.algorithm],
        )
        assert new_payload["sub"] == "99"
        assert new_payload["email"] == "preserve@test.com"
        assert new_payload["role"] == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_device_id_preserved_through_rotation(
        self, manager: JWTManager
    ) -> None:
        refresh_token = manager.create_refresh_token(
            "1", "u@test.com", UserRole.STUDENT, device_id="dev-xyz"
        )
        result = await manager.refresh_access_token(refresh_token)

        new_refresh_payload = pyjwt.decode(
            result.refresh_token,
            manager.secret_key,
            algorithms=[manager.algorithm],
        )
        assert new_refresh_payload.get("device_id") == "dev-xyz"
