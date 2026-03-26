"""Tests for bucket-based rate limiter in auth module."""

import time
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.auth import (
    RATE_LIMITS,
    _check_rate_limit,
    _get_client_ip,
    _rate_buckets,
    _record_attempt,
)


def _make_request(ip: str = "1.2.3.4", forwarded_for: str | None = None) -> MagicMock:
    """Create a mock Request with configurable IP."""
    req = MagicMock()
    req.client.host = ip
    req.headers = {}
    if forwarded_for:
        req.headers["x-forwarded-for"] = forwarded_for
    # Make .get work on the dict
    req.headers = {**({"x-forwarded-for": forwarded_for} if forwarded_for else {})}
    req.headers = MagicMock(wraps=req.headers)
    req.headers.get = lambda key, default=None: (
        forwarded_for if key == "x-forwarded-for" and forwarded_for else default
    )
    return req


@pytest.fixture(autouse=True)
def _clear_rate_buckets():
    """Reset rate limiter state between tests."""
    _rate_buckets.clear()
    yield
    _rate_buckets.clear()


class TestGetClientIp:
    def test_direct_connection(self):
        req = _make_request(ip="10.0.0.1")
        assert _get_client_ip(req) == "10.0.0.1"

    def test_trusted_proxy_uses_forwarded_for(self):
        req = _make_request(ip="127.0.0.1", forwarded_for="203.0.113.50")
        assert _get_client_ip(req) == "203.0.113.50"

    def test_untrusted_proxy_ignores_forwarded_for(self):
        req = _make_request(ip="10.0.0.99", forwarded_for="203.0.113.50")
        assert _get_client_ip(req) == "10.0.0.99"

    def test_forwarded_for_takes_first_ip(self):
        req = _make_request(ip="127.0.0.1", forwarded_for="1.1.1.1, 2.2.2.2, 3.3.3.3")
        assert _get_client_ip(req) == "1.1.1.1"

    def test_no_client_returns_unknown(self):
        req = MagicMock()
        req.client = None
        assert _get_client_ip(req) == "unknown"


class TestCheckRateLimit:
    def test_under_limit_passes(self):
        req = _make_request()
        # Should not raise for first attempt
        _check_rate_limit(req, "login")

    def test_at_limit_raises_429(self):
        req = _make_request(ip="5.5.5.5")
        max_attempts, _ = RATE_LIMITS["login"]

        # Fill up to the limit
        for _ in range(max_attempts):
            _record_attempt(req, "login")

        with pytest.raises(HTTPException) as exc_info:
            _check_rate_limit(req, "login")
        assert exc_info.value.status_code == 429
        assert "saniye" in exc_info.value.detail

    def test_different_ips_independent(self):
        req_a = _make_request(ip="1.1.1.1")
        req_b = _make_request(ip="2.2.2.2")
        max_attempts, _ = RATE_LIMITS["login"]

        # Fill IP A to the limit
        for _ in range(max_attempts):
            _record_attempt(req_a, "login")

        # IP A should be blocked
        with pytest.raises(HTTPException):
            _check_rate_limit(req_a, "login")

        # IP B should be fine
        _check_rate_limit(req_b, "login")

    def test_different_buckets_independent(self):
        req = _make_request(ip="3.3.3.3")
        max_attempts, _ = RATE_LIMITS["login"]

        # Fill login bucket
        for _ in range(max_attempts):
            _record_attempt(req, "login")

        # Login blocked
        with pytest.raises(HTTPException):
            _check_rate_limit(req, "login")

        # Register bucket should be fine
        _check_rate_limit(req, "register")

    def test_expired_attempts_cleaned(self):
        req = _make_request(ip="4.4.4.4")
        max_attempts, window = RATE_LIMITS["register"]

        # Insert old timestamps (expired)
        old_time = time.time() - window - 1
        _rate_buckets["register"]["4.4.4.4"] = [old_time] * max_attempts

        # Should pass because old attempts are expired
        _check_rate_limit(req, "register")

    def test_unknown_bucket_uses_defaults(self):
        req = _make_request(ip="6.6.6.6")
        # Unknown bucket should use default (10, 60)
        _check_rate_limit(req, "unknown_bucket")

    def test_register_bucket_config(self):
        assert RATE_LIMITS["register"] == (5, 60)

    def test_password_reset_bucket_config(self):
        assert RATE_LIMITS["password_reset"] == (5, 300)

    def test_2fa_verify_bucket_config(self):
        assert RATE_LIMITS["2fa_verify"] == (10, 60)


class TestRecordAttempt:
    def test_records_timestamp(self):
        req = _make_request(ip="7.7.7.7")
        before = time.time()
        _record_attempt(req, "login")
        after = time.time()

        timestamps = _rate_buckets["login"]["7.7.7.7"]
        assert len(timestamps) == 1
        assert before <= timestamps[0] <= after

    def test_accumulates_attempts(self):
        req = _make_request(ip="8.8.8.8")
        for _ in range(3):
            _record_attempt(req, "login")

        assert len(_rate_buckets["login"]["8.8.8.8"]) == 3
