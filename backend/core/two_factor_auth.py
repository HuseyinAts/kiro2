"""
Two-Factor Authentication (2FA) Service
PHASE 2 Sprint 4: Security Hardening

Implements TOTP-based 2FA with:
- Secret key generation
- QR code generation for authenticator apps
- TOTP validation
- Backup codes generation and validation
- MFA recovery with email verification (REQ-1.5)
- Admin MFA enforcement (REQ-1.6)
"""
import base64
import hashlib
import io
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pyotp
import qrcode

from core.structured_logger import get_logger

logger = get_logger(__name__)


# ==================== DATA CLASSES ====================


@dataclass
class RecoveryToken:
    """
    MFA kurtarma token'i.

    MFA'yi kaybeden kullanicilar icin email dogrulama ile
    kurtarma islemi baslatir. REQ-1.5 uyumlu.

    Attributes:
        token: Benzersiz kurtarma token'i
        user_email: Kullanici email adresi
        email_code: Email ile gonderilen dogrulama kodu
        created_at: Olusturulma zamani
        expires_at: Son gecerlilik zamani
        verified: Email dogrulandi mi?
        used: Kullanildi mi?
    """
    token: str
    user_email: str
    email_code: str
    created_at: datetime
    expires_at: datetime
    verified: bool = False
    used: bool = False


@dataclass
class EnforcementResult:
    """
    MFA zorunluluk kontrol sonucu.

    Admin kullanicilari icin MFA zorunluluk durumunu raporlar.
    REQ-1.6 uyumlu.

    Attributes:
        mfa_required: MFA zorunlu mu?
        mfa_enabled: MFA aktif mi?
        enforcement_needed: Zorunluluk uygulanmali mi?
        role: Kullanici rolu
        message: Aciklama mesaji
    """
    mfa_required: bool
    mfa_enabled: bool
    enforcement_needed: bool
    role: str
    message: str


# ==================== CONSTANTS ====================


# MFA zorunlu roller (REQ-1.6)
MFA_REQUIRED_ROLES: set[str] = {"admin", "super_admin"}

# Recovery token suresi (REQ-1.5: 15 dakika)
RECOVERY_TOKEN_EXPIRY_MINUTES: int = 15


class TwoFactorAuthService:
    """
    Two-Factor Authentication service using TOTP.

    Ozellikler:
    - TOTP token uretimi ve dogrulama
    - QR kod olusturma
    - Backup kod yonetimi
    - MFA kurtarma (REQ-1.5)
    - Admin zorunlulugu (REQ-1.6)
    """

    def __init__(self, app_name: str = "Kiro2 Egitim"):
        """
        2FA servisini baslatir.

        Args:
            app_name: Authenticator uygulamasinda gorunecek uygulama adi
        """
        self.app_name = app_name
        # Recovery token deposu (production'da Redis kullanilmali)
        self._recovery_tokens: dict[str, RecoveryToken] = {}
        # Kullanici MFA durumu deposu (production'da veritabaninda saklanmali)
        self._user_mfa_status: dict[int, bool] = {}

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key
        
        Returns:
            Base32 encoded secret key
            
        Example:
            "JBSWY3DPEHPK3PXP"
        """
        secret = pyotp.random_base32()
        logger.info("2fa_secret_generated")
        return secret

    def get_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        issuer: str | None = None
    ) -> str:
        """
        Generate provisioning URI for authenticator apps
        
        Args:
            secret: TOTP secret key
            user_email: User's email address
            issuer: Optional issuer name
            
        Returns:
            otpauth:// URI for QR code
            
        Example:
            "otpauth://totp/Kiro2:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Kiro2"
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer or self.app_name
        )
        logger.info("2fa_provisioning_uri_generated", email=user_email)
        return uri

    def generate_qr_code(
        self,
        secret: str,
        user_email: str,
        issuer: str | None = None
    ) -> str:
        """
        Generate QR code image as base64 string
        
        Args:
            secret: TOTP secret key
            user_email: User's email
            issuer: Optional issuer name
            
        Returns:
            Base64 encoded PNG image
            
        Usage:
            <img src="data:image/png;base64,{qr_code}" />
        """
        # Get provisioning URI
        uri = self.get_provisioning_uri(secret, user_email, issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        logger.info("2fa_qr_code_generated", email=user_email)
        return qr_base64

    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token
        
        Args:
            secret: User's TOTP secret key
            token: 6-digit token from authenticator app
            window: Time window (±30 seconds per window)
            
        Returns:
            True if token is valid
            
        Window explanation:
            - window=0: Only current time
            - window=1: ±30 seconds (recommended)
            - window=2: ±60 seconds
        """
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=window)

            if is_valid:
                logger.info("2fa_token_verified_success")
            else:
                logger.warning("2fa_token_verification_failed")

            return is_valid

        except Exception as e:
            logger.error("2fa_token_verification_error", error=str(e))
            return False

    def get_current_token(self, secret: str) -> str:
        """
        Get current TOTP token (for testing)
        
        Args:
            secret: TOTP secret key
            
        Returns:
            Current 6-digit token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """
        Generate backup recovery codes
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of 8-character alphanumeric codes
            
        Example:
            ["A1B2C3D4", "E5F6G7H8", ...]
        """
        backup_codes = []
        for _ in range(count):
            # Generate 8-character code
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)

        logger.info("2fa_backup_codes_generated", count=count)
        return backup_codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash backup code for secure storage
        
        Args:
            code: Plain backup code
            
        Returns:
            SHA-256 hashed code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    def verify_backup_code(
        self,
        code: str,
        hashed_codes: list[str]
    ) -> tuple[bool, str | None]:
        """
        Verify backup code against hashed codes

        Args:
            code: Plain backup code entered by user
            hashed_codes: List of hashed backup codes

        Returns:
            (is_valid, matched_hash)

        Note: Backup codes are single-use. Remove matched hash after use.
        """
        code_hash = self.hash_backup_code(code)

        if code_hash in hashed_codes:
            logger.info("2fa_backup_code_verified")
            return True, code_hash
        logger.warning("2fa_backup_code_invalid")
        return False, None

    # ==================== MFA RECOVERY (REQ-1.5) ====================

    def _generate_email_code(self) -> str:
        """
        Email dogrulama kodu olusturur.

        Returns:
            6 haneli numerik kod
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    def initiate_mfa_recovery(self, user_email: str) -> RecoveryToken:
        """
        MFA kurtarma islemini baslatir.

        Kullaniciya email ile dogrulama kodu gonderilmesi icin
        kurtarma token'i olusturur. Token 15 dakika gecerlidir (REQ-1.5).

        Args:
            user_email: Kullanicinin kayitli email adresi

        Returns:
            RecoveryToken: Kurtarma token bilgileri

        Example:
            >>> recovery = two_factor_auth.initiate_mfa_recovery("user@example.com")
            >>> # Email ile recovery.email_code gonder
            >>> print(f"Token: {recovery.token}")

        Note:
            email_code degeri kullaniciya email ile gonderilmeli,
            asla client'a dogrudan verilmemelidir.
        """
        now = datetime.now(UTC)

        # Benzersiz token olustur
        token = secrets.token_urlsafe(32)

        # Email dogrulama kodu olustur
        email_code = self._generate_email_code()

        # Recovery token olustur
        recovery = RecoveryToken(
            token=token,
            user_email=user_email,
            email_code=email_code,
            created_at=now,
            expires_at=now + timedelta(minutes=RECOVERY_TOKEN_EXPIRY_MINUTES),
            verified=False,
            used=False,
        )

        # Token'i depola
        self._recovery_tokens[token] = recovery

        logger.info(
            "mfa_recovery_initiated",
            email=user_email,
            token_prefix=token[:8],
            expires_in_minutes=RECOVERY_TOKEN_EXPIRY_MINUTES,
        )

        return recovery

    def verify_mfa_recovery(self, token: str, email_code: str) -> bool:
        """
        MFA kurtarma email kodunu dogrular.

        Kullanicinin girdigi email dogrulama kodunu kontrol eder.

        Args:
            token: Kurtarma token'i
            email_code: Kullanicinin girdigi 6 haneli kod

        Returns:
            bool: Dogrulama basarili mi?

        Example:
            >>> is_valid = two_factor_auth.verify_mfa_recovery(
            ...     token="abc123...",
            ...     email_code="123456"
            ... )
            >>> if is_valid:
            ...     two_factor_auth.complete_mfa_recovery(token)
        """
        recovery = self._recovery_tokens.get(token)

        # Token bulunamadi
        if not recovery:
            logger.warning("mfa_recovery_token_not_found", token_prefix=token[:8])
            return False

        # Token suresi dolmus
        now = datetime.now(UTC)
        if now > recovery.expires_at:
            logger.warning(
                "mfa_recovery_token_expired",
                token_prefix=token[:8],
                expired_at=recovery.expires_at.isoformat(),
            )
            # Suresi dolmus token'i temizle
            del self._recovery_tokens[token]
            return False

        # Token zaten kullanilmis
        if recovery.used:
            logger.warning("mfa_recovery_token_already_used", token_prefix=token[:8])
            return False

        # Email kodu eslesmesi (buyuk/kucuk harf duyarsiz, bosluk temizle)
        provided_code = email_code.strip()
        expected_code = recovery.email_code.strip()

        if provided_code != expected_code:
            logger.warning(
                "mfa_recovery_code_mismatch",
                token_prefix=token[:8],
                email=recovery.user_email,
            )
            return False

        # Dogrulama basarili
        recovery.verified = True

        logger.info(
            "mfa_recovery_verified",
            token_prefix=token[:8],
            email=recovery.user_email,
        )

        return True

    def complete_mfa_recovery(self, token: str) -> bool:
        """
        MFA kurtarma islemini tamamlar ve MFA'yi devre disi birakir.

        Bu metod, verify_mfa_recovery basarili olduktan sonra
        cagrilmalidir.

        Args:
            token: Dogrulanmis kurtarma token'i

        Returns:
            bool: Islem basarili mi?

        Example:
            >>> if two_factor_auth.verify_mfa_recovery(token, code):
            ...     success = two_factor_auth.complete_mfa_recovery(token)
            ...     if success:
            ...         print("MFA devre disi birakildi")

        Note:
            Bu islem MFA'yi tamamen devre disi birakir.
            Kullanici yeniden MFA kurmalidir.
        """
        recovery = self._recovery_tokens.get(token)

        # Token bulunamadi
        if not recovery:
            logger.warning("mfa_recovery_complete_token_not_found", token_prefix=token[:8])
            return False

        # Token dogrulanmamis
        if not recovery.verified:
            logger.warning(
                "mfa_recovery_complete_not_verified",
                token_prefix=token[:8],
                email=recovery.user_email,
            )
            return False

        # Token zaten kullanilmis
        if recovery.used:
            logger.warning("mfa_recovery_complete_already_used", token_prefix=token[:8])
            return False

        # Token'i kullanildi olarak isaretle
        recovery.used = True

        # Token'i depolardan kaldir
        del self._recovery_tokens[token]

        logger.info(
            "mfa_recovery_completed",
            email=recovery.user_email,
            token_prefix=token[:8],
        )

        # NOT: Gercek implementasyonda burada veritabanindan
        # kullanicinin MFA ayarlarini silmek gerekir

        return True

    def get_recovery_token_info(self, token: str) -> RecoveryToken | None:
        """
        Kurtarma token bilgilerini getirir.

        Args:
            token: Kurtarma token'i

        Returns:
            RecoveryToken veya None (bulunamadiysa)
        """
        return self._recovery_tokens.get(token)

    def cleanup_expired_recovery_tokens(self) -> int:
        """
        Suresi dolmus kurtarma token'larini temizler.

        Returns:
            int: Temizlenen token sayisi
        """
        now = datetime.now(UTC)
        expired_tokens = [
            token for token, recovery in self._recovery_tokens.items()
            if now > recovery.expires_at
        ]

        for token in expired_tokens:
            del self._recovery_tokens[token]

        if expired_tokens:
            logger.info(
                "mfa_recovery_tokens_cleaned",
                count=len(expired_tokens),
            )

        return len(expired_tokens)

    # ==================== MFA ADMIN ENFORCEMENT (REQ-1.6) ====================

    def is_mfa_required_for_role(self, role: str) -> bool:
        """
        Rol icin MFA zorunlu mu kontrol eder.

        Admin ve super_admin rolleri icin MFA zorunludur (REQ-1.6).

        Args:
            role: Kullanici rolu (string)

        Returns:
            bool: MFA zorunlu mu?

        Example:
            >>> two_factor_auth.is_mfa_required_for_role("admin")
            True
            >>> two_factor_auth.is_mfa_required_for_role("student")
            False
        """
        # Kucuk harfe cevir ve temizle
        normalized_role = role.lower().strip()

        is_required = normalized_role in MFA_REQUIRED_ROLES

        logger.debug(
            "mfa_role_check",
            role=role,
            normalized_role=normalized_role,
            is_required=is_required,
        )

        return is_required

    def set_user_mfa_status(self, user_id: int, enabled: bool) -> None:
        """
        Kullanici MFA durumunu ayarlar.

        Args:
            user_id: Kullanici ID
            enabled: MFA aktif mi?
        """
        self._user_mfa_status[user_id] = enabled
        logger.info("mfa_status_updated", user_id=user_id, enabled=enabled)

    def get_user_mfa_status(self, user_id: int) -> bool:
        """
        Kullanici MFA durumunu getirir.

        Args:
            user_id: Kullanici ID

        Returns:
            bool: MFA aktif mi?
        """
        return self._user_mfa_status.get(user_id, False)

    def enforce_mfa_for_admin(self, user_id: int, role: str) -> EnforcementResult:
        """
        Admin kullanicilari icin MFA zorunlulugunu kontrol eder.

        Admin ve super_admin kullanicilarinin MFA'yi aktif
        etmesi zorunludur (REQ-1.6).

        Args:
            user_id: Kullanici ID
            role: Kullanici rolu

        Returns:
            EnforcementResult: Zorunluluk kontrol sonucu

        Example:
            >>> result = two_factor_auth.enforce_mfa_for_admin(
            ...     user_id=123,
            ...     role="admin"
            ... )
            >>> if result.enforcement_needed:
            ...     print("MFA kurulumu gerekli!")
            ...     # Kullaniciyi MFA kurulum sayfasina yonlendir
        """
        # Rol icin MFA zorunlu mu?
        mfa_required = self.is_mfa_required_for_role(role)

        # Kullanicinin MFA durumu
        mfa_enabled = self.get_user_mfa_status(user_id)

        # Zorunluluk uygulanmali mi?
        enforcement_needed = mfa_required and not mfa_enabled

        # Mesaj belirleme
        if not mfa_required:
            message = f"'{role}' rolu icin MFA zorunlu degildir"
        elif mfa_enabled:
            message = "MFA zaten aktif, zorunluluk karsilaniyor"
        else:
            message = f"UYARI: '{role}' rolu icin MFA zorunludur. Lutfen MFA'yi aktif edin"

        result = EnforcementResult(
            mfa_required=mfa_required,
            mfa_enabled=mfa_enabled,
            enforcement_needed=enforcement_needed,
            role=role,
            message=message,
        )

        # Zorunluluk ihlali varsa logla
        if enforcement_needed:
            logger.warning(
                "mfa_enforcement_violation",
                user_id=user_id,
                role=role,
                enforcement_message=message,
            )
        else:
            logger.debug(
                "mfa_enforcement_check",
                user_id=user_id,
                role=role,
                mfa_required=mfa_required,
                mfa_enabled=mfa_enabled,
            )

        return result

    def get_mfa_required_roles(self) -> set[str]:
        """
        MFA zorunlu rollerin listesini dondurur.

        Returns:
            set[str]: MFA zorunlu roller
        """
        return MFA_REQUIRED_ROLES.copy()


# Global instance
two_factor_auth = TwoFactorAuthService()

__all__ = [
    "MFA_REQUIRED_ROLES",
    "RECOVERY_TOKEN_EXPIRY_MINUTES",
    "EnforcementResult",
    "RecoveryToken",
    "TwoFactorAuthService",
    "two_factor_auth",
]
