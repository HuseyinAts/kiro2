"""
KIRO2 Unified Session System
Consolidated session and token management solution
"""

import asyncio
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - sessions will be memory-only")


class SessionStatus(Enum):
    """Session status enumeration"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class TokenType(Enum):
    """Token type enumeration"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"
    API = "api"


class DeviceType(Enum):
    """Device type enumeration"""

    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    API = "api"


@dataclass
class SessionInfo:
    """Session information"""

    session_id: str
    user_id: str
    device_id: str
    device_type: DeviceType
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == SessionStatus.ACTIVE and not self.is_expired

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionInfo":
        """Create from dictionary"""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            device_id=data["device_id"],
            device_type=DeviceType(data["device_type"]),
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            status=SessionStatus(data["status"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TokenInfo:
    """Token information"""

    token_id: str
    user_id: str
    token_type: TokenType
    session_id: str | None
    created_at: datetime
    expires_at: datetime
    scopes: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "token_id": self.token_id,
            "user_id": self.user_id,
            "token_type": self.token_type.value,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "scopes": list(self.scopes),
            "metadata": self.metadata,
        }


class SessionConfig:
    """Session management configuration"""

    def __init__(
        self,
        # Session settings
        session_timeout: int = 3600,  # 1 hour
        max_sessions_per_user: int = 5,
        extend_on_activity: bool = True,
        # Token settings
        access_token_lifetime: int = 3600,  # 1 hour
        refresh_token_lifetime: int = 86400 * 7,  # 7 days
        jwt_secret: str = None,
        jwt_algorithm: str = "HS256",
        # Security settings
        require_device_verification: bool = False,
        track_ip_changes: bool = True,
        max_failed_attempts: int = 5,
        lockout_duration: int = 300,  # 5 minutes
        # Redis settings
        redis_url: str = "redis://localhost:6379/1",
        redis_key_prefix: str = "kiro2:session",
        # Cleanup settings
        cleanup_interval: int = 3600,  # 1 hour
        enable_cleanup: bool = True,
    ):
        self.session_timeout = session_timeout
        self.max_sessions_per_user = max_sessions_per_user
        self.extend_on_activity = extend_on_activity

        self.access_token_lifetime = access_token_lifetime
        self.refresh_token_lifetime = refresh_token_lifetime
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.jwt_algorithm = jwt_algorithm

        self.require_device_verification = require_device_verification
        self.track_ip_changes = track_ip_changes
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration

        self.redis_url = redis_url
        self.redis_key_prefix = redis_key_prefix

        self.cleanup_interval = cleanup_interval
        self.enable_cleanup = enable_cleanup


class DeviceFingerprint:
    """Device fingerprinting for security"""

    @staticmethod
    def generate_device_id(
        user_agent: str, ip_address: str, additional_data: dict[str, Any] = None
    ) -> str:
        """Generate device fingerprint"""
        fingerprint_data = {
            "user_agent": user_agent,
            "ip_network": ".".join(ip_address.split(".")[:3])
            + ".0",  # Network-level IP
            **(additional_data or {}),
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    @staticmethod
    def detect_device_type(user_agent: str) -> DeviceType:
        """Detect device type from user agent"""
        user_agent_lower = user_agent.lower()

        if any(
            mobile in user_agent_lower
            for mobile in ["mobile", "android", "iphone", "ipad"]
        ):
            if "ipad" in user_agent_lower or "tablet" in user_agent_lower:
                return DeviceType.TABLET
            return DeviceType.MOBILE
        if any(desktop in user_agent_lower for desktop in ["electron", "desktop"]):
            return DeviceType.DESKTOP
        return DeviceType.WEB


class UnifiedSessionManager:
    """
    Unified session manager combining session and token management:
    - Session lifecycle management
    - JWT token generation and validation
    - Device tracking and fingerprinting
    - Security features (lockouts, IP tracking)
    - Redis-based storage with fallback
    """

    def __init__(self, config: SessionConfig | None = None):
        self.config = config or SessionConfig()
        self.redis_client: redis.Redis | None = None
        self._memory_sessions: dict[str, SessionInfo] = {}
        self._memory_tokens: dict[str, TokenInfo] = {}
        self._failed_attempts: dict[str, tuple[int, datetime]] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize session manager"""
        if self._initialized:
            return

        try:
            # Initialize Redis connection if available
            if REDIS_AVAILABLE:
                self.redis_client = redis.from_url(
                    self.config.redis_url, encoding="utf-8", decode_responses=True
                )

                # Test Redis connection
                try:
                    await self.redis_client.ping()
                    logger.info("Redis connection established for sessions")
                except Exception as e:
                    logger.warning(
                        f"Redis connection failed, using memory storage: {e}"
                    )
                    self.redis_client = None

            # Start cleanup task
            if self.config.enable_cleanup:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            self._initialized = True
            logger.info("Unified session manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown session manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

    def _make_redis_key(self, key_type: str, identifier: str) -> str:
        """Create Redis key"""
        return f"{self.config.redis_key_prefix}:{key_type}:{identifier}"

    async def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        additional_data: dict[str, Any] = None,
    ) -> SessionInfo:
        """Create new session"""
        # Generate device fingerprint
        device_id = DeviceFingerprint.generate_device_id(
            user_agent, ip_address, additional_data
        )
        device_type = DeviceFingerprint.detect_device_type(user_agent)

        # Check session limits
        user_sessions = await self.get_user_sessions(user_id)
        if len(user_sessions) >= self.config.max_sessions_per_user:
            # Remove oldest session
            oldest_session = min(user_sessions, key=lambda s: s.last_activity)
            await self.revoke_session(oldest_session.session_id)

        # Create session
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()

        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(seconds=self.config.session_timeout),
            metadata=additional_data or {},
        )

        # Store session
        await self._store_session(session)

        logger.info(f"Session created for user {user_id}: {session_id}")
        return session

    async def _store_session(self, session: SessionInfo) -> None:
        """Store session in Redis or memory"""
        session_key = self._make_redis_key("session", session.session_id)
        user_sessions_key = self._make_redis_key("user_sessions", session.user_id)

        if self.redis_client:
            try:
                # Store session data
                await self.redis_client.hset(session_key, mapping=session.to_dict())

                # Add to user sessions set
                await self.redis_client.sadd(user_sessions_key, session.session_id)

                # Set expiration
                expire_seconds = int(
                    (session.expires_at - datetime.now()).total_seconds()
                )
                if expire_seconds > 0:
                    await self.redis_client.expire(session_key, expire_seconds)
                    await self.redis_client.expire(user_sessions_key, expire_seconds)

            except Exception as e:
                logger.error(f"Failed to store session in Redis: {e}")
                # Fallback to memory
                self._memory_sessions[session.session_id] = session
        else:
            # Memory storage
            self._memory_sessions[session.session_id] = session

    async def get_session(self, session_id: str) -> SessionInfo | None:
        """Get session by ID"""
        session_key = self._make_redis_key("session", session_id)

        if self.redis_client:
            try:
                session_data = await self.redis_client.hgetall(session_key)
                if session_data:
                    return SessionInfo.from_dict(session_data)
            except Exception as e:
                logger.error(f"Failed to get session from Redis: {e}")

        # Fallback to memory
        return self._memory_sessions.get(session_id)

    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            return False

        now = datetime.now()
        session.last_activity = now

        # Extend expiration if configured
        if self.config.extend_on_activity:
            session.expires_at = now + timedelta(seconds=self.config.session_timeout)

        await self._store_session(session)
        return True

    async def get_user_sessions(self, user_id: str) -> list[SessionInfo]:
        """Get all sessions for a user"""
        user_sessions_key = self._make_redis_key("user_sessions", user_id)
        sessions = []

        if self.redis_client:
            try:
                session_ids = await self.redis_client.smembers(user_sessions_key)
                for session_id in session_ids:
                    session = await self.get_session(session_id)
                    if session and session.is_active:
                        sessions.append(session)
            except Exception as e:
                logger.error(f"Failed to get user sessions from Redis: {e}")

        # Add memory sessions
        for session in self._memory_sessions.values():
            if session.user_id == user_id and session.is_active:
                sessions.append(session)

        return sessions

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.status = SessionStatus.REVOKED
        await self._store_session(session)

        # Remove from Redis
        if self.redis_client:
            try:
                session_key = self._make_redis_key("session", session_id)
                user_sessions_key = self._make_redis_key(
                    "user_sessions", session.user_id
                )

                await self.redis_client.delete(session_key)
                await self.redis_client.srem(user_sessions_key, session_id)
            except Exception as e:
                logger.error(f"Failed to revoke session in Redis: {e}")

        # Remove from memory
        self._memory_sessions.pop(session_id, None)

        logger.info(f"Session revoked: {session_id}")
        return True

    async def revoke_user_sessions(
        self, user_id: str, except_session_id: str = None
    ) -> int:
        """Revoke all sessions for a user"""
        sessions = await self.get_user_sessions(user_id)
        revoked_count = 0

        for session in sessions:
            if session.session_id != except_session_id:
                if await self.revoke_session(session.session_id):
                    revoked_count += 1

        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count

    def generate_access_token(
        self,
        user_id: str,
        session_id: str,
        scopes: set[str] = None,
        custom_claims: dict[str, Any] = None,
    ) -> str:
        """Generate JWT access token"""
        now = datetime.now()
        token_id = secrets.token_urlsafe(16)

        payload = {
            "jti": token_id,
            "sub": user_id,
            "sid": session_id,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(seconds=self.config.access_token_lifetime)).timestamp()
            ),
            "type": TokenType.ACCESS.value,
            "scopes": list(scopes or set()),
            **(custom_claims or {}),
        }

        token = jwt.encode(
            payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm
        )

        # Store token info
        token_info = TokenInfo(
            token_id=token_id,
            user_id=user_id,
            token_type=TokenType.ACCESS,
            session_id=session_id,
            created_at=now,
            expires_at=now + timedelta(seconds=self.config.access_token_lifetime),
            scopes=scopes or set(),
        )

        asyncio.create_task(self._store_token(token_info))

        return token

    def generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT refresh token"""
        now = datetime.now()
        token_id = secrets.token_urlsafe(16)

        payload = {
            "jti": token_id,
            "sub": user_id,
            "sid": session_id,
            "iat": int(now.timestamp()),
            "exp": int(
                (
                    now + timedelta(seconds=self.config.refresh_token_lifetime)
                ).timestamp()
            ),
            "type": TokenType.REFRESH.value,
        }

        token = jwt.encode(
            payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm
        )

        # Store token info
        token_info = TokenInfo(
            token_id=token_id,
            user_id=user_id,
            token_type=TokenType.REFRESH,
            session_id=session_id,
            created_at=now,
            expires_at=now + timedelta(seconds=self.config.refresh_token_lifetime),
        )

        asyncio.create_task(self._store_token(token_info))

        return token

    async def _store_token(self, token_info: TokenInfo) -> None:
        """Store token information"""
        if self.redis_client:
            try:
                token_key = self._make_redis_key("token", token_info.token_id)
                await self.redis_client.hset(token_key, mapping=token_info.to_dict())

                expire_seconds = int(
                    (token_info.expires_at - datetime.now()).total_seconds()
                )
                if expire_seconds > 0:
                    await self.redis_client.expire(token_key, expire_seconds)

            except Exception as e:
                logger.error(f"Failed to store token in Redis: {e}")
                self._memory_tokens[token_info.token_id] = token_info
        else:
            self._memory_tokens[token_info.token_id] = token_info

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )

            # Check if token is revoked (if tracking in Redis/memory)
            token_id = payload.get("jti")
            if token_id:
                # Could add blacklist check here
                pass

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")

        return None

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str] | None:
        """Refresh access token using refresh token"""
        payload = self.validate_token(refresh_token)
        if not payload or payload.get("type") != TokenType.REFRESH.value:
            return None

        user_id = payload.get("sub")
        session_id = payload.get("sid")

        # Verify session is still active
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            return None

        # Generate new tokens
        new_access_token = self.generate_access_token(user_id, session_id)
        new_refresh_token = self.generate_refresh_token(user_id, session_id)

        return new_access_token, new_refresh_token

    async def _cleanup_loop(self) -> None:
        """Background cleanup of expired sessions and tokens"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired(self) -> None:
        """Clean up expired sessions and tokens"""
        now = datetime.now()
        cleaned_sessions = 0
        cleaned_tokens = 0

        # Cleanup memory sessions
        expired_sessions = [
            sid
            for sid, session in self._memory_sessions.items()
            if session.is_expired or session.status != SessionStatus.ACTIVE
        ]

        for session_id in expired_sessions:
            del self._memory_sessions[session_id]
            cleaned_sessions += 1

        # Cleanup memory tokens
        expired_tokens = [
            tid for tid, token in self._memory_tokens.items() if token.is_expired
        ]

        for token_id in expired_tokens:
            del self._memory_tokens[token_id]
            cleaned_tokens += 1

        if cleaned_sessions > 0 or cleaned_tokens > 0:
            logger.info(
                f"Cleaned up {cleaned_sessions} sessions and {cleaned_tokens} tokens"
            )

    async def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self._memory_sessions)
        active_sessions = len(
            [s for s in self._memory_sessions.values() if s.is_active]
        )

        if self.redis_client:
            try:
                # Count Redis sessions (approximate)
                redis_sessions = 0
                async for key in self.redis_client.scan_iter(
                    match=f"{self.config.redis_key_prefix}:session:*"
                ):
                    redis_sessions += 1
                total_sessions += redis_sessions
            except Exception:
                pass

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "memory_sessions": len(self._memory_sessions),
            "redis_available": self.redis_client is not None,
            "config": {
                "session_timeout": self.config.session_timeout,
                "max_sessions_per_user": self.config.max_sessions_per_user,
                "access_token_lifetime": self.config.access_token_lifetime,
                "refresh_token_lifetime": self.config.refresh_token_lifetime,
            },
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform session system health check"""
        status = {
            "initialized": self._initialized,
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": False,
            "stats": await self.get_session_stats(),
        }

        if self.redis_client:
            try:
                await self.redis_client.ping()
                status["redis_connected"] = True
            except Exception as e:
                status["redis_error"] = str(e)

        return status


# Global instance
_session_manager: UnifiedSessionManager | None = None


def get_session_manager() -> UnifiedSessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = UnifiedSessionManager()
    return _session_manager


async def initialize_sessions():
    """Initialize session system"""
    manager = get_session_manager()
    await manager.initialize()


# Backward compatibility aliases
SessionManager = UnifiedSessionManager
TokenManager = UnifiedSessionManager
SessionManagement = UnifiedSessionManager
TokenManagement = UnifiedSessionManager
