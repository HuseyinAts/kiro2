"""
Kimlik doğrulama API endpoint'leri (Task 48.4: Enhanced with Refresh Token)
SECURITY FIX: Authorization checks added to prevent IDOR attacks
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from collections import defaultdict
from contextlib import contextmanager  # noqa: F401 -- kept for backward compat
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import redis.asyncio as aioredis

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.authorization import require_student_owner_or_privileged
from core.config import settings as app_settings
from core.dependencies import JWT_ALGORITHM, JWT_SECRET, get_db
from core.jwt_auth import UserRole as JWTUserRole
from core.jwt_auth import get_jwt_manager
from database.connection import get_sync_session_context
from models import (
    Kullanici,
    KullaniciGiris,
    KullaniciOlustur,
    KullaniciRolu,
    OgrenciProfilOlusturGirdi,
    OgrenciProfili,
    OgretmenProfilOlusturGirdi,
    OgretmenProfili,
    TokenYaniti,
    VeliProfilOlusturGirdi,
    VeliProfili,
)
from models.database import User as DBUser
from services.user_service import kullanici_servisi

# Cookie path constants (must match between set and delete)
ACCESS_TOKEN_COOKIE_PATH = "/api"  # noqa: S105


class TwoFactorRequired(Exception):
    """Raised when 2FA verification is needed before issuing tokens."""

    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email
        super().__init__("2FA verification required")


REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth"  # noqa: S105

# Computed once at module import
_IS_DEV = app_settings.environment == "development"
logger = logging.getLogger(__name__)

# ── Rate Limiting ──────────────────────────────────────────────────────────

# Only trust X-Forwarded-For from these IPs (reverse proxy / load balancer)
_TRUSTED_PROXIES = {"127.0.0.1", "::1", "172.17.0.1"}  # localhost + Docker default

# Per-bucket in-memory rate counters: bucket_name -> {ip -> [timestamps]}
_rate_buckets: dict[str, dict[str, list[float]]] = defaultdict(
    lambda: defaultdict(list)
)

# Bucket configs: (max_attempts, window_seconds)
RATE_LIMITS = {
    "login": (10, 60),
    "register": (5, 60),
    "password_reset": (5, 300),
    "2fa_verify": (10, 60),
    "award_xp": (10, 60),
    "quest_progress": (20, 60),
    "claim_bonus": (3, 60),
    "oba_contribute": (10, 60),
}


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For only from trusted proxies."""
    client_host = request.client.host if request.client else "unknown"
    if client_host in _TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return client_host


def _check_rate_limit(request: Request, bucket: str = "login") -> None:
    """Raise 429 if IP exceeds rate limit for the given bucket."""
    max_attempts, window = RATE_LIMITS.get(bucket, (10, 60))
    client_ip = _get_client_ip(request)
    now = time.time()
    attempts = _rate_buckets[bucket][client_ip]
    _rate_buckets[bucket][client_ip] = [t for t in attempts if now - t < window]
    if len(_rate_buckets[bucket][client_ip]) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail=f"Cok fazla istek. {window} saniye sonra tekrar deneyin.",
        )


def _record_attempt(request: Request, bucket: str = "login") -> None:
    """Record an attempt for rate limiting."""
    client_ip = _get_client_ip(request)
    _rate_buckets[bucket][client_ip].append(time.time())


# Backward compat aliases
def _check_login_rate_limit(request: Request) -> None:
    _check_rate_limit(request, "login")


def _record_failed_login(request: Request) -> None:
    _record_attempt(request, "login")


_GENERIC_ERROR = "Islem basarisiz. Lutfen tekrar deneyin."

# Allowlisted Turkish user-facing ValueError messages (safe to expose)
_SAFE_PATTERNS = {
    "zaten",  # "profil zaten mevcut", "email zaten kayitli"
    "bulunamadı",  # "kullanici bulunamadı"
    "geçersiz",  # "geçersiz format"
    "eksik",  # "eksik alan"
    "mevcut",  # "profil zaten mevcut"
}


def _safe_user_detail(e: Exception) -> str:
    """Return ValueError message if it's user-actionable, otherwise generic."""
    msg = str(e)
    msg_lower = msg.lower()
    if any(p in msg_lower for p in _SAFE_PATTERNS):
        return msg
    return _GENERIC_ERROR


# FIX 2026-04-01: _sync_session kaldirildi.
# SQLAlchemy 2.x'te db.bind attribute yok -> AttributeError/503.
# Refresh token persist zaten async await db.execute() ile yapiliyor.
# Bu contextmanager dead code olarak kaldi, kullanilan yer yok.


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def database_authenticate(
    giris_data: KullaniciGiris,
    db: AsyncSession,
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

    # 2FA gate: if user has 2FA enabled, don't issue tokens yet
    if getattr(db_user, "is_2fa_enabled", False) and db_user.secret_2fa:
        raise TwoFactorRequired(user_id=str(db_user.id), email=db_user.email)

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
    # Refresh token'i async ile kaydet (sync session asyncpg ile calismiyor)
    try:
        import hashlib as _hashlib

        from sqlalchemy import text as _text

        _payload = pyjwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        _token_hash = _hashlib.sha256(refresh_token.encode()).hexdigest()
        _jti = _payload.get("jti", "") if _payload else ""
        _exp = (
            datetime.fromtimestamp(_payload.get("exp", 0), tz=UTC)
            if _payload
            else datetime.now(UTC)
        )
        await db.execute(
            _text("""
                INSERT INTO refresh_tokens
                    (id, user_id, token_hash, jti, device_type, expires_at,
                     revoked, usage_count, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :uid, :th, :jti, 'desktop', :exp,
                     false, 0, now(), now())
                ON CONFLICT DO NOTHING
            """),
            {"uid": str(db_user.id), "th": _token_hash, "jti": _jti, "exp": _exp},
        )
    except Exception as _rt_err:
        logger.warning(f"Failed to persist refresh token to DB: {_rt_err}")

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
                db_user.created_at.isoformat() if db_user.created_at else None
            ),
            "son_giris": (
                db_user.last_login.isoformat() if db_user.last_login else None
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
                        "message": "Kullanıcı kaydı başarıyla oluşturuldu",
                    }
                }
            },
        },
        400: {
            "description": (
                "Geçersiz istek - E-posta zaten kayıtlı veya doğrulama hatası"
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
async def kullanici_kayit(
    request: Request,
    kullanici_data: KullaniciOlustur,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Yeni kullanıcı kaydı — PostgreSQL'e yazar (DB-backed).

    Request Body:
      email, sifre, ad_soyad, rol (ogrenci/veli/ogretmen/admin)
    """
    _check_rate_limit(request, "register")

    import uuid as _uuid

    from sqlalchemy import text as _text

    # Rol eşleştirme: Türkçe → enum değeri
    ROL_MAP = {
        "ogrenci": "STUDENT",
        "student": "STUDENT",
        "veli": "PARENT",
        "parent": "PARENT",
        "ogretmen": "TEACHER",
        "teacher": "TEACHER",
        "admin": "ADMIN",
    }
    rol_str = ROL_MAP.get(str(kullanici_data.rol).lower(), "STUDENT")

    # E-posta benzersizlik kontrolü
    dup = await db.execute(
        _text("SELECT id FROM users WHERE email = :email"),
        {"email": kullanici_data.email},
    )
    if dup.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanımda",
        )

    # Şifre hash
    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pw_hash = _pwd_ctx.hash(kullanici_data.sifre)

    # Ad / soyad ayır
    parts = (kullanici_data.ad_soyad or "").strip().split(" ", 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""

    user_id = str(_uuid.uuid4())

    await db.execute(
        _text("""
        INSERT INTO users
            (id, email, username, password_hash, first_name, last_name,
             role, is_active, is_verified, total_xp, level,
             elo_rating, is_premium, is_parent, created_at, updated_at)
        VALUES
            (:id, :email, :username, :pw_hash, :first_name, :last_name,
             CAST(:role AS userrole), TRUE, FALSE, 0, 1,
             1200, FALSE, FALSE, NOW(), NOW())
    """),
        {
            "id": user_id,
            "email": kullanici_data.email,
            "username": kullanici_data.email.split("@")[0],
            "pw_hash": pw_hash,
            "first_name": first_name,
            "last_name": last_name,
            "role": rol_str,
        },
    )

    # ── student_profiles oluştur (öğrenci rolü için) ─────────────────
    # Bu kayıt olmadan: exam_sessions FK kırık, theta persist edemez,
    # learning path kişiselleştiremez, dashboard hep sıfır gösterir.
    if rol_str == "STUDENT":
        profile_id = str(_uuid.uuid4())
        grade_level = getattr(kullanici_data, "sinif", 11)  # Default: 11. sınıf
        if not isinstance(grade_level, int) or grade_level < 9 or grade_level > 12:
            grade_level = 11

        await db.execute(
            _text("""
            INSERT INTO student_profiles
                (id, user_id, grade_level, veli_onay, current_level,
                 total_study_hours, total_questions_solved, correct_answers,
                 irt_ability, created_at, updated_at)
            VALUES
                (:id, :user_id, :grade_level, FALSE, 0.0,
                 0, 0, 0,
                 0.0, NOW(), NOW())
        """),
            {
                "id": profile_id,
                "user_id": user_id,
                "grade_level": grade_level,
            },
        )

    await db.commit()

    logger.info(f"Yeni kullanıcı kaydı: {kullanici_data.email} ({rol_str})")
    return {
        "success": True,
        "message": "Kullanıcı kaydı başarıyla oluşturuldu",
        "id": user_id,
    }


# English alias for registration endpoint
@router.post(
    "/register",
    summary="User Registration (English alias)",
    description="Create a new user account - English endpoint alias for /kayit",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,  # Hide from OpenAPI docs to avoid duplication
)
async def kullanici_kayit_en(
    request: Request,
    kullanici_data: KullaniciOlustur,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """English alias for /kayit - registration."""
    return await kullanici_kayit(request, kullanici_data, db)


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
    except TwoFactorRequired as e:
        return {
            "success": False,
            "requires_2fa": True,
            "message": "2FA doğrulaması gerekli",
            "email": e.email,
        }
    except ValueError:
        _record_failed_login(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


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
    db: AsyncSession = Depends(get_db),
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
            "user": token_yaniti["user"],
        }
    except TwoFactorRequired as e:
        # 2FA enabled — credentials OK but TOTP verification needed
        return {
            "success": False,
            "requires_2fa": True,
            "message": "2FA doğrulaması gerekli",
            "email": e.email,
        }
    except ValueError:
        _record_failed_login(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token bulunamadı"
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
                "Kimlik doğrulama hatası - Geçersiz veya süresi dolmuş token"
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
    name_parts = mevcut_kullanici.ad_soyad.split(" ", 1)
    ad = name_parts[0] if len(name_parts) > 0 else ""
    soyad = name_parts[1] if len(name_parts) > 1 else ""

    # KullaniciRolu values already match frontend format: "ogrenci", "admin" etc.
    frontend_role = mevcut_kullanici.rol.value

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
                if mevcut_kullanici.olusturma_tarihi
                else None
            ),
            "son_giris": (
                mevcut_kullanici.son_giris.isoformat()
                if mevcut_kullanici.son_giris
                else None
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
                "application/json": {"example": {"message": "Basariyla cikis yapildi"}}
            },
        },
        400: {
            "description": "Gecersiz token",
            "content": {"application/json": {"example": {"detail": "Gecersiz token"}}},
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
async def validate_token(request: Request) -> dict[str, bool]:
    """
    Validate authentication token
    Frontend endpoint - checks if the provided token is valid

    Supports both Bearer token and httpOnly cookie authentication.

    Returns:
    {
        "valid": boolean
    }
    """
    try:
        # Support both Bearer token and cookie (like mevcut_kullanici_getir)
        token = None

        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

        # Fallback to cookie
        if not token:
            token = request.cookies.get("access_token")

        if not token:
            return {"valid": False}

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
            return {"valid": False}
    except Exception:
        return {"valid": False}


class ChangePasswordRequest(BaseModel):
    """Change password request model"""

    currentPassword: str = Field(..., min_length=8, max_length=128)  # noqa: N815
    newPassword: str = Field(..., min_length=8, max_length=128)  # noqa: N815


class RevokeDeviceRequest(BaseModel):
    """Revoke device request model"""

    device_id: str = Field(..., max_length=200)


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
    # GF14: Business errors MUST raise HTTPException so the HTTP status
    # reflects reality. Returning {"success": false} with implicit HTTP 200
    # silently corrupts response.ok checks in clients and monitoring.
    try:
        # Get user from database
        result = await db.execute(
            select(DBUser).where(DBUser.id == mevcut_kullanici.kullanici_id)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        # Verify current password
        if not pwd_context.verify(request_data.currentPassword, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Mevcut şifre yanlış")

        # Validate new password (same policy as registration)
        pw_error = _validate_password(request_data.newPassword)
        if pw_error:
            raise HTTPException(status_code=400, detail=pw_error)

        # Hash and update new password
        db_user.password_hash = pwd_context.hash(request_data.newPassword)
        db_user.updated_at = datetime.now(UTC)
        await db.commit()

        return {"success": True, "message": "Şifre başarıyla değiştirildi"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Password change failed: {e!s}")
        raise HTTPException(
            status_code=500,
            detail="Şifre değiştirme başarısız. Lütfen tekrar deneyin.",
        ) from e


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model"""

    email: str = Field(..., max_length=254)


# Redis-backed password reset token store (15 minute TTL)
# Graceful fallback to in-memory dict if Redis unavailable


class RedisPasswordResetStore:
    """Redis-backed password reset token store with 15-min TTL."""

    KEY_PREFIX = "password_reset"
    TTL_SECONDS = 900  # 15 minutes

    def __init__(self, redis_client: aioredis.Redis | None):
        self._redis = redis_client
        self._memory: dict[str, dict[str, Any]] = {}

    async def set(self, token: str, user_id: str, email: str) -> None:
        """Store token with 15-min TTL."""
        entry = {
            "user_id": user_id,
            "email": email,
            "expires_at": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
        }
        if self._redis:
            try:
                key = f"{self.KEY_PREFIX}:{token}"
                await self._redis.setex(key, self.TTL_SECONDS, json.dumps(entry))
                return
            except Exception:
                pass
        # Fallback to in-memory
        self._memory[token] = entry

    async def get(self, token: str) -> dict[str, Any] | None:
        """Retrieve token data, or None if expired/missing."""
        if self._redis:
            try:
                key = f"{self.KEY_PREFIX}:{token}"
                raw = await self._redis.get(key)
                if raw:
                    return json.loads(raw)
                return None
            except Exception:
                pass
        # Fallback to in-memory
        entry = self._memory.get(token)
        if entry:
            expires_at = datetime.fromisoformat(entry["expires_at"])
            if expires_at > datetime.now(UTC):
                return entry
            # Expired — clean up
            del self._memory[token]
        return None

    async def delete(self, token: str) -> None:
        """Invalidate token."""
        if self._redis:
            try:
                key = f"{self.KEY_PREFIX}:{token}"
                await self._redis.delete(key)
                return
            except Exception:
                pass
        self._memory.pop(token, None)


_redis_client_for_tokens: aioredis.Redis | None = None


async def _get_token_store() -> RedisPasswordResetStore:
    """Lazy-initialize Redis client and token store."""
    global _redis_client_for_tokens
    if _redis_client_for_tokens is None:
        try:
            import os

            import redis.asyncio as aioredis

            _redis_client_for_tokens = aioredis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
            )
            # Verify connection
            await _redis_client_for_tokens.ping()
        except Exception:
            _redis_client_for_tokens = None
    return RedisPasswordResetStore(_redis_client_for_tokens)


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
    _check_rate_limit(request, "password_reset")

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

        # Store token in Redis (with 15-min TTL), fallback to memory
        store = await _get_token_store()
        await store.set(reset_token, db_user.id, db_user.email)

        # TODO: Send email with reset link
        # reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
        # await send_password_reset_email(db_user.email, reset_link)

        return {"success": True, "message": success_message}
    except Exception:
        return {"success": False, "message": "Şifre sıfırlama başarısız"}


class ResetPasswordRequest(BaseModel):
    """Reset password request model"""

    token: str = Field(..., max_length=200)
    newPassword: str = Field(..., min_length=8, max_length=128)  # noqa: N815


@router.post("/reset-password", summary="Reset Password", include_in_schema=False)
async def reset_password(
    request: Request,
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
    _check_rate_limit(request, "password_reset")
    try:
        store = await _get_token_store()
        token_data = await store.get(request_data.token)
        if not token_data:
            return {"success": False, "message": "Geçersiz veya süresi dolmuş token"}

        # Validate new password (same policy as registration)
        pw_error = _validate_password(request_data.newPassword)
        if pw_error:
            return {"success": False, "message": pw_error}

        # Invalidate token BEFORE password update to prevent race condition
        # (two concurrent requests with same token — only first proceeds)
        await store.delete(request_data.token)

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

        return {"success": True, "message": "Şifre başarıyla sıfırlandı"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Password reset failed: {e!s}")
        return {
            "success": False,
            "message": "Şifre sıfırlama başarısız. Lütfen tekrar deneyin.",
        }


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
            "STUDENT": "ogrenci",
            "TEACHER": "ogretmen",
            "PARENT": "veli",
            "ADMIN": "admin",
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
                    db_user.created_at.isoformat() if db_user.created_at else None
                ),
                "son_giris": (
                    db_user.last_login.isoformat() if db_user.last_login else None
                ),
                "telefon": getattr(db_user, "phone", "") or "",
                "profil_resmi": None,
            },
        }
    except Exception:
        await db.rollback()
        return {"success": False, "user": None}


@router.post(
    "/ogrenci-profil",
    response_model=OgrenciProfili,
    summary="Ogrenci Profili Olustur",
    description=(
        "Yeni ogrenci profili olusturma - hedef sinav, konu tercihleri ve ogrenme stili"
    ),
    responses={
        200: {"description": "Ogrenci profili basariyla olusturuldu"},
        400: {"description": "Gecersiz profil verisi"},
        401: {"description": "Yetkilendirme hatasi"},
    },
)
async def ogrenci_profil_olustur(
    body: OgrenciProfilOlusturGirdi,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> OgrenciProfili:
    """
    Ogrenci profili olustur

    Hedef sinav (TYT/AYT/YDT), konu tercihleri ve ogrenme stilini icerir.
    """
    try:
        uid = mevcut_kullanici.kullanici_id
        profil_data = OgrenciProfili(
            ogrenci_id=uid,
            kullanici_id=uid,
            sinif_seviyesi=body.sinif_seviyesi,
            okul_adi=body.okul_adi,
            hedef_sinav=body.hedef_sinav,
            hedef_universiteler=body.hedef_universiteler,
            ogrenme_stili=body.ogrenme_stili,
            guclu_alanlar=body.guclu_alanlar,
            zayif_alanlar=body.zayif_alanlar,
            gunluk_calisma_hedefi=body.gunluk_calisma_hedefi,
            veli_onay=False,
            veli_kullanici_id=None,
        )

        return await kullanici_servisi.ogrenci_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_user_detail(e),
        )


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
                "Erisim engellendi - sadece kendi profilinizi gorebilirsiniz"
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
    body: OgretmenProfilOlusturGirdi,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> OgretmenProfili:
    """
    Ogretmen profili olustur

    Brans, okul ve deneyim bilgilerini icerir.
    """
    try:
        uid = mevcut_kullanici.kullanici_id
        profil_data = OgretmenProfili(
            ogretmen_id=uid,
            kullanici_id=uid,
            okul_adi=body.okul_adi,
            brans=body.brans,
            deneyim_yili=body.deneyim_yili,
            sinif_listesi=body.sinif_listesi,
        )

        return await kullanici_servisi.ogretmen_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_user_detail(e),
        )


@router.post(
    "/veli-profil",
    response_model=VeliProfili,
    summary="Veli Profili Olustur",
    description=(
        "Yeni veli profili olusturma — iletisim tercihleri. "
        "Cocuk kullanici baglantisı ayrı onaylı uçlar üzerinden yapılır (gövdede ogrenci ID yok)."
    ),
    responses={
        200: {"description": "Veli profili basariyla olusturuldu"},
        400: {"description": "Gecersiz profil verisi"},
        401: {"description": "Yetkilendirme hatasi"},
    },
)
async def veli_profil_olustur(
    body: VeliProfilOlusturGirdi,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> VeliProfili:
    """
    Veli profili olustur

    Cocuk bilgileri ve iletisim tercihlerini icerir.
    """
    try:
        uid = mevcut_kullanici.kullanici_id
        profil_data = VeliProfili(
            veli_id=uid,
            kullanici_id=uid,
            cocuk_ogrenci_ids=[],
            email_bildirimleri=body.email_bildirimleri,
            sms_bildirimleri=body.sms_bildirimleri,
        )

        return await kullanici_servisi.veli_profili_olustur(profil_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_user_detail(e),
        )


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

        with get_sync_session_context() as sync_db:
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
    except Exception:
        logger.exception(
            "refresh_token: beklenmeyen hata (istemciye genel 401 donuldu)"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
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

        with get_sync_session_context() as sync_db:
            jwt_manager.revoke_all_user_tokens(sync_db, mevcut_kullanici.kullanici_id)

        return {"message": "Tüm cihazlardan başarıyla çıkış yapıldı"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
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

        with get_sync_session_context() as sync_db:
            jwt_manager.revoke_device_tokens(
                sync_db, mevcut_kullanici.kullanici_id, device_id
            )

        return {"message": f"Cihaz {device_id} token'ları iptal edildi"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
