"""
Biometric Authentication Unit Tests - KIRO2 Auth Enhancement

Task 5.2 gereksinimlerini karsilar.
"""

from datetime import UTC, datetime

import pytest

from core.biometric_auth_service import (
    BiometricAuthService,
    BiometricError,
    BiometricStrength,
    BiometricType,
    ChallengeResponse,
    DeviceInfo,
    DevicePlatform,
)


@pytest.fixture
def biometric_service() -> BiometricAuthService:
    """Test biometric servisi."""
    return BiometricAuthService()


@pytest.fixture
def ios_device_info() -> DeviceInfo:
    """iOS cihaz bilgisi."""
    return DeviceInfo(
        device_id="ios_test_device",
        platform=DevicePlatform.IOS,
        platform_version="17.0",
        model="iPhone 15",
        manufacturer="Apple",
        biometric_types=[BiometricType.FACE],
        is_biometric_enrolled=True,
        security_level=BiometricStrength.STRONG,
    )


@pytest.fixture
def android_device_info() -> DeviceInfo:
    """Android cihaz bilgisi."""
    return DeviceInfo(
        device_id="android_test_device",
        platform=DevicePlatform.ANDROID,
        platform_version="14",
        model="Pixel 8",
        manufacturer="Google",
        biometric_types=[BiometricType.FINGERPRINT],
        is_biometric_enrolled=True,
        security_level=BiometricStrength.STRONG,
    )


class TestDeviceCapabilityCheck:
    """Device capability check testleri (REQ-4.1)."""

    @pytest.mark.asyncio
    async def test_ios_device_face_id_supported(
        self,
        biometric_service: BiometricAuthService,
        ios_device_info: DeviceInfo,
    ) -> None:
        """iOS cihazda Face ID desteklenmeli."""
        capability = await biometric_service.check_device_capability(ios_device_info)

        assert capability.is_supported is True
        assert capability.is_enrolled is True
        assert BiometricType.FACE in capability.available_types
        assert capability.recommended_type == BiometricType.FACE
        assert capability.security_level == BiometricStrength.STRONG

    @pytest.mark.asyncio
    async def test_android_device_fingerprint_supported(
        self,
        biometric_service: BiometricAuthService,
        android_device_info: DeviceInfo,
    ) -> None:
        """Android cihazda parmak izi desteklenmeli."""
        capability = await biometric_service.check_device_capability(android_device_info)

        assert capability.is_supported is True
        assert BiometricType.FINGERPRINT in capability.available_types

    @pytest.mark.asyncio
    async def test_device_without_biometric_enrollment(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Biyometrik kayitli olmayan cihaz tespiti."""
        device = DeviceInfo(
            device_id="test_device",
            platform=DevicePlatform.IOS,
            platform_version="17.0",
            is_biometric_enrolled=False,
        )

        capability = await biometric_service.check_device_capability(device)

        assert capability.is_supported is True
        assert capability.is_enrolled is False
        assert capability.error == BiometricError.BIOMETRIC_NOT_ENROLLED

    @pytest.mark.asyncio
    async def test_fallback_always_available(
        self,
        biometric_service: BiometricAuthService,
        ios_device_info: DeviceInfo,
    ) -> None:
        """Fallback her zaman mevcut olmali (REQ-4.4)."""
        capability = await biometric_service.check_device_capability(ios_device_info)

        assert capability.can_fallback is True


class TestChallengeGeneration:
    """Challenge generation testleri (REQ-4.5)."""

    @pytest.mark.asyncio
    async def test_generate_challenge_success(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Challenge basariyla olusturulmali."""
        result = await biometric_service.generate_challenge(user_id=123)

        assert result.success is True
        assert result.data is not None

        challenge = result.data
        assert challenge.id.startswith("bio_")
        assert challenge.user_id == 123
        assert len(challenge.challenge_bytes) > 20
        assert challenge.expires_at > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_challenge_unique_ids(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Her challenge benzersiz ID'ye sahip olmali."""
        result1 = await biometric_service.generate_challenge(user_id=1)
        result2 = await biometric_service.generate_challenge(user_id=1)

        assert result1.data.id != result2.data.id
        assert result1.data.challenge_bytes != result2.data.challenge_bytes

    @pytest.mark.asyncio
    async def test_challenge_with_device_id(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Challenge device ID ile olusturulabilmeli."""
        result = await biometric_service.generate_challenge(
            user_id=123,
            device_id="device_abc",
            biometric_type=BiometricType.FINGERPRINT,
        )

        assert result.success is True
        assert result.data.device_id == "device_abc"
        assert result.data.biometric_type == BiometricType.FINGERPRINT


class TestChallengeVerification:
    """Challenge response verification testleri (REQ-4.5, REQ-4.6)."""

    @pytest.mark.asyncio
    async def test_verify_invalid_challenge_id(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Gecersiz challenge ID hata dondurmeli."""
        response = ChallengeResponse(
            challenge_id="invalid_challenge",
            signature="test_sig",
            client_data="{}",
            authenticator_data="test_data",
            biometric_type=BiometricType.FINGERPRINT,
            liveness_check_passed=True,
        )

        result = await biometric_service.verify_challenge_response(response)

        assert result.success is False
        assert result.error == BiometricError.CHALLENGE_INVALID

    @pytest.mark.asyncio
    async def test_verify_liveness_check_required(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Liveness check basarisizsa dogrulama basarisiz olmali (REQ-4.6)."""
        # Once challenge olustur
        gen_result = await biometric_service.generate_challenge(user_id=123)
        challenge = gen_result.data

        # Liveness check basarisiz response
        response = ChallengeResponse(
            challenge_id=challenge.id,
            signature="test_sig",
            client_data="{}",
            authenticator_data="test_data",
            biometric_type=BiometricType.FINGERPRINT,
            liveness_check_passed=False,  # Basarisiz
        )

        result = await biometric_service.verify_challenge_response(response)

        assert result.success is False
        assert result.error == BiometricError.LIVENESS_CHECK_FAILED

    @pytest.mark.asyncio
    async def test_verify_valid_response(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Gecerli response basariyla dogrulanmali."""
        # Challenge olustur
        gen_result = await biometric_service.generate_challenge(user_id=456)
        challenge = gen_result.data

        # Gecerli response
        response = ChallengeResponse(
            challenge_id=challenge.id,
            signature="valid_signature",
            client_data="{}",
            authenticator_data="valid_data",
            biometric_type=BiometricType.FINGERPRINT,
            liveness_check_passed=True,
        )

        result = await biometric_service.verify_challenge_response(response)

        assert result.success is True
        assert result.data["user_id"] == 456


class TestCredentialManagement:
    """Credential yonetimi testleri (REQ-4.2, REQ-4.3)."""

    @pytest.mark.asyncio
    async def test_register_credential(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Credential basariyla kaydedilmeli."""
        result = await biometric_service.register_credential(
            user_id=123,
            device_id="device_abc",
            public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            biometric_type=BiometricType.FACE,
        )

        assert result.success is True
        assert result.data.user_id == 123
        assert result.data.device_id == "device_abc"

    @pytest.mark.asyncio
    async def test_revoke_credential(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Credential basariyla iptal edilmeli."""
        # Kaydet
        await biometric_service.register_credential(
            user_id=123,
            device_id="device_xyz",
            public_key="test_key",
            biometric_type=BiometricType.FINGERPRINT,
        )

        # Iptal et
        result = await biometric_service.revoke_credential(
            user_id=123,
            device_id="device_xyz",
        )

        assert result.success is True
        assert result.data["revoked"] is True

    @pytest.mark.asyncio
    async def test_get_user_credentials(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Kullanici credential'lari listelenebilmeli."""
        # Birden fazla credential kaydet
        await biometric_service.register_credential(
            user_id=100,
            device_id="device_1",
            public_key="key1",
            biometric_type=BiometricType.FACE,
        )
        await biometric_service.register_credential(
            user_id=100,
            device_id="device_2",
            public_key="key2",
            biometric_type=BiometricType.FINGERPRINT,
        )

        credentials = await biometric_service.get_user_credentials(user_id=100)

        assert len(credentials) == 2


class TestFallbackMechanism:
    """Fallback mekanizmasi testleri (REQ-4.4)."""

    @pytest.mark.asyncio
    async def test_fallback_token_generation(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Fallback token olusturulabilmeli."""
        result = await biometric_service.fallback_to_password(
            user_id=123,
            reason="biometric_not_available",
        )

        assert result.success is True
        assert result.data.user_id == 123
        assert len(result.data.token) > 20
        assert result.data.reason == "biometric_not_available"


class TestRateLimiting:
    """Rate limiting testleri."""

    @pytest.mark.asyncio
    async def test_rate_limiting_after_failed_attempts(
        self,
        biometric_service: BiometricAuthService,
    ) -> None:
        """Cok fazla basarisiz denemede rate limiting uygulanmali."""
        # Basarisiz denemeler kaydet
        for _ in range(6):
            await biometric_service._record_failed_attempt(user_id=999)

        # Rate limit kontrolu
        is_limited = await biometric_service._is_rate_limited(user_id=999)

        assert is_limited is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
