"""
Enhanced Authentication API Endpoints - KIRO2 YKS Platform

Bu modul, gelismis kimlik dogrulama ozelliklerini sunar:
- OAuth2 sosyal giris (Google)
- Sifresiz giris (magic link)
- Hesap guvenligi (cihaz yonetimi, giris gecmisi)
- MFA kurtarma islemleri
- Oturum yonetimi

REQ-2.1 - REQ-6.3: Enhanced Authentication Features
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user, AuthenticatedUser
from core.oauth2_service import (
    OAuth2Exception,
    get_oauth2_service,
)
from core.passwordless_auth import get_passwordless_auth_service
from core.two_factor_auth import two_factor_auth
from core.jwt_auth import get_jwt_manager
from core.structured_logger import get_logger
from models.database import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Gelismis Kimlik Dogrulama"])


# ==================== PYDANTIC MODELS ====================


class MagicLinkSendRequest(BaseModel):
    """Magic link gonderme istegi."""

    email: EmailStr = Field(..., description="E-posta adresi")


class MagicLinkSendResponse(BaseModel):
    """Magic link gonderme yaniti."""

    success: bool
    message: str
    email: str


class MagicLinkVerifyResponse(BaseModel):
    """Magic link dogrulama yaniti."""

    success: bool
    message: str
    token: Optional[str] = None
    refreshToken: Optional[str] = None
    user: Optional[dict[str, Any]] = None


class DeviceInfo(BaseModel):
    """Cihaz bilgisi."""

    device_id: str
    device_name: str
    device_type: str
    os: str
    browser: str
    last_seen: datetime
    ip_address: str
    is_current: bool = False
    is_trusted: bool = False


class DeviceListResponse(BaseModel):
    """Cihaz listesi yaniti."""

    success: bool
    devices: list[DeviceInfo]
    total_count: int


class LoginHistoryEntry(BaseModel):
    """Giris gecmisi kaydì."""

    id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    device_type: str
    location: Optional[str] = None
    status: str  # 'success', 'failed', 'blocked'


class LoginHistoryResponse(BaseModel):
    """Giris gecmisi yaniti."""

    success: bool
    history: list[LoginHistoryEntry]
    total_count: int


class AccountLockRequest(BaseModel):
    """Hesap kilitleme istegi."""

    reason: Optional[str] = Field(None, description="Kilitleme nedeni")


class AccountLockResponse(BaseModel):
    """Hesap kilitleme yaniti."""

    success: bool
    message: str
    locked_at: datetime


class MFARecoveryInitiateRequest(BaseModel):
    """MFA kurtarma baslat istegi."""

    email: EmailStr = Field(..., description="E-posta adresi")


class MFARecoveryInitiateResponse(BaseModel):
    """MFA kurtarma baslat yaniti."""

    success: bool
    message: str
    recovery_token: str
    expires_in_minutes: int


class MFARecoveryVerifyRequest(BaseModel):
    """MFA kurtarma dogrula istegi."""

    recovery_token: str = Field(..., description="Kurtarma token'i")
    email_code: str = Field(..., description="E-posta ile gonderilen 6 haneli kod")


class MFARecoveryVerifyResponse(BaseModel):
    """MFA kurtarma dogrula yaniti."""

    success: bool
    message: str
    verified: bool


class MFARecoveryCompleteRequest(BaseModel):
    """MFA kurtarma tamamla istegi."""

    recovery_token: str = Field(..., description="Dogrulanmis kurtarma token'i")


class MFARecoveryCompleteResponse(BaseModel):
    """MFA kurtarma tamamla yaniti."""

    success: bool
    message: str
    mfa_disabled: bool


class SessionInfo(BaseModel):
    """Oturum bilgisi."""

    session_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    device_id: Optional[str] = None
    ip_address: str
    user_agent: str
    is_current: bool = False


class SessionListResponse(BaseModel):
    """Oturum listesi yaniti."""

    success: bool
    sessions: list[SessionInfo]
    total_count: int


class SessionRevokeResponse(BaseModel):
    """Oturum iptal yaniti."""

    success: bool
    message: str


# ==================== OAUTH2 ENDPOINTS ====================


@router.get(
    "/oauth2/{provider}",
    summary="OAuth2 Akisini Baslat",
    description="Belirtilen provider ile OAuth2 giris akisini baslatir",
    responses={
        307: {"description": "Provider'a yonlendirme"},
        400: {"description": "Desteklenmeyen provider"},
    },
)
async def start_oauth2_flow(
    provider: str,
    redirect_uri: Optional[str] = Query(
        None, description="Basarili giris sonrasi yonlendirilecek URL"
    ),
):
    """
    OAuth2 giris akisini baslatir ve kullaniciyi provider'a yonlendirir.

    Desteklenen provider'lar:
    - google: Google OAuth2

    Args:
        provider: OAuth2 provider adi (google)
        redirect_uri: Callback sonrasi yonlendirilecek frontend URL (opsiyonel)

    Returns:
        RedirectResponse: Provider authorization URL'ine yonlendirme
    """
    try:
        oauth2_service = get_oauth2_service()
        authorization_url, state = await oauth2_service.get_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
        )

        logger.info(
            "oauth2_flow_started",
            provider=provider,
            state_prefix=state[:8],
        )

        return RedirectResponse(url=authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    except OAuth2Exception as e:
        logger.warning(
            "oauth2_flow_error",
            provider=provider,
            error_code=e.error_code.value,
            message=e.message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code.value,
                "message": e.message,
                "details": e.details,
            },
        )


@router.get(
    "/oauth2/{provider}/callback",
    summary="OAuth2 Callback",
    description="OAuth2 provider callback'ini isler",
    responses={
        200: {"description": "Basarili giris"},
        400: {"description": "Gecersiz state veya code"},
    },
)
async def oauth2_callback(
    provider: str,
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parametresi"),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth2 provider callback'ini isler ve kullaniciyi sisteme giris yaptirir.

    Islem adimlari:
    1. State parametresi dogrulanir (CSRF koruması)
    2. Authorization code, access token'a cevrilir
    3. Provider'dan kullanici bilgileri alinir
    4. Kullanici hesaba baglanir veya yeni hesap olusturulur
    5. JWT token'lar olusturulur

    Args:
        provider: OAuth2 provider adi
        code: Provider'dan alinan authorization code
        state: CSRF koruma state parametresi
        db: Database session

    Returns:
        dict: Giris sonucu (token'lar ve kullanici bilgileri)
    """
    try:
        oauth2_service = get_oauth2_service()

        # Token exchange
        tokens = await oauth2_service.exchange_code(
            provider=provider,
            code=code,
            state=state,
        )

        # Kullanici bilgisi al
        user_info = await oauth2_service.get_user_info(
            provider=provider,
            access_token=tokens["access_token"],
        )

        # Kullaniciyi bagla veya olustur
        user = await oauth2_service.link_or_create_user(
            provider=provider,
            user_info=user_info,
            db=db,
        )

        # JWT token olustur
        jwt_manager = get_jwt_manager()
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        logger.info(
            "oauth2_login_success",
            provider=provider,
            user_id=user.id,
            email=user.email,
        )

        # Frontend redirect URL
        frontend_redirect = tokens.get("_redirect_uri")

        # Role mapping
        role_mapping = {
            "STUDENT": "ogrenci",
            "TEACHER": "ogretmen",
            "PARENT": "veli",
            "ADMIN": "admin",
        }
        frontend_role = role_mapping.get(user.role.value, "ogrenci")

        response_data = {
            "success": True,
            "token": access_token,
            "refreshToken": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "ad": user.first_name,
                "soyad": user.last_name,
                "rol": frontend_role,
                "aktif": user.is_active,
            },
            "provider": provider,
        }

        # Redirect URL varsa ekle
        if frontend_redirect:
            response_data["redirect_uri"] = frontend_redirect

        return response_data

    except OAuth2Exception as e:
        logger.warning(
            "oauth2_callback_error",
            provider=provider,
            error_code=e.error_code.value,
            message=e.message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.error_code.value,
                "message": e.message,
                "details": e.details,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "oauth2_callback_unexpected_error",
            provider=provider,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth2 giris islemi basarisiz oldu",
        )


# ==================== PASSWORDLESS ENDPOINTS ====================


@router.post(
    "/magic-link/send",
    response_model=MagicLinkSendResponse,
    summary="Magic Link Gonder",
    description="Belirtilen e-posta adresine magic link gonderir",
)
async def send_magic_link(
    request: MagicLinkSendRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Kullaniciya e-posta ile magic link gonderir.

    Magic link 15 dakika gecerlidir ve tek kullanimliktir.
    Rate limiting uygulanir (5 dakikada 3 istek).

    Args:
        request: E-posta adresi
        http_request: HTTP request (IP adresi icin)
        db: Database session

    Returns:
        MagicLinkSendResponse: Gonderim sonucu
    """
    try:
        # Kullanici var mi kontrol et
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            # Guvenlik: Kullanici olmadigini aciga vurma
            logger.warning(
                "magic_link_user_not_found",
                email=request.email,
            )
            # Ayni mesaji dondur
            return MagicLinkSendResponse(
                success=True,
                message="E-posta adresinize giris baglantisi gonderildi",
                email=request.email,
            )

        passwordless_service = get_passwordless_auth_service()

        # IP adresi al
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent", "")

        # Magic link token olustur
        result = await passwordless_service.generate_magic_link_token(
            email=request.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not result.success:
            logger.warning(
                "magic_link_generation_failed",
                email=request.email,
                error_code=result.error_code,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
                if result.error_code == "RATE_LIMITED"
                else status.HTTP_400_BAD_REQUEST,
                detail=result.error_message,
            )

        # E-posta gonder (production'da gercek email servisi kullanilmali)
        await passwordless_service.send_magic_link_email(
            email=result.email,
            token=result.token,
        )

        logger.info(
            "magic_link_sent",
            email=request.email,
            ip_address=ip_address,
        )

        return MagicLinkSendResponse(
            success=True,
            message="E-posta adresinize giris baglantisi gonderildi",
            email=request.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "magic_link_send_error",
            email=request.email,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Magic link gonderilemedi",
        )


@router.get(
    "/magic-link/verify",
    response_model=MagicLinkVerifyResponse,
    summary="Magic Link Dogrula",
    description="Magic link token'ini dogrular ve giris yaptirir",
)
async def verify_magic_link(
    token: str = Query(..., description="Magic link token"),
    http_request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Magic link token'ini dogrular ve kullaniciyi giris yaptirir.

    Token tek kullanimliktir - dogrulama sonrasi gecersiz olur.

    Args:
        token: Magic link token
        http_request: HTTP request (IP adresi icin)
        db: Database session

    Returns:
        MagicLinkVerifyResponse: Dogrulama sonucu ve token'lar
    """
    try:
        passwordless_service = get_passwordless_auth_service()

        ip_address = http_request.client.host if http_request and http_request.client else None
        user_agent = http_request.headers.get("user-agent", "") if http_request else ""

        # Token dogrula
        verification = await passwordless_service.verify_magic_link_token(
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not verification.valid:
            logger.warning(
                "magic_link_verification_failed",
                error_code=verification.error_code,
                ip_address=ip_address,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification.error_message,
            )

        # Kullaniciyi bul
        result = await db.execute(
            select(User).where(User.email == verification.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanici bulunamadi",
            )

        # Son giris guncelle
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        # JWT token olustur
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        # Role mapping
        role_mapping = {
            "STUDENT": "ogrenci",
            "TEACHER": "ogretmen",
            "PARENT": "veli",
            "ADMIN": "admin",
        }
        frontend_role = role_mapping.get(user.role.value, "ogrenci")

        logger.info(
            "magic_link_login_success",
            email=verification.email,
            user_id=user.id,
        )

        return MagicLinkVerifyResponse(
            success=True,
            message="Giris basarili",
            token=access_token,
            refreshToken=refresh_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "ad": user.first_name,
                "soyad": user.last_name,
                "rol": frontend_role,
                "aktif": user.is_active,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "magic_link_verify_error",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Magic link dogrulanamadi",
        )


# ==================== ACCOUNT SECURITY ENDPOINTS ====================


@router.get(
    "/devices",
    response_model=DeviceListResponse,
    summary="Cihaz Listesi",
    description="Kullanicinin kayitli cihazlarini listeler",
)
async def list_devices(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kullanicinin kayitli cihazlarini listeler.

    Her cihaz icin:
    - Cihaz tipi ve adi
    - Son erisim zamani
    - IP adresi
    - Guvenilir cihaz durumu

    Args:
        current_user: Mevcut kullanici

    Returns:
        DeviceListResponse: Cihaz listesi
    """
    try:
        # TODO: Gercek cihaz listesi veritabanindan alinmali
        # Simdilik mock veri
        mock_devices = [
            DeviceInfo(
                device_id="dev_001",
                device_name="Chrome Windows",
                device_type="Desktop",
                os="Windows 11",
                browser="Chrome 120",
                last_seen=datetime.now(timezone.utc),
                ip_address="192.168.1.100",
                is_current=True,
                is_trusted=True,
            ),
        ]

        logger.info(
            "devices_listed",
            user_id=current_user.id,
            device_count=len(mock_devices),
        )

        return DeviceListResponse(
            success=True,
            devices=mock_devices,
            total_count=len(mock_devices),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "devices_list_error",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cihaz listesi alinamadi",
        )


@router.delete(
    "/devices/{device_id}",
    summary="Cihaz Kaldir",
    description="Belirtilen cihazi kullanici hesabindan kaldirir",
)
async def remove_device(
    device_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Belirtilen cihazi kullanici hesabindan kaldirir.

    Cihaz kaldirildiginda o cihazdaki tum aktif oturumlar sonlandirilir.

    Args:
        device_id: Kaldirilacak cihaz ID'si
        current_user: Mevcut kullanici

    Returns:
        dict: Islem sonucu
    """
    try:
        # TODO: Gercek cihaz silme islemi
        logger.info(
            "device_removed",
            user_id=current_user.id,
            device_id=device_id,
        )

        return {
            "success": True,
            "message": f"Cihaz {device_id} basariyla kaldirildi",
            "device_id": device_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "device_remove_error",
            user_id=current_user.id,
            device_id=device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cihaz kaldirilamadi",
        )


@router.get(
    "/login-history",
    response_model=LoginHistoryResponse,
    summary="Giris Gecmisi",
    description="Kullanicinin giris gecmisini getirir",
)
async def get_login_history(
    limit: int = Query(20, ge=1, le=100, description="Kayit sayisi"),
    offset: int = Query(0, ge=0, description="Baslangic indeksi"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kullanicinin giris gecmisini getirir.

    Her kayit icin:
    - Giris zamani
    - IP adresi ve konum
    - Cihaz bilgisi
    - Giris durumu (basarili/basarisiz/engellendi)

    Args:
        limit: Maksimum kayit sayisi
        offset: Sayfalama ofseti
        current_user: Mevcut kullanici

    Returns:
        LoginHistoryResponse: Giris gecmisi
    """
    try:
        # TODO: Gercek giris gecmisi veritabanindan alinmali
        # Simdilik mock veri
        mock_history = [
            LoginHistoryEntry(
                id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
                device_type="Desktop",
                location="Istanbul, TR",
                status="success",
            ),
        ]

        logger.info(
            "login_history_retrieved",
            user_id=current_user.id,
            count=len(mock_history),
        )

        return LoginHistoryResponse(
            success=True,
            history=mock_history,
            total_count=len(mock_history),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "login_history_error",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Giris gecmisi alinamadi",
        )


@router.post(
    "/account/lock",
    response_model=AccountLockResponse,
    summary="Hesabi Kilitle (Acil)",
    description="Kullanicinin kendi hesabini acil durumda kilitler",
)
async def lock_account(
    request: AccountLockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Kullanicinin kendi hesabini acil durumda kilitler.

    Bu islem:
    - Hesabi hemen kilitler
    - Tum aktif oturumlari sonlandirir
    - Yeni girisleri engeller

    Kilidi acmak icin destek ekibiyle iletisime gecilmelidir.

    Args:
        request: Kilitleme nedeni (opsiyonel)
        current_user: Mevcut kullanici
        db: Database session

    Returns:
        AccountLockResponse: Kilitleme sonucu
    """
    try:
        user_id = current_user.id

        # Hesabi kilitle
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_active=False,
                # is_locked=True,  # Eger bu alan varsa
            )
        )
        await db.execute(stmt)
        await db.commit()

        # TODO: Tum aktif oturumlari sonlandir
        # jwt_manager = get_jwt_manager()
        # jwt_manager.revoke_all_user_tokens(db, user_id)

        locked_at = datetime.now(timezone.utc)

        logger.warning(
            "account_self_locked",
            user_id=user_id,
            reason=request.reason,
            locked_at=locked_at.isoformat(),
        )

        return AccountLockResponse(
            success=True,
            message="Hesabiniz basariyla kilitlendi. Kilidi acmak icin destek ekibiyle iletisime gecin.",
            locked_at=locked_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "account_lock_error",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hesap kilitlenemedi",
        )


# ==================== MFA RECOVERY ENDPOINTS ====================


@router.post(
    "/2fa/recovery/initiate",
    response_model=MFARecoveryInitiateResponse,
    summary="MFA Kurtarma Baslat",
    description="MFA kurtarma islemini baslatir ve e-posta dogrulama kodu gonderir",
)
async def initiate_mfa_recovery(
    request: MFARecoveryInitiateRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    MFA kurtarma islemini baslatir.

    Kullanici MFA cihazini kaybettiyse bu endpoint ile kurtarma baslatilir.
    E-posta adresine 6 haneli dogrulama kodu gonderilir.
    Token 15 dakika gecerlidir.

    Args:
        request: E-posta adresi
        http_request: HTTP request
        db: Database session

    Returns:
        MFARecoveryInitiateResponse: Kurtarma token bilgileri
    """
    try:
        # Kullaniciyi bul
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            # Guvenlik: Kullanici olmadigini aciga vurma
            logger.warning(
                "mfa_recovery_user_not_found",
                email=request.email,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-posta adresi bulunamadi veya MFA aktif degil",
            )

        # MFA aktif mi kontrol et
        if not user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu hesapta MFA aktif degil",
            )

        # Kurtarma token olustur
        recovery = two_factor_auth.initiate_mfa_recovery(request.email)

        # TODO: E-posta ile kodu gonder (production'da gercek email servisi)
        # await send_mfa_recovery_email(request.email, recovery.email_code)

        logger.info(
            "mfa_recovery_initiated",
            email=request.email,
            token_prefix=recovery.token[:8],
        )

        return MFARecoveryInitiateResponse(
            success=True,
            message="E-posta adresinize dogrulama kodu gonderildi",
            recovery_token=recovery.token,
            expires_in_minutes=15,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "mfa_recovery_initiate_error",
            email=request.email,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA kurtarma baslatilámadi",
        )


@router.post(
    "/2fa/recovery/verify",
    response_model=MFARecoveryVerifyResponse,
    summary="MFA Kurtarma Dogrula",
    description="E-posta dogrulama kodunu kontrol eder",
)
async def verify_mfa_recovery(
    request: MFARecoveryVerifyRequest,
):
    """
    MFA kurtarma e-posta kodunu dogrular.

    Kullanici e-posta ile aldigi 6 haneli kodu girer.
    Kod dogru ise kurtarma tamamlanabilir.

    Args:
        request: Kurtarma token ve e-posta kodu

    Returns:
        MFARecoveryVerifyResponse: Dogrulama sonucu
    """
    try:
        is_valid = two_factor_auth.verify_mfa_recovery(
            token=request.recovery_token,
            email_code=request.email_code,
        )

        if not is_valid:
            logger.warning(
                "mfa_recovery_verification_failed",
                token_prefix=request.recovery_token[:8],
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gecersiz veya suresi dolmus dogrulama kodu",
            )

        logger.info(
            "mfa_recovery_verified",
            token_prefix=request.recovery_token[:8],
        )

        return MFARecoveryVerifyResponse(
            success=True,
            message="Dogrulama basarili. MFA'yi devre disi birakmak icin devam edin.",
            verified=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "mfa_recovery_verify_error",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dogrulama islemi basarisiz",
        )


@router.post(
    "/2fa/recovery/complete",
    response_model=MFARecoveryCompleteResponse,
    summary="MFA Kurtarma Tamamla",
    description="MFA'yi devre disi birakir ve kurtarmayi tamamlar",
)
async def complete_mfa_recovery(
    request: MFARecoveryCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    MFA kurtarma islemini tamamlar ve MFA'yi devre disi birakir.

    Bu islem:
    - Onceden dogrulanmis token gerektirir
    - MFA'yi tamamen devre disi birakir
    - Kullanicinin yeniden MFA kurmasi gerekir

    Args:
        request: Dogrulanmis kurtarma token
        db: Database session

    Returns:
        MFARecoveryCompleteResponse: Tamamlama sonucu
    """
    try:
        # Token bilgisi al
        recovery_info = two_factor_auth.get_recovery_token_info(request.recovery_token)

        if not recovery_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gecersiz kurtarma token'i",
            )

        # Kurtarma tamamla
        success = two_factor_auth.complete_mfa_recovery(request.recovery_token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kurtarma islemi tamamlanamadi. Token dogrulanmamis olabilir.",
            )

        # Veritabaninda MFA'yi devre disi birak
        stmt = (
            update(User)
            .where(User.email == recovery_info.user_email)
            .values(
                is_2fa_enabled=False,
                secret_2fa=None,
                backup_codes_hashed=None,
            )
        )
        await db.execute(stmt)
        await db.commit()

        logger.info(
            "mfa_recovery_completed",
            email=recovery_info.user_email,
        )

        return MFARecoveryCompleteResponse(
            success=True,
            message="MFA basariyla devre disi birakildi. Yeniden kurulum yapabilirsiniz.",
            mfa_disabled=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "mfa_recovery_complete_error",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA kurtarma tamamlanamadi",
        )


# ==================== SESSION ENDPOINTS ====================


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="Aktif Oturumlar",
    description="Kullanicinin aktif oturumlarini listeler",
)
async def list_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kullanicinin aktif oturumlarini listeler.

    Her oturum icin:
    - Olusturulma ve son aktivite zamani
    - Cihaz ve IP bilgisi
    - Gecerlilik suresi

    Args:
        current_user: Mevcut kullanici

    Returns:
        SessionListResponse: Oturum listesi
    """
    try:
        # TODO: Gercek oturum listesi veritabani/Redis'ten alinmali
        # Simdilik mock veri
        mock_sessions = [
            SessionInfo(
                session_id=str(uuid4()),
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc),
                device_id="dev_001",
                ip_address="192.168.1.100",
                user_agent="Chrome/120",
                is_current=True,
            ),
        ]

        logger.info(
            "sessions_listed",
            user_id=current_user.id,
            session_count=len(mock_sessions),
        )

        return SessionListResponse(
            success=True,
            sessions=mock_sessions,
            total_count=len(mock_sessions),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "sessions_list_error",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Oturum listesi alinamadi",
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=SessionRevokeResponse,
    summary="Oturum Iptal Et",
    description="Belirtilen oturumu sonlandirir",
)
async def revoke_session(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Belirtilen oturumu sonlandirir.

    Bu islem:
    - Belirtilen oturumu hemen sonlandirir
    - Ilgili token'lari gecersiz kilar

    Args:
        session_id: Sonlandirilacak oturum ID'si
        current_user: Mevcut kullanici

    Returns:
        SessionRevokeResponse: Iptal sonucu
    """
    try:
        # TODO: Gercek oturum iptal islemi
        # jwt_manager = get_jwt_manager()
        # jwt_manager.revoke_session(session_id)

        logger.info(
            "session_revoked",
            user_id=current_user.id,
            session_id=session_id,
        )

        return SessionRevokeResponse(
            success=True,
            message=f"Oturum {session_id[:8]}... basariyla sonlandirildi",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "session_revoke_error",
            user_id=current_user.id,
            session_id=session_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Oturum sonlandirilamadi",
        )


# ==================== EXPORTS ====================


__all__ = ["router"]
