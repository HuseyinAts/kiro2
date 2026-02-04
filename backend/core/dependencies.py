"""
FastAPI Dependencies
Ortak bağımlılıklar ve yardımcı fonksiyonlar
"""

import logging
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# JWT Security
security = HTTPBearer()

# SECURITY FIX: Use config settings instead of hardcoded values
from core.config import settings

JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """
    JWT token'dan mevcut kullanıcıyı al
    """
    try:
        token = credentials.credentials

        # JWT token'ı decode et
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Mock user data (gerçek uygulamada database'den alınmalı)
        user_data = {
            "user_id": user_id,
            "username": payload.get("username", "test_user"),
            "role": payload.get("role", "student"),
            "email": payload.get("email", "test@example.com"),
        }

        return user_data

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Admin yetkisi olan kullanıcıyı al
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user


async def get_current_teacher_user(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Öğretmen yetkisi olan kullanıcıyı al
    """
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required"
        )

    return current_user


async def get_current_student_user(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Öğrenci yetkisi olan kullanıcıyı al
    """
    if current_user.get("role") not in ["student", "teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student access required"
        )

    return current_user


# Mock authentication için test kullanıcısı oluştur
def create_mock_jwt_token(user_id: str = "test_user", role: str = "student") -> str:
    """
    Test için mock JWT token oluştur
    """
    payload = {
        "sub": user_id,
        "username": user_id,
        "role": role,
        "email": f"{user_id}@example.com",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Test için mock kullanıcı
MOCK_USER = {
    "user_id": "test_student",
    "username": "test_student",
    "role": "student",
    "email": "test@example.com",
}


async def get_mock_current_user() -> dict[str, Any]:
    """
    Test için mock kullanıcı döndür
    """
    return MOCK_USER


async def get_db():
    """
    Real database dependency
    SECURITY FIX: Use real database session instead of mock
    """
    from core.database import get_async_session

    async for session in get_async_session():
        yield session


async def get_redis():
    """
    Real Redis dependency
    SECURITY FIX: Use real Redis connection
    """
    from core.cache import cache_manager

    if not cache_manager.enabled:
        await cache_manager.initialize()

    yield cache_manager


async def get_elasticsearch():
    """
    Real Elasticsearch dependency
    SECURITY FIX: Use real Elasticsearch connection
    """
    from core.elasticsearch_config import get_global_elasticsearch_service

    es_service = await get_global_elasticsearch_service()
    yield es_service


async def get_database_service():
    """
    Database service dependency
    SECURITY FIX: Use real database service
    """
    from core.database import db_manager

    yield db_manager


async def get_cache_service():
    """
    Cache service dependency
    SECURITY FIX: Use real cache service
    """
    from core.cache import cache_manager

    yield cache_manager


def verify_token(token: str) -> dict[str, Any]:
    """
    JWT token'ı doğrula ve payload döndür
    """
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
    """
    Access token oluştur
    """
    import datetime

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
