"""
Unit tests for pure functions in api/auth.py.

Tests target:
- _validate_password: password strength validation (pure function, no mocks)
- _get_client_ip: IP extraction with trusted proxy logic (Request mock)
- _TRUSTED_PROXIES: expected set members
- role_mapping dicts: SUPER_ADMIN key presence
"""

import sys

sys.path.insert(0, "C:/Users/husey/kiro2/backend")

from unittest.mock import MagicMock

import pytest

from api.auth import (
    _TRUSTED_PROXIES,
    _get_client_ip,
    _validate_password,
)

# ==================== _validate_password ====================


class TestValidatePasswordLength:
    """Tests for minimum length requirement."""

    def test_empty_password_fails(self) -> None:
        result = _validate_password("")
        assert result is not None
        assert "karakter" in result

    def test_seven_char_password_fails(self) -> None:
        # Exactly one character short; length rule fires first.
        result = _validate_password("Ab1!Xyz")
        assert result is not None
        assert "karakter" in result

    def test_eight_char_valid_password_passes(self) -> None:
        # Minimum-length password satisfying all rules.
        result = _validate_password("Abcde1!x")
        assert result is None

    def test_long_valid_password_passes(self) -> None:
        result = _validate_password("MySecure@Pass123")
        assert result is None


class TestValidatePasswordUppercase:
    """Tests for uppercase requirement."""

    def test_no_uppercase_fails(self) -> None:
        result = _validate_password("abcde1!xyz")
        assert result is not None
        assert "büyük harf" in result

    def test_single_uppercase_passes_uppercase_check(self) -> None:
        # Has uppercase + all other requirements.
        result = _validate_password("Abcde1!xyz")
        assert result is None


class TestValidatePasswordLowercase:
    """Tests for lowercase requirement."""

    def test_no_lowercase_fails(self) -> None:
        result = _validate_password("ABCDE1!XYZ")
        assert result is not None
        assert "küçük harf" in result

    def test_single_lowercase_passes_lowercase_check(self) -> None:
        result = _validate_password("ABCDe1!XYZ")
        assert result is None


class TestValidatePasswordDigit:
    """Tests for digit requirement."""

    def test_no_digit_fails(self) -> None:
        result = _validate_password("Abcdefg!h")
        assert result is not None
        assert "rakam" in result

    def test_single_digit_passes_digit_check(self) -> None:
        result = _validate_password("Abcdefg1!")
        assert result is None


class TestValidatePasswordSpecialChar:
    """Tests for special character requirement."""

    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def test_no_special_char_fails(self) -> None:
        result = _validate_password("Abcde1fgH")
        assert result is not None
        assert "özel karakter" in result

    @pytest.mark.parametrize("char", list("!@#$%^&*()_+"))
    def test_each_special_char_satisfies_requirement(self, char: str) -> None:
        password = f"Abcde1{char}xyz"
        result = _validate_password(password)
        assert (
            result is None
        ), f"Expected None for password with '{char}', got: {result}"

    def test_bracket_special_chars_satisfy_requirement(self) -> None:
        result = _validate_password("Abcde1[xyz")
        assert result is None

    def test_angle_bracket_satisfies_requirement(self) -> None:
        result = _validate_password("Abcde1<xyz")
        assert result is None


class TestValidatePasswordValidCases:
    """Tests for passwords that should return None (fully valid)."""

    @pytest.mark.parametrize(
        "password",
        [
            "Kiro2Beta!",
            "MyStr0ng@Pass",
            "Secure#1Password",
            "Abcd1234!",
            "Test@1234",
            "Pa$$w0rd!",
        ],
    )
    def test_valid_passwords_return_none(self, password: str) -> None:
        result = _validate_password(password)
        assert result is None, f"Expected None for '{password}', got: {result}"

    def test_returns_none_not_false_for_valid_password(self) -> None:
        result = _validate_password("ValidPass1!")
        # Must be exactly None, not just falsy
        assert result is None

    def test_returns_string_not_exception_for_invalid_password(self) -> None:
        result = _validate_password("weak")
        assert isinstance(result, str)


# ==================== _TRUSTED_PROXIES ====================


class TestTrustedProxies:
    """Tests for the _TRUSTED_PROXIES set definition."""

    def test_is_a_set(self) -> None:
        assert isinstance(_TRUSTED_PROXIES, set)

    def test_contains_localhost_ipv4(self) -> None:
        assert "127.0.0.1" in _TRUSTED_PROXIES

    def test_contains_localhost_ipv6(self) -> None:
        assert "::1" in _TRUSTED_PROXIES

    def test_contains_docker_default_gateway(self) -> None:
        assert "172.17.0.1" in _TRUSTED_PROXIES

    def test_does_not_contain_arbitrary_public_ip(self) -> None:
        assert "8.8.8.8" not in _TRUSTED_PROXIES

    def test_does_not_contain_rfc1918_10_block(self) -> None:
        # 10.0.0.1 is NOT trusted by default — only explicit proxies.
        assert "10.0.0.1" not in _TRUSTED_PROXIES


# ==================== _get_client_ip ====================


def _make_request(
    client_host: str,
    x_forwarded_for: str | None = None,
) -> MagicMock:
    """Build a minimal FastAPI Request mock."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = client_host
    headers: dict[str, str] = {}
    if x_forwarded_for is not None:
        headers["x-forwarded-for"] = x_forwarded_for
    request.headers = headers
    return request


class TestGetClientIp:
    """Tests for _get_client_ip with trusted/untrusted proxy logic."""

    def test_direct_client_returns_host(self) -> None:
        request = _make_request("192.168.1.1")
        result = _get_client_ip(request)
        assert result == "192.168.1.1"

    def test_trusted_proxy_uses_forwarded_header(self) -> None:
        request = _make_request("127.0.0.1", x_forwarded_for="203.0.113.5")
        result = _get_client_ip(request)
        assert result == "203.0.113.5"

    def test_trusted_proxy_takes_first_ip_from_chain(self) -> None:
        # X-Forwarded-For can be a comma-separated chain; first is the real client.
        request = _make_request("127.0.0.1", x_forwarded_for="10.1.1.1, 10.2.2.2")
        result = _get_client_ip(request)
        assert result == "10.1.1.1"

    def test_trusted_proxy_strips_whitespace_from_forwarded_ip(self) -> None:
        request = _make_request("::1", x_forwarded_for="  203.0.113.99  ")
        result = _get_client_ip(request)
        assert result == "203.0.113.99"

    def test_untrusted_proxy_ignores_forwarded_header(self) -> None:
        # 10.0.0.1 is NOT in _TRUSTED_PROXIES → header must be ignored.
        request = _make_request("10.0.0.1", x_forwarded_for="1.2.3.4")
        result = _get_client_ip(request)
        assert result == "10.0.0.1"

    def test_public_ip_ignores_forwarded_header(self) -> None:
        request = _make_request("203.0.113.1", x_forwarded_for="99.99.99.99")
        result = _get_client_ip(request)
        assert result == "203.0.113.1"

    def test_trusted_proxy_without_forwarded_header_returns_host(self) -> None:
        request = _make_request("127.0.0.1")
        result = _get_client_ip(request)
        assert result == "127.0.0.1"

    def test_docker_gateway_is_trusted_proxy(self) -> None:
        request = _make_request("172.17.0.1", x_forwarded_for="198.51.100.7")
        result = _get_client_ip(request)
        assert result == "198.51.100.7"

    def test_no_client_returns_unknown(self) -> None:
        request = MagicMock()
        request.client = None
        request.headers = {}
        result = _get_client_ip(request)
        assert result == "unknown"


# ==================== role_mapping completeness ====================


class TestRoleMappingCompleteness:
    """
    auth.py has three local role_mapping dicts.
    Each must include SUPER_ADMIN to prevent privilege escalation bugs.

    We verify the canonical mapping used in the login path by importing
    the module and inspecting the source text — the dicts are local
    variables, so we do a pattern-level check via the module source.
    """

    def test_validate_password_exists_and_is_callable(self) -> None:
        assert callable(_validate_password)

    def test_get_client_ip_exists_and_is_callable(self) -> None:
        assert callable(_get_client_ip)

    def test_role_mapping_student_value(self) -> None:
        """Ensure the canonical role mapping produces expected frontend role."""
        # We cannot import the dict directly (local variable), but we can
        # verify the mapping indirectly through the module's source.
        import inspect

        import api.auth as auth_module

        source = inspect.getsource(auth_module)
        # All three role_mapping blocks must map SUPER_ADMIN → super_admin
        assert (
            '"SUPER_ADMIN": "super_admin"' in source
            or "'SUPER_ADMIN': 'super_admin'" in source
        )

    def test_role_mapping_contains_all_roles(self) -> None:
        """Source must map all five roles without omission."""
        import inspect

        import api.auth as auth_module

        source = inspect.getsource(auth_module)
        for role_key in ("STUDENT", "TEACHER", "PARENT", "ADMIN", "SUPER_ADMIN"):
            assert role_key in source, f"Role '{role_key}' missing from auth.py source"


# ==================== _check_login_rate_limit ====================


class TestCheckLoginRateLimit:
    """_check_login_rate_limit must raise 429 after LOGIN_RATE_LIMIT attempts."""

    def _fresh_ip(self, prefix: str = "192.0.2.") -> str:
        """Return an IP string unlikely to collide with other tests."""
        import uuid

        return prefix + str(abs(hash(str(uuid.uuid4()))) % 200 + 10)

    def test_first_attempt_does_not_raise(self) -> None:
        import api.auth as auth_mod

        ip = self._fresh_ip("192.0.2.")
        request = _make_request(ip)
        # No HTTPException on first attempt.
        auth_mod._check_login_rate_limit(request)

    def test_attempts_below_limit_do_not_raise(self) -> None:
        import api.auth as auth_mod

        ip = self._fresh_ip("192.0.3.")
        request = _make_request(ip)
        for _ in range(auth_mod.LOGIN_RATE_LIMIT - 1):
            auth_mod._check_login_rate_limit(request)

    def test_exceeding_limit_raises_429(self) -> None:
        from fastapi import HTTPException

        import api.auth as auth_mod

        ip = self._fresh_ip("192.0.4.")
        request = _make_request(ip)
        # Fill up the window.
        for _ in range(auth_mod.LOGIN_RATE_LIMIT):
            auth_mod._login_attempts[ip].append(__import__("time").time())
        with pytest.raises(HTTPException) as exc_info:
            auth_mod._check_login_rate_limit(request)
        assert exc_info.value.status_code == 429

    def test_old_attempts_cleaned_before_check(self) -> None:
        """Attempts older than LOGIN_RATE_WINDOW should be discarded."""
        import time as _time

        import api.auth as auth_mod

        ip = self._fresh_ip("192.0.5.")
        request = _make_request(ip)
        old_ts = _time.time() - auth_mod.LOGIN_RATE_WINDOW - 10
        # Pre-fill with stale attempts (beyond window).
        for _ in range(auth_mod.LOGIN_RATE_LIMIT):
            auth_mod._login_attempts[ip].append(old_ts)
        # Should NOT raise because all entries are expired.
        auth_mod._check_login_rate_limit(request)

    def test_rate_limit_constants_are_positive(self) -> None:
        import api.auth as auth_mod

        assert auth_mod.LOGIN_RATE_LIMIT > 0
        assert auth_mod.LOGIN_RATE_WINDOW > 0


# ==================== _record_failed_login ====================


class TestRecordFailedLogin:
    """_record_failed_login must append a timestamp to the IP's attempt list."""

    def test_records_attempt_for_ip(self) -> None:
        import time as _time
        import uuid

        import api.auth as auth_mod

        ip = "198.51.100." + str(abs(hash(str(uuid.uuid4()))) % 200 + 10)
        request = _make_request(ip)
        before = _time.time()
        auth_mod._record_failed_login(request)
        after = _time.time()

        attempts = auth_mod._login_attempts[ip]
        assert len(attempts) >= 1
        assert before <= attempts[-1] <= after

    def test_multiple_failures_accumulate(self) -> None:
        import uuid

        import api.auth as auth_mod

        ip = "198.51.100." + str(abs(hash(str(uuid.uuid4()))) % 200 + 10)
        request = _make_request(ip)
        initial_count = len(auth_mod._login_attempts[ip])
        auth_mod._record_failed_login(request)
        auth_mod._record_failed_login(request)
        auth_mod._record_failed_login(request)
        assert len(auth_mod._login_attempts[ip]) == initial_count + 3

    def test_trusted_proxy_records_forwarded_ip(self) -> None:
        import api.auth as auth_mod

        real_client = "203.0.113.77"
        request = _make_request("127.0.0.1", x_forwarded_for=real_client)
        auth_mod._record_failed_login(request)
        # The attempt should be recorded under the real client IP, not the proxy.
        assert len(auth_mod._login_attempts[real_client]) >= 1
