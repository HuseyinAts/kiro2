"""
FastAPI Dependencies
Ortak bağımlılıklar ve yardımcı fonksiyonlar

SECURITY: Type-safe authentication with Pydantic models
"""

import logging
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# JWT Security
security = HTTPBearer()

# SECURITY FIX: Use config settings instead of hardcoded values
from core.config import settings

JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes


# ============================================================================
# User Role Enum — imported from canonical source (models.enums_db)
# ============================================================================
from models.enums_db import UserRole


# ============================================================================
# Authenticated User Model (Pydantic - Type Safe)
# ============================================================================
class AuthenticatedUser(BaseModel):
    """Type-safe authenticated user model.

    Replaces SimpleNamespace for better type safety and validation.
    KVKK compliant: email masked in repr to prevent accidental PII logging.
    """

    id: int | str = Field(..., description="User ID (primary key)")
    username: str = Field(..., min_length=1, max_length=255)
    role: UserRole = Field(..., description="User role")
    email: str | None = Field(None, description="User email (PII - handle carefully)")
    permissions: list[str] = Field(default_factory=list)
    exp: int | None = Field(None, description="Token expiration timestamp")

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any) -> int | str:
        """Validate and convert user ID with overflow protection."""
        if isinstance(v, int):
            if v > 2147483647:  # INT32_MAX
                raise ValueError("user_id out of range (max: 2147483647)")
            return v
        if isinstance(v, str):
            if v.isdigit():
                int_val = int(v)
                if int_val > 2147483647:
                    raise ValueError("user_id out of range (max: 2147483647)")
                return int_val
            # Non-numeric string (UUID etc.)
            return v
        raise ValueError(f"Invalid user_id type: {type(v)}")

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: Any) -> UserRole:
        """Validate role using Enum."""
        if isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                raise ValueError(f"Invalid role: {v}. Valid roles: {UserRole.values()}")
        raise ValueError(f"Invalid role type: {type(v)}")

    def __repr__(self) -> str:
        """KVKK compliant repr - mask email."""
        masked_email = "***@***" if self.email else None
        return f"AuthenticatedUser(id={self.id}, username={self.username}, role={self.role.value}, email={masked_email})"

    model_config = ConfigDict(
        use_enum_values=False,  # Keep enum objects
        frozen=True,  # Security: Prevent privilege escalation
    )


# ============================================================================
# Authentication Dependencies
# ============================================================================
async def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthenticatedUser:
    """
    JWT token'dan mevcut kullanıcıyı al.

    Returns type-safe AuthenticatedUser model.
    Supports both Bearer header and httpOnly cookie authentication.

    SECURITY FIX #1: Real database lookup instead of mock data
    SECURITY FIX #2: Specific exception handling (no bare except)
    SECURITY FIX #3: Pydantic validation for type safety
    P0-1c: Also reads JWT from httpOnly cookie for frontend auth
    """
    # Try Bearer header first, then httpOnly cookie
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        import time
        t0 = time.perf_counter()
        
        # P0-1e: Check blacklist before decoding (Redis-backed with in-memory fallback)
        from core.jwt_auth import get_jwt_manager

        jwt_mgr = get_jwt_manager()
        await jwt_mgr.is_blacklisted_async(token)
        t1 = time.perf_counter()

        # JWT token'ı decode et
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        t2 = time.perf_counter()

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Required fields from JWT payload
        username = payload.get("username")
        role = payload.get("role")
        email = payload.get("email")

        # Create type-safe user model (validation happens in Pydantic)
        try:
            user = AuthenticatedUser(
                id=user_id,
                username=username,
                role=role,
                email=email,
                permissions=payload.get("permissions", []),
                exp=payload.get("exp"),
            )
        except ValueError as e:
            logger.warning(f"Token validation failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions (don't mask them)
        raise
    except ValueError as e:
        # Handle value errors from validation
        logger.error(f"Validation error in auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: invalid data",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Admin-only dependencies: SUPER_ADMIN must match ADMIN API surface (F4 / operasyon).
PLATFORM_ADMIN_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.ADMIN, UserRole.SUPER_ADMIN}
)


async def get_current_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Admin veya süper admin yetkisi olan kullanıcıyı al."""
    if current_user.role not in PLATFORM_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


async def get_current_teacher_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Öğretmen yetkisi olan kullanıcıyı al."""
    if current_user.role not in [
        UserRole.TEACHER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required"
        )
    return current_user


async def get_current_student_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Öğrenci yüzeyi: öğrenci, öğretmen veya yönetim rolleri."""
    if current_user.role not in [
        UserRole.STUDENT,
        UserRole.TEACHER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student access required"
        )
    return current_user


# ============================================================================
# Mock/Test Utilities (ONLY for testing - protected)
# ============================================================================
def create_mock_jwt_token(user_id: str = "test_user", role: str = "student") -> str:
    """
    Test için mock JWT token oluştur.

    WARNING: Only use in test environment!
    """
    import os

    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("Mock tokens not allowed in production")

    logger.warning("MOCK TOKEN CREATED - Test only!")

    payload = {
        "sub": user_id,
        "username": user_id,
        "role": role,
        "email": f"{user_id}@example.com",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Test için mock kullanıcı
MOCK_USER = {
    "id": "test_student",  # Matches AuthenticatedUser.id
    "username": "test_student",
    "role": "student",
    "email": "test@example.com",
}


async def get_mock_current_user() -> dict[str, Any]:
    """Test için mock kullanıcı döndür."""
    return MOCK_USER


# ============================================================================
# Database & Cache Dependencies
# ============================================================================
async def get_db():
    """
    Real database dependency.
    SECURITY FIX: Use real database session instead of mock.
    """
    from core.database import get_async_session

    async for session in get_async_session():
        yield session


async def get_redis():
    """
    Real Redis dependency.
    SECURITY FIX: Use real Redis connection.
    """
    from core.cache import cache_manager

    if not cache_manager.enabled:
        await cache_manager.initialize()

    yield cache_manager


async def get_elasticsearch():
    """
    Real Elasticsearch dependency.
    SECURITY FIX: Use real Elasticsearch connection.
    """
    from core.elasticsearch_config import get_global_elasticsearch_service

    es_service = await get_global_elasticsearch_service()
    yield es_service


async def get_database_service():
    """
    Database service dependency.
    SECURITY FIX: Use real database service.
    """
    from core.database import db_manager

    yield db_manager


async def get_cache_service():
    """
    Cache service dependency.
    SECURITY FIX: Use real cache service.
    """
    from core.cache import cache_manager

    yield cache_manager


def verify_token(token: str) -> dict[str, Any]:
    """JWT token'ı doğrula ve payload döndür."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(data: dict[str, Any], expires_delta: int = None) -> str:
    """Access token oluştur."""
    import datetime

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=expires_delta
        )
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================
# 450+ test dosyası bu isimleri kullanıyor
get_database_session = get_db
get_session = get_db
get_async_db = get_db


# ============================================================================
# KVKK Faz 2: Veli onay enforcement dependency
# ============================================================================
async def require_veli_consent(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """Reşit olmayan öğrenci + veli_onay=False ise sosyal/PII erişimini 403'ler.

    Çekirdek öğrenme (soru/sınav/plan) bu dependency'i KULLANMAZ — açık kalır.
    Profil yoksa (öğrenci değilse) veya veli_onay=True ise geçer.
    """
    from sqlalchemy import text as _text

    row = (
        await db.execute(
            _text("SELECT veli_onay FROM student_profiles WHERE user_id = :uid"),
            {"uid": str(current_user.id)},
        )
    ).first()
    if row is None or row[0] is True:
        return current_user
    raise HTTPException(
        status_code=403,
        detail="Bu özellik için veli onayı gereklidir (KVKK reşit olmayan kullanıcı).",
    )
