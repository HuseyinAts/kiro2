"""
2FA Login Gate Tests.

Tests that the login flow correctly gates users with 2FA enabled,
requiring TOTP verification before issuing JWT cookies.
"""

import pytest

from api.auth import TwoFactorRequired, database_authenticate


class TestTwoFactorRequired:
    """Test TwoFactorRequired exception semantics."""

    def test_exception_carries_user_info(self):
        exc = TwoFactorRequired(user_id="u-123", email="test@example.com")
        assert exc.user_id == "u-123"
        assert exc.email == "test@example.com"
        assert "2FA" in str(exc)

    def test_exception_is_exception(self):
        exc = TwoFactorRequired(user_id="u-1", email="a@b.com")
        assert isinstance(exc, Exception)


class TestDatabaseAuthenticate2FAGate:
    """Test that database_authenticate raises TwoFactorRequired for 2FA users."""

    @pytest.mark.asyncio
    async def test_2fa_enabled_raises_twofactor_required(self, monkeypatch):
        """When is_2fa_enabled=True and secret_2fa set, should raise TwoFactorRequired."""
        from unittest.mock import AsyncMock, MagicMock, patch

        # Mock DB user with 2FA enabled
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_2fa_enabled = True
        mock_user.secret_2fa = "JBSWY3DPEHPK3PXP"
        mock_user.id = "user-2fa"
        mock_user.email = "twofa@test.com"
        mock_user.password_hash = "$2b$12$fake_hash"

        # Mock DB session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        # Mock password verification to pass
        mock_giris = MagicMock()
        mock_giris.email = "twofa@test.com"
        mock_giris.get_password.return_value = "ValidPass123!"

        with patch("api.auth.pwd_context") as mock_pwd:
            mock_pwd.verify.return_value = True

            with pytest.raises(TwoFactorRequired) as exc_info:
                await database_authenticate(mock_giris, mock_db)

            assert exc_info.value.user_id == "user-2fa"
            assert exc_info.value.email == "twofa@test.com"

    @pytest.mark.asyncio
    async def test_2fa_disabled_proceeds_normally(self, monkeypatch):
        """When is_2fa_enabled=False, should NOT raise TwoFactorRequired."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.is_2fa_enabled = False
        mock_user.secret_2fa = None
        mock_user.id = "user-normal"
        mock_user.email = "normal@test.com"
        mock_user.password_hash = "$2b$12$fake"
        mock_user.role = MagicMock()
        mock_user.role.value = "STUDENT"
        mock_user.username = "normal"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.phone = ""
        from datetime import UTC, datetime

        mock_user.created_at = datetime.now(UTC)
        mock_user.last_login = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        mock_db.bind = MagicMock(spec=[])  # No sync_engine
        mock_db.commit = AsyncMock()

        mock_giris = MagicMock()
        mock_giris.email = "normal@test.com"
        mock_giris.get_password.return_value = "ValidPass123!"

        with (
            patch("api.auth.pwd_context") as mock_pwd,
            patch("api.auth.get_jwt_manager") as mock_jwt_fn,
        ):
            mock_pwd.verify.return_value = True
            mock_jwt_mgr = MagicMock()
            mock_jwt_mgr.create_access_token.return_value = "access-token"
            mock_jwt_mgr.create_refresh_token.return_value = "refresh-token"
            mock_jwt_mgr.access_token_expire_minutes = 60
            mock_jwt_fn.return_value = mock_jwt_mgr

            result = await database_authenticate(mock_giris, mock_db)

            # Should succeed — no TwoFactorRequired
            assert result["success"] is True
            assert result["token"] == "access-token"
