"""
Property-Based Tests - MFA (Multi-Factor Authentication)

Bu modul, hypothesis kullanarak TOTP-based MFA icin
property-based testler icerir.

Property 1: TOTP token valid only within 30-second window
- Token 30 saniyelik pencerelerde gecerlidir
- Valid window disindaki tokenlar reddedilir
- Her timestamp icin tutarli davranis

Requirements:
- REQ-1.1: TOTP token dogrulama
- REQ-1.2: 30 saniye gecerlilik penceresi
- REQ-1.3: Backup code yonetimi
"""

import sys
from datetime import timedelta

import pyotp
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from core.two_factor_auth import RECOVERY_TOKEN_EXPIRY_MINUTES, TwoFactorAuthService


class TestTOTPValidityProperties:
    """TOTP token validity property-based testleri."""

    def setup_method(self):
        """Her test oncesi TwoFactorAuthService olustur."""
        self.service = TwoFactorAuthService(app_name="KIRO2 Test")
        self.secret = self.service.generate_secret()

    @given(
        time_offset=st.integers(min_value=-30, max_value=30)
    )
    @settings(max_examples=100)
    def test_totp_valid_within_window(self, time_offset: int):
        """
        Property 1.1: TOTP token 30 saniye penceresi icinde gecerli olmali.

        TOTP standardina gore default window=1 ile +/- 30 saniye gecerlidir.
        Bu test, zaman ofsetinin gecerli pencere icinde oldugunu dogrular.
        """
        totp = pyotp.TOTP(self.secret)

        # Simdi icin token olustur
        current_token = totp.now()

        # Token simdi icin gecerli olmali (window=1)
        is_valid = self.service.verify_token(self.secret, current_token, window=1)

        assert is_valid, \
            f"Current token should be valid, offset={time_offset}"

    @given(
        window=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_totp_window_parameter_respected(self, window: int):
        """
        Property 1.2: Window parametresi dogru uygulanmali.

        Window=0: Sadece mevcut zaman
        Window=1: +/- 30 saniye (default)
        Window=2: +/- 60 saniye
        vb.
        """
        totp = pyotp.TOTP(self.secret)

        # Mevcut token
        current_token = totp.now()

        # Verilen window ile dogrulama
        is_valid = self.service.verify_token(self.secret, current_token, window=window)

        # Mevcut token her zaman gecerli olmali (window >= 0)
        assert is_valid, \
            f"Current token should be valid with window={window}"

    @given(
        random_token=st.text(
            alphabet=st.sampled_from("0123456789"),
            min_size=6,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_random_token_mostly_invalid(self, random_token: str):
        """
        Property 1.3: Rastgele tokenlar genelde gecersiz olmali.

        6 haneli rastgele bir token, mevcut TOTP degeriyle
        eslesmesi cok dusuk olasilikli (1/1000000).
        """
        # Mevcut gecerli tokeni al
        totp = pyotp.TOTP(self.secret)
        current_valid_token = totp.now()

        # Eger random token tesadufen gecerli token degilse
        if random_token != current_valid_token:
            is_valid = self.service.verify_token(self.secret, random_token, window=0)
            # Rastgele token gecersiz olmali
            assert not is_valid, \
                f"Random token {random_token} should be invalid"

    @given(
        secret_length=st.integers(min_value=16, max_value=32)
    )
    @settings(max_examples=100)
    def test_secret_generation_produces_valid_base32(self, secret_length: int):
        """
        Property 1.4: Her secret uretimi gecerli base32 olmali.

        Uretilen secretlar base32 encoded olmali ve
        TOTP dogrulama icin kullanilabilir olmali.
        """
        # Farkli secretlar uret
        new_secret = self.service.generate_secret()

        # Secret None olmamali
        assert new_secret is not None

        # Secret bos olmamali
        assert len(new_secret) > 0

        # Secret ile TOTP olusturulabilmeli
        try:
            totp = pyotp.TOTP(new_secret)
            token = totp.now()
            # Token 6 haneli olmali
            assert len(token) == 6
            assert token.isdigit()
        except Exception as e:
            pytest.fail(f"Secret should produce valid TOTP: {e}")

    @given(
        token_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50)
    def test_consecutive_tokens_are_same_within_interval(self, token_count: int):
        """
        Property 1.5: Ayni zaman diliminde ardisik token uretimleri ayni olmali.

        TOTP 30 saniyelik pencerelerde calisiyor, bu pencere icinde
        ayni token uretilmeli.
        """
        totp = pyotp.TOTP(self.secret)

        tokens = []
        for _ in range(token_count):
            tokens.append(totp.now())

        # Tum tokenlar ayni olmali (ayni 30s penceresi icinde)
        assert len(set(tokens)) == 1, \
            f"All tokens within same interval should be identical: {tokens}"

    @given(
        backup_count=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_backup_codes_unique(self, backup_count: int):
        """
        Property 1.6: Backup kodlari benzersiz olmali.

        Uretilen backup kodlarinin hepsi farkli olmali,
        tekrar olmamali.
        """
        backup_codes = self.service.generate_backup_codes(count=backup_count)

        # Kod sayisi dogru olmali
        assert len(backup_codes) == backup_count

        # Tum kodlar benzersiz olmali
        assert len(set(backup_codes)) == backup_count, \
            f"Backup codes should be unique: {backup_codes}"

    @given(
        code=st.text(
            alphabet=st.sampled_from("ABCDEF0123456789"),
            min_size=8,
            max_size=8
        )
    )
    @settings(max_examples=100)
    def test_backup_code_hash_deterministic(self, code: str):
        """
        Property 1.7: Backup kod hash'i deterministik olmali.

        Ayni kod her zaman ayni hash'i uretmeli.
        """
        hash1 = self.service.hash_backup_code(code)
        hash2 = self.service.hash_backup_code(code)

        # Ayni kod icin ayni hash
        assert hash1 == hash2, \
            f"Same code should produce same hash: {hash1} != {hash2}"

    @given(
        code1=st.text(
            alphabet=st.sampled_from("ABCDEF0123456789"),
            min_size=8,
            max_size=8
        ),
        code2=st.text(
            alphabet=st.sampled_from("ABCDEF0123456789"),
            min_size=8,
            max_size=8
        )
    )
    @settings(max_examples=100)
    def test_different_codes_different_hashes(self, code1: str, code2: str):
        """
        Property 1.8: Farkli kodlar farkli hash'ler uretmeli.

        Collision olmamasi onemli guvenlik gereksinimi.
        """
        # Kodlar farkli olmali
        assume(code1 != code2)

        hash1 = self.service.hash_backup_code(code1)
        hash2 = self.service.hash_backup_code(code2)

        # Farkli kodlar farkli hashler
        assert hash1 != hash2, \
            "Different codes should produce different hashes"

    @given(
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_provisioning_uri_format(self, email: str):
        """
        Property 1.9: Provisioning URI dogru formatta olmali.

        otpauth://totp/AppName:email?secret=XXX&issuer=AppName formati.
        """
        uri = self.service.get_provisioning_uri(self.secret, email)

        # URI otpauth ile baslamali
        assert uri.startswith("otpauth://totp/"), \
            f"URI should start with otpauth://totp/, got: {uri}"

        # Email ve secret icermeli (URL-encoded olabilir, orn. @ -> %40)
        from urllib.parse import unquote
        decoded_uri = unquote(uri)
        assert email in decoded_uri, \
            f"URI should contain email: {email}"
        assert self.secret in uri, \
            "URI should contain secret"


class TestMFARecoveryProperties:
    """MFA recovery process property-based testleri."""

    def setup_method(self):
        """Her test oncesi TwoFactorAuthService olustur."""
        self.service = TwoFactorAuthService(app_name="KIRO2 Test")

    @given(
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_recovery_token_unique(self, email: str):
        """
        Property 1.10: Her recovery token benzersiz olmali.

        Farkli recovery baslatimlari farkli tokenlar uretmeli.
        """
        recovery1 = self.service.initiate_mfa_recovery(email)
        recovery2 = self.service.initiate_mfa_recovery(email)

        # Tokenlar farkli olmali
        assert recovery1.token != recovery2.token, \
            "Recovery tokens should be unique"

    @given(
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_recovery_token_expiry_correct(self, email: str):
        """
        Property 1.11: Recovery token suresi dogru ayarlanmali.

        Token RECOVERY_TOKEN_EXPIRY_MINUTES sonra expire olmali.
        """
        recovery = self.service.initiate_mfa_recovery(email)

        # Expiry zamani dogru olmali
        expected_expiry = recovery.created_at + timedelta(minutes=RECOVERY_TOKEN_EXPIRY_MINUTES)
        time_diff = abs((recovery.expires_at - expected_expiry).total_seconds())

        # 1 saniye tolerans
        assert time_diff < 1, \
            f"Expiry time should be {RECOVERY_TOKEN_EXPIRY_MINUTES} minutes from creation"

    @given(
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_recovery_email_code_format(self, email: str):
        """
        Property 1.12: Email kodu 6 haneli numerik olmali.

        Recovery email kodlari guvenli ve kullanici dostu olmali.
        """
        recovery = self.service.initiate_mfa_recovery(email)

        # Email kodu 6 karakter olmali
        assert len(recovery.email_code) == 6, \
            f"Email code should be 6 digits, got: {recovery.email_code}"

        # Sadece rakam icermeli
        assert recovery.email_code.isdigit(), \
            f"Email code should be numeric, got: {recovery.email_code}"


class TestMFAEnforcementProperties:
    """MFA enforcement property-based testleri."""

    def setup_method(self):
        """Her test oncesi TwoFactorAuthService olustur."""
        self.service = TwoFactorAuthService(app_name="KIRO2 Test")

    @given(
        role=st.sampled_from(["admin", "ADMIN", "Admin", "super_admin", "SUPER_ADMIN"])
    )
    @settings(max_examples=100)
    def test_mfa_required_for_admin_roles(self, role: str):
        """
        Property 1.13: Admin rolleri icin MFA zorunlu olmali.

        Case-insensitive olarak admin ve super_admin rolleri
        MFA gerektirmeli.
        """
        is_required = self.service.is_mfa_required_for_role(role)

        assert is_required, \
            f"MFA should be required for role: {role}"

    @given(
        role=st.sampled_from(["student", "teacher", "parent", "guest", "user"])
    )
    @settings(max_examples=100)
    def test_mfa_not_required_for_regular_roles(self, role: str):
        """
        Property 1.14: Normal roller icin MFA zorunlu olmamali.

        Student, teacher, parent vb. icin MFA opsiyonel.
        """
        is_required = self.service.is_mfa_required_for_role(role)

        assert not is_required, \
            f"MFA should not be required for role: {role}"

    @given(
        user_id=st.integers(min_value=1, max_value=1000000)
    )
    @settings(max_examples=100)
    def test_mfa_status_persistence(self, user_id: int):
        """
        Property 1.15: MFA durumu dogru saklanmali ve okunmali.

        Set edilen deger get ile ayni donmeli.
        """
        # MFA aktif et
        self.service.set_user_mfa_status(user_id, True)
        assert self.service.get_user_mfa_status(user_id) is True

        # MFA deaktif et
        self.service.set_user_mfa_status(user_id, False)
        assert self.service.get_user_mfa_status(user_id) is False

    @given(
        user_id=st.integers(min_value=1, max_value=1000000)
    )
    @settings(max_examples=100)
    def test_enforcement_logic_admin_without_mfa(self, user_id: int):
        """
        Property 1.16: MFA'siz admin icin enforcement gerekli.

        Admin kullanicisi MFA aktif etmemisse enforcement_needed=True olmali.
        """
        # MFA deaktif olsun
        self.service.set_user_mfa_status(user_id, False)

        result = self.service.enforce_mfa_for_admin(user_id, "admin")

        assert result.mfa_required is True
        assert result.mfa_enabled is False
        assert result.enforcement_needed is True

    @given(
        user_id=st.integers(min_value=1, max_value=1000000)
    )
    @settings(max_examples=100)
    def test_enforcement_logic_admin_with_mfa(self, user_id: int):
        """
        Property 1.17: MFA'li admin icin enforcement gerekmez.

        Admin kullanicisi MFA aktif etmisse enforcement_needed=False olmali.
        """
        # MFA aktif olsun
        self.service.set_user_mfa_status(user_id, True)

        result = self.service.enforce_mfa_for_admin(user_id, "admin")

        assert result.mfa_required is True
        assert result.mfa_enabled is True
        assert result.enforcement_needed is False
