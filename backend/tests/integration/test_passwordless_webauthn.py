"""
Passwordless/WebAuthn Integration Tests - KIRO2 Auth Enhancement

Task 6.2 gereksinimlerini karsilar.
"""

import base64
import json

import pytest

from core.passwordless_auth import (
    PasswordlessAuthEvent,
    PasswordlessAuthService,
    WebAuthnService,
)


@pytest.fixture
def passwordless_service() -> PasswordlessAuthService:
    """Test passwordless servisi."""
    return PasswordlessAuthService()


@pytest.fixture
def webauthn_service() -> WebAuthnService:
    """Test WebAuthn servisi."""
    return WebAuthnService(rp_id="localhost", rp_name="Test App")


class TestMagicLinkFlow:
    """Magic link akisi testleri (REQ-5.1, REQ-5.2)."""

    @pytest.mark.asyncio
    async def test_generate_magic_link_success(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Magic link basariyla olusturulmali."""
        result = await passwordless_service.generate_magic_link_token(
            email="test@example.com",
            ip_address="127.0.0.1",
        )

        assert result.success is True
        assert result.email == "test@example.com"
        assert result.token is not None
        assert len(result.token) > 20

    @pytest.mark.asyncio
    async def test_magic_link_15_minute_expiry(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Magic link 15 dakika gecerli olmali (REQ-5.1)."""
        assert passwordless_service.MAGIC_LINK_EXPIRE_MINUTES == 15

    @pytest.mark.asyncio
    async def test_verify_magic_link_token(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Gecerli token basariyla dogrulanmali."""
        # Token olustur
        gen_result = await passwordless_service.generate_magic_link_token(
            email="verify@example.com",
        )
        token = gen_result.token

        # Dogrula
        verify_result = await passwordless_service.verify_magic_link_token(token)

        assert verify_result.valid is True
        assert verify_result.email == "verify@example.com"

    @pytest.mark.asyncio
    async def test_magic_link_single_use(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Token tek kullanimlik olmali (REQ-5.2)."""
        # Token olustur
        gen_result = await passwordless_service.generate_magic_link_token(
            email="single@example.com",
        )
        token = gen_result.token

        # Ilk kullanim - basarili
        first_verify = await passwordless_service.verify_magic_link_token(token)
        assert first_verify.valid is True

        # Ikinci kullanim - basarisiz
        second_verify = await passwordless_service.verify_magic_link_token(token)
        assert second_verify.valid is False
        assert second_verify.error_code in ["TOKEN_ALREADY_USED", "INVALID_TOKEN"]

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Gecersiz email reddedilmeli."""
        result = await passwordless_service.generate_magic_link_token(
            email="invalid-email",
        )

        assert result.success is False
        assert result.error_code == "INVALID_EMAIL"


class TestWebAuthnRegistration:
    """WebAuthn kayit testleri (REQ-5.3, REQ-5.4)."""

    @pytest.mark.asyncio
    async def test_generate_registration_options(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Kayit secenekleri basariyla olusturulmali."""
        result = await webauthn_service.generate_registration_options(
            user_id=123,
            user_name="user@example.com",
            user_display_name="Test User",
        )

        assert result.success is True
        options = result.data

        assert options.challenge is not None
        assert len(options.challenge) > 20
        assert options.rp_id == "localhost"
        assert options.user_name == "user@example.com"
        assert len(options.pub_key_cred_params) > 0

    @pytest.mark.asyncio
    async def test_verify_registration_response(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Kayit yaniti basariyla dogrulanmali."""
        # Kayit secenekleri olustur
        options_result = await webauthn_service.generate_registration_options(
            user_id=456,
            user_name="register@example.com",
        )
        challenge = options_result.data.challenge

        # Client data olustur (simulated)
        client_data = {
            "type": "webauthn.create",
            "challenge": challenge,
            "origin": "https://localhost",
        }
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        # Kayit yanitini dogrula
        result = await webauthn_service.verify_registration_response(
            credential_id="test_credential_123",
            client_data_json=client_data_json,
            attestation_object="test_attestation",
            expected_challenge=challenge,
            device_name="Test Device",
        )

        assert result.success is True
        assert result.data.user_id == 456
        assert result.data.device_name == "Test Device"


class TestWebAuthnAuthentication:
    """WebAuthn dogrulama testleri (REQ-5.5)."""

    @pytest.mark.asyncio
    async def test_generate_authentication_options(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Dogrulama secenekleri olusturulmali."""
        result = await webauthn_service.generate_authentication_options()

        assert result.success is True
        options = result.data

        assert options.challenge is not None
        assert options.rp_id == "localhost"

    @pytest.mark.asyncio
    async def test_full_webauthn_flow(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Tam WebAuthn akisi (kayit + dogrulama)."""
        # 1. Kayit
        reg_options = await webauthn_service.generate_registration_options(
            user_id=789,
            user_name="flow@example.com",
        )
        reg_challenge = reg_options.data.challenge

        client_data = {
            "type": "webauthn.create",
            "challenge": reg_challenge,
            "origin": "https://localhost",
        }
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        reg_result = await webauthn_service.verify_registration_response(
            credential_id="flow_credential",
            client_data_json=client_data_json,
            attestation_object="test_attestation",
            expected_challenge=reg_challenge,
        )
        assert reg_result.success is True

        # 2. Dogrulama
        auth_options = await webauthn_service.generate_authentication_options(
            user_id=789,
        )
        auth_challenge = auth_options.data.challenge

        auth_client_data = {
            "type": "webauthn.get",
            "challenge": auth_challenge,
            "origin": "https://localhost",
        }
        auth_client_data_json = base64.urlsafe_b64encode(
            json.dumps(auth_client_data).encode()
        ).decode().rstrip("=")

        auth_result = await webauthn_service.verify_authentication_response(
            credential_id="flow_credential",
            client_data_json=auth_client_data_json,
            authenticator_data="test_auth_data",
            signature="test_signature",
            expected_challenge=auth_challenge,
        )

        assert auth_result.success is True
        assert auth_result.data["user_id"] == 789


class TestFallbackMechanism:
    """Fallback mekanizmasi testleri (REQ-5.6)."""

    def test_fallback_supported(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Fallback desteklenmeli."""
        assert passwordless_service.supports_fallback_to_password() is True

    @pytest.mark.asyncio
    async def test_log_fallback_event(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Fallback eventi loglanmali."""
        await passwordless_service.log_fallback_to_password(
            email="fallback@example.com",
            ip_address="127.0.0.1",
            reason="user_preference",
        )

        logs = passwordless_service.get_recent_audit_logs(
            email="fallback@example.com",
            event_type=PasswordlessAuthEvent.FALLBACK_TO_PASSWORD,
        )

        assert len(logs) > 0


class TestCredentialManagement:
    """Credential yonetimi testleri."""

    @pytest.mark.asyncio
    async def test_get_user_credentials(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Kullanici credential'lari listelenebilmeli."""
        # Credential kaydet
        reg_options = await webauthn_service.generate_registration_options(
            user_id=100,
            user_name="list@example.com",
        )
        challenge = reg_options.data.challenge

        client_data = {
            "type": "webauthn.create",
            "challenge": challenge,
            "origin": "https://localhost",
        }
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        await webauthn_service.verify_registration_response(
            credential_id="list_credential",
            client_data_json=client_data_json,
            attestation_object="test",
            expected_challenge=challenge,
        )

        # Listele
        credentials = await webauthn_service.get_user_credentials(user_id=100)

        assert len(credentials) >= 1

    @pytest.mark.asyncio
    async def test_revoke_credential(
        self,
        webauthn_service: WebAuthnService,
    ) -> None:
        """Credential iptal edilebilmeli."""
        # Kaydet
        reg_options = await webauthn_service.generate_registration_options(
            user_id=200,
            user_name="revoke@example.com",
        )
        challenge = reg_options.data.challenge

        client_data = {
            "type": "webauthn.create",
            "challenge": challenge,
            "origin": "https://localhost",
        }
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        await webauthn_service.verify_registration_response(
            credential_id="revoke_credential",
            client_data_json=client_data_json,
            attestation_object="test",
            expected_challenge=challenge,
        )

        # Iptal et
        result = await webauthn_service.revoke_credential(
            credential_id="revoke_credential",
            user_id=200,
        )

        assert result.success is True


class TestRateLimiting:
    """Rate limiting testleri."""

    @pytest.mark.asyncio
    async def test_rate_limiting_on_multiple_requests(
        self,
        passwordless_service: PasswordlessAuthService,
    ) -> None:
        """Cok fazla istek rate limit'e takilmali."""
        email = "ratelimit@example.com"

        # Maksimum deneme sayisi kadar istek yap
        for i in range(passwordless_service.MAX_MAGIC_LINK_ATTEMPTS + 1):
            result = await passwordless_service.generate_magic_link_token(
                email=email,
            )

        # Son istek rate limited olmali
        assert result.success is False
        assert result.error_code == "RATE_LIMITED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
