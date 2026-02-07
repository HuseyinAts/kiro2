"""
JWT Authentication System
P0 Fix: Authentication and authorization for Learning Path API

AUTH SYSTEM HIERARCHY (2025-01-24):
Bu proje 16+ auth modulu iceriyor! Hiyerarsi:

1. CORE AUTH (Temel):
   - auth.py (BU DOSYA) - JWT token + RBAC
   - auth_dependencies.py - FastAPI dependency injection
   - jwt_auth.py - JWT helpers (DUPLICATE risk!)

2. MIDDLEWARE:
   - auth_middleware.py - Request auth middleware
   - auth_rate_limiting.py - Rate limiting for auth

3. ENHANCED AUTH:
   - enhanced_authentication.py - Gelismis auth (50KB!)
   - two_factor_auth.py - 2FA/MFA
   - passwordless_auth.py - Magic link auth
   - biometric_auth_service.py - Biometric auth
   - oauth2_service.py - OAuth2 integration

4. SPECIALIZED:
   - learning_path_auth.py - Learning path ozel auth
   - auth_security_utils.py - Security utilities
   - authorization.py - Authorization helpers
   - session_auth_caching.py - Session caching

5. UNIFIED/CONSOLIDATED (Hedef):
   - unified_auth_service.py - Unified servis
   - consolidated_auth_dependencies.py - Consolidated deps

REFACTORING NEEDED:
16 dosya cok fazla! Konsolidasyon onerisi:
1. core/auth/base.py - Temel auth (JWT, password)
2. core/auth/middleware.py - Auth middleware
3. core/auth/advanced.py - 2FA, OAuth2, passwordless
4. core/auth/dependencies.py - FastAPI deps

ONEMLI: auth/ klasoru olusturulamadi (auth.py cakismasi).
Oncelikle auth.py -> core_auth.py yeniden adlandirilmali.

Features:
- JWT token generation and validation
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Protected route decorators
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from database.connection import get_async_session
from models.user import Kullanici, KullaniciRolu

logger = logging.getLogger(__name__)

# JWT Configuration - SECURITY: Use centralized Settings, no hardcoded defaults
_settings = get_settings()
JWT_SECRET_KEY = _settings.jwt_secret_key
JWT_ALGORITHM = _settings.jwt_algorithm
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = _settings.jwt_access_token_expire_minutes

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


class AuthService:
    """Authentication service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})

        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def generate_student_id(name: str) -> str:
        """
        Generate unique, unpredictable student ID.

        SECURITY FIX: Previous implementation used timestamp + name which
        was predictable and vulnerable to account enumeration attacks.
        Now uses cryptographically secure random values for unpredictability.

        Args:
            name: Student name (used only for prefix, not for uniqueness)

        Returns:
            Unique student ID in format: STU_{uuid8}_{hex8}
        """
        # Use UUID v4 (random) for uniqueness
        uuid_part = uuid4().hex[:8].upper()
        # Add cryptographically secure random hex for extra entropy
        random_part = secrets.token_hex(4).upper()
        return f"STU_{uuid_part}_{random_part}"


# Dependency: Get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> Kullanici:
    """
    Get current authenticated user from JWT token
    Raises 401 if token is invalid or user not found
    """
    token = credentials.credentials

    try:
        payload = AuthService.decode_token(token)
        kullanici_id: str = payload.get("sub")
        if kullanici_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    from sqlalchemy import select

    result = await session.execute(
        select(Kullanici).where(Kullanici.kullanici_id == kullanici_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.aktif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    return user


# Dependency: Get current student user
async def get_current_student(
    current_user: Kullanici = Depends(get_current_user),
) -> Kullanici:
    """
    Get current student user
    Raises 403 if user is not a student
    """
    if current_user.rol != KullaniciRolu.OGRENCI:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Student role required",
        )
    return current_user


# Dependency: Get current teacher user
async def get_current_teacher(
    current_user: Kullanici = Depends(get_current_user),
) -> Kullanici:
    """
    Get current teacher user
    Raises 403 if user is not a teacher
    """
    if current_user.rol != KullaniciRolu.OGRETMEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Teacher role required",
        )
    return current_user


# Dependency: Get current admin user
async def get_current_admin(
    current_user: Kullanici = Depends(get_current_user),
) -> Kullanici:
    """
    Get current admin user
    Raises 403 if user is not an admin
    """
    if current_user.rol != KullaniciRolu.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin role required",
        )
    return current_user


# Dependency: Verify student_id ownership
async def verify_student_ownership(
    student_id: str,
    current_user: Kullanici = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> bool:
    """
    Verify that current user owns the student_id
    Admins and teachers can access any student
    Students can only access their own data
    """
    # Admins and teachers have full access
    if current_user.rol in [KullaniciRolu.ADMIN, KullaniciRolu.OGRETMEN]:
        return True

    # Students can only access their own data
    if current_user.rol == KullaniciRolu.OGRENCI:
        # Fetch student profile to verify ownership
        from sqlalchemy import select
        from models.learning_path_models import LearningPathStudentProfile

        result = await session.execute(
            select(LearningPathStudentProfile).where(LearningPathStudentProfile.student_id == student_id)
        )
        profile = result.scalar_one_or_none()

        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )

        # Check if profile belongs to current user
        if profile.user_id != current_user.kullanici_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own data",
            )

        return True

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


# Optional authentication (for public endpoints that benefit from user context)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Kullanici]:
    """
    Get current user if token provided, otherwise None
    Does not raise exception if no token
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
