"""
JWT Authentication System (Task 48.4: Enhanced with Database
Refresh Tokens). Production-ready JWT with refresh tokens,
blacklisting, and security features.

Blacklist: Redis-backed with in-memory fallback.
"""
import hashlib
import logging
import secrets
import time
from datetime import UTC, datetime, timedelta
from enum import Enum

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import get_settings

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Token türleri"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"  # noqa: S105
    EMAIL_VERIFICATION = "email_verification"


from models.enums_db import UserRole  # Canonical source — DO NOT redefine


class TokenPayload(BaseModel):
    """JWT token payload model"""

    sub: str  # user_id
    email: str
    role: UserRole
    exp: datetime
    iat: datetime
    type: TokenType
    jti: str  # JWT ID for blacklisting
    device_id: str | None = None
    permissions: list[str] = []


class JWTTokens(BaseModel):
    """JWT token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    refresh_expires_in: int


class JWTManager:
    """JWT token yönetimi ve güvenlik"""

    # Redis key prefix for blacklisted tokens
    BLACKLIST_PREFIX = "jwt:blacklist:"
    # Max in-memory blacklist entries to prevent unbounded memory growth
    MAX_MEMORY_BLACKLIST = 10_000

    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer(auto_error=False)

        # JWT ayarları
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
        self.access_token_expire_minutes = self.settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.jwt_refresh_token_expire_days

        # In-memory fallback blacklist: {identifier: added_timestamp}
        # Bounded to MAX_MEMORY_BLACKLIST; evicts oldest entries when full.
        self.blacklisted_tokens: dict[str, float] = {}

        # Redis client (initialized lazily via connect_redis)
        self._redis = None
        self._redis_available = False

        # Device tracking (brute force koruması için)
        self.device_attempts: dict[str, dict] = {}

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        username: str | None = None,
        permissions: list[str] | None = None,
        device_id: str | None = None,
    ) -> str:
        """Access token oluştur"""
        if permissions is None:
            permissions = self._get_default_permissions(role)

        expire = datetime.now(UTC) + timedelta(
            minutes=self.access_token_expire_minutes
        )

        payload = {
            "sub": user_id,
            "username": username or email.split("@")[0],
            "email": email,
            "role": role.jwt_value,  # lowercase for JWT compat
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TokenType.ACCESS.value,
            "jti": secrets.token_urlsafe(32),
            "device_id": device_id,
            "permissions": permissions,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self, user_id: str, email: str, role: UserRole, device_id: str | None = None
    ) -> str:
        """Refresh token oluştur"""
        expire = datetime.now(UTC) + timedelta(
            days=self.refresh_token_expire_days
        )

        payload = {
            "sub": user_id,
            "email": email,
            "role": role.jwt_value,  # lowercase for JWT compat
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TokenType.REFRESH.value,
            "jti": secrets.token_urlsafe(32),
            "device_id": device_id,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        permissions: list[str] | None = None,
        device_id: str | None = None,
    ) -> JWTTokens:
        """Access ve refresh token çifti oluştur"""
        access_token = self.create_access_token(
            user_id, email, role, permissions, device_id
        )
        refresh_token = self.create_refresh_token(user_id, email, role, device_id)

        return JWTTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            refresh_expires_in=self.refresh_token_expire_days * 24 * 60 * 60,
        )

    def verify_token(self, token: str, token_type: TokenType = None) -> TokenPayload:
        """Token doğrula ve payload döndür.

        Note: Uses sync in-memory blacklist only. For Redis-backed check,
        use is_blacklisted_async() in async endpoints (see core/dependencies.py).
        """
        try:
            # Token blacklist kontrolü (in-memory only; async path checks Redis)
            if self._is_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )

            # JWT decode
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Token type kontrolü
            if token_type and payload.get("type") != token_type.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected: {token_type.value}",
                )

            # Payload validation
            if not payload.get("sub") or not payload.get("email"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            # Expiration check (jwt library handles this automatically)
            # Role validation (case-insensitive via _missing_)
            role = payload.get("role")
            try:
                resolved_role = UserRole(role)
            except (ValueError, KeyError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user role in token",
                )

            return TokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                role=resolved_role,
                exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
                iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
                type=TokenType(payload["type"]),
                jti=payload.get("jti", ""),
                device_id=payload.get("device_id"),
                permissions=payload.get("permissions", []),
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {e!s}",
            )

    async def refresh_access_token(
        self, refresh_token: str, db: Session = None, request: Request = None
    ) -> JWTTokens:
        """
        Refresh token ile yeni access token oluştur (Task 48.4: Database-backed)

        Args:
            refresh_token: Refresh token string
            db: Database session (optional - for persistence)
            request: FastAPI request (optional - for IP/user-agent tracking)

        Returns:
            JWTTokens: Yeni access ve refresh token çifti
        """
        # Refresh token doğrula
        payload = self.verify_token(refresh_token, TokenType.REFRESH)

        # Database persistence varsa, refresh token'ı kontrol et
        if db:
            from models.database import RefreshToken

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            db_token = (
                db.query(RefreshToken)
                .filter(
                    RefreshToken.jti == payload.jti,
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked.is_(False),
                )
                .first()
            )

            if not db_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked or does not exist",
                )

            # Token expiration kontrolü
            if db_token.expires_at < datetime.now(UTC):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has expired",
                )

            # Usage tracking
            db_token.last_used_at = datetime.now(UTC)
            db_token.usage_count += 1

            # Revoke eski token (rotation policy)
            db_token.revoked = True
            db_token.revoked_at = datetime.now(UTC)
            db_token.revoke_reason = "rotated"

        # Yeni token çifti oluştur
        new_tokens = self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            role=payload.role,
            permissions=payload.permissions,
            device_id=payload.device_id,
        )

        # Yeni refresh token'ı database'e kaydet
        if db and request:
            self._save_refresh_token_to_db(
                db,
                new_tokens.refresh_token,
                payload.sub,
                payload.device_id,
                request,
            )

        # Eski refresh token'ı Redis + in-memory blacklist'e ekle
        await self.blacklist_token_async(refresh_token)

        # Database değişikliklerini commit et
        if db:
            db.commit()

        return new_tokens

    async def connect_redis(self, max_retries: int = 3, retry_delay: float = 2.0):
        """Connect to Redis for blacklist persistence. Called during app startup."""
        for attempt in range(1, max_retries + 1):
            try:
                from redis import asyncio as aioredis
                redis_url = self.settings.redis_url
                self._redis = await aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                await self._redis.ping()
                self._redis_available = True
                logger.info("JWT blacklist connected to Redis")
                return
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        f"JWT Redis connect attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    import asyncio
                    await asyncio.sleep(retry_delay)
                else:
                    logger.warning(
                        "JWT blacklist Redis unavailable after "
                        f"{max_retries} attempts, using in-memory fallback: {e}"
                    )
                    self._redis_available = False

    def _get_blacklist_key(self, identifier: str) -> str:
        """Build Redis key for a blacklisted token identifier."""
        return f"{self.BLACKLIST_PREFIX}{identifier}"

    def _extract_jti_and_ttl(self, token: str) -> tuple[str | None, int]:
        """Extract JTI and remaining TTL (seconds) from a token.

        Returns (jti_or_hash, ttl_seconds). TTL defaults to 24h if unreadable.

        NOTE: verify_exp=False is intentional — we need to extract JTI from
        expired tokens for blacklisting (logout of expired-but-not-yet-purged tokens).
        This method is ONLY used for blacklist key extraction, never for authentication.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},  # Intentional: see docstring
            )
            jti = payload.get("jti")
            # Calculate remaining TTL from token expiry
            exp = payload.get("exp")
            if exp:
                remaining = int(exp - datetime.now(UTC).timestamp())
                ttl = max(remaining, 60)  # minimum 60s to handle clock skew
            else:
                ttl = 86400  # 24h default
            return jti, ttl
        except (jwt.DecodeError, jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            # Can't decode: use token hash, default 24h TTL
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            return token_hash, 86400

    def _enforce_memory_limit(self):
        """Evict oldest blacklist entries when limit reached."""
        if len(self.blacklisted_tokens) < self.MAX_MEMORY_BLACKLIST:
            return
        # First pass: remove entries older than 24h (expired tokens)
        cutoff = time.time() - 86400
        expired = [k for k, ts in self.blacklisted_tokens.items() if ts < cutoff]
        for k in expired:
            del self.blacklisted_tokens[k]
        # If still over limit, evict oldest 20%
        if len(self.blacklisted_tokens) >= self.MAX_MEMORY_BLACKLIST:
            evict_count = self.MAX_MEMORY_BLACKLIST // 5
            sorted_keys = sorted(
                self.blacklisted_tokens, key=self.blacklisted_tokens.get,
            )
            for k in sorted_keys[:evict_count]:
                del self.blacklisted_tokens[k]
            logger.warning(
                f"Blacklist evicted {evict_count} oldest entries "
                f"({len(self.blacklisted_tokens)} remaining)"
            )

    def blacklist_token(self, token: str):
        """Synchronous blacklist — adds to in-memory dict.

        For Redis persistence, use blacklist_token_async() instead.
        """
        identifier, _ = self._extract_jti_and_ttl(token)
        if identifier:
            self._enforce_memory_limit()
            self.blacklisted_tokens[identifier] = time.time()

    async def blacklist_token_async(self, token: str):
        """Blacklist a token in Redis (with in-memory fallback).

        Uses SETEX so tokens auto-expire from blacklist when they would
        have expired naturally — no manual cleanup needed.
        """
        identifier, ttl = self._extract_jti_and_ttl(token)
        if not identifier:
            return

        # Always add to in-memory (immediate effect for current process)
        self._enforce_memory_limit()
        self.blacklisted_tokens[identifier] = time.time()

        # Persist to Redis if available
        if self._redis_available and self._redis:
            try:
                key = self._get_blacklist_key(identifier)
                await self._redis.setex(key, ttl, "1")
            except Exception as e:
                logger.warning(
                    "Redis blacklist write failed, disabling Redis "
                    f"(in-memory still active): {e}"
                )
                self._redis_available = False

    def _is_blacklisted(self, token: str) -> bool:
        """Synchronous blacklist check — in-memory only.

        For Redis-backed check, use is_blacklisted_async().
        """
        identifier, _ = self._extract_jti_and_ttl(token)
        return bool(identifier and identifier in self.blacklisted_tokens)

    async def is_blacklisted_async(self, token: str) -> bool:
        """Check if token is blacklisted (Redis + in-memory fallback).

        Checks in-memory first (fast path), then Redis for cross-process persistence.
        """
        identifier, _ = self._extract_jti_and_ttl(token)
        if not identifier:
            return False

        # Fast path: in-memory check
        if identifier in self.blacklisted_tokens:
            return True

        # Redis check for cross-process/restart persistence
        if self._redis_available and self._redis:
            try:
                key = self._get_blacklist_key(identifier)
                result = await self._redis.exists(key)
                if result:
                    # Sync to in-memory for faster subsequent checks
                    self.blacklisted_tokens[identifier] = time.time()
                    return True
            except Exception as e:
                logger.warning(
                    "Redis blacklist read failed, disabling Redis "
                    f"(using in-memory only): {e}"
                )
                self._redis_available = False

        return False

    def _get_default_permissions(self, role: UserRole) -> list[str]:
        """Role'e göre default permission'ları döndür"""
        permission_map = {
            UserRole.STUDENT: [
                "exam:take",
                "exam:view_results",
                "dashboard:view",
                "content:view",
                "learning_style:view",
                "zpd:view",
            ],
            UserRole.TEACHER: [
                "exam:create",
                "exam:manage",
                "exam:view_all_results",
                "student:view",
                "student:manage",
                "content:create",
                "content:manage",
                "dashboard:teacher",
                "reports:view",
            ],
            UserRole.PARENT: [
                "child:view",
                "child:track",
                "reports:child",
                "dashboard:parent",
            ],
            UserRole.ADMIN: [
                "user:manage",
                "content:admin",
                "system:monitor",
                "reports:admin",
                "dashboard:admin",
            ],
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
        }

        return permission_map.get(role, [])

    def hash_password(self, password: str) -> str:
        """Şifre hash'le"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifre doğrula"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def _cleanup_stale_device_attempts(self, max_age_minutes: int = 120) -> None:
        """Remove device_attempts entries older than max_age_minutes."""
        if len(self.device_attempts) < 100:
            return  # Skip cleanup for small dicts
        now = datetime.now(UTC)
        cutoff = timedelta(minutes=max_age_minutes)
        stale = [
            k for k, v in self.device_attempts.items()
            if now - v["window_start"] > cutoff
        ]
        for k in stale:
            del self.device_attempts[k]

    def check_rate_limit(
        self, identifier: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """Rate limiting kontrolü"""
        now = datetime.now(UTC)

        # Periodic cleanup of stale entries
        self._cleanup_stale_device_attempts()

        if identifier not in self.device_attempts:
            self.device_attempts[identifier] = {"attempts": 1, "window_start": now}
            return True  # İlk deneme de sayılır

        device_data = self.device_attempts[identifier]

        # Window reset kontrolü
        if now - device_data["window_start"] > timedelta(minutes=window_minutes):
            device_data["attempts"] = 0
            device_data["window_start"] = now

        # Attempt sayısı kontrolü
        if device_data["attempts"] >= max_attempts:
            return False

        device_data["attempts"] += 1
        return True

    def create_password_reset_token(self, user_id: str, email: str) -> str:
        """Şifre sıfırlama token'ı oluştur"""
        expire = datetime.now(UTC) + timedelta(hours=1)  # 1 saat geçerli

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TokenType.RESET_PASSWORD.value,
            "jti": secrets.token_urlsafe(32),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Email doğrulama token'ı oluştur"""
        expire = datetime.now(UTC) + timedelta(hours=24)  # 24 saat geçerli

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": TokenType.EMAIL_VERIFICATION.value,
            "jti": secrets.token_urlsafe(32),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _save_refresh_token_to_db(
        self,
        db: Session,
        refresh_token: str,
        user_id: str,
        device_id: str | None,
        request: Request,
    ):
        """
        Refresh token'ı database'e kaydet (Task 48.4)

        Args:
            db: Database session
            refresh_token: Refresh token string
            user_id: User ID
            device_id: Device ID
            request: FastAPI request for IP/user-agent
        """
        from models.database import RefreshToken

        # Token payload'ı decode et
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                # verify_exp=False: we store the token even if expired,
                # so rotation records are complete for audit/revocation
                options={"verify_exp": False},
            )
        except Exception:
            return  # Silent fail

        # Token hash oluştur
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Device bilgilerini çıkar
        user_agent = request.headers.get("user-agent", "") if request else ""
        ip_address = request.client.host if request and request.client else None

        # Device type detection (simple heuristic)
        device_type = "desktop"
        if user_agent:
            ua_lower = user_agent.lower()
            if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
                device_type = "mobile"
            elif "tablet" in ua_lower or "ipad" in ua_lower:
                device_type = "tablet"

        # Database'e kaydet
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=payload.get("jti", ""),
            device_id=device_id,
            device_name=None,  # Can be set by client
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            expires_at=datetime.fromtimestamp(payload.get("exp", 0), tz=UTC),
            revoked=False,
        )

        db.add(db_token)

    def revoke_refresh_token(
        self, db: Session, refresh_token: str | None = None, jti: str | None = None
    ):
        """
        Refresh token'ı revoke et (Task 48.4)

        Args:
            db: Database session
            refresh_token: Refresh token string (optional)
            jti: JWT ID (optional)
        """
        from models.database import RefreshToken

        if refresh_token:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            db_token = (
                db.query(RefreshToken)
                .filter(RefreshToken.token_hash == token_hash)
                .first()
            )
        elif jti:
            db_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        else:
            return

        if db_token and not db_token.revoked:
            db_token.revoked = True
            db_token.revoked_at = datetime.now(UTC)
            db_token.revoke_reason = "manual_revoke"
            db.commit()

    def revoke_all_user_tokens(self, db: Session, user_id: str):
        """
        Kullanıcının tüm refresh token'larını revoke et (Task 48.4)
        Logout from all devices

        Args:
            db: Database session
            user_id: User ID
        """
        from models.database import RefreshToken

        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        ).update(
            {
                "revoked": True,
                "revoked_at": datetime.now(UTC),
                "revoke_reason": "logout_all_devices",
            }
        )
        db.commit()

    def revoke_device_tokens(self, db: Session, user_id: str, device_id: str):
        """
        Belirli bir cihazın tüm token'larını revoke et (Task 48.4)

        Args:
            db: Database session
            user_id: User ID
            device_id: Device ID
        """
        from models.database import RefreshToken

        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id,
            RefreshToken.revoked.is_(False),
        ).update(
            {
                "revoked": True,
                "revoked_at": datetime.now(UTC),
                "revoke_reason": "device_revoke",
            }
        )
        db.commit()

    def cleanup_expired_tokens(self, db: Session):
        """
        Expired refresh token'ları database'den sil (Task 48.4)
        Maintenance task to be run periodically

        Args:
            db: Database session
        """
        from models.database import RefreshToken

        # 30 gün önce expire olmuş token'ları sil
        cutoff_date = datetime.now(UTC) - timedelta(days=30)

        db.query(RefreshToken).filter(RefreshToken.expires_at < cutoff_date).delete()
        db.commit()


# Global JWT manager instance
jwt_manager = JWTManager()


def get_jwt_manager() -> JWTManager:
    """JWT manager instance'ını döndür"""
    return jwt_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    jwt_mgr: JWTManager = Depends(get_jwt_manager),
) -> TokenPayload:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Usage::

        @app.get("/protected")
        async def protected_route(
            current_user: TokenPayload = Depends(get_current_user),
        ):
            return {"user_id": current_user.sub}

    Args:
        credentials: HTTP Bearer token from request header
        jwt_mgr: JWT manager instance

    Returns:
        TokenPayload: Decoded and validated token payload containing user info

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check Redis-backed blacklist (cross-process revocation)
    if await jwt_mgr.is_blacklisted_async(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return jwt_mgr.verify_token(token, TokenType.ACCESS)



async def get_current_active_user(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Get current user and verify they are active (not disabled/banned)

    Usage:
        @app.get("/active-only")
        async def active_route(user: TokenPayload = Depends(get_current_active_user)):
            return {"user_id": user.sub}

    Note: Currently just returns the user, but can be extended to check
    user status in database
    """
    # TODO: Add database check for user active status if needed
    # Example:
    # user_in_db = await get_user_from_db(current_user.sub)
    # if not user_in_db.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def require_role(
    required_roles: list[UserRole],
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Require user to have one of the specified roles

    Usage:
        @app.get("/admin-only")
        async def admin_route(
            user: TokenPayload = Depends(
                lambda: require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])
            )
        ):
            return {"admin_data": "..."}

    Args:
        required_roles: List of allowed roles
        current_user: Current authenticated user

    Returns:
        TokenPayload: Current user if role matches

    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    if current_user.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Insufficient permissions. Required roles: "
                f"{[r.value for r in required_roles]}"
            ),
        )

    return current_user


async def require_permission(
    required_permission: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Require user to have a specific permission

    Usage:
        @app.post("/create-exam")
        async def create_exam(
            user: TokenPayload = Depends(
                lambda: require_permission("exam:create")
            )
        ):
            return {"status": "created"}

    Args:
        required_permission: Permission string (e.g., "exam:create")
        current_user: Current authenticated user

    Returns:
        TokenPayload: Current user if permission exists

    Raises:
        HTTPException: 403 if user doesn't have required permission
    """
    # Super admin has all permissions
    if current_user.role == UserRole.SUPER_ADMIN or "*" in current_user.permissions:
        return current_user

    if required_permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission required: {required_permission}",
        )

    return current_user


async def require_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Require user to be admin or super_admin

    Usage:
        @app.get("/admin-panel")
        async def admin_panel(user: TokenPayload = Depends(require_admin)):
            return {"admin_data": "..."}

    Args:
        current_user: Current authenticated user

    Returns:
        TokenPayload: Current user if admin role

    Raises:
        HTTPException: 403 if user is not admin
    """
    admin_roles = [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    if current_user.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
