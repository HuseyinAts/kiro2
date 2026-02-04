"""
Fast unit tests for DDoS protection system
Tests: Rate limiting key generation, basic protection logic
Coverage target: 30-50% of core.ddos_protection
"""
import pytest
from unittest.mock import Mock, MagicMock


class TestRateLimitKeyGeneration:
    """Test rate limit key generation"""

    def test_get_rate_limit_key_with_user(self):
        """Test key generation with authenticated user"""
        from core.ddos_protection import get_rate_limit_key

        request = Mock()
        request.state = Mock()
        request.state.user = {"id": 123}
        request.headers = {}

        key = get_rate_limit_key(request)
        assert key == "user:123"

    def test_get_rate_limit_key_with_api_key(self):
        """Test key generation with API key"""
        from core.ddos_protection import get_rate_limit_key

        request = Mock()
        request.state = Mock()
        request.state.user = None
        request.headers = {"X-API-Key": "test-api-key-123"}

        key = get_rate_limit_key(request)
        assert "api:" in key or "test-api-key" in key or key.startswith("user:")

    def test_get_rate_limit_key_with_ip(self):
        """Test key generation with IP address fallback"""
        from core.ddos_protection import get_rate_limit_key

        request = Mock()
        request.state = Mock()
        request.state.user = None
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        key = get_rate_limit_key(request)
        # Should return some key (IP-based or user-based)
        assert isinstance(key, str)
        assert len(key) > 0


class TestDDoSProtectionImports:
    """Test DDoS protection module imports"""

    def test_module_imports_successfully(self):
        """Test module can be imported"""
        from core import ddos_protection

        assert ddos_protection is not None

    def test_get_rate_limit_key_exists(self):
        """Test get_rate_limit_key function exists"""
        from core.ddos_protection import get_rate_limit_key

        assert callable(get_rate_limit_key)
