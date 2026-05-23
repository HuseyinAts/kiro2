"""S197 phantom audit cleanup — basic enum/dataclass/helper coverage.

Targets zero-cost surface: enums, dataclasses, pure helper methods.
BaseHTTPMiddleware.dispatch() is intentionally excluded — those methods
require a full HTTP context and are covered by e2e/golden_flow tests.

Import strategy: `fastapi.middleware.base` does not exist in FastAPI 0.128.0
(moved to starlette). We patch it and the heavy internal deps before importing
the module under test.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module-level mock setup — must happen before the module is imported.
# We mock the broken import path and all heavy internal deps so that the
# pure surface (enums, dataclasses, helpers) can be exercised in isolation.
# ---------------------------------------------------------------------------

_MOCKED = [
    "fastapi.middleware.base",
    "core.enhanced_authentication",
    "core.error_context",
    "core.error_monitoring",
    "core.exceptions",
    "core.rbac_system",
    "core.response_models",
]

for _mod in _MOCKED:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from core.security_middleware import (  # noqa: E402 (must follow mocks)
    BlockAction,
    RateLimiter,
    RateLimitRecord,
    RateLimitType,
    SecurityLevel,
    SecurityMiddlewareConfig,
    SecurityThreat,
    SecurityValidator,
    get_security_middleware_config,
    update_security_config,
)

# ===========================================================================
# SecurityLevel enum
# ===========================================================================


class TestSecurityLevelEnum:
    def test_has_five_levels(self) -> None:
        assert len(list(SecurityLevel)) == 5

    def test_public_value(self) -> None:
        assert SecurityLevel.PUBLIC.value == "public"

    def test_authenticated_value(self) -> None:
        assert SecurityLevel.AUTHENTICATED.value == "authenticated"

    def test_authorized_value(self) -> None:
        assert SecurityLevel.AUTHORIZED.value == "authorized"

    def test_admin_value(self) -> None:
        assert SecurityLevel.ADMIN.value == "admin"

    def test_system_value(self) -> None:
        assert SecurityLevel.SYSTEM.value == "system"

    def test_membership(self) -> None:
        assert SecurityLevel("public") is SecurityLevel.PUBLIC
        assert SecurityLevel("admin") is SecurityLevel.ADMIN


# ===========================================================================
# RateLimitType enum
# ===========================================================================


class TestRateLimitTypeEnum:
    def test_has_four_types(self) -> None:
        assert len(list(RateLimitType)) == 4

    def test_per_ip_value(self) -> None:
        assert RateLimitType.PER_IP.value == "per_ip"

    def test_per_user_value(self) -> None:
        assert RateLimitType.PER_USER.value == "per_user"

    def test_per_endpoint_value(self) -> None:
        assert RateLimitType.PER_ENDPOINT.value == "per_endpoint"

    def test_global_value(self) -> None:
        assert RateLimitType.GLOBAL.value == "global"


# ===========================================================================
# SecurityThreat enum
# ===========================================================================


class TestSecurityThreatEnum:
    def test_has_eight_threats(self) -> None:
        assert len(list(SecurityThreat)) == 8

    @pytest.mark.parametrize(
        "value",
        [
            "brute_force",
            "ddos",
            "sql_injection",
            "xss",
            "csrf",
            "suspicious_user_agent",
            "malformed_request",
            "rate_limit_exceeded",
        ],
    )
    def test_each_threat_value(self, value: str) -> None:
        assert SecurityThreat(value) is not None

    def test_high_severity_threats_exist(self) -> None:
        """SQL injection and XSS must be in the enum — they gate blocking logic."""
        assert SecurityThreat.SQL_INJECTION.value == "sql_injection"
        assert SecurityThreat.XSS.value == "xss"


# ===========================================================================
# BlockAction enum
# ===========================================================================


class TestBlockActionEnum:
    def test_has_five_actions(self) -> None:
        assert len(list(BlockAction)) == 5

    def test_log_value(self) -> None:
        assert BlockAction.LOG.value == "log"

    def test_block_value(self) -> None:
        assert BlockAction.BLOCK.value == "block"

    def test_temporary_ban_value(self) -> None:
        assert BlockAction.TEMPORARY_BAN.value == "temporary_ban"


# ===========================================================================
# SecurityMiddlewareConfig dataclass
# ===========================================================================


class TestSecurityMiddlewareConfig:
    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(SecurityMiddlewareConfig)

    def test_default_instantiation(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg is not None

    def test_enable_authentication_default_true(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.enable_authentication is True

    def test_enable_rate_limiting_default_true(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.enable_rate_limiting is True

    def test_global_rate_limit_default(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.global_rate_limit_per_minute == 1000

    def test_user_rate_limit_default(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.user_rate_limit_per_minute == 100

    def test_ip_rate_limit_default(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.ip_rate_limit_per_minute == 200

    def test_max_request_size_10mb(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.max_request_size == 10 * 1024 * 1024

    def test_security_headers_auto_populated(self) -> None:
        """__post_init__ must populate security_headers when empty."""
        cfg = SecurityMiddlewareConfig()
        assert len(cfg.security_headers) > 0
        assert "X-Content-Type-Options" in cfg.security_headers
        assert "X-Frame-Options" in cfg.security_headers

    def test_trusted_proxies_contain_localhost(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert "127.0.0.1" in cfg.trusted_proxies

    def test_allow_credentials_default_true(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert cfg.allow_credentials is True

    def test_custom_values_accepted(self) -> None:
        cfg = SecurityMiddlewareConfig(
            enable_authentication=False,
            global_rate_limit_per_minute=500,
        )
        assert cfg.enable_authentication is False
        assert cfg.global_rate_limit_per_minute == 500

    def test_ip_whitelist_starts_empty(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert isinstance(cfg.ip_whitelist, set)
        assert len(cfg.ip_whitelist) == 0

    def test_ip_blacklist_starts_empty(self) -> None:
        cfg = SecurityMiddlewareConfig()
        assert isinstance(cfg.ip_blacklist, set)
        assert len(cfg.ip_blacklist) == 0


# ===========================================================================
# RateLimitRecord dataclass
# ===========================================================================


class TestRateLimitRecord:
    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(RateLimitRecord)

    def test_default_instantiation(self) -> None:
        rec = RateLimitRecord()
        assert rec.warning_count == 0
        assert rec.blocked_until is None

    def test_not_blocked_by_default(self) -> None:
        rec = RateLimitRecord()
        assert rec.is_blocked() is False

    def test_add_request_increments_count(self) -> None:
        rec = RateLimitRecord()
        now = datetime.now(UTC)
        rec.add_request(now)
        assert rec.get_request_count() == 1

    def test_add_multiple_requests(self) -> None:
        rec = RateLimitRecord()
        now = datetime.now(UTC)
        for _ in range(5):
            rec.add_request(now)
        assert rec.get_request_count() == 5

    def test_old_requests_pruned_from_window(self) -> None:
        rec = RateLimitRecord()
        two_minutes_ago = datetime.now(UTC) - timedelta(minutes=2)
        rec.add_request(two_minutes_ago)
        # Only request older than 1 minute should be pruned on next add
        rec.add_request(datetime.now(UTC))
        assert rec.get_request_count() == 1

    def test_is_blocked_when_blocked_until_future(self) -> None:
        rec = RateLimitRecord()
        rec.blocked_until = datetime.now(UTC) + timedelta(minutes=15)
        assert rec.is_blocked() is True

    def test_is_not_blocked_when_block_expired(self) -> None:
        rec = RateLimitRecord()
        rec.blocked_until = datetime.now(UTC) - timedelta(minutes=1)
        assert rec.is_blocked() is False


# ===========================================================================
# SecurityValidator — pure helpers
# ===========================================================================


@pytest.fixture
def validator() -> SecurityValidator:
    cfg = SecurityMiddlewareConfig()
    return SecurityValidator(cfg)


class TestSecurityValidatorHelpers:
    def test_clean_text_not_sql_injection(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("hello world") is False

    def test_union_select_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("union select * from users") is True

    def test_drop_table_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("drop table users") is True

    def test_insert_into_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("insert into users values(1)") is True

    def test_delete_from_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("delete from users where 1=1") is True

    def test_sql_comment_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_sql_injection("admin'--") is True

    def test_clean_text_not_xss(self, validator: SecurityValidator) -> None:
        assert validator._check_xss("hello world") is False

    def test_script_tag_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_xss("<script>alert(1)</script>") is True

    def test_javascript_protocol_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_xss("javascript:alert(1)") is True

    def test_onerror_event_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_xss("onerror=malicious()") is True

    def test_iframe_detected(self, validator: SecurityValidator) -> None:
        assert validator._check_xss("<iframe src='evil'>") is True


# ===========================================================================
# RateLimiter — pure IP validation helper
# ===========================================================================


@pytest.fixture
def rate_limiter() -> RateLimiter:
    return RateLimiter(SecurityMiddlewareConfig())


class TestRateLimiterIPValidation:
    def test_valid_ipv4(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("192.168.1.1") is True

    def test_valid_ipv4_loopback(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("127.0.0.1") is True

    def test_valid_ipv6_loopback(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("::1") is True

    def test_valid_ipv6_full(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("2001:db8::1") is True

    def test_invalid_hostname(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("not-an-ip") is False

    def test_invalid_injection_attempt(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("1.2.3.4; DROP TABLE users") is False

    def test_empty_string_invalid(self, rate_limiter: RateLimiter) -> None:
        assert rate_limiter._is_valid_ip("") is False


# ===========================================================================
# Global config helpers
# ===========================================================================


class TestGlobalConfigHelpers:
    def test_get_security_middleware_config_returns_config(self) -> None:
        cfg = get_security_middleware_config()
        assert isinstance(cfg, SecurityMiddlewareConfig)

    def test_update_security_config_mutates_global(self) -> None:
        original = get_security_middleware_config().log_all_requests
        try:
            update_security_config(log_all_requests=not original)
            assert get_security_middleware_config().log_all_requests is not original
        finally:
            update_security_config(log_all_requests=original)

    def test_update_security_config_ignores_unknown_keys(self) -> None:
        # Must not raise on unknown key
        update_security_config(nonexistent_key_xyz="value")
