"""
API Key Management System (Task 48.6)
Scoped API keys for third-party integrations

Features:
- API key generation with crypto-secure randomness
- Scoped permissions (read-only, write, admin)
- IP whitelisting
- Rate limiting per key
- Key rotation
- Usage tracking
- Automatic expiration

Session 153 (GF117 real fix): ported from sync `sqlalchemy.orm.Session` to
`sqlalchemy.ext.asyncio.AsyncSession`. Previously this module used
`self.db.query(...)` + `self.db.commit()` against an async engine via a
`Session(bind=db.bind.sync_engine)` shim in `api/api_key_api.py`, which
tripped `MissingGreenlet` / `greenlet_spawn has not been called` on every
request. Session 149 shimmed the callers with a 503 handler-boundary
degrade; this is the follow-up real port.

Also removed the four wrapped `HTTPException(500/401, detail=f"...{e}")`
re-raises inside this module. They defeated the handler's
`except HTTPException: raise` guard by burying internal errors inside
wrapped 5xx's, which is exactly the anti-pattern flagged in
`.claude/rules/middleware.md`. Legitimate 4xx HTTPExceptions (401 invalid
key, 403 IP / scope, 404 not found, 429 rate limit) are preserved — those
represent real API semantics that handlers should propagate unchanged.

Author: Claude
Date: 2025-10-27 (original) / 2026-04-12 (async port)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum

import redis
from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.structured_logger import get_logger

logger = get_logger("api_key_manager")


class APIKeyScope(str, Enum):
    """API key permission scopes"""

    # Read-only scopes
    READ_EXAM = "read:exam"
    READ_CONTENT = "read:content"
    READ_STUDENT = "read:student"
    READ_ANALYTICS = "read:analytics"

    # Write scopes
    WRITE_EXAM = "write:exam"
    WRITE_CONTENT = "write:content"
    WRITE_STUDENT = "write:student"

    # Admin scopes
    ADMIN_USER = "admin:user"
    ADMIN_SYSTEM = "admin:system"

    # Special scopes
    ALL = "*"  # Full access (use with caution)


class APIKeyPrefix:
    """API key prefix for identification"""

    # Prefix format: kiro2_<env>_<random>
    # Example: kiro2_prod_1a2b3c4d
    PRODUCTION = "kiro2_prod"
    STAGING = "kiro2_stag"
    DEVELOPMENT = "kiro2_dev"
    TEST = "kiro2_test"


class APIKeyManager:
    """
    API Key Management System (Task 48.6)

    Usage:
        manager = APIKeyManager(db)
        api_key = await manager.create_api_key(
            user_id="user_123",
            name="Integration API Key",
            scopes=[APIKeyScope.READ_EXAM, APIKeyScope.READ_CONTENT],
            rate_limit=1000
        )
    """

    def __init__(
        self,
        db: AsyncSession,
        environment: str = "production",
        redis_client: redis.Redis | None = None,
    ):
        self.db = db
        self.environment = environment

        # Initialize Redis client for rate limiting
        if redis_client:
            self.redis_client = redis_client
        else:
            try:
                settings = get_settings()
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    db=0,
                    decode_responses=True,
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established for API key rate limiting")
            except Exception as e:
                logger.warning(
                    f"Redis connection failed, falling back to in-memory rate limiting: {e}"
                )
                self.redis_client = None

        # Environment prefix mapping
        self.prefix_map = {
            "production": APIKeyPrefix.PRODUCTION,
            "staging": APIKeyPrefix.STAGING,
            "development": APIKeyPrefix.DEVELOPMENT,
            "test": APIKeyPrefix.TEST,
        }

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: list[APIKeyScope],
        description: str | None = None,
        rate_limit: int = 1000,
        expires_in_days: int | None = None,
        allowed_ips: list[str] | None = None,
        request: Request = None,
    ) -> dict[str, str]:
        """
        Create new API key (Task 48.6)

        Args:
            user_id: Owner user ID
            name: Human-readable name
            scopes: List of permission scopes
            description: Optional description
            rate_limit: Requests per hour (default: 1000)
            expires_in_days: Expiration period (None = never expires)
            allowed_ips: IP whitelist (None = all IPs allowed)
            request: FastAPI request for IP tracking

        Returns:
            Dictionary with api_key (plaintext - show once!) and metadata
        """
        from models.database import APIKey

        # Generate API key (crypto-secure)
        api_key = self._generate_api_key()

        # Hash API key for storage
        key_hash = self._hash_api_key(api_key)

        # Extract prefix (first 8 chars after environment prefix)
        prefix = api_key.split("_")[2][:8] if "_" in api_key else api_key[:8]

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        # Get IP address
        ip_address = request.client.host if request and request.client else None

        # Create database entry
        db_api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=prefix,
            name=name,
            description=description,
            scopes={"scopes": [scope.value for scope in scopes]},
            allowed_ips={"ips": allowed_ips} if allowed_ips else None,
            rate_limit=rate_limit,
            is_active=True,
            expires_at=expires_at,
            created_from_ip=ip_address,
        )

        try:
            self.db.add(db_api_key)
            await self.db.commit()
            await self.db.refresh(db_api_key)
        except Exception:
            await self.db.rollback()
            raise

        logger.info(
            f"[API KEY] Created new API key: {name}",
            extra_data={
                "user_id": user_id,
                "api_key_id": db_api_key.id,
                "scopes": [s.value for s in scopes],
                "rate_limit": rate_limit,
            },
        )

        # Return plaintext key (only time it's visible!)
        return {
            "api_key": api_key,  # IMPORTANT: Show only once!
            "api_key_id": db_api_key.id,
            "prefix": prefix,
            "name": name,
            "scopes": [s.value for s in scopes],
            "rate_limit": rate_limit,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "created_at": db_api_key.created_at.isoformat(),
        }

    async def verify_api_key(
        self,
        api_key: str,
        required_scope: APIKeyScope | None = None,
        request: Request = None,
    ) -> dict[str, any]:
        """
        Verify API key and check permissions (Task 48.6)

        Args:
            api_key: API key to verify
            required_scope: Required permission scope
            request: FastAPI request for IP check and rate limiting

        Returns:
            Dictionary with user_id and scopes

        Raises:
            HTTPException: If key is invalid, revoked, expired, or lacks permissions
        """
        from models.database import APIKey

        # Hash API key
        key_hash = self._hash_api_key(api_key)

        # Find API key in database
        result = await self.db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,  # noqa: E712
                APIKey.revoked == False,  # noqa: E712
            )
        )
        db_api_key = result.scalar_one_or_none()

        if not db_api_key:
            logger.warning(
                "[API KEY] Invalid or revoked API key attempted",
                extra_data={"key_hash": key_hash[:16]},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API key",
            )

        # Check expiration
        if db_api_key.expires_at and db_api_key.expires_at < datetime.now(UTC):
            logger.warning(
                "[API KEY] Expired API key attempted",
                extra_data={
                    "api_key_id": db_api_key.id,
                    "expired_at": db_api_key.expires_at.isoformat(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
            )

        # Check IP whitelist
        if request and db_api_key.allowed_ips:
            client_ip = request.client.host if request.client else None
            allowed_ips = db_api_key.allowed_ips.get("ips", [])
            if client_ip not in allowed_ips:
                logger.warning(
                    "[API KEY] IP not whitelisted",
                    extra_data={
                        "api_key_id": db_api_key.id,
                        "client_ip": client_ip,
                        "allowed_ips": allowed_ips,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not whitelisted",
                )

        # Check rate limit
        if request:
            self._check_rate_limit(db_api_key, request)

        # Check required scope
        api_key_scopes = db_api_key.scopes.get("scopes", [])
        if required_scope:
            # Check if key has required scope or wildcard
            if "*" not in api_key_scopes and required_scope.value not in api_key_scopes:
                logger.warning(
                    "[API KEY] Insufficient permissions",
                    extra_data={
                        "api_key_id": db_api_key.id,
                        "required_scope": required_scope.value,
                        "api_key_scopes": api_key_scopes,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key lacks required scope: {required_scope.value}",
                )

        # Update usage tracking
        db_api_key.last_used_at = datetime.now(UTC)
        db_api_key.usage_count += 1
        if request and request.client:
            db_api_key.last_used_ip = request.client.host

        await self.db.commit()

        return {
            "user_id": db_api_key.user_id,
            "api_key_id": db_api_key.id,
            "scopes": api_key_scopes,
            "rate_limit": db_api_key.rate_limit,
        }

    async def revoke_api_key(self, api_key_id: str, reason: str = "manual_revoke"):
        """
        Revoke API key (Task 48.6)

        Args:
            api_key_id: API key ID to revoke
            reason: Revocation reason
        """
        from models.database import APIKey

        result = await self.db.execute(select(APIKey).where(APIKey.id == api_key_id))
        db_api_key = result.scalar_one_or_none()

        if not db_api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {api_key_id} not found",
            )

        db_api_key.revoked = True
        db_api_key.revoked_at = datetime.now(UTC)
        db_api_key.revoke_reason = reason
        db_api_key.is_active = False

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        logger.info(
            f"[API KEY] Revoked API key: {db_api_key.name}",
            extra_data={"api_key_id": api_key_id, "reason": reason},
        )

    async def rotate_api_key(
        self, api_key_id: str, request: Request = None
    ) -> dict[str, str]:
        """
        Rotate API key (generates new key, revokes old) (Task 48.6)

        Args:
            api_key_id: API key ID to rotate
            request: FastAPI request for IP tracking

        Returns:
            New API key details
        """
        from models.database import APIKey

        # Get old key
        result = await self.db.execute(select(APIKey).where(APIKey.id == api_key_id))
        old_key = result.scalar_one_or_none()

        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {api_key_id} not found",
            )

        # Create new key with same settings
        scopes = [APIKeyScope(s) for s in old_key.scopes.get("scopes", [])]
        allowed_ips = old_key.allowed_ips.get("ips") if old_key.allowed_ips else None

        new_key = await self.create_api_key(
            user_id=old_key.user_id,
            name=f"{old_key.name} (Rotated)",
            scopes=scopes,
            description=f"Rotated from {old_key.name}",
            rate_limit=old_key.rate_limit,
            expires_in_days=(
                (old_key.expires_at - datetime.now(UTC)).days
                if old_key.expires_at
                else None
            ),
            allowed_ips=allowed_ips,
            request=request,
        )

        # Revoke old key
        await self.revoke_api_key(api_key_id, reason="rotated")

        logger.info(
            f"[API KEY] Rotated API key: {old_key.name}",
            extra_data={
                "old_key_id": api_key_id,
                "new_key_id": new_key["api_key_id"],
            },
        )

        return new_key

    def _generate_api_key(self) -> str:
        """
        Generate crypto-secure API key

        Format: kiro2_<env>_<random_32_chars>
        Example: kiro2_prod_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
        """
        prefix = self.prefix_map.get(self.environment, APIKeyPrefix.PRODUCTION)
        random_part = secrets.token_urlsafe(32)  # 32 bytes = 43 chars base64

        return f"{prefix}_{random_part}"

    def _hash_api_key(self, api_key: str) -> str:
        """
        Hash API key for secure storage

        Args:
            api_key: Plaintext API key

        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _check_rate_limit(self, api_key, request: Request):
        """
        Check rate limit for API key with Redis-based sliding window (Task 48.6)

        Args:
            api_key: APIKey database model
            request: FastAPI request

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not api_key.rate_limit:
            return  # No rate limit set

        now = datetime.now(UTC)
        window = 3600  # 1 hour in seconds
        key = f"api_key_rate_limit:{api_key.id}"

        if self.redis_client:
            # Redis-based sliding window rate limiting
            try:
                pipe = self.redis_client.pipeline()

                # Remove old entries outside the window
                pipe.zremrangebyscore(key, 0, (now.timestamp() - window))

                # Count current requests in the window
                pipe.zcard(key)

                # Add current request timestamp
                pipe.zadd(key, {str(now.timestamp()): now.timestamp()})

                # Set expiration to cleanup
                pipe.expire(key, window + 60)

                results = pipe.execute()
                current_count = results[1]

                if current_count >= api_key.rate_limit:
                    logger.warning(
                        "[API KEY] Rate limit exceeded",
                        extra_data={
                            "api_key_id": api_key.id,
                            "current_count": current_count,
                            "rate_limit": api_key.rate_limit,
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "rate_limit_exceeded",
                            "message": f"Rate limit of {api_key.rate_limit} requests per hour exceeded",
                            "retry_after": window,
                        },
                    )

                logger.debug(
                    "[API KEY] Rate limit check passed (Redis)",
                    extra_data={
                        "api_key_id": api_key.id,
                        "current_count": current_count,
                        "rate_limit": api_key.rate_limit,
                    },
                )

            except redis.RedisError as e:
                logger.error(
                    f"[API KEY] Redis rate limit check failed: {e}, falling back to in-memory"
                )
                self._check_rate_limit_fallback(api_key, now, window)
        else:
            # Fallback to in-memory rate limiting
            self._check_rate_limit_fallback(api_key, now, window)

    def _check_rate_limit_fallback(self, api_key, now: datetime, window: int):
        """
        Fallback in-memory rate limiting when Redis is unavailable

        Args:
            api_key: APIKey database model
            now: Current datetime
            window: Time window in seconds
        """
        # Simple database-based check (not ideal for high traffic)
        if api_key.last_used_at:
            time_since_last_use = now - api_key.last_used_at
            if time_since_last_use.total_seconds() < window:
                # Rough estimate - production should use proper sliding window
                # This is a simplified check that resets hourly
                estimated_rate = api_key.usage_count / max(
                    time_since_last_use.total_seconds() / window, 1
                )

                if estimated_rate >= api_key.rate_limit:
                    logger.warning(
                        "[API KEY] Rate limit exceeded (fallback)",
                        extra_data={
                            "api_key_id": api_key.id,
                            "estimated_rate": estimated_rate,
                            "rate_limit": api_key.rate_limit,
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "rate_limit_exceeded",
                            "message": f"Rate limit of {api_key.rate_limit} requests per hour exceeded",
                            "retry_after": window - time_since_last_use.total_seconds(),
                        },
                    )

        logger.debug(
            "[API KEY] Rate limit check passed (fallback)",
            extra_data={
                "api_key_id": api_key.id,
                "usage_count": api_key.usage_count,
                "rate_limit": api_key.rate_limit,
            },
        )


def get_api_key_manager(
    db: AsyncSession, environment: str = "production"
) -> APIKeyManager:
    """
    Get API key manager instance

    Args:
        db: Async database session
        environment: Environment name (production, staging, development, test)

    Returns:
        APIKeyManager instance
    """
    return APIKeyManager(db, environment)
