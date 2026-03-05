"""
Kimlik doğrulama API endpoint'leri (Task 48.4: Enhanced with Refresh Token)
SECURITY FIX: Authorization checks added to prevent IDOR attacks
"""
import logging
import secrets
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.authorization import require_student_owner_or_privileged
from core.config import settings as app_settings
from core.dependencies import JWT_ALGORITHM, JWT_SECRET, get_db
from core.jwt_auth import UserRole as JWTUserRole
from core.jwt_auth import get_jwt_manager
from models import (
    Kullanici,
    KullaniciGiris,
    KullaniciOlustur,
    KullaniciRolu,
    OgrenciProfili,
    OgretmenProfili,
    TokenYaniti,
    VeliProfili,
)
from models.database import User as DBUser
from services.user_service import kullanici_servisi

# Cookie path constants (must match between set and delete)
ACCESS_TOKEN_COOKIE_PATH = "/api"  # noqa: S105
REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth"  # noqa: S105

# Computed once at module import
_IS_DEV = app_settings.environment == "development"
logger = logging.getLogger(__name__)

# P1-1: Simple in-memory rate limiter for login endpoints (5 attempts/minute per IP)

_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_RATE_LIMIT = 10  # max attempts per IP per window
LOGIN_RATE_WINDOW = 60  # seconds


# Only trust X-Forwarded-For from these IPs (reverse proxy / load balancer)
_TRUSTED_PROXIES = {"127.0.0.1", "::1", "172.17.0.1"}  # localhost + Docker default


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For only from trusted proxies."""
    client_host = request.client.host if request.client else "unknown"
    if client_host in _TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return client_host


def _check_login_rate_limit(request: Request) -> None:
    """Raise 429 if IP exceeds failed login rate limit."""
    client_ip = _get_client_ip(request)
    now = time.time()
    # Clean old entries
    _login_attempts[client_ip] = [
        t for t in _login_attempts[client_ip] if now - t < LOGIN_RATE_WINDOW
    ]
    if len(_login_attempts[client_ip]) >= LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                "Cok fazla giris denemesi. "
                f"{LOGIN_RATE_WINDOW} saniye sonra tekrar deneyin."
            ),
        )


def _record_failed_login(request: Request) -> None:
    """Record a failed login attempt for rate limiting."""
    client_ip = _get_client_ip(request)
    _login_attempts[client_ip].append(time.time())

@contextmanager
def _sync_session(db: AsyncSession):
    """Create a sync session from async session for JWT DB operations.

    Raises HTTPException 503 if sync engine is unavailable.
    """
    from sqlalchemy.orm import Session as SyncSession

    if not hasattr(db.bind, "sync_engine"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Veritabanı servisi geçici olarak kullanılamıyor",
        )
    session = SyncSession(bind=db.bind.sync_engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Minimum password length + complexity (consistent across register/change/reset)
_MIN_PASSWORD_LENGTH = 8


def _validate_password(password: str) -> str | None:
    """Return error message if password is too weak, else None."""
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Şifre en az {_MIN_PASSWORD_LENGTH} karakter olmalı"
    if not any(c.isupper() for c in password):
        return "Şifre en az bir büyük harf içermelidir"
    if not any(c.islower() for c in password):
        return "Şifre en az bir küçük harf içermelidir"
    if not any(c.isdigit() for c in password):
        return "Şifre en az bir rakam içermelidir"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return "Şifre en az bir özel karakter içermelidir"
    return None


router = APIRouter(prefix="/api/v1/auth", tags=["Kimlik Doğrulama"])
security = HTTPBearer()


class RefreshTokenRequest(BaseModel):
    """Refresh token request model - accepts refreshToken in body"""
    refreshToken: str | None = None  # noqa: N815 (frontend contract)


async def mevcut_kullanici_getir(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> Kullanici:
    """Mevcut kullanıcıyı token'dan getir (Bearer header veya httpOnly cookie).

    Supports both JWT tokens (from database_authenticate) and legacy in-memory tokens.
    """
    # Try Bearer header first, then httpOnly cookie (P0-1c)
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check blacklist (Redis-backed)
    jwt_mgr = get_jwt_manager()
    if await jwt_mgr.is_blacklisted_async(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token iptal edilmiş",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try JWT decode first (primary auth path after P0-1 fix)

    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Map JWT role to KullaniciRolu
        jwt_role = payload.get("role", "student")
        role_map = {
            "student": KullaniciRolu.OGRENCI,
            "teacher": KullaniciRolu.OGRETMEN,
            "admin": KullaniciRolu.ADMIN,
            "parent": KullaniciRolu.VELI,
            "super_admin": KullaniciRolu.SUPER_ADMIN,
        }
        rol = role_map.get(jwt_role, KullaniciRolu.OGRENCI)

        return Kullanici(
            id=payload.get("sub", ""),
            email=payload.get("email", ""),
            ad_soyad=payload.get("username", payload.get("email", "").split("@")[0]),
            telefon=None,
            aktif=True,
            rol=rol,
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token süresi dolmuş",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError:
        pass  # Not a valid JWT — fall through to legacy token check

    # Fallback: try legacy in-memory token validation
    kullanici = await kullanici_servisi.token_dogrula(token)
    if not kullanici:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return kullanici


async def database_authenticate(
    giris_data: KullaniciGiris, db: AsyncSession,
) -> dict[str, Any]:
    """
    Database-backed authentication function
    Queries the database User table instead of in-memory storage
    """
    # Query user from database by email
    result = await db.execute(select(DBUser).where(DBUser.email == giris_data.email))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise ValueError("Geçersiz e-posta veya şifre")

    # Check if user is active
    if not db_user.is_active:
        raise ValueError("Hesap aktif değil")

    # Verify password using bcrypt (support both 'sifre' and 'password' fields)
    password = giris_data.get_password()
    if not password:
        raise ValueError("Şifre alanı boş olamaz")
    if not pwd_context.verify(password, db_user.password_hash):
        raise ValueError("Geçersiz e-posta veya şifre")

    # Create JWT tokens (P0-1 fix: replaces random tokens)
    jwt_mgr = get_jwt_manager()
    jwt_role = JWTUserRole(db_user.role.value.lower())
    token = jwt_mgr.create_access_token(
        user_id=str(db_user.id),
        email=db_user.email,
        role=jwt_role,
        username=db_user.username,
    )
    refresh_token = jwt_mgr.create_refresh_token(
        user_id=str(db_user.id),
        email=db_user.email,
        role=jwt_role,
    )
    expires_in = jwt_mgr.access_token_expire_minutes * 60

    # Save refresh token to DB for rotation/revocation support
    if hasattr(db.bind, "sync_engine"):
        from sqlalchemy.orm import Session as SyncSession

        sync_db = SyncSession(bind=db.bind.sync_engine)
        try:
            jwt_mgr._save_refresh_token_to_db(
                sync_db, refresh_token, str(db_user.id), None, None,
            )
            sync_db.commit()
        except Exception:
            logger.warning("Failed to persist refresh token to DB")
        finally:
            sync_db.close()

    # Update last login
    db_user.last_login = datetime.now(UTC)
    await db.commit()

    # Map backend role to frontend role format
    role_mapping = {
        "STUDENT": "ogrenci",
        "TEACHER": "ogretmen",
        "PARENT": "veli",
        "ADMIN": "admin",
        "SUPER_ADMIN": "super_admin",
    }
    frontend_role = role_mapping.get(db_user.role.value, "ogrenci")

    # Convert DB user to Pydantic model (for backward compatibility)
    kullanici = Kullanici(
        kullanici_id=db_user.id,
        email=db_user.email,
        ad_soyad=f"{db_user.first_name} {db_user.last_name}",
        telefon=db_user.phone or "",
        aktif=db_user.is_active,
        rol=KullaniciRolu(frontend_role),
        olusturma_tarihi=db_user.created_at,
        son_giris=db_user.last_login,
    )

    # Store token in in-memory service for backward compatibility with token validation
    kullanici_servisi.aktif_tokenlar[token] = {
        "kullanici_id": db_user.id,
        "expires_at": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    kullanici_servisi.kullanicilar[db_user.id] = kullanici

    # Return frontend-compatible response format
    return {
        "success": True,
        "token": token,
        "refreshToken": refresh_token,
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "ad": db_user.first_name,
            "soyad": db_user.last_name,
            "rol": frontend_role,
            "aktif": db_user.is_active,
            "olusturma_tarihi": (
                db_user.created_at.isoformat()
                if db_user.created_at else None
            ),
            "son_giris": (
                db_user.last_login.isoformat()
                if db_user.last_login else None
            ),
            "telefon": db_user.phone or "",
            "profil_resmi": None,  # TODO: Add profile image support
        },
        # Keep backward compatibility fields
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "kullanici": kullanici,
    }


@router.post(
    "/kayit",
    summary="Kullanıcı Kaydı",
    description="Yeni kullanıcı kaydı oluşturur ve başarı mesajı döner",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Kullanıcı başarıyla oluşturuldu",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Kullanıcı kaydı başarıyla oluşturuldu"
                    }
                }
            },
        },
        400: {
            "description": (
                "Geçersiz istek - E-posta zaten kayıtlı"
                " veya doğrulama hatası"
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "email_exists": {
                            "summary": "E-posta zaten kayıtlı",
                            "value": {"detail": "Bu e-posta adresi zaten kayıtlı"},
                        },
                        "weak_password": {
                            "summary": "Zayıf şifre",
                            "value": {
                                "detail": "Şifre en az bir büyük harf içermelidir"
                            },
                        },
                    }
                }
            },
        },
        422: {
            "description": "Doğrulama hatası - Geçersiz veri formatı",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def kullanici_kayit(kullanici_data: KullaniciOlustur) -> dict[str, Any]:
    """
    Yeni kullanıcı kaydı oluştur

    Bu endpoint ile platformda yeni kullanıcı hesabı oluşturabilirsiniz.
    Kullanıcı kayıt işlemi aşağıdaki adımları içerir:

    1. E-posta adresinin benzersiz olduğu kontrol edilir
    2. Şifre güvenlik politikalarına uygunluğu doğrulanır
    3. Kullanıcı hesabı oluşturulur
    4. Şifre güvenli bir şekilde hash'lenir (bcrypt)
    5. Kullanıcı bilgileri döner

    **Şifre Gereksinimleri (SECURITY):**
    - Minimum 8 karakter
    - En az bir büyük harf (A-Z)
    - En az bir küçük harf (a-z)
    - En az bir rakam (0-9)
    - En az bir özel karakter (!@#$%^&* vb.)
    - Yaygın kullanılan şifreler kabul edilmez (password123, 12345678, vb.)

    **Kullanıcı Rolleri:**
    - `ogrenci`: Öğrenci kullanıcı (varsayılan)
    - `veli`: Veli kullanıcı
    - `ogretmen`: Öğretmen kullanıcı
    - `admin`: Sistem yöneticisi
    - `super_admin`: Süper yönetici

    **Request Body:**
    ```json
    {
      "email": "ahmet@example.com",
      "ad_soyad": "Ahmet Yılmaz",
      "sifre": "GucluSifre123!",
      "rol": "ogrenci",
      "telefon": "+905551234567",
      "aktif": true
    }
    ```

    **Başarılı Yanıt (201) - Frontend Format:**
    ```json
    {
      "success": true,
      "message": "Kullanıcı kaydı başarıyla oluşturuldu"
    }
    ```

    **Hata Durumları:**
    - **400**: E-posta zaten kayıtlı veya şifre güvenlik gereksinimlerini karşılamıyor
    - **422**: Geçersiz e-posta formatı veya eksik zorunlu alanlar
    """
    try:
        await kullanici_servisi.kullanici_olustur(kullanici_data)
        # Return frontend-compatible format {success, message}
        return {
            "success": True,
            "message": "Kullanıcı kaydı başarıyla oluşturuldu"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# English alias for registration endpoint
@router.post(
    "/register",
    summary="User Registration (English alias)",
    description="Create a new user account - English endpoint alias for /kayit",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,  # Hide from OpenAPI docs to avoid duplication
)
async def kullanici_kayit_en(kullanici_data: KullaniciOlustur) -> dict[str, Any]:
    """English alias for /kayit - registration."""
    return await kullanici_kayit(kullanici_data)


@router.post(
    "/giris",
    response_model=TokenYaniti,
    summary="Kullanıcı Girişi",
    description="Kullanıcı kimlik doğrulama ve JWT token alma",
    responses={
        200: {
            "description": "Başarılı giriş - JWT access token döner",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "kullanici": {
                            "kullanici_id": "usr_1a2b3c4d5e6f",
                            "email": "ahmet@example.com",
                            "ad_soyad": "Ahmet Yılmaz",
                            "rol": "ogrenci",
                            "aktif": True,
                            "olusturma_tarihi": "2025-11-17T10:30:00Z",
                            "son_giris": "2025-11-17T14:30:00Z",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Kimlik doğrulama hatası - Geçersiz e-posta veya şifre",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_credentials": {
                            "summary": "Geçersiz kimlik bilgileri",
                            "value": {"detail": "Geçersiz e-posta veya şifre"},
                        },
                        "inactive_account": {
                            "summary": "Devre dışı hesap",
                            "value": {"detail": "Hesap devre dışı bırakılmış"},
                        },
                    }
                }
            },
        },
        422: {
            "description": "Doğrulama hatası - Geçersiz e-posta formatı",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def kullanici_giris(
    request: Request,
    giris_data: KullaniciGiris,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Kullanıcı girişi yap ve JWT access token al

    Bu endpoint ile kullanıcı kimlik doğrulaması yapılır ve JWT (JSON Web Token)
    access token alınır. Token, korumalı endpoint'lere erişim için kullanılır.

    **Kimlik Doğrulama İşlemi:**
    1. E-posta adresi ve şifre doğrulanır
    2. Hesap aktiflik durumu kontrol edilir
    3. JWT access token oluşturulur
    4. Son giriş tarihi güncellenir
    5. Token ve kullanıcı bilgileri döner

    **Token Kullanımı:**
    Dönen access token'ı korumalı endpoint'lere erişmek için kullanın:
    ```
    Authorization: Bearer <access_token>
    ```

    **Token Geçerlilik Süresi:**
    - Access token: 1 saat (3600 saniye)
    - Refresh token: 7 gün (refresh endpoint ile yenilenebilir)

    **Request Body:**
    ```json
    {
      "email": "ahmet@example.com",
      "sifre": "GucluSifre123!"
    }
    ```

    **Başarılı Yanıt (200):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 3600,
      "kullanici": {
        "kullanici_id": "usr_1a2b3c4d5e6f",
        "email": "ahmet@example.com",
        "ad_soyad": "Ahmet Yılmaz",
        "rol": "ogrenci",
        "aktif": true,
        "son_giris": "2025-11-17T14:30:00Z"
      }
    }
    ```

    **Hata Durumları:**
    - **401**: Geçersiz e-posta/şifre veya hesap devre dışı
    - **422**: Geçersiz e-posta formatı veya eksik alanlar

    **Güvenlik Notları:**
    - Şifre bcrypt ile hash'lenerek saklanır
    - Rate limiting uygulanır (5 başarısız deneme sonrası geçici blok)
    - HTTPS üzerinden kullanılmalıdır (production)
    """
    _check_login_rate_limit(request)

    try:
        # Use database-backed authentication instead of in-memory service
        return await database_authenticate(giris_data, db)
    except ValueError as e:
        _record_failed_login(request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# English alias for login endpoint
@router.post(
    "/login",
    response_model=TokenYaniti,
    summary="User Login (English alias)",
    description="User authentication and JWT token retrieval",
    include_in_schema=False,
)
async def kullanici_giris_en(
    request: Request,
    giris_data: KullaniciGiris,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """English alias for /giris endpoint - User login"""
    return await kullanici_giris(request, giris_data, db)


# SECURITY FIX #5: httpOnly cookie based login
@router.post(
    "/login/secure",
    summary="Secure Login with httpOnly Cookie",
    description="Login with httpOnly cookie for XSS protection",
)
async def secure_login(
    request: Request,
    giris_data: KullaniciGiris,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    SECURITY FIX #5: Secure login endpoint with httpOnly cookies

    This endpoint sets tokens in httpOnly cookies instead of returning them
    in the response body, preventing XSS attacks from stealing tokens.

    Cookie Settings:
    - httponly: True (cannot be accessed by JavaScript)
    - secure: True (only sent over HTTPS)
    - samesite: 'lax' (CSRF protection)
    - max_age: 24 hours for access token, 7 days for refresh token
    """
    # P1-1: Rate limit check (5 attempts/minute per IP)
    _check_login_rate_limit(request)

    try:
        token_yaniti = await database_authenticate(giris_data, db)

        # Set access token as httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=token_yaniti["token"],
            httponly=True,
            secure=not _IS_DEV,  # HTTP in dev, HTTPS in prod
            samesite="lax",
            max_age=86400,  # 24 hours
            path=ACCESS_TOKEN_COOKIE_PATH,
        )

        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=token_yaniti["refreshToken"],
            httponly=True,
            secure=not _IS_DEV,
            samesite="lax",
            max_age=604800,  # 7 days
            path=REFRESH_TOKEN_COOKIE_PATH,
        )

        # Return user info without tokens in body
        return {
            "success": True,
            "message": "Giriş başarılı",
            "user": token_yaniti["user"]
        }
    except ValueError as e:
        _record_failed_login(request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/logout/secure",
    summary="Secure Logout (Clear Cookies + Blacklist)",
    description="Blacklist JWT tokens and clear httpOnly cookies on logout",
)
async def secure_logout(request: Request, response: Response) -> dict[str, Any]:
    """
    P0-1e: Logout with JWT blacklisting.

    Blacklists access and refresh tokens so they can't be reused,
    then clears httpOnly cookies.
    """
    jwt_mgr = get_jwt_manager()

    # Blacklist access token if present (Redis-backed with in-memory fallback)
    access_token = request.cookies.get("access_token")
    if access_token:
        await jwt_mgr.blacklist_token_async(access_token)

    # Blacklist refresh token if present
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await jwt_mgr.blacklist_token_async(refresh_token)

    response.delete_cookie(key="access_token", path=ACCESS_TOKEN_COOKIE_PATH)
    response.delete_cookie(key="refresh_token", path=REFRESH_TOKEN_COOKIE_PATH)
    return {"success": True, "message": "Çıkış başarılı"}


@router.post(
    "/refresh/secure",
    summary="Secure Token Refresh",
    description="Refresh access token using httpOnly refresh cookie",
)
async def secure_refresh(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    """
    P0-1d: JWT-based token refresh.

    Reads refresh token from httpOnly cookie, validates it via JWTManager,
    and issues a new access+refresh token pair as httpOnly cookies.
    """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token bulunamadı"
        )

    try:
        jwt_mgr = get_jwt_manager()
        new_tokens = await jwt_mgr.refresh_access_token(refresh_token)
    except HTTPException:
        # Clear stale cookies on invalid/expired refresh token
        response.delete_cookie(key="access_token", path=ACCESS_TOKEN_COOKIE_PATH)
        response.delete_cookie(key="refresh_token", path=REFRESH_TOKEN_COOKIE_PATH)
        raise

    # Set new access token as httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=new_tokens.access_token,
        httponly=True,
        secure=not _IS_DEV,
        samesite="lax",
        max_age=new_tokens.expires_in,
        path=ACCESS_TOKEN_COOKIE_PATH,
    )

    # Set new refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_tokens.refresh_token,
        httponly=True,
        secure=not _IS_DEV,
        samesite="lax",
        max_age=new_tokens.refresh_expires_in,
        path=REFRESH_TOKEN_COOKIE_PATH,
    )

    return {"success": True, "message": "Token yenilendi"}


@router.get(
    "/profil",
    response_model=Kullanici,
    summary="Kullanıcı Profili",
    description="Mevcut kullanıcının profil bilgilerini getir",
    responses={
        200: {
            "description": "Kullanıcı profil bilgileri",
            "content": {
                "application/json": {
                    "example": {
                        "kullanici_id": "usr_1a2b3c4d5e6f",
                        "email": "ahmet@example.com",
                        "ad_soyad": "Ahmet Yılmaz",
                        "rol": "ogrenci",
                        "aktif": True,
                        "olusturma_tarihi": "2025-11-17T10:30:00Z",
                        "son_giris": "2025-11-17T14:30:00Z",
                        "telefon": "+905551234567",
                    }
                }
            },
        },
        401: {
            "description": (
                "Kimlik doğrulama hatası"
                " - Geçersiz veya süresi dolmuş token"
            ),
            "content": {
                "application/json": {
                    "example": {"detail": "Geçersiz veya süresi dolmuş token"}
                }
            },
        },
    },
)
async def kullanici_profil(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> Kullanici:
    """
    Mevcut kullanıcının profil bilgilerini getir

    Bu endpoint, JWT token ile kimliği doğrulanan kullanıcının
    profil bilgilerini döner. Token'dan kullanıcı ID'si çözümlenir
    ve ilgili kullanıcı bilgileri getirilir.

    **Kimlik Doğrulama:**
    Bu endpoint korumalıdır. İstek header'ında geçerli bir JWT token gereklidir:
    ```
    Authorization: Bearer <access_token>
    ```

    **Dönen Bilgiler:**
    - Kullanıcı ID (UUID)
    - E-posta adresi
    - Ad soyad
    - Kullanıcı rolü
    - Hesap durumu (aktif/pasif)
    - Kayıt tarihi
    - Son giriş tarihi
    - Telefon numarası (varsa)

    **Başarılı Yanıt (200):**
    ```json
    {
      "kullanici_id": "usr_1a2b3c4d5e6f",
      "email": "ahmet@example.com",
      "ad_soyad": "Ahmet Yılmaz",
      "rol": "ogrenci",
      "aktif": true,
      "olusturma_tarihi": "2025-11-17T10:30:00Z",
      "son_giris": "2025-11-17T14:30:00Z",
      "telefon": "+905551234567"
    }
    ```

    **Hata Durumları:**
    - **401**: Token geçersiz, süresi dolmuş veya eksik

    **Kullanım Örneği:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/auth/profil" \\
      -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    ```
    """
    return mevcut_kullanici


@router.get("/me", summary="Get Current User (English alias)", include_in_schema=False)
async def get_current_user(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> dict[str, Any]:
    """
    Get current user profile - English alias for /profil
    Returns user data wrapped in {user: ...} format for frontend compatibility
    """
    # Convert Kullanici model to frontend-expected format
    # Frontend expects User interface with ad, soyad (split name)
    name_parts = mevcut_kullanici.ad_soyad.split(' ', 1)
    ad = name_parts[0] if len(name_parts) > 0 else ""
    soyad = name_parts[1] if len(name_parts) > 1 else ""

    # Map backend role to frontend role format
    role_mapping = {
        "STUDENT": "ogrenci",
        "TEACHER": "ogretmen",
        "PARENT": "veli",
        "ADMIN": "admin",
        "SUPER_ADMIN": "super_admin",
    }
    frontend_role = role_mapping.get(mevcut_kullanici.rol.value, "ogrenci")

    return {
        "user": {
            "id": mevcut_kullanici.kullanici_id,
            "email": mevcut_kullanici.email,
            "ad": ad,
            "soyad": soyad,
            "rol": frontend_role,
            "aktif": mevcut_kullanici.aktif,
            "olusturma_tarihi": (
                mevcut_kullanici.olusturma_tarihi.isoformat()
                if mevcut_kullanici.olusturma_tarihi else None
            ),
            "son_giris": (
                mevcut_kullanici.son_giris.isoformat()
                if mevcut_kullanici.son_giris else None
            ),
            "telefon": mevcut_kullanici.telefon or "",
            "profil_resmi": None,  # TODO: Add profile image support
        }
    }


@router.post(
    "/cikis",
    summary="Kullanici Cikisi",
    description="Oturum sonlandirma ve JWT token iptali",
    responses={
        200: {
            "description": "Basarili cikis",
            "content": {
                "application/json": {
                    "example": {"message": "Basariyla cikis yapildi"}
                }
            },
        },
        400: {
            "description": "Gecersiz token",
            "content": {
                "application/json": {
                    "example": {"detail": "Gecersiz token"}
                }
            },
        },
        401: {
            "description": "Yetkilendirme hatasi",
            "content": {
                "application/json": {
                    "example": {"detail": "Gecersiz veya suresi dolmus token"}
                }
            },
        },
    },
)
async def kullanici_cikis(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, str]:
    """
    Kullanici cikisi yap ve token'i gecersiz kil

    Bu endpoint mevcut JWT token'i blacklist'e ekler ve kullaniciyi
    sistemden cikarir. Token artik gecerli olmayacaktir.

    **Islem Adimlari:**
    1. Token dogrulanir
    2. Token blacklist'e eklenir
    3. Aktif oturum sonlandirilir

    **Guvenlik:**
    - Token aninda gecersiz olur
    - Ayni token ile yeni istek yapilamaz
    """
    token = credentials.credentials

    # Blacklist token in Redis (P0-1e: Redis-backed with in-memory fallback)
    jwt_mgr = get_jwt_manager()
    await jwt_mgr.blacklist_token_async(token)

    # Also call legacy service for backward compatibility
    await kullanici_servisi.kullanici_cikis(token)

    return {"message": "Başarıyla çıkış yapıldı"}


@router.post("/logout", summary="User Logout (English alias)", include_in_schema=False)
async def user_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, str]:
    """
    User logout - English alias for /cikis
    Invalidates the authentication token
    """
    return await kullanici_cikis(credentials)


@router.post("/validate", summary="Validate Token", include_in_schema=False)
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, bool]:
    """
    Validate authentication token
    Frontend endpoint - checks if the provided token is valid

    Returns:
    {
        "valid": boolean
    }
    """
    try:
        token = credentials.credentials

        # Check JWT blacklist first (Redis-backed)
        jwt_mgr = get_jwt_manager()
        if await jwt_mgr.is_blacklisted_async(token):
            return {"valid": False}

        # Try JWT decode (primary auth path)
        try:
            pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {"valid": True}
        except pyjwt.ExpiredSignatureError:
            return {"valid": False}
        except pyjwt.InvalidTokenError:
            pass  # Not a JWT — fall through to legacy check

        # Legacy fallback: in-memory token validation
        kullanici = await kullanici_servisi.token_dogrula(token)
        return {"valid": bool(kullanici and kullanici.aktif)}
    except Exception:
        return {"valid": False}


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    currentPassword: str  # noqa: N815 (frontend contract)
    newPassword: str  # noqa: N815 (frontend contract)


class RevokeDeviceRequest(BaseModel):
    """Revoke device request model"""
    device_id: str


@router.post("/change-password", summary="Change Password", include_in_schema=False)
async def change_password(
    request_data: ChangePasswordRequest,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Change user password
    Frontend endpoint - requires current password and new password

    Returns:
    {
        "success": boolean,
        "message": string
    }
    """
    try:
        # Get user from database
        result = await db.execute(
            select(DBUser).where(DBUser.id == mevcut_kullanici.kullanici_id)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        # Verify current password
        if not pwd_context.verify(request_data.currentPassword, db_user.password_hash):
            return {"success": False, "message": "Mevcut şifre yanlış"}

        # Validate new password (same policy as registration)
        pw_error = _validate_password(request_data.newPassword)
        if pw_error:
            return {"success": False, "message": pw_error}

        # Hash and update new password
        db_user.password_hash = pwd_context.hash(request_data.newPassword)
        db_user.updated_at = datetime.now(UTC)
        await db.commit()

        return {"success": True, "message": "Şifre başarıyla değiştirildi"}
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": f"Şifre değiştirme başarısız: {e!s}"}


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model"""
    email: str


# In-memory store for password reset tokens (15 minute TTL)
# Production should use Redis or database table
_password_reset_tokens: dict[str, dict[str, Any]] = {}


@router.post("/forgot-password", summary="Forgot Password", include_in_schema=False)
async def forgot_password(
    request: Request,
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Request password reset
    Frontend endpoint - sends password reset email

    Returns:
    {
        "success": boolean,
        "message": string
    }
    """
    _check_login_rate_limit(request)

    try:
        # Check if user exists
        result = await db.execute(
            select(DBUser).where(DBUser.email == request_data.email)
        )
        db_user = result.scalar_one_or_none()

        # Always return success to prevent email enumeration attacks
        success_message = "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi"

        if not db_user:
            # Don't reveal that user doesn't exist
            return {"success": True, "message": success_message}

        # Generate secure reset token (valid for 15 minutes)
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        # Store token (in production, use Redis with TTL or database)
        _password_reset_tokens[reset_token] = {
            "user_id": db_user.id,
            "email": db_user.email,
            "expires_at": expires_at,
        }

        # Clean up expired tokens
        current_time = datetime.now(UTC)
        expired = [k for k, v in _password_reset_tokens.items()
                   if v["expires_at"] < current_time]
        for k in expired:
            del _password_reset_tokens[k]

        # TODO: Send email with reset link
        # reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
        # await send_password_reset_email(db_user.email, reset_link)

        return {"success": True, "message": success_message}
    except Exception as e:
        return {"success": False, "message": f"Şifre sıfırlama başarısız: {e!s}"}


class ResetPasswordRequest(BaseModel):
    """Reset password request model"""
    token: str
    newPassword: str  # noqa: N815 (frontend contract)


@router.post("/reset-password", summary="Reset Password", include_in_schema=False)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Reset password with token
    Frontend endpoint - resets password using reset token

    Returns:
    {
        "success": boolean,
        "message": string
    }
    """
    try:
        # Validate token exists
        token_data = _password_reset_tokens.get(request_data.token)
        if not token_data:
            return {"success": False, "message": "Geçersiz veya süresi dolmuş token"}

        # Check token expiration
        if token_data["expires_at"] < datetime.now(UTC):
            del _password_reset_tokens[request_data.token]
            return {"success": False, "message": "Token süresi dolmuş"}

        # Validate new password (same policy as registration)
        pw_error = _validate_password(request_data.newPassword)
        if pw_error:
            return {"success": False, "message": pw_error}

        # Get user and update password
        result = await db.execute(
            select(DBUser).where(DBUser.id == token_data["user_id"])
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        # Hash and update password
        db_user.password_hash = pwd_context.hash(request_data.newPassword)
        db_user.updated_at = datetime.now(UTC)
        await db.commit()

        # Invalidate used token
        del _password_reset_tokens[request_data.token]

        return {"success": True, "message": "Şifre başarıyla sıfırlandı"}
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": f"Şifre sıfırlama başarısız: {e!s}"}


@router.put("/profile", summary="Update Profile", include_in_schema=False)
async def update_profile(
    user_data: dict[str, Any],
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update user profile
    Frontend endpoint - updates user information

    Returns:
    {
        "success": boolean,
        "user": User object
    }
    """
    try:
        # Get user from database
        result = await db.execute(
            select(DBUser).where(DBUser.id == mevcut_kullanici.kullanici_id)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            return {"success": False, "user": None}

        # Update allowed fields
        allowed_fields = ["ad", "soyad", "telefon", "profil_resmi"]
        updated = False

        for field in allowed_fields:
            if field in user_data:
                if field in ("ad", "soyad"):
                    # Update full_name from ad + soyad
                    ad = user_data.get("ad", "")
                    soyad = user_data.get("soyad", "")
                    if ad or soyad:
                        db_user.full_name = f"{ad} {soyad}".strip()
                        updated = True
                elif field == "telefon" and hasattr(db_user, "phone"):
                    db_user.phone = user_data[field]
                    updated = True

        if updated:
            db_user.updated_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(db_user)

        # Build response user object
        full_name = db_user.full_name or ""
        name_parts = full_name.split(" ", 1)
        ad = name_parts[0] if name_parts else ""
        soyad = name_parts[1] if len(name_parts) > 1 else ""

        # Map role
        role_mapping = {
            "STUDENT": "ogrenci", "TEACHER": "ogretmen",
            "PARENT": "veli", "ADMIN": "admin",
            "SUPER_ADMIN": "super_admin",
        }
        rol = role_mapping.get(db_user.role.value, "ogrenci")

        return {
            "success": True,
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "ad": ad,
                "soyad": soyad,
                "rol": rol,
                "aktif": db_user.is_active,
                "olusturma_tarihi": (
                    db_user.created_at.isoformat()
                    if db_user.created_at else None
                ),
                "son_giris": (
                    db_user.last_login.isoformat()
                    if db_user.last_login else None
                ),
                "telefon": getattr(db_user, "phone", "") or "",
                "profil_resmi": None,
            }
        }
    except Exception:
        await db.rollback()
        return {"success": False, "user": None}


@router.post(
    "/ogrenci-profil",
    response_model=OgrenciProfili,
    summary="Ogrenci Profili Olustur",
    description=(
        "Yeni ogrenci profili olusturma"
        " - hedef sinav, konu tercihleri ve ogrenme stili"
    ),
    responses={
        200: {"description": "Ogrenci profili basariyla olusturuldu"},
        400: {"description": "Gecersiz profil verisi"},
        401: {"description": "Yetkilendirme hatasi"},
    },
)
async def ogrenci_profil_olustur(
    profil_data: OgrenciProfili,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> OgrenciProfili:
    """
    Ogrenci profili olustur

    Hedef sinav (TYT/AYT/YDT), konu tercihleri ve ogrenme stilini icerir.
    """
    try:
        # Kullanıcı ID'yi otomatik ata
        profil_data.kullanici_id = mevcut_kullanici.kullanici_id

        return await kullanici_servisi.ogrenci_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/ogrenci-profil/{ogrenci_id}",
    response_model=OgrenciProfili,
    summary="Ogrenci Profili Getir",
    description="Belirli bir ogrencinin profil bilgilerini getirir",
    responses={
        200: {"description": "Ogrenci profil bilgileri"},
        401: {"description": "Yetkilendirme hatasi"},
        403: {
            "description": (
                "Erisim engellendi"
                " - sadece kendi profilinizi gorebilirsiniz"
            ),
        },
        404: {"description": "Ogrenci profili bulunamadi"},
    },
)
async def ogrenci_profil_getir(
    ogrenci_id: str, mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir)
) -> OgrenciProfili:
    """
    Ogrenci profil bilgilerini getir

    SECURITY: Sadece kendi profilinizi veya yetkiniz varsa
    baska profilleri gorebilirsiniz.
    """
    profil = await kullanici_servisi.ogrenci_profili_getir(ogrenci_id)

    if not profil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Öğrenci profili bulunamadı"
        )

    # SECURITY FIX: Authorization check using centralized helper
    require_student_owner_or_privileged(mevcut_kullanici, profil.kullanici_id)

    return profil


@router.post(
    "/ogretmen-profil",
    response_model=OgretmenProfili,
    summary="Ogretmen Profili Olustur",
    description="Yeni ogretmen profili olusturma - brans, okul ve deneyim bilgileri",
    responses={
        200: {"description": "Ogretmen profili basariyla olusturuldu"},
        400: {"description": "Gecersiz profil verisi"},
        401: {"description": "Yetkilendirme hatasi"},
    },
)
async def ogretmen_profil_olustur(
    profil_data: OgretmenProfili,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> OgretmenProfili:
    """
    Ogretmen profili olustur

    Brans, okul ve deneyim bilgilerini icerir.
    """
    try:
        # Kullanıcı ID'yi otomatik ata
        profil_data.kullanici_id = mevcut_kullanici.kullanici_id

        return await kullanici_servisi.ogretmen_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/veli-profil",
    response_model=VeliProfili,
    summary="Veli Profili Olustur",
    description="Yeni veli profili olusturma - cocuk bilgileri ve iletisim tercihleri",
    responses={
        200: {"description": "Veli profili basariyla olusturuldu"},
        400: {"description": "Gecersiz profil verisi"},
        401: {"description": "Yetkilendirme hatasi"},
    },
)
async def veli_profil_olustur(
    profil_data: VeliProfili,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> VeliProfili:
    """
    Veli profili olustur

    Cocuk bilgileri ve iletisim tercihlerini icerir.
    """
    try:
        # Kullanıcı ID'yi otomatik ata
        profil_data.kullanici_id = mevcut_kullanici.kullanici_id

        return await kullanici_servisi.veli_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Task 48.4: JWT Refresh Token Endpoints
@router.post(
    "/refresh",
    summary="Refresh Access Token",
    description="Refresh token ile yeni access token al",
    responses={
        200: {
            "description": "Yeni access token başarıyla oluşturuldu",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                    }
                }
            },
        },
        401: {
            "description": "Refresh token geçersiz, süresi dolmuş veya iptal edilmiş",
            "content": {
                "application/json": {
                    "examples": {
                        "expired_token": {
                            "summary": "Token süresi dolmuş",
                            "value": {"detail": "Refresh token süresi dolmuş"},
                        },
                        "revoked_token": {
                            "summary": "Token iptal edilmiş",
                            "value": {"detail": "Refresh token iptal edilmiş"},
                        },
                        "invalid_token": {
                            "summary": "Geçersiz token",
                            "value": {"detail": "Geçersiz refresh token"},
                        },
                    }
                }
            },
        },
    },
)
async def refresh_token(
    request_body: RefreshTokenRequest | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Refresh token kullanarak yeni access token al (Task 48.4)
    Frontend compatibility: Accepts token in body
    {refreshToken: string} or Authorization header

    Bu endpoint, süresi dolmak üzere olan veya dolmuş access token'ı
    yenilemek için kullanılır. Refresh token ile yeni bir access token
    ve yeni bir refresh token alırsınız.

    **Token Yenileme İşlemi:**
    1. Refresh token doğrulanır
    2. Token'ın iptal edilip edilmediği kontrol edilir
    3. Yeni access token oluşturulur
    4. Yeni refresh token oluşturulur (token rotation)
    5. Eski refresh token iptal edilir (güvenlik)
    6. Yeni token çifti döner

    **Kimlik Doğrulama (İki Yöntem):**
    1. Authorization header (backward compatibility):
    ```
    Authorization: Bearer <refresh_token>
    ```
    2. Request body (frontend compatibility):
    ```json
    {
      "refreshToken": "<refresh_token>"
    }
    ```

    **Token Geçerlilik Süreleri:**
    - Yeni access token: 1 saat (3600 saniye)
    - Yeni refresh token: 7 gün
    - Eski refresh token: Otomatik iptal edilir

    **Başarılı Yanıt (200) - Frontend Format:**
    ```json
    {
      "success": true,
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

    **Hata Durumları:**
    - **401**: Refresh token geçersiz, süresi dolmuş veya iptal edilmiş

    **Güvenlik Özellikleri:**
    - Refresh token rotation (her yenilemede yeni refresh token)
    - Eski refresh token otomatik iptal (replay attack önleme)
    - IP ve User-Agent kontrolü (opsiyonel)
    - Token blacklist yönetimi

    **Kullanım Örneği:**
    ```bash
    # Via header
    curl -X POST "http://localhost:8000/api/v1/auth/refresh" \\
      -H "Authorization: Bearer <refresh_token>"

    # Via body (frontend)
    curl -X POST "http://localhost:8000/api/v1/auth/refresh" \\
      -H "Content-Type: application/json" \\
      -d '{"refreshToken": "<refresh_token>"}'
    ```

    **Not:**
    Access token süresi dolmadan önce yenilemeniz önerilir.
    Tipik strateji: Token'ın %75'i geçtiğinde yenile (45 dakika sonra)
    """
    try:
        # Extract token from body or header
        # (frontend sends in body, backward compat uses header)
        refresh_token_str = None
        if request_body and request_body.refreshToken:
            refresh_token_str = request_body.refreshToken
        elif credentials:
            refresh_token_str = credentials.credentials

        if not refresh_token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Refresh token bulunamadı."
                    " Lütfen Authorization header"
                    " veya request body kullanın."
                ),
            )

        jwt_manager = get_jwt_manager()

        with _sync_session(db) as sync_db:
            new_tokens = await jwt_manager.refresh_access_token(
                refresh_token_str, db=sync_db, request=request
            )

        # Return frontend-compatible format {success, token, refreshToken}
        # while keeping backward compatibility fields
        return {
            "success": True,
            "token": new_tokens.access_token,
            "refreshToken": new_tokens.refresh_token,
            # Backward compatibility
            "access_token": new_tokens.access_token,
            "refresh_token": new_tokens.refresh_token,
            "token_type": new_tokens.token_type,
            "expires_in": new_tokens.expires_in,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Refresh token başarısız: {e!s}",
        )


@router.post(
    "/logout-all",
    summary="Tum Cihazlardan Cikis",
    description="Tum aktif oturumlari sonlandirir ve tum refresh token'lari iptal eder",
    responses={
        200: {
            "description": "Basarili",
            "content": {
                "application/json": {
                    "example": {"message": "Tum cihazlardan basariyla cikis yapildi"}
                }
            },
        },
        401: {"description": "Yetkilendirme hatasi"},
        500: {"description": "Sunucu hatasi"},
    },
)
async def logout_all_devices(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Tum cihazlardan cikis yap

    Kullanicinin tum refresh token'larini revoke eder.
    Guvenlik ihlali suphelendiginde kullanilir.
    """
    try:
        jwt_manager = get_jwt_manager()

        with _sync_session(db) as sync_db:
            jwt_manager.revoke_all_user_tokens(sync_db, mevcut_kullanici.kullanici_id)

        return {"message": "Tüm cihazlardan başarıyla çıkış yapıldı"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout başarısız: {e!s}",
        )


@router.post(
    "/revoke-device",
    summary="Cihaz Tokenlari Iptal Et",
    description="Belirli bir cihazdaki oturumu sonlandirir",
    responses={
        200: {
            "description": "Basarili",
            "content": {
                "application/json": {
                    "example": {"message": "Cihaz device_123 token'lari iptal edildi"}
                }
            },
        },
        401: {"description": "Yetkilendirme hatasi"},
        500: {"description": "Sunucu hatasi"},
    },
)
async def revoke_device(
    request_data: RevokeDeviceRequest,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Belirli bir cihazdaki oturumu sonlandir

    Kayip veya calinan cihazlarda guvenlik icin kullanilir.
    """
    device_id = request_data.device_id
    try:
        jwt_manager = get_jwt_manager()

        with _sync_session(db) as sync_db:
            jwt_manager.revoke_device_tokens(
                sync_db, mevcut_kullanici.kullanici_id, device_id
            )

        return {"message": f"Cihaz {device_id} token'ları iptal edildi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device revoke başarısız: {e!s}",
        )
