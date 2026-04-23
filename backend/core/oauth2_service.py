"""
OAuth2 Authentication Service - KIRO2 YKS Platform

Bu moduel, sosyal giris (Google OAuth2) islevselligini saglar.
Authorization Code Grant flow'u kullanir ve CSRF korumasini destekler.

REQ-2.1: Authorization code grant flow
REQ-2.2: Google OAuth2 API destegi
REQ-2.3: State parameter ile CSRF koruması
REQ-2.4: Access + Refresh token exchange
REQ-2.5: Provider'dan kullanici bilgisi fetch
REQ-2.6: Email-based account linking/merge

Kullanim:
    oauth2_service = get_oauth2_service()
    auth_url, state = await oauth2_service.get_authorization_url("google")
    tokens = await oauth2_service.exchange_code("google", code, state)
    user_info = await oauth2_service.get_user_info("google", tokens["access_token"])
    user = await oauth2_service.link_or_create_user("google", user_info, db)
"""

import hashlib
import logging
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Structured logging
logger = logging.getLogger(__name__)


# ==================== ENUMS ====================


class OAuth2Provider(str, Enum):
    """Desteklenen OAuth2 provider'lari.

    Attributes:
        GOOGLE: Google OAuth2 API
    """

    GOOGLE = "google"


class OAuth2Error(str, Enum):
    """OAuth2 hata kodlari.

    Attributes:
        INVALID_STATE: State parametresi gecersiz (CSRF korumasi)
        INVALID_CODE: Authorization code gecersiz
        TOKEN_EXCHANGE_FAILED: Token exchange islemi basarisiz
        USER_INFO_FAILED: Kullanici bilgisi alinamadi
        PROVIDER_NOT_SUPPORTED: Provider desteklenmiyor
        ACCOUNT_LINK_FAILED: Hesap baglama basarisiz
    """

    INVALID_STATE = "invalid_state"
    INVALID_CODE = "invalid_code"
    TOKEN_EXCHANGE_FAILED = "token_exchange_failed"
    USER_INFO_FAILED = "user_info_failed"
    PROVIDER_NOT_SUPPORTED = "provider_not_supported"
    ACCOUNT_LINK_FAILED = "account_link_failed"


# ==================== DATA CLASSES ====================


@dataclass
class OAuth2ProviderConfig:
    """OAuth2 Provider konfigurasyonu.

    Her OAuth2 provider icin gerekli URL ve credential bilgilerini icerir.

    Attributes:
        name: Provider adi (google, github, vb.)
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        redirect_uri: Callback URL
        authorization_url: Authorization endpoint URL
        token_url: Token exchange endpoint URL
        userinfo_url: User info endpoint URL
        scopes: Istenen yetkiler listesi
    """

    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str] = field(default_factory=list)


@dataclass
class OAuth2Tokens:
    """OAuth2 token bilgileri.

    Token exchange sonrasi donen token bilgilerini icerir.

    Attributes:
        access_token: API erisimi icin access token
        refresh_token: Token yenileme icin refresh token (opsiyonel)
        token_type: Token tipi (genellikle "Bearer")
        expires_in: Token gecerlilik suresi (saniye)
        scope: Verilen yetkiler
        id_token: OpenID Connect ID token (opsiyonel)
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str | None = None
    id_token: str | None = None


@dataclass
class OAuth2UserInfo:
    """OAuth2 kullanici bilgileri.

    Provider'dan alinan kullanici profil bilgilerini icerir.

    Attributes:
        provider: OAuth2 provider adi
        provider_user_id: Provider'daki kullanici ID'si
        email: Kullanici e-posta adresi
        email_verified: E-posta dogrulama durumu
        name: Tam ad
        given_name: Ad
        family_name: Soyad
        picture: Profil resmi URL'i
        locale: Dil/bolge tercihi
    """

    provider: str
    provider_user_id: str
    email: str
    email_verified: bool = False
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None


@dataclass
class OAuth2State:
    """OAuth2 state bilgileri.

    CSRF koruması icin state parametresi ve metadata.

    Attributes:
        state: Kriptografik olarak guvenli state token
        provider: OAuth2 provider adi
        created_at: State olusturulma zamani
        expires_at: State gecerlilik suresi sonu
        redirect_uri: Callback sonrasi yonlendirilecek URL (opsiyonel)
    """

    state: str
    provider: str
    created_at: datetime
    expires_at: datetime
    redirect_uri: str | None = None


# ==================== EXCEPTIONS ====================


class OAuth2Exception(Exception):
    """OAuth2 islemlerinde olusan hatalar icin base exception.

    Attributes:
        error_code: OAuth2Error enum degeri
        message: Hata aciklamasi
        details: Ek hata detaylari (opsiyonel)
    """

    def __init__(
        self,
        error_code: OAuth2Error,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        """OAuth2Exception olusturur.

        Args:
            error_code: Hata kodu
            message: Hata mesaji
            details: Ek detaylar
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


# ==================== PROVIDER CONFIGURATIONS ====================

# Google OAuth2 Configuration
# Dokumanasyon: https://developers.google.com/identity/protocols/oauth2
GOOGLE_CONFIG = OAuth2ProviderConfig(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    redirect_uri=os.environ.get(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/auth/oauth2/google/callback",
    ),
    authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
    scopes=[
        "openid",
        "email",
        "profile",
    ],
)

# Provider configurations mapping
PROVIDER_CONFIGS: dict[str, OAuth2ProviderConfig] = {
    OAuth2Provider.GOOGLE.value: GOOGLE_CONFIG,
}


# ==================== OAUTH2 SERVICE ====================


class OAuth2Service:
    """OAuth2 Authentication Service.

    Sosyal giris (Google OAuth2) islemlerini yoneten servis sinifi.
    Authorization Code Grant flow'u kullanir ve CSRF korumasini saglar.

    Features:
        - Authorization URL olusturma (state ile CSRF korumasi)
        - Authorization code'u token'a cevirme
        - Provider'dan kullanici bilgisi alma
        - Mevcut hesaba OAuth hesabi baglama veya yeni hesap olusturma
        - State token yonetimi ve dogrulama

    Attributes:
        STATE_EXPIRY_MINUTES: State token gecerlilik suresi (varsayilan 10 dakika)

    Example:
        >>> service = OAuth2Service()
        >>> url, state = await service.get_authorization_url("google")
        >>> # Kullanici url'e yonlendirilir, callback'te code gelir
        >>> tokens = await service.exchange_code("google", code, state)
        >>> user_info = await service.get_user_info("google", tokens["access_token"])
    """

    STATE_EXPIRY_MINUTES = 10

    def __init__(self) -> None:
        """OAuth2Service instance'i olusturur.

        In-memory state store kullanir. Production'da Redis kullanilmalidir.
        """
        # In-memory state store (production'da Redis kullanilmali)
        self._states: dict[str, OAuth2State] = {}

        # HTTP client for API calls
        self._http_client: httpx.AsyncClient | None = None

        logger.info("OAuth2Service baslatildi")

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP client instance'i dondurur.

        Lazy initialization ile HTTP client olusturur.

        Returns:
            httpx.AsyncClient: HTTP client instance
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._http_client

    async def close(self) -> None:
        """HTTP client'i kapatir.

        Servis kapatilirken cagrilmalidir.
        """
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _get_provider_config(self, provider: str) -> OAuth2ProviderConfig:
        """Provider konfigurasyonunu dondurur.

        Args:
            provider: Provider adi ("google")

        Returns:
            OAuth2ProviderConfig: Provider konfigurasyonu

        Raises:
            OAuth2Exception: Provider desteklenmiyorsa
        """
        provider_lower = provider.lower()
        if provider_lower not in PROVIDER_CONFIGS:
            raise OAuth2Exception(
                error_code=OAuth2Error.PROVIDER_NOT_SUPPORTED,
                message=f"OAuth2 provider desteklenmiyor: {provider}",
                details={"provider": provider, "supported": list(PROVIDER_CONFIGS.keys())},
            )
        return PROVIDER_CONFIGS[provider_lower]

    def _generate_state(self) -> str:
        """Kriptografik olarak guvenli state token olusturur.

        Returns:
            str: 32 byte'lik URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(32)

    def _store_state(
        self,
        state: str,
        provider: str,
        redirect_uri: str | None = None,
    ) -> OAuth2State:
        """State token'i saklar.

        Args:
            state: State token
            provider: Provider adi
            redirect_uri: Callback sonrasi yonlendirilecek URL

        Returns:
            OAuth2State: Saklanan state bilgisi
        """
        now = datetime.now(UTC)
        state_obj = OAuth2State(
            state=state,
            provider=provider,
            created_at=now,
            expires_at=now + timedelta(minutes=self.STATE_EXPIRY_MINUTES),
            redirect_uri=redirect_uri,
        )
        self._states[state] = state_obj

        # Eski state'leri temizle (10000'den fazla birikirse)
        if len(self._states) > 10000:
            self._cleanup_expired_states()

        return state_obj

    def _verify_state(self, state: str, provider: str) -> OAuth2State:
        """State token'i dogrular ve kaldirir.

        Args:
            state: Dogrulanacak state token
            provider: Beklenen provider adi

        Returns:
            OAuth2State: Dogrulanan state bilgisi

        Raises:
            OAuth2Exception: State gecersiz veya suresi dolmussa
        """
        state_obj = self._states.pop(state, None)

        if state_obj is None:
            logger.warning(
                "OAuth2 state dogrulanamadi: state bulunamadi",
                extra={"state_hash": hashlib.sha256(state.encode()).hexdigest()[:8]},
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.INVALID_STATE,
                message="Gecersiz state parametresi. CSRF saldirisi olabilir.",
                details={"reason": "state_not_found"},
            )

        now = datetime.now(UTC)
        if now > state_obj.expires_at:
            logger.warning(
                "OAuth2 state suresi dolmus",
                extra={
                    "state_hash": hashlib.sha256(state.encode()).hexdigest()[:8],
                    "expired_at": state_obj.expires_at.isoformat(),
                },
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.INVALID_STATE,
                message="State parametresinin suresi dolmus. Lutfen tekrar deneyin.",
                details={"reason": "state_expired"},
            )

        if state_obj.provider != provider.lower():
            logger.warning(
                "OAuth2 state provider uyusmazligi",
                extra={
                    "expected": state_obj.provider,
                    "received": provider,
                },
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.INVALID_STATE,
                message="State parametresi farkli bir provider icin olusturulmus.",
                details={"reason": "provider_mismatch"},
            )

        return state_obj

    def _cleanup_expired_states(self) -> int:
        """Suresi dolmus state'leri temizler.

        Returns:
            int: Temizlenen state sayisi
        """
        now = datetime.now(UTC)
        expired = [
            state for state, obj in self._states.items() if now > obj.expires_at
        ]
        for state in expired:
            del self._states[state]

        if expired:
            logger.info(f"Suresi dolmus {len(expired)} state temizlendi")

        return len(expired)

    async def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        """OAuth2 authorization URL'i olusturur.

        REQ-2.1: Authorization code grant flow
        REQ-2.3: State parameter ile CSRF koruması

        Args:
            provider: OAuth2 provider adi ("google")
            redirect_uri: Callback sonrasi yonlendirilecek frontend URL (opsiyonel)

        Returns:
            tuple[str, str]: (authorization_url, state) tuple'i

        Raises:
            OAuth2Exception: Provider desteklenmiyorsa

        Example:
            >>> url, state = await service.get_authorization_url("google")
            >>> # state'i session'da sakla
            >>> # kullaniciyi url'e yonlendir
        """
        config = self._get_provider_config(provider)

        # Client ID kontrolu
        if not config.client_id:
            raise OAuth2Exception(
                error_code=OAuth2Error.PROVIDER_NOT_SUPPORTED,
                message=f"{provider} OAuth2 yapilandirilmamis. GOOGLE_CLIENT_ID ayarlayin.",
                details={"provider": provider},
            )

        # State token olustur (CSRF koruması - REQ-2.3)
        state = self._generate_state()
        self._store_state(state, provider, redirect_uri)

        # Authorization URL parametreleri
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state,
            "access_type": "offline",  # Refresh token almak icin
            "prompt": "consent",  # Her seferinde consent ekrani goster
        }

        # URL olustur
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{config.authorization_url}?{query_string}"

        logger.info(
            "OAuth2 authorization URL olusturuldu",
            extra={
                "provider": provider,
                "state_hash": hashlib.sha256(state.encode()).hexdigest()[:8],
            },
        )

        return authorization_url, state

    async def exchange_code(
        self,
        provider: str,
        code: str,
        state: str,
    ) -> dict[str, Any]:
        """Authorization code'u access token'a cevirir.

        REQ-2.3: State parameter dogrulama (CSRF koruması)
        REQ-2.4: Access + Refresh token exchange

        Args:
            provider: OAuth2 provider adi
            code: Authorization code
            state: State token (CSRF dogrulama icin)

        Returns:
            dict: Token bilgileri
                - access_token: API erisim token'i
                - refresh_token: Token yenileme token'i (opsiyonel)
                - token_type: Token tipi ("Bearer")
                - expires_in: Gecerlilik suresi (saniye)
                - scope: Verilen yetkiler
                - id_token: OpenID Connect ID token (opsiyonel)

        Raises:
            OAuth2Exception: State gecersiz veya token exchange basarisizsa

        Example:
            >>> tokens = await service.exchange_code("google", code, state)
            >>> access_token = tokens["access_token"]
        """
        # State dogrula (CSRF koruması - REQ-2.3)
        state_obj = self._verify_state(state, provider)

        config = self._get_provider_config(provider)
        client = await self._get_http_client()

        # Token exchange request
        token_data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": config.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            response = await client.post(
                config.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                logger.error(
                    "OAuth2 token exchange basarisiz",
                    extra={
                        "provider": provider,
                        "status_code": response.status_code,
                        "error": error_data.get("error", "unknown"),
                    },
                )
                raise OAuth2Exception(
                    error_code=OAuth2Error.TOKEN_EXCHANGE_FAILED,
                    message="Token exchange basarisiz oldu.",
                    details={
                        "status_code": response.status_code,
                        "error": error_data.get("error"),
                        "error_description": error_data.get("error_description"),
                    },
                )

            tokens = response.json()

            logger.info(
                "OAuth2 token exchange basarili",
                extra={
                    "provider": provider,
                    "has_refresh_token": "refresh_token" in tokens,
                    "expires_in": tokens.get("expires_in"),
                },
            )

            # State'teki redirect_uri'yi de dondur
            tokens["_redirect_uri"] = state_obj.redirect_uri

            return tokens

        except httpx.HTTPError as e:
            logger.error(
                f"OAuth2 token exchange HTTP hatasi: {e}",
                extra={"provider": provider},
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.TOKEN_EXCHANGE_FAILED,
                message="Token exchange sirasinda baglanti hatasi olustu.",
                details={"error": str(e)},
            )

    async def get_user_info(
        self,
        provider: str,
        access_token: str,
    ) -> OAuth2UserInfo:
        """Provider'dan kullanici bilgilerini alir.

        REQ-2.5: Provider'dan kullanici bilgisi fetch

        Args:
            provider: OAuth2 provider adi
            access_token: API erisim token'i

        Returns:
            OAuth2UserInfo: Kullanici profil bilgileri

        Raises:
            OAuth2Exception: Kullanici bilgisi alinamazsa

        Example:
            >>> user_info = await service.get_user_info("google", access_token)
            >>> print(user_info.email)
        """
        config = self._get_provider_config(provider)
        client = await self._get_http_client()

        try:
            response = await client.get(
                config.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                logger.error(
                    "OAuth2 user info alma basarisiz",
                    extra={
                        "provider": provider,
                        "status_code": response.status_code,
                    },
                )
                raise OAuth2Exception(
                    error_code=OAuth2Error.USER_INFO_FAILED,
                    message="Kullanici bilgisi alinamadi.",
                    details={
                        "status_code": response.status_code,
                        "error": error_data.get("error"),
                    },
                )

            data = response.json()

            # Google user info response mapping
            user_info = OAuth2UserInfo(
                provider=provider,
                provider_user_id=data.get("sub", ""),
                email=data.get("email", ""),
                email_verified=data.get("email_verified", False),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
                locale=data.get("locale"),
            )

            logger.info(
                "OAuth2 user info alindi",
                extra={
                    "provider": provider,
                    "email": user_info.email,
                    "email_verified": user_info.email_verified,
                },
            )

            return user_info

        except httpx.HTTPError as e:
            logger.error(
                f"OAuth2 user info HTTP hatasi: {e}",
                extra={"provider": provider},
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.USER_INFO_FAILED,
                message="Kullanici bilgisi alinirken baglanti hatasi olustu.",
                details={"error": str(e)},
            )

    async def link_or_create_user(
        self,
        provider: str,
        user_info: OAuth2UserInfo,
        db: AsyncSession,
    ) -> Any:  # Returns User model
        """OAuth hesabini mevcut kullaniciya baglar veya yeni kullanici olusturur.

        REQ-2.6: Email-based account linking/merge

        Islem mantigi:
        1. Email ile mevcut kullanici ara
        2. Kullanici varsa OAuth hesabini bagla
        3. Kullanici yoksa yeni hesap olustur

        Args:
            provider: OAuth2 provider adi
            user_info: Provider'dan alinan kullanici bilgileri
            db: AsyncSession database baglantisi

        Returns:
            User: Baglanan veya olusturulan kullanici

        Raises:
            OAuth2Exception: Hesap baglama/olusturma basarisizsa

        Example:
            >>> user = await service.link_or_create_user("google", user_info, db)
            >>> print(f"Hos geldin, {user.first_name}!")
        """
        # Import here to avoid circular imports
        from backend.models.database import User, UserRole

        try:
            # Email ile mevcut kullanici ara
            result = await db.execute(
                select(User).where(User.email == user_info.email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Mevcut kullaniciya OAuth hesabi bagla
                logger.info(
                    "OAuth hesabi mevcut kullaniciya baglaniyor",
                    extra={
                        "user_id": existing_user.id,
                        "provider": provider,
                        "email": user_info.email,
                    },
                )

                # Son giris zamanini guncelle
                existing_user.last_login = datetime.now(UTC)

                # Email verified degilse ve OAuth'tan verified geldiyse guncelle
                if not existing_user.is_verified and user_info.email_verified:
                    existing_user.is_verified = True
                    logger.info(
                        "Kullanici email dogrulandi (OAuth)",
                        extra={"user_id": existing_user.id},
                    )

                await db.commit()
                await db.refresh(existing_user)

                return existing_user

            # Yeni kullanici olustur
            logger.info(
                "OAuth ile yeni kullanici olusturuluyor",
                extra={
                    "provider": provider,
                    "email": user_info.email,
                },
            )

            # Username olustur (email'in @ oncesi kismi + random suffix)
            email_prefix = user_info.email.split("@")[0]
            random_suffix = secrets.token_hex(4)
            username = f"{email_prefix}_{random_suffix}"

            # Isim bilgilerini ayarla
            first_name = user_info.given_name or user_info.name or email_prefix
            family_name = user_info.family_name or ""

            # Yeni kullanici olustur
            new_user = User(
                id=str(uuid.uuid4()),
                email=user_info.email,
                username=username,
                password_hash="",  # OAuth kullanicisi, sifre yok
                first_name=first_name,
                last_name=family_name,
                role=UserRole.STUDENT,  # Varsayilan rol: ogrenci
                is_active=True,
                is_verified=user_info.email_verified,
                last_login=datetime.now(UTC),
            )

            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "Yeni OAuth kullanicisi olusturuldu",
                extra={
                    "user_id": new_user.id,
                    "provider": provider,
                    "email": user_info.email,
                },
            )

            return new_user

        except Exception as e:
            await db.rollback()
            logger.error(
                f"OAuth hesap baglama/olusturma hatasi: {e}",
                extra={
                    "provider": provider,
                    "email": user_info.email,
                },
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.ACCOUNT_LINK_FAILED,
                message="Hesap baglama veya olusturma islemi basarisiz oldu.",
                details={"error": str(e)},
            )

    async def refresh_access_token(
        self,
        provider: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Refresh token kullanarak yeni access token alir.

        Args:
            provider: OAuth2 provider adi
            refresh_token: Refresh token

        Returns:
            dict: Yeni token bilgileri

        Raises:
            OAuth2Exception: Token yenileme basarisizsa
        """
        config = self._get_provider_config(provider)
        client = await self._get_http_client()

        token_data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = await client.post(
                config.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                logger.error(
                    "OAuth2 token refresh basarisiz",
                    extra={
                        "provider": provider,
                        "status_code": response.status_code,
                    },
                )
                raise OAuth2Exception(
                    error_code=OAuth2Error.TOKEN_EXCHANGE_FAILED,
                    message="Token yenileme basarisiz oldu.",
                    details={
                        "status_code": response.status_code,
                        "error": error_data.get("error"),
                    },
                )

            tokens = response.json()

            logger.info(
                "OAuth2 token refresh basarili",
                extra={
                    "provider": provider,
                    "expires_in": tokens.get("expires_in"),
                },
            )

            return tokens

        except httpx.HTTPError as e:
            logger.error(
                f"OAuth2 token refresh HTTP hatasi: {e}",
                extra={"provider": provider},
            )
            raise OAuth2Exception(
                error_code=OAuth2Error.TOKEN_EXCHANGE_FAILED,
                message="Token yenileme sirasinda baglanti hatasi olustu.",
                details={"error": str(e)},
            )

    def get_stats(self) -> dict[str, Any]:
        """OAuth2 servis istatistiklerini dondurur.

        Returns:
            dict: Servis istatistikleri
                - active_states: Aktif state token sayisi
                - expired_states: Suresi dolmus state sayisi
                - supported_providers: Desteklenen provider listesi
        """
        now = datetime.now(UTC)
        active = sum(1 for s in self._states.values() if now <= s.expires_at)
        expired = len(self._states) - active

        return {
            "active_states": active,
            "expired_states": expired,
            "total_states": len(self._states),
            "supported_providers": list(PROVIDER_CONFIGS.keys()),
            "state_expiry_minutes": self.STATE_EXPIRY_MINUTES,
        }


# ==================== GLOBAL SERVICE INSTANCE ====================

_oauth2_service: OAuth2Service | None = None


def get_oauth2_service() -> OAuth2Service:
    """Global OAuth2Service instance'ini dondurur.

    Singleton pattern ile tek bir OAuth2Service instance'i kullanilir.

    Returns:
        OAuth2Service: Global servis instance'i

    Example:
        >>> oauth2_service = get_oauth2_service()
        >>> url, state = await oauth2_service.get_authorization_url("google")
    """
    global _oauth2_service
    if _oauth2_service is None:
        _oauth2_service = OAuth2Service()
    return _oauth2_service


async def shutdown_oauth2_service() -> None:
    """OAuth2 servisini kapatir.

    Uygulama kapanirken HTTP client'i temizlemek icin cagrilmalidir.
    """
    global _oauth2_service
    if _oauth2_service is not None:
        await _oauth2_service.close()
        _oauth2_service = None
        logger.info("OAuth2Service kapatildi")
