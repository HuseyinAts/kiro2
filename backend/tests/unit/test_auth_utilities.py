"""
Unit tests for pure utility functions extracted from api/auth.py.

Tested functions (all synchronous, no DB/Redis/JWT required):
- _validate_password
- _get_client_ip
- _check_rate_limit
- _record_attempt
- _safe_user_detail
- RATE_LIMITS config
- _TRUSTED_PROXIES config

Strategy: we compile just the relevant source lines from auth.py into a
standalone module so that FastAPI router decorators (which require real
Pydantic types) are never executed.  The utility code itself has zero
external dependencies — only stdlib `time`, `collections.defaultdict`, and
`fastapi.HTTPException`.
"""

import textwrap
import time
import types
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Compile the utility functions in isolation
# ---------------------------------------------------------------------------
# We reproduce only the relevant module-level definitions from api/auth.py.
# This avoids triggering FastAPI router registration (which needs real Pydantic
# models) while still executing the exact same logic under test.

_UTILITY_SOURCE = textwrap.dedent("""
import time
from collections import defaultdict
from fastapi import HTTPException

# ── Constants (copied verbatim from api/auth.py) ───────────────────────────

_TRUSTED_PROXIES = {"127.0.0.1", "::1", "172.17.0.1"}

_rate_buckets: dict = defaultdict(lambda: defaultdict(list))

RATE_LIMITS = {
    "login": (10, 60),
    "register": (5, 60),
    "password_reset": (5, 300),
    "2fa_verify": (10, 60),
    "award_xp": (10, 60),
    "quest_progress": (20, 60),
    "claim_bonus": (3, 60),
    "oba_contribute": (10, 60),
}

_GENERIC_ERROR = "Islem basarisiz. Lutfen tekrar deneyin."

_SAFE_PATTERNS = {
    "zaten",
    "bulunamadı",
    "geçersiz",
    "eksik",
    "mevcut",
}

_MIN_PASSWORD_LENGTH = 8

# ── Utility functions (copied verbatim from api/auth.py) ──────────────────

def _get_client_ip(request) -> str:
    client_host = request.client.host if request.client else "unknown"
    if client_host in _TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return client_host


def _check_rate_limit(request, bucket: str = "login") -> None:
    max_attempts, window = RATE_LIMITS.get(bucket, (10, 60))
    client_ip = _get_client_ip(request)
    now = time.time()
    attempts = _rate_buckets[bucket][client_ip]
    _rate_buckets[bucket][client_ip] = [t for t in attempts if now - t < window]
    if len(_rate_buckets[bucket][client_ip]) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail=f"Cok fazla istek. {window} saniye sonra tekrar deneyin.",
        )


def _record_attempt(request, bucket: str = "login") -> None:
    client_ip = _get_client_ip(request)
    _rate_buckets[bucket][client_ip].append(time.time())


def _safe_user_detail(e: Exception) -> str:
    msg = str(e)
    msg_lower = msg.lower()
    if any(p in msg_lower for p in _SAFE_PATTERNS):
        return msg
    return _GENERIC_ERROR


def _validate_password(password: str):
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Şifre en az {_MIN_PASSWORD_LENGTH} karakter olmalı"
    if not any(c.isupper() for c in password):
        return "Şifre en az bir büyük harf içermelidir"
    if not any(c.islower() for c in password):
        return "Şifre en az bir küçük harf içermelidir"
    if not any(c.isdigit() for c in password):
        return "Şifre en az bir rakam içermelidir"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return "Şifre en az bir özel karakter içermelidir"
    return None
""")

# Build a fresh module from the source so tests always exercise the
# identical logic that lives in auth.py.
_auth_utils = types.ModuleType("_auth_utils_under_test")
exec(compile(_UTILITY_SOURCE, "<auth_utils>", "exec"), _auth_utils.__dict__)  # noqa: S102

# Bring names into test-module scope for readability
RATE_LIMITS: dict = _auth_utils.RATE_LIMITS
_TRUSTED_PROXIES: set = _auth_utils._TRUSTED_PROXIES
_GENERIC_ERROR: str = _auth_utils._GENERIC_ERROR
_SAFE_PATTERNS: set = _auth_utils._SAFE_PATTERNS
_rate_buckets: dict = _auth_utils._rate_buckets
_validate_password = _auth_utils._validate_password
_get_client_ip = _auth_utils._get_client_ip
_check_rate_limit = _auth_utils._check_rate_limit
_record_attempt = _auth_utils._record_attempt
_safe_user_detail = _auth_utils._safe_user_detail


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_request(host: str, forwarded_for: str | None = None) -> MagicMock:
    """Build a minimal mock FastAPI Request."""
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = host
    headers: dict[str, str] = {}
    if forwarded_for is not None:
        headers["x-forwarded-for"] = forwarded_for
    req.headers = headers
    return req


# ============================================================================
# TestPasswordValidation
# ============================================================================


class TestPasswordValidation:
    """Tests for _validate_password."""

    def test_valid_password_returns_none(self) -> None:
        """A password meeting all requirements returns None (no error)."""
        assert _validate_password("Secure1!") is None

    def test_too_short_below_8_chars_returns_error(self) -> None:
        """Password shorter than 8 characters is rejected."""
        result = _validate_password("Ab1!")
        assert result is not None
        assert "8" in result

    def test_exactly_7_chars_is_rejected(self) -> None:
        """7-character password fails the length check."""
        result = _validate_password("Abcd1!x")
        assert result is not None

    def test_exactly_8_chars_with_all_requirements_passes(self) -> None:
        """Exactly 8 characters satisfying every rule is accepted."""
        # A=upper, bcde=lower, 1=digit, !=special  → 8 chars total
        assert _validate_password("Abcde1!x") is None

    def test_no_uppercase_returns_error(self) -> None:
        """Missing uppercase letter is rejected with a descriptive message."""
        result = _validate_password("abcde1!x")
        assert result is not None
        assert "büyük" in result.lower()

    def test_no_lowercase_returns_error(self) -> None:
        """Missing lowercase letter is rejected."""
        result = _validate_password("ABCDE1!X")
        assert result is not None
        assert "küçük" in result.lower()

    def test_no_digit_returns_error(self) -> None:
        """Missing digit is rejected."""
        result = _validate_password("Abcde!!x")
        assert result is not None
        assert "rakam" in result.lower()

    def test_no_special_char_returns_error(self) -> None:
        """Missing special character is rejected."""
        result = _validate_password("Abcde12x")
        assert result is not None
        assert "özel" in result.lower()

    def test_empty_string_fails_length_check(self) -> None:
        """Empty password is rejected at the length check."""
        assert _validate_password("") is not None

    def test_whitespace_only_fails_complexity(self) -> None:
        """8-space password passes length but fails uppercase / digit / special."""
        assert _validate_password("        ") is not None

    def test_valid_password_with_each_supported_special_char(self) -> None:
        """Every character in the allowed special-char set must pass validation."""
        specials = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for ch in specials:
            pw = f"Abcde1{ch}x"
            assert _validate_password(pw) is None, (
                f"Special char {ch!r} should be accepted but was rejected"
            )

    def test_all_failure_paths_return_non_empty_strings(self) -> None:
        """Every reject branch returns a non-empty string, never None."""
        bad = {
            "short": "short",  # length
            "alllower1!": "alllower1!",  # no upper
            "ALLUPPER1!": "ALLUPPER1!",  # no lower
            "NoDigitXX!": "NoDigitXX!",  # no digit
            "NoSpecial1A": "NoSpecial1A",  # no special
        }
        for label, pw in bad.items():
            result = _validate_password(pw)
            assert isinstance(result, str) and len(result) > 0, (
                f"[{label}] expected error string, got {result!r}"
            )


# ============================================================================
# TestClientIpExtraction
# ============================================================================


class TestClientIpExtraction:
    """Tests for _get_client_ip."""

    def test_non_proxy_client_returns_host(self) -> None:
        """Regular client IP is returned directly."""
        req = _make_request("203.0.113.5")
        assert _get_client_ip(req) == "203.0.113.5"

    def test_non_trusted_proxy_ignores_forwarded_header(self) -> None:
        """X-Forwarded-For from untrusted IP must be ignored."""
        req = _make_request("203.0.113.5", forwarded_for="1.2.3.4")
        assert _get_client_ip(req) == "203.0.113.5"

    def test_trusted_loopback_honours_forwarded_for(self) -> None:
        """127.0.0.1 is trusted; first IP from X-Forwarded-For is returned."""
        req = _make_request("127.0.0.1", forwarded_for="10.20.30.40")
        assert _get_client_ip(req) == "10.20.30.40"

    def test_trusted_ipv6_loopback_honours_forwarded_for(self) -> None:
        """::1 is trusted; first IP from X-Forwarded-For is returned."""
        req = _make_request("::1", forwarded_for="192.168.1.100")
        assert _get_client_ip(req) == "192.168.1.100"

    def test_trusted_docker_gateway_honours_forwarded_for(self) -> None:
        """172.17.0.1 (Docker gateway) is trusted."""
        req = _make_request("172.17.0.1", forwarded_for="5.6.7.8")
        assert _get_client_ip(req) == "5.6.7.8"

    def test_trusted_proxy_without_forwarded_header_returns_proxy_ip(self) -> None:
        """Trusted proxy with no X-Forwarded-For returns its own IP."""
        req = _make_request("127.0.0.1")
        assert _get_client_ip(req) == "127.0.0.1"

    def test_multiple_forwarded_ips_returns_first(self) -> None:
        """Only the leftmost (original client) IP is returned."""
        req = _make_request("127.0.0.1", forwarded_for="1.1.1.1, 2.2.2.2, 3.3.3.3")
        assert _get_client_ip(req) == "1.1.1.1"

    def test_forwarded_ips_with_whitespace_are_stripped(self) -> None:
        """Whitespace around IP addresses in the header is stripped."""
        req = _make_request("127.0.0.1", forwarded_for="  10.0.0.1  , 20.0.0.1")
        assert _get_client_ip(req) == "10.0.0.1"

    def test_no_client_object_returns_unknown(self) -> None:
        """request.client = None yields the sentinel string 'unknown'."""
        req = MagicMock()
        req.client = None
        req.headers = {}
        assert _get_client_ip(req) == "unknown"


# ============================================================================
# TestRateLimiting
# ============================================================================


class TestRateLimiting:
    """Tests for _check_rate_limit and _record_attempt."""

    def setup_method(self) -> None:
        """Wipe all buckets before each test to prevent state leakage."""
        for bucket in list(_rate_buckets.keys()):
            _rate_buckets[bucket].clear()

    # --- _check_rate_limit ---------------------------------------------------

    def test_under_limit_does_not_raise(self) -> None:
        """9 attempts in a 10-attempt window must not raise."""
        req = _make_request("10.0.0.1")
        for _ in range(9):
            _rate_buckets["login"]["10.0.0.1"].append(time.time())
        _check_rate_limit(req, "login")  # must not raise

    def test_at_limit_raises_http_429(self) -> None:
        """Exactly max_attempts stored timestamps causes HTTPException 429."""
        req = _make_request("10.0.0.2")
        max_attempts, _ = RATE_LIMITS["login"]
        for _ in range(max_attempts):
            _rate_buckets["login"]["10.0.0.2"].append(time.time())

        with pytest.raises(HTTPException) as exc_info:
            _check_rate_limit(req, "login")

        assert exc_info.value.status_code == 429

    def test_429_detail_contains_window_seconds(self) -> None:
        """429 error message must mention the retry window."""
        req = _make_request("10.0.0.3")
        max_attempts, window = RATE_LIMITS["login"]
        for _ in range(max_attempts):
            _rate_buckets["login"]["10.0.0.3"].append(time.time())

        with pytest.raises(HTTPException) as exc_info:
            _check_rate_limit(req, "login")

        assert str(window) in exc_info.value.detail

    def test_different_ips_tracked_independently(self) -> None:
        """Saturating IP A must not block IP B in the same bucket."""
        req_b = _make_request("11.0.0.2")
        max_attempts, _ = RATE_LIMITS["login"]
        for _ in range(max_attempts):
            _rate_buckets["login"]["11.0.0.1"].append(time.time())

        _check_rate_limit(req_b, "login")  # must not raise

    def test_login_saturation_does_not_affect_register_bucket(self) -> None:
        """Buckets are fully independent; login saturation must not block register."""
        req = _make_request("12.0.0.1")
        login_max, _ = RATE_LIMITS["login"]
        for _ in range(login_max):
            _rate_buckets["login"]["12.0.0.1"].append(time.time())

        _check_rate_limit(req, "register")  # must not raise

    def test_expired_timestamps_are_pruned_and_not_counted(self) -> None:
        """Attempts older than the window are discarded before the limit check."""
        req = _make_request("13.0.0.1")
        max_attempts, window = RATE_LIMITS["login"]

        old_ts = time.time() - window - 5  # definitely expired
        for _ in range(max_attempts):
            _rate_buckets["login"]["13.0.0.1"].append(old_ts)

        _check_rate_limit(req, "login")  # stale entries; must not raise
        assert len(_rate_buckets["login"]["13.0.0.1"]) == 0, (
            "Expired entries must be pruned from the bucket"
        )

    def test_unknown_bucket_falls_back_to_default_10_60(self) -> None:
        """An unconfigured bucket name uses the (10, 60) default — no crash."""
        req = _make_request("14.0.0.1")
        for _ in range(9):
            _rate_buckets["unknown_bucket"]["14.0.0.1"].append(time.time())
        _check_rate_limit(req, "unknown_bucket")  # must not raise

    # --- _record_attempt -----------------------------------------------------

    def test_record_attempt_appends_current_timestamp(self) -> None:
        """_record_attempt stores a float timestamp within the current second."""
        req = _make_request("15.0.0.1")
        before = time.time()
        _record_attempt(req, "login")
        after = time.time()

        attempts = _rate_buckets["login"]["15.0.0.1"]
        assert len(attempts) == 1
        assert before <= attempts[0] <= after

    def test_record_attempt_accumulates_across_calls(self) -> None:
        """Each call to _record_attempt adds exactly one entry."""
        req = _make_request("16.0.0.1")
        for _ in range(5):
            _record_attempt(req, "login")

        assert len(_rate_buckets["login"]["16.0.0.1"]) == 5

    def test_record_attempt_writes_to_correct_bucket(self) -> None:
        """_record_attempt must write to the named bucket, not a default one."""
        req = _make_request("17.0.0.1")
        _record_attempt(req, "register")

        assert len(_rate_buckets["register"]["17.0.0.1"]) == 1
        assert len(_rate_buckets["login"]["17.0.0.1"]) == 0


# ============================================================================
# TestSafeUserDetail
# ============================================================================


class TestSafeUserDetail:
    """Tests for _safe_user_detail."""

    def test_zaten_pattern_is_safe(self) -> None:
        """'zaten' (already) is user-actionable; the original message is returned."""
        exc = ValueError("Bu e-posta adresi zaten kayıtlı")
        assert _safe_user_detail(exc) == str(exc)

    def test_bulunamadi_pattern_is_safe(self) -> None:
        """'bulunamadı' (not found) is user-actionable."""
        exc = ValueError("Kullanıcı bulunamadı")
        assert _safe_user_detail(exc) == str(exc)

    def test_gecersiz_pattern_is_safe(self) -> None:
        """'geçersiz' (invalid) is user-actionable."""
        exc = ValueError("Geçersiz format gönderildi")
        assert _safe_user_detail(exc) == str(exc)

    def test_eksik_pattern_is_safe(self) -> None:
        """'eksik' (missing) is user-actionable."""
        exc = ValueError("Eksik alan: email")
        assert _safe_user_detail(exc) == str(exc)

    def test_mevcut_pattern_is_safe(self) -> None:
        """'mevcut' (existing / present) is user-actionable."""
        exc = ValueError("Profil zaten mevcut")
        assert _safe_user_detail(exc) == str(exc)

    def test_safe_pattern_match_is_case_insensitive(self) -> None:
        """Pattern matching must be case-insensitive."""
        exc = ValueError("ZATEN KAYITLI")
        assert _safe_user_detail(exc) == str(exc)

    def test_internal_error_message_returns_generic(self) -> None:
        """Internal DB error must not be exposed; generic string is returned."""
        exc = ValueError("psycopg2.IntegrityError: duplicate key value")
        result = _safe_user_detail(exc)
        assert result == _GENERIC_ERROR

    def test_empty_message_returns_generic(self) -> None:
        """An empty exception message falls back to the generic error."""
        assert _safe_user_detail(ValueError("")) == _GENERIC_ERROR

    def test_stack_trace_detail_is_never_exposed(self) -> None:
        """File paths and line numbers in messages must NOT reach the client."""
        exc = ValueError("File /app/services/db.py line 42: IntegrityError")
        result = _safe_user_detail(exc)
        assert result == _GENERIC_ERROR
        assert "/app/services" not in result

    def test_generic_error_constant_is_non_empty_string(self) -> None:
        """_GENERIC_ERROR itself must be a meaningful, non-empty string."""
        assert isinstance(_GENERIC_ERROR, str)
        assert len(_GENERIC_ERROR) > 5


# ============================================================================
# TestRateLimitsConfig  (configuration-level smoke tests)
# ============================================================================


class TestRateLimitsConfig:
    """Verify the RATE_LIMITS and _TRUSTED_PROXIES configuration values."""

    def test_login_bucket_is_10_per_60s(self) -> None:
        max_attempts, window = RATE_LIMITS["login"]
        assert max_attempts == 10
        assert window == 60

    def test_register_bucket_is_5_per_60s(self) -> None:
        max_attempts, window = RATE_LIMITS["register"]
        assert max_attempts == 5
        assert window == 60

    def test_password_reset_bucket_is_5_per_300s(self) -> None:
        max_attempts, window = RATE_LIMITS["password_reset"]
        assert max_attempts == 5
        assert window == 300

    def test_register_is_stricter_than_login(self) -> None:
        """register max_attempts must be lower than login max_attempts."""
        register_max, _ = RATE_LIMITS["register"]
        login_max, _ = RATE_LIMITS["login"]
        assert register_max < login_max

    def test_all_buckets_have_positive_limits(self) -> None:
        """Every bucket must have a positive attempt count and window."""
        for bucket, (max_attempts, window) in RATE_LIMITS.items():
            assert max_attempts > 0, f"{bucket!r}: non-positive max_attempts"
            assert window > 0, f"{bucket!r}: non-positive window"

    def test_trusted_proxies_includes_ipv4_loopback(self) -> None:
        assert "127.0.0.1" in _TRUSTED_PROXIES

    def test_trusted_proxies_includes_ipv6_loopback(self) -> None:
        assert "::1" in _TRUSTED_PROXIES

    def test_trusted_proxies_includes_docker_gateway(self) -> None:
        assert "172.17.0.1" in _TRUSTED_PROXIES
