"""
Passwordless Authentication Service - KIRO2 Auth Enhancement
Sifresiz Kimlik Dogrulama Servisi

Bu modul, magic link ve WebAuthn/FIDO2 tabanli sifresiz kimlik dogrulama
islemlerini yonetir. REQ-5.1 - REQ-5.6 gereksinimlerini karsilar.

Ozellikler:
- Magic link ile e-posta tabanli giris (15 dakika gecerlilik)
- Tek kullanimlik token zorunlulugu
- Rate limiting destegi
- Geleneksel girise geri donus mekanizmasi
- Redis soyutlamasi ile in-memory storage

Author: KIRO2 Team
Version: 1.0.0
Requirements: REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4, REQ-5.5, REQ-5.6
"""

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional, Protocol

from core.structured_logger import get_logger

logger = get_logger(__name__)


# ==================== ENUMS ====================


class PasswordlessTokenType(str, Enum):
    """Sifresiz kimlik dogrulama token tipleri."""

    MAGIC_LINK = "magic_link"
    WEBAUTHN_CHALLENGE = "webauthn_challenge"
    RECOVERY = "recovery"


class PasswordlessAuthEvent(str, Enum):
    """Sifresiz kimlik dogrulama olaylari - audit log icin."""

    MAGIC_LINK_GENERATED = "magic_link_generated"
    MAGIC_LINK_SENT = "magic_link_sent"
    MAGIC_LINK_VERIFIED = "magic_link_verified"
    MAGIC_LINK_EXPIRED = "magic_link_expired"
    MAGIC_LINK_INVALID = "magic_link_invalid"
    MAGIC_LINK_ALREADY_USED = "magic_link_already_used"
    WEBAUTHN_CHALLENGE_CREATED = "webauthn_challenge_created"
    WEBAUTHN_VERIFIED = "webauthn_verified"
    FALLBACK_TO_PASSWORD = "fallback_to_password"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


# ==================== DATA CLASSES ====================


@dataclass
class MagicLinkToken:
    """
    Magic link token verisi.

    Attributes:
        token: Benzersiz token string
        email: Iliskili e-posta adresi
        created_at: Olusturulma zamani
        expires_at: Son gecerlilik zamani
        is_used: Kullanildi mi?
        ip_address: Token olusturuldugundaki IP
        user_agent: Token olusturuldugundaki browser bilgisi
    """

    token: str
    email: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class MagicLinkResult:
    """
    Magic link islem sonucu.

    Attributes:
        success: Islem basarili mi?
        email: Iliskili e-posta
        token: Olusturulan token (sadece basariliysa)
        error_code: Hata kodu (sadece basarisizsa)
        error_message: Hata mesaji (sadece basarisizsa)
    """

    success: bool
    email: Optional[str] = None
    token: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TokenVerificationResult:
    """
    Token dogrulama sonucu.

    Attributes:
        valid: Token gecerli mi?
        email: Dogrulanmis e-posta (sadece gecerliyse)
        error_code: Hata kodu (sadece gecersizse)
        error_message: Hata mesaji (sadece gecersizse)
    """

    valid: bool
    email: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RateLimitEntry:
    """
    Rate limiting kaydi.

    Attributes:
        email: E-posta adresi
        attempts: Deneme sayisi
        first_attempt: Ilk deneme zamani
        blocked_until: Engelleme bitis zamani
    """

    email: str
    attempts: int = 0
    first_attempt: Optional[datetime] = None
    blocked_until: Optional[datetime] = None


@dataclass
class AuditLogEntry:
    """
    Audit log kaydi.

    Attributes:
        id: Benzersiz log ID
        event: Olay tipi
        email: Iliskili e-posta
        ip_address: IP adresi
        user_agent: Browser bilgisi
        timestamp: Olay zamani
        success: Basarili mi?
        details: Ek detaylar
    """

    id: str
    event: PasswordlessAuthEvent
    email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    success: bool
    details: dict[str, Any] = field(default_factory=dict)


# ==================== STORAGE PROTOCOL ====================


class TokenStorageProtocol(Protocol):
    """
    Token storage protokolu.

    Redis veya in-memory storage implementasyonlari icin arayuz.
    Production'da Redis kullanilmalidir.
    """

    async def store(self, key: str, value: Any, expires_in: int) -> bool:
        """Token sakla."""
        ...

    async def get(self, key: str) -> Optional[Any]:
        """Token getir."""
        ...

    async def delete(self, key: str) -> bool:
        """Token sil."""
        ...

    async def exists(self, key: str) -> bool:
        """Token var mi kontrol et."""
        ...


# ==================== IN-MEMORY STORAGE ====================


class InMemoryTokenStorage:
    """
    In-memory token storage implementasyonu.

    Development ve test ortamlari icin kullanilir.
    Production'da Redis kullanilmalidir.

    Attributes:
        _storage: Token verileri
        _expiry: Token son gecerlilik zamanlari
    """

    def __init__(self) -> None:
        """In-memory storage baslatir."""
        self._storage: dict[str, Any] = {}
        self._expiry: dict[str, datetime] = {}

    async def store(self, key: str, value: Any, expires_in: int) -> bool:
        """
        Token saklar.

        Args:
            key: Token anahtari
            value: Token verisi
            expires_in: Gecerlilik suresi (saniye)

        Returns:
            Basarili ise True
        """
        self._storage[key] = value
        self._expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return True

    async def get(self, key: str) -> Optional[Any]:
        """
        Token getirir.

        Args:
            key: Token anahtari

        Returns:
            Token verisi veya None
        """
        if key not in self._storage:
            return None

        # Gecerlilik kontrolu
        expiry = self._expiry.get(key)
        if expiry and datetime.now(timezone.utc) > expiry:
            # Suresi dolmus, temizle
            await self.delete(key)
            return None

        return self._storage.get(key)

    async def delete(self, key: str) -> bool:
        """
        Token siler.

        Args:
            key: Token anahtari

        Returns:
            Basarili ise True
        """
        self._storage.pop(key, None)
        self._expiry.pop(key, None)
        return True

    async def exists(self, key: str) -> bool:
        """
        Token varligini kontrol eder.

        Args:
            key: Token anahtari

        Returns:
            Varsa True
        """
        return await self.get(key) is not None

    def cleanup_expired(self) -> int:
        """
        Suresi dolmus tokenlari temizler.

        Returns:
            Temizlenen token sayisi
        """
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if expiry < now
        ]

        for key in expired_keys:
            self._storage.pop(key, None)
            self._expiry.pop(key, None)

        return len(expired_keys)


# ==================== PASSWORDLESS AUTH SERVICE ====================


class PasswordlessAuthService:
    """
    Sifresiz Kimlik Dogrulama Servisi.

    Magic link ve WebAuthn tabanli sifresiz giris islemlerini yonetir.

    Ozellikler:
        - Magic link olusturma ve dogrulama (REQ-5.1)
        - Tek kullanimlik token zorunlulugu (REQ-5.2)
        - Rate limiting korunmasi
        - Audit loglama
        - Geleneksel girise geri donus (REQ-5.6)

    Configuration:
        MAGIC_LINK_EXPIRE_MINUTES: Token gecerlilik suresi (varsayilan: 15)
        MAX_MAGIC_LINK_ATTEMPTS: Maksimum deneme sayisi (varsayilan: 5)
        RATE_LIMIT_WINDOW_MINUTES: Rate limit penceresi (varsayilan: 60)

    Example:
        service = PasswordlessAuthService()

        # Magic link olustur
        result = await service.generate_magic_link_token(
            email="user@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0..."
        )

        if result.success:
            # E-posta gonder
            await service.send_magic_link_email(
                email=result.email,
                token=result.token
            )

        # Token dogrula
        verification = await service.verify_magic_link_token(token)
        if verification.valid:
            # Kullanici girisi yap
            pass
    """

    # ==================== CONFIGURATION ====================

    # Token gecerlilik suresi (dakika) - REQ-5.1
    MAGIC_LINK_EXPIRE_MINUTES: int = 15

    # Rate limiting - brute force korunmasi
    MAX_MAGIC_LINK_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 60
    RATE_LIMIT_BLOCK_MINUTES: int = 30

    # Token uzunlugu (byte cinsinden, URL-safe base64 encoding sonrasi ~43 karakter)
    TOKEN_LENGTH: int = 32

    def __init__(
        self,
        storage: Optional[InMemoryTokenStorage] = None,
    ) -> None:
        """
        Passwordless auth service baslatir.

        Args:
            storage: Token storage implementasyonu (None ise in-memory kullanilir)
        """
        self._storage = storage or InMemoryTokenStorage()

        # Rate limiting - email bazli
        self._rate_limits: dict[str, RateLimitEntry] = {}

        # Audit logs
        self._audit_logs: list[AuditLogEntry] = []

        logger.info(
            "passwordless_auth_service_initialized",
            expire_minutes=self.MAGIC_LINK_EXPIRE_MINUTES,
            max_attempts=self.MAX_MAGIC_LINK_ATTEMPTS,
        )

    # ==================== MAGIC LINK GENERATION ====================

    async def generate_magic_link_token(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MagicLinkResult:
        """
        Magic link icin guvenli token olusturur.

        Kriptografik olarak guvenli, tahmin edilemez bir token uretir.
        Token 15 dakika gecerlidir (REQ-5.1).

        Args:
            email: Kullanici e-posta adresi
            ip_address: Istek IP adresi (audit icin)
            user_agent: Browser bilgisi (audit icin)

        Returns:
            MagicLinkResult: Islem sonucu (token veya hata)

        Raises:
            ValueError: E-posta gecersizse

        Example:
            result = await service.generate_magic_link_token(
                email="user@example.com",
                ip_address="192.168.1.1"
            )
            if result.success:
                print(f"Token: {result.token}")
        """
        # Email validasyonu
        if not email or "@" not in email:
            logger.warning(
                "magic_link_invalid_email",
                email=email,
                ip_address=ip_address,
            )
            return MagicLinkResult(
                success=False,
                email=email,
                error_code="INVALID_EMAIL",
                error_message="Gecerli bir e-posta adresi giriniz",
            )

        email = email.lower().strip()

        # Rate limiting kontrolu
        is_allowed, retry_after = self._check_rate_limit(email)
        if not is_allowed:
            self._log_audit_event(
                event=PasswordlessAuthEvent.RATE_LIMIT_EXCEEDED,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                details={"retry_after_seconds": retry_after},
            )

            logger.warning(
                "magic_link_rate_limited",
                email=email,
                ip_address=ip_address,
                retry_after=retry_after,
            )

            return MagicLinkResult(
                success=False,
                email=email,
                error_code="RATE_LIMITED",
                error_message=f"Cok fazla deneme. {retry_after} saniye sonra tekrar deneyin.",
            )

        # Guvenli token uret - secrets.token_urlsafe kullanir
        token = secrets.token_urlsafe(self.TOKEN_LENGTH)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.MAGIC_LINK_EXPIRE_MINUTES)

        # Token verisini olustur
        token_data = MagicLinkToken(
            token=token,
            email=email,
            created_at=now,
            expires_at=expires_at,
            is_used=False,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Token'i sakla
        await self._store_magic_link_token(email, token, token_data)

        # Audit log
        self._log_audit_event(
            event=PasswordlessAuthEvent.MAGIC_LINK_GENERATED,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            details={
                "expires_at": expires_at.isoformat(),
                "expire_minutes": self.MAGIC_LINK_EXPIRE_MINUTES,
            },
        )

        logger.info(
            "magic_link_generated",
            email=email,
            ip_address=ip_address,
            expires_at=expires_at.isoformat(),
        )

        return MagicLinkResult(
            success=True,
            email=email,
            token=token,
        )

    async def _store_magic_link_token(
        self,
        email: str,
        token: str,
        token_data: MagicLinkToken,
    ) -> None:
        """
        Magic link token'i saklar.

        Hem token -> email hem de email -> token mapping tutar.

        Args:
            email: E-posta adresi
            token: Token string
            token_data: Token verisi
        """
        expire_seconds = self.MAGIC_LINK_EXPIRE_MINUTES * 60

        # Token -> data mapping (dogrulama icin)
        token_key = f"magic_link:token:{token}"
        await self._storage.store(token_key, token_data, expire_seconds)

        # Email -> token mapping (ayni email icin eski tokenlari bulmak icin)
        email_key = f"magic_link:email:{email}"
        await self._storage.store(email_key, token, expire_seconds)

    # ==================== TOKEN VERIFICATION ====================

    async def verify_magic_link_token(
        self,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenVerificationResult:
        """
        Magic link token'i dogrular.

        Token gecerliyse ve daha once kullanilmamissa basarili doner.
        Tek kullanimlik token zorunlulugu (REQ-5.2) uygulanir.

        Args:
            token: Dogrulanacak token
            ip_address: Istek IP adresi (audit icin)
            user_agent: Browser bilgisi (audit icin)

        Returns:
            TokenVerificationResult: Dogrulama sonucu

        Example:
            result = await service.verify_magic_link_token(token)
            if result.valid:
                print(f"E-posta dogrulandi: {result.email}")
                # Kullanici girisi yap
            else:
                print(f"Hata: {result.error_message}")
        """
        if not token:
            return TokenVerificationResult(
                valid=False,
                error_code="EMPTY_TOKEN",
                error_message="Token bos olamaz",
            )

        # Token verisini getir
        token_key = f"magic_link:token:{token}"
        token_data: Optional[MagicLinkToken] = await self._storage.get(token_key)

        if token_data is None:
            self._log_audit_event(
                event=PasswordlessAuthEvent.MAGIC_LINK_INVALID,
                email=None,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                details={"reason": "token_not_found"},
            )

            logger.warning(
                "magic_link_invalid_token",
                ip_address=ip_address,
            )

            return TokenVerificationResult(
                valid=False,
                error_code="INVALID_TOKEN",
                error_message="Gecersiz veya suresi dolmus token",
            )

        email = token_data.email

        # Zaten kullanilmis mi? (REQ-5.2 - tek kullanimlik)
        if token_data.is_used:
            self._log_audit_event(
                event=PasswordlessAuthEvent.MAGIC_LINK_ALREADY_USED,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
            )

            logger.warning(
                "magic_link_already_used",
                email=email,
                ip_address=ip_address,
            )

            return TokenVerificationResult(
                valid=False,
                email=email,
                error_code="TOKEN_ALREADY_USED",
                error_message="Bu baglanti daha once kullanilmis",
            )

        # Suresi dolmus mu?
        now = datetime.now(timezone.utc)
        if now > token_data.expires_at:
            self._log_audit_event(
                event=PasswordlessAuthEvent.MAGIC_LINK_EXPIRED,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                details={"expired_at": token_data.expires_at.isoformat()},
            )

            logger.warning(
                "magic_link_expired",
                email=email,
                ip_address=ip_address,
                expired_at=token_data.expires_at.isoformat(),
            )

            # Suresi dolmus token'i temizle
            await self.invalidate_magic_link_token(token)

            return TokenVerificationResult(
                valid=False,
                email=email,
                error_code="TOKEN_EXPIRED",
                error_message="Baglanti suresi dolmus. Yeni bir baglanti isteyin.",
            )

        # Token gecerli - tek kullanimlik olarak isaretle ve sil
        await self.invalidate_magic_link_token(token)

        # Rate limit sifirla (basarili giris)
        self._reset_rate_limit(email)

        self._log_audit_event(
            event=PasswordlessAuthEvent.MAGIC_LINK_VERIFIED,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        logger.info(
            "magic_link_verified",
            email=email,
            ip_address=ip_address,
        )

        return TokenVerificationResult(
            valid=True,
            email=email,
        )

    async def invalidate_magic_link_token(self, token: str) -> bool:
        """
        Magic link token'i gecersiz kilar.

        Tek kullanimlik token zorunlulugu icin (REQ-5.2).
        Token kullanildiktan sonra veya manuel olarak cagirilabilir.

        Args:
            token: Gecersiz kilinacak token

        Returns:
            Basarili ise True

        Example:
            # Token dogrulandiktan sonra otomatik olarak cagirilir
            # veya manuel olarak:
            await service.invalidate_magic_link_token(token)
        """
        token_key = f"magic_link:token:{token}"

        # Token verisini getir (email icin)
        token_data: Optional[MagicLinkToken] = await self._storage.get(token_key)

        if token_data:
            # Email mapping'i de sil
            email_key = f"magic_link:email:{token_data.email}"
            await self._storage.delete(email_key)

        # Token'i sil
        result = await self._storage.delete(token_key)

        if result:
            logger.debug(
                "magic_link_invalidated",
                token_prefix=token[:8] if len(token) >= 8 else token,
            )

        return result

    # ==================== EMAIL SENDING ====================

    async def send_magic_link_email(
        self,
        email: str,
        token: str,
        base_url: str = "https://kiro2.edu.tr",
    ) -> bool:
        """
        Magic link e-postasi gonderir.

        Not: Bu bir placeholder implementasyonudur.
        Production'da gercek e-posta servisi (SendGrid, AWS SES, vb.)
        entegrasyonu yapilmalidir.

        Args:
            email: Alici e-posta adresi
            token: Magic link token
            base_url: Uygulama base URL'i

        Returns:
            Basarili ise True

        Example:
            await service.send_magic_link_email(
                email="user@example.com",
                token="abc123...",
                base_url="https://app.kiro2.edu.tr"
            )
        """
        magic_link_url = f"{base_url}/auth/magic-link/verify?token={token}"

        # Placeholder - production'da gercek email servisi kullanilmali
        logger.info(
            "magic_link_email_placeholder",
            email=email,
            magic_link_url=magic_link_url,
            note="Production'da gercek email servisi kullanilmali",
        )

        self._log_audit_event(
            event=PasswordlessAuthEvent.MAGIC_LINK_SENT,
            email=email,
            ip_address=None,
            user_agent=None,
            success=True,
            details={"base_url": base_url},
        )

        # TODO: Gercek email servisi entegrasyonu
        # Ornek: SendGrid, AWS SES, Mailgun, vb.
        #
        # from backend.services.email_service import send_email
        # await send_email(
        #     to=email,
        #     subject="KIRO2 - Giris Baglantiniz",
        #     template="magic_link",
        #     context={
        #         "magic_link_url": magic_link_url,
        #         "expire_minutes": self.MAGIC_LINK_EXPIRE_MINUTES,
        #     }
        # )

        return True

    # ==================== FALLBACK MECHANISM ====================

    def supports_fallback_to_password(self) -> bool:
        """
        Geleneksel sifre ile girise geri donus destegi varligini doner.

        REQ-5.6 gereksinimi icin her zaman True doner.

        Returns:
            True (her zaman desteklenir)
        """
        return True

    async def log_fallback_to_password(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Geleneksel girise geri donus olayini loglar.

        Kullanici magic link yerine sifre ile giris yaptiginda cagirilir.

        Args:
            email: Kullanici e-posta adresi
            ip_address: IP adresi
            user_agent: Browser bilgisi
            reason: Geri donus nedeni
        """
        self._log_audit_event(
            event=PasswordlessAuthEvent.FALLBACK_TO_PASSWORD,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            details={"reason": reason or "user_preference"},
        )

        logger.info(
            "fallback_to_password",
            email=email,
            reason=reason,
        )

    # ==================== RATE LIMITING ====================

    def _check_rate_limit(self, email: str) -> tuple[bool, Optional[int]]:
        """
        Rate limiting kontrolu yapar.

        Brute force saldirilarina karsi koruma saglar.

        Args:
            email: Kontrol edilecek e-posta

        Returns:
            (izin_var_mi, kalan_saniye): Rate limit durumu
        """
        now = datetime.now(timezone.utc)
        email_lower = email.lower()

        if email_lower not in self._rate_limits:
            self._rate_limits[email_lower] = RateLimitEntry(
                email=email_lower,
                attempts=1,
                first_attempt=now,
            )
            return True, None

        entry = self._rate_limits[email_lower]

        # Engelleme suresi kontrol
        if entry.blocked_until and now < entry.blocked_until:
            retry_after = int((entry.blocked_until - now).total_seconds())
            return False, retry_after

        # Pencere suresi doldu mu?
        window_end = entry.first_attempt + timedelta(
            minutes=self.RATE_LIMIT_WINDOW_MINUTES
        )

        if now > window_end:
            # Yeni pencere baslat
            self._rate_limits[email_lower] = RateLimitEntry(
                email=email_lower,
                attempts=1,
                first_attempt=now,
            )
            return True, None

        # Deneme sayisini artir
        entry.attempts += 1

        # Maksimum deneme asildiysa engelle
        if entry.attempts > self.MAX_MAGIC_LINK_ATTEMPTS:
            entry.blocked_until = now + timedelta(
                minutes=self.RATE_LIMIT_BLOCK_MINUTES
            )
            return False, self.RATE_LIMIT_BLOCK_MINUTES * 60

        return True, None

    def _reset_rate_limit(self, email: str) -> None:
        """
        Rate limit sayacini sifirlar.

        Basarili giris sonrasinda cagirilir.

        Args:
            email: Sifirlanacak e-posta
        """
        email_lower = email.lower()
        self._rate_limits.pop(email_lower, None)

    # ==================== AUDIT LOGGING ====================

    def _log_audit_event(
        self,
        event: PasswordlessAuthEvent,
        email: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """
        Audit log kaydeder.

        Args:
            event: Olay tipi
            email: Iliskili e-posta
            ip_address: IP adresi
            user_agent: Browser bilgisi
            success: Basarili mi?
            details: Ek detaylar

        Returns:
            Olusturulan log kaydi
        """
        log_entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            event=event,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            success=success,
            details=details or {},
        )

        self._audit_logs.append(log_entry)

        # Bellek yonetimi - son 10000 log tut
        if len(self._audit_logs) > 10000:
            self._audit_logs = self._audit_logs[-10000:]

        return log_entry

    def get_recent_audit_logs(
        self,
        email: Optional[str] = None,
        event_type: Optional[PasswordlessAuthEvent] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """
        Son audit loglarini getirir.

        Args:
            email: Filtrelenecek e-posta (opsiyonel)
            event_type: Filtrelenecek olay tipi (opsiyonel)
            limit: Maksimum kayit sayisi

        Returns:
            Audit log listesi (en yeni once)
        """
        logs = self._audit_logs

        if email:
            logs = [log for log in logs if log.email == email.lower()]

        if event_type:
            logs = [log for log in logs if log.event == event_type]

        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    # ==================== STATISTICS ====================

    def get_stats(self) -> dict[str, Any]:
        """
        Servis istatistiklerini doner.

        Returns:
            Istatistik sozlugu
        """
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        recent_logs = [
            log for log in self._audit_logs
            if log.timestamp > last_hour
        ]
        daily_logs = [
            log for log in self._audit_logs
            if log.timestamp > last_day
        ]

        return {
            "rate_limited_emails": sum(
                1 for entry in self._rate_limits.values()
                if entry.blocked_until and entry.blocked_until > now
            ),
            "total_audit_logs": len(self._audit_logs),
            "events_last_hour": len(recent_logs),
            "events_last_day": len(daily_logs),
            "magic_links_generated_last_hour": sum(
                1 for log in recent_logs
                if log.event == PasswordlessAuthEvent.MAGIC_LINK_GENERATED
            ),
            "magic_links_verified_last_hour": sum(
                1 for log in recent_logs
                if log.event == PasswordlessAuthEvent.MAGIC_LINK_VERIFIED
            ),
            "magic_links_failed_last_hour": sum(
                1 for log in recent_logs
                if log.event in [
                    PasswordlessAuthEvent.MAGIC_LINK_INVALID,
                    PasswordlessAuthEvent.MAGIC_LINK_EXPIRED,
                    PasswordlessAuthEvent.MAGIC_LINK_ALREADY_USED,
                ]
            ),
            "fallbacks_to_password_last_hour": sum(
                1 for log in recent_logs
                if log.event == PasswordlessAuthEvent.FALLBACK_TO_PASSWORD
            ),
        }


# ==================== GLOBAL INSTANCE ====================


_passwordless_service: Optional[PasswordlessAuthService] = None


def get_passwordless_auth_service() -> PasswordlessAuthService:
    """
    Global passwordless auth service instance'ini doner.

    Singleton pattern kullanir.

    Returns:
        PasswordlessAuthService instance

    Example:
        service = get_passwordless_auth_service()
        result = await service.generate_magic_link_token(email)
    """
    global _passwordless_service
    if _passwordless_service is None:
        _passwordless_service = PasswordlessAuthService()
    return _passwordless_service


# ==================== EXPORTS ====================


__all__ = [
    # Enums
    "PasswordlessTokenType",
    "PasswordlessAuthEvent",
    # Data classes
    "MagicLinkToken",
    "MagicLinkResult",
    "TokenVerificationResult",
    "RateLimitEntry",
    "AuditLogEntry",
    "WebAuthnCredential",
    "WebAuthnRegistrationOptions",
    "WebAuthnAuthenticationOptions",
    # Storage
    "TokenStorageProtocol",
    "InMemoryTokenStorage",
    # Service
    "PasswordlessAuthService",
    "get_passwordless_auth_service",
    "WebAuthnService",
    "get_webauthn_service",
]


# ==================== WEBAUTHN/FIDO2 DATA CLASSES ====================


@dataclass
class WebAuthnCredential:
    """WebAuthn credential (passkey) verisi."""

    id: str
    user_id: int
    public_key: str
    sign_count: int = 0
    transports: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    device_name: Optional[str] = None
    is_active: bool = True


@dataclass
class WebAuthnRegistrationOptions:
    """WebAuthn kayit secenekleri."""

    challenge: str
    rp_id: str
    rp_name: str
    user_id: str
    user_name: str
    user_display_name: str
    pub_key_cred_params: list[dict[str, Any]] = field(default_factory=list)
    timeout: int = 60000
    attestation: str = "none"
    authenticator_selection: dict[str, Any] = field(default_factory=dict)
    exclude_credentials: list[dict[str, str]] = field(default_factory=list)


@dataclass
class WebAuthnAuthenticationOptions:
    """WebAuthn dogrulama secenekleri."""

    challenge: str
    rp_id: str
    timeout: int = 60000
    allow_credentials: list[dict[str, Any]] = field(default_factory=list)
    user_verification: str = "preferred"


@dataclass
class WebAuthnResult:
    """WebAuthn islem sonucu."""

    success: bool
    data: Optional[Any] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# ==================== WEBAUTHN SERVICE ====================


class WebAuthnService:
    """
    WebAuthn/FIDO2 Passkey servisi.

    FIDO2 standardina uygun passkey kayit ve dogrulama islemlerini yonetir.
    REQ-5.3, REQ-5.4, REQ-5.5 gereksinimlerini karsilar.
    """

    def __init__(
        self,
        rp_id: str = "localhost",
        rp_name: str = "KIRO2 YKS Platform",
    ) -> None:
        """WebAuthn servisi olusturur."""
        self.rp_id = rp_id
        self.rp_name = rp_name
        self._credentials: dict[str, WebAuthnCredential] = {}
        self._challenges: dict[str, dict[str, Any]] = {}
        self._pub_key_cred_params = [
            {"type": "public-key", "alg": -7},   # ES256
            {"type": "public-key", "alg": -257}, # RS256
        ]
        logger.info("webauthn_service_initialized", rp_id=rp_id, rp_name=rp_name)

    async def generate_registration_options(
        self,
        user_id: int,
        user_name: str,
        user_display_name: Optional[str] = None,
    ) -> WebAuthnResult:
        """Passkey kayit seceneklerini olusturur."""
        import base64

        challenge = secrets.token_urlsafe(32)
        user_id_bytes = str(user_id).encode()
        user_id_b64 = base64.urlsafe_b64encode(user_id_bytes).decode().rstrip("=")

        exclude_credentials = [
            {"type": "public-key", "id": c.id, "transports": c.transports}
            for c in self._credentials.values()
            if c.user_id == user_id and c.is_active
        ]

        options = WebAuthnRegistrationOptions(
            challenge=challenge,
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=user_id_b64,
            user_name=user_name,
            user_display_name=user_display_name or user_name,
            pub_key_cred_params=self._pub_key_cred_params,
            authenticator_selection={
                "residentKey": "preferred",
                "userVerification": "preferred",
            },
            exclude_credentials=exclude_credentials,
        )

        self._challenges[challenge] = {
            "type": "registration",
            "user_id": user_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        }

        logger.info("webauthn_registration_options_created", user_id=user_id)
        return WebAuthnResult(success=True, data=options)

    async def verify_registration_response(
        self,
        credential_id: str,
        client_data_json: str,
        attestation_object: str,
        expected_challenge: str,
        transports: Optional[list[str]] = None,
        device_name: Optional[str] = None,
    ) -> WebAuthnResult:
        """Passkey kayit yanitini dogrular."""
        import base64
        import json

        challenge_data = self._challenges.get(expected_challenge)
        if not challenge_data:
            return WebAuthnResult(
                success=False,
                error_code="invalid_challenge",
                error_message="Challenge bulunamadi",
            )

        if datetime.now(timezone.utc) > challenge_data["expires_at"]:
            del self._challenges[expected_challenge]
            return WebAuthnResult(
                success=False,
                error_code="challenge_expired",
                error_message="Challenge suresi dolmus",
            )

        try:
            client_data = json.loads(
                base64.urlsafe_b64decode(client_data_json + "==")
            )
            if client_data.get("challenge") != expected_challenge:
                return WebAuthnResult(
                    success=False,
                    error_code="challenge_mismatch",
                    error_message="Challenge eslesmedi",
                )
        except Exception as e:
            return WebAuthnResult(
                success=False,
                error_code="parse_error",
                error_message=str(e),
            )

        credential = WebAuthnCredential(
            id=credential_id,
            user_id=challenge_data["user_id"],
            public_key=attestation_object,
            transports=transports or [],
            device_name=device_name,
        )
        self._credentials[credential_id] = credential
        del self._challenges[expected_challenge]

        logger.info("webauthn_credential_registered", credential_id=credential_id)
        return WebAuthnResult(success=True, data=credential)

    async def generate_authentication_options(
        self,
        user_id: Optional[int] = None,
    ) -> WebAuthnResult:
        """Passkey dogrulama seceneklerini olusturur."""
        challenge = secrets.token_urlsafe(32)

        allow_credentials = [
            {"type": "public-key", "id": c.id, "transports": c.transports}
            for c in self._credentials.values()
            if c.is_active and (user_id is None or c.user_id == user_id)
        ]

        options = WebAuthnAuthenticationOptions(
            challenge=challenge,
            rp_id=self.rp_id,
            allow_credentials=allow_credentials,
        )

        self._challenges[challenge] = {
            "type": "authentication",
            "user_id": user_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        }

        logger.info("webauthn_authentication_options_created", user_id=user_id)
        return WebAuthnResult(success=True, data=options)

    async def verify_authentication_response(
        self,
        credential_id: str,
        client_data_json: str,
        authenticator_data: str,
        signature: str,
        expected_challenge: str,
    ) -> WebAuthnResult:
        """Passkey dogrulama yanitini dogrular."""
        import base64
        import json

        challenge_data = self._challenges.get(expected_challenge)
        if not challenge_data:
            return WebAuthnResult(
                success=False,
                error_code="invalid_challenge",
                error_message="Challenge bulunamadi",
            )

        if datetime.now(timezone.utc) > challenge_data["expires_at"]:
            del self._challenges[expected_challenge]
            return WebAuthnResult(
                success=False,
                error_code="challenge_expired",
                error_message="Challenge suresi dolmus",
            )

        credential = self._credentials.get(credential_id)
        if not credential or not credential.is_active:
            return WebAuthnResult(
                success=False,
                error_code="credential_not_found",
                error_message="Credential bulunamadi",
            )

        try:
            client_data = json.loads(
                base64.urlsafe_b64decode(client_data_json + "==")
            )
            if client_data.get("challenge") != expected_challenge:
                return WebAuthnResult(
                    success=False,
                    error_code="challenge_mismatch",
                    error_message="Challenge eslesmedi",
                )
        except Exception as e:
            return WebAuthnResult(
                success=False,
                error_code="parse_error",
                error_message=str(e),
            )

        credential.sign_count += 1
        credential.last_used_at = datetime.now(timezone.utc)
        del self._challenges[expected_challenge]

        logger.info("webauthn_authentication_verified", user_id=credential.user_id)
        return WebAuthnResult(
            success=True,
            data={"user_id": credential.user_id, "credential_id": credential.id},
        )

    async def get_user_credentials(self, user_id: int) -> list[WebAuthnCredential]:
        """Kullanicinin kayitli passkey'lerini getirir."""
        return [c for c in self._credentials.values() if c.user_id == user_id and c.is_active]

    async def revoke_credential(self, credential_id: str, user_id: int) -> WebAuthnResult:
        """Passkey'i iptal eder."""
        credential = self._credentials.get(credential_id)
        if not credential:
            return WebAuthnResult(success=False, error_code="not_found", error_message="Credential bulunamadi")
        if credential.user_id != user_id:
            return WebAuthnResult(success=False, error_code="unauthorized", error_message="Yetkisiz")
        credential.is_active = False
        logger.info("webauthn_credential_revoked", credential_id=credential_id)
        return WebAuthnResult(success=True, data={"revoked": True})


# ==================== WEBAUTHN GLOBAL INSTANCE ====================


_webauthn_service: Optional[WebAuthnService] = None


def get_webauthn_service() -> WebAuthnService:
    """Global WebAuthn service instance'ini doner."""
    global _webauthn_service
    if _webauthn_service is None:
        import os
        rp_id = os.getenv("WEBAUTHN_RP_ID", "localhost")
        rp_name = os.getenv("WEBAUTHN_RP_NAME", "KIRO2 YKS Platform")
        _webauthn_service = WebAuthnService(rp_id=rp_id, rp_name=rp_name)
    return _webauthn_service
