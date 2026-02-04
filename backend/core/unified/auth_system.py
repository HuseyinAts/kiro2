"""
KIRO2 Unified Authentication System
Consolidated authentication solution combining all auth functionality
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import hashlib
import logging
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods"""

    JWT_TOKEN = "jwt_token"
    SESSION_TOKEN = "session_token"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    MULTI_FACTOR = "multi_factor"


class UserRole(Enum):
    """User roles for RBAC"""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"
    SUPER_ADMIN = "super_admin"


class AuthEvent(Enum):
    """Authentication events for logging"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class AuthConfig:
    """Unified authentication configuration"""

    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 30
    jwt_refresh_expiry_days: int = 7

    # Session Configuration
    session_timeout_minutes: int = 60
    session_refresh_threshold_minutes: int = 15
    max_concurrent_sessions: int = 3

    # Security Configuration
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Multi-factor Authentication
    mfa_enabled: bool = False
    mfa_issuer: str = "KIRO2"
    mfa_window: int = 1

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 15

    # Turkish Optimization
    turkish_locale: str = "tr_TR"
    turkish_timezone: str = "Europe/Istanbul"


@dataclass
class AuthContext:
    """Authentication context for current request"""

    user_id: str | None = None
    username: str | None = None
    email: str | None = None
    roles: set[UserRole] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)
    session_id: str | None = None
    token_type: AuthMethod | None = None
    authenticated: bool = False
    mfa_verified: bool = False
    device_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class LoginAttempt:
    """Track login attempts for rate limiting"""

    username: str
    ip_address: str
    attempts: int = 0
    first_attempt: datetime = field(default_factory=datetime.now)
    last_attempt: datetime = field(default_factory=datetime.now)
    locked_until: datetime | None = None


class UnifiedAuthManager:
    """
    Unified authentication manager combining all auth functionality:
    - JWT token management
    - Session management
    - Multi-factor authentication
    - Rate limiting and security
    - Role-based access control (RBAC)
    - Turkish optimization
    """

    def __init__(self, config: AuthConfig | None = None):
        self.config = config or AuthConfig()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer(auto_error=False)
        self.optional_security = HTTPBearer(auto_error=False)

        # In-memory stores (should be replaced with Redis in production)
        self.active_sessions: dict[str, AuthContext] = {}
        self.refresh_tokens: dict[str, str] = {}  # refresh_token -> user_id
        self.login_attempts: dict[str, LoginAttempt] = {}
        self.blacklisted_tokens: set[str] = set()

    async def initialize(self) -> None:
        """Initialize authentication manager"""
        try:
            # Initialize password hashing
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            # Initialize Redis client for rate limiting and session storage
            try:
                import redis

                self.redis_client = redis.Redis(
                    host=self.config.get("redis_host", "localhost"),
                    port=self.config.get("redis_port", 6379),
                    password=self.config.get("redis_password", None),
                    db=0,
                    decode_responses=True,
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established for authentication system")
            except Exception as e:
                logger.warning(
                    f"Redis connection failed, some features may be limited: {e}"
                )
                self.redis_client = None

            # Rate limiting backend initialized via Redis client
            # Audit logging initialized via structured logger

            logger.info(
                "Auth manager initialized successfully with rate limiting support"
            )

        except Exception as e:
            logger.error(f"Failed to initialize auth manager: {e}")
            raise

    # Password Management
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Validate password strength according to Turkish standards"""
        errors = []

        if len(password) < self.config.password_min_length:
            errors.append(
                f"Şifre en az {self.config.password_min_length} karakter olmalıdır"
            )

        if self.config.password_require_uppercase and not any(
            c.isupper() for c in password
        ):
            errors.append("Şifre en az bir büyük harf içermelidir")

        if self.config.password_require_numbers and not any(
            c.isdigit() for c in password
        ):
            errors.append("Şifre en az bir rakam içermelidir")

        if self.config.password_require_special and not any(
            c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password
        ):
            errors.append("Şifre en az bir özel karakter içermelidir")

        # Check for Turkish characters
        turkish_chars = "çğıöşüÇĞIÖŞÜ"
        if any(c in turkish_chars for c in password):
            errors.append("Şifre Türkçe karakter içeremez (güvenlik nedeniyle)")

        return len(errors) == 0, errors

    # Token Management
    def create_access_token(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        extra_claims: dict | None = None,
    ) -> str:
        """Create JWT access token"""
        now = datetime.now(UTC)
        expiry = now + timedelta(minutes=self.config.jwt_expiry_minutes)

        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "iat": now.timestamp(),
            "exp": expiry.timestamp(),
            "type": "access",
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
        token = secrets.token_urlsafe(32)
        self.refresh_tokens[token] = user_id
        return token

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode JWT token"""
        try:
            if token in self.blacklisted_tokens:
                return None

            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Check expiry
            if datetime.fromtimestamp(payload["exp"], UTC) < datetime.now(UTC):
                return None

            return payload

        except jwt.InvalidTokenError:
            return None

    def blacklist_token(self, token: str) -> None:
        """Blacklist a token (logout)"""
        self.blacklisted_tokens.add(token)

    async def refresh_access_token(
        self, refresh_token: str, db_session=None
    ) -> tuple[str, str] | None:
        """Refresh access token using refresh token"""
        user_id = self.refresh_tokens.get(refresh_token)
        if not user_id:
            return None

        # Get user data from database
        try:
            if db_session:
                from sqlalchemy import select
                from models.database import User

                result = await db_session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user or not user.is_active:
                    logger.warning(
                        f"User {user_id} not found or inactive for token refresh"
                    )
                    return None

                username = user.username
                roles = [user.role.value]
            else:
                # Fallback: use minimal user data
                logger.warning(
                    "No database session provided for token refresh, using minimal data"
                )
                username = "user"
                roles = ["student"]

            new_access_token = self.create_access_token(user_id, username, roles)
            new_refresh_token = self.create_refresh_token(user_id)

            # Remove old refresh token
            del self.refresh_tokens[refresh_token]

            return new_access_token, new_refresh_token

        except Exception as e:
            logger.error(f"Error refreshing token for user {user_id}: {e}")
            return None

    # Session Management
    def create_session(
        self,
        user_id: str,
        username: str,
        roles: list[UserRole],
        ip_address: str,
        user_agent: str,
    ) -> str:
        """Create user session"""
        session_id = str(uuid.uuid4())

        context = AuthContext(
            user_id=user_id,
            username=username,
            roles=set(roles),
            session_id=session_id,
            token_type=AuthMethod.SESSION_TOKEN,
            authenticated=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.active_sessions[session_id] = context
        return session_id

    def get_session(self, session_id: str) -> AuthContext | None:
        """Get active session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        # Check session timeout
        if (datetime.now() - session.last_activity).total_seconds() > (
            self.config.session_timeout_minutes * 60
        ):
            self.end_session(session_id)
            return None

        # Update last activity
        session.last_activity = datetime.now()
        return session

    def end_session(self, session_id: str) -> bool:
        """End user session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def end_all_user_sessions(self, user_id: str) -> int:
        """End all sessions for a user"""
        sessions_to_remove = [
            sid for sid, ctx in self.active_sessions.items() if ctx.user_id == user_id
        ]

        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]

        return len(sessions_to_remove)

    # Rate Limiting
    def check_rate_limit(self, identifier: str, ip_address: str) -> bool:
        """Check if user/IP is rate limited"""
        key = f"{identifier}:{ip_address}"
        attempt = self.login_attempts.get(key)

        if not attempt:
            return True

        # Check if still locked out
        if attempt.locked_until and datetime.now() < attempt.locked_until:
            return False

        # Check rate limit window
        window_start = datetime.now() - timedelta(
            minutes=self.config.rate_limit_window_minutes
        )
        if attempt.first_attempt < window_start:
            # Reset counter
            self.login_attempts[key] = LoginAttempt(
                username=identifier, ip_address=ip_address, attempts=0
            )
            return True

        return attempt.attempts < self.config.max_login_attempts

    def record_login_attempt(
        self, identifier: str, ip_address: str, success: bool
    ) -> None:
        """Record login attempt for rate limiting"""
        key = f"{identifier}:{ip_address}"
        attempt = self.login_attempts.get(
            key, LoginAttempt(username=identifier, ip_address=ip_address)
        )

        if success:
            # Reset on successful login
            if key in self.login_attempts:
                del self.login_attempts[key]
        else:
            attempt.attempts += 1
            attempt.last_attempt = datetime.now()

            # Lock out if too many attempts
            if attempt.attempts >= self.config.max_login_attempts:
                attempt.locked_until = datetime.now() + timedelta(
                    minutes=self.config.lockout_duration_minutes
                )

            self.login_attempts[key] = attempt

    # Authentication Methods
    async def authenticate_user(
        self, username: str, password: str, ip_address: str, db_session=None
    ) -> AuthContext | None:
        """Authenticate user with username/password"""
        # Check rate limiting
        if not self.check_rate_limit(username, ip_address):
            self.record_login_attempt(username, ip_address, False)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla başarısız giriş denemesi. Lütfen daha sonra tekrar deneyin.",
            )

        try:
            # Get user from database
            if db_session:
                from sqlalchemy import select
                from models.database import User

                result = await db_session.execute(
                    select(User).where(
                        (User.username == username) | (User.email == username)
                    )
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.info(f"User not found: {username}")
                    self.record_login_attempt(username, ip_address, False)
                    return None

                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted login: {username}")
                    self.record_login_attempt(username, ip_address, False)
                    return None

                # Verify password
                if not self.verify_password(password, user.password_hash):
                    logger.info(f"Invalid password for user: {username}")
                    self.record_login_attempt(username, ip_address, False)
                    return None

                # Successful authentication
                self.record_login_attempt(username, ip_address, True)

                # Update last login
                user.last_login = datetime.now()
                await db_session.commit()

                return AuthContext(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    roles={UserRole(user.role.value)},
                    authenticated=True,
                    ip_address=ip_address,
                )
            else:
                # Fallback: mock authentication for backward compatibility
                logger.warning(
                    "No database session provided for authentication, using mock data"
                )
                if username == "test" and password == "test123":
                    self.record_login_attempt(username, ip_address, True)

                    return AuthContext(
                        user_id="test_user_id",
                        username=username,
                        roles={UserRole.STUDENT},
                        authenticated=True,
                        ip_address=ip_address,
                    )
                self.record_login_attempt(username, ip_address, False)
                return None

        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            self.record_login_attempt(username, ip_address, False)
            return None

    async def authenticate_token(self, token: str) -> AuthContext | None:
        """Authenticate using JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None

        return AuthContext(
            user_id=payload["sub"],
            username=payload["username"],
            roles={UserRole(role) for role in payload.get("roles", [])},
            token_type=AuthMethod.JWT_TOKEN,
            authenticated=True,
        )

    # Authorization (RBAC)
    def has_role(self, context: AuthContext, required_role: UserRole) -> bool:
        """Check if user has required role"""
        return required_role in context.roles

    def has_permission(self, context: AuthContext, permission: str) -> bool:
        """Check if user has required permission"""
        return permission in context.permissions

    def has_any_role(self, context: AuthContext, roles: list[UserRole]) -> bool:
        """Check if user has any of the required roles"""
        return any(role in context.roles for role in roles)

    # FastAPI Dependencies
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials
        | None = Depends(HTTPBearer(auto_error=False)),
    ) -> AuthContext:
        """FastAPI dependency to get current authenticated user"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kimlik doğrulama gerekli",
                headers={"WWW-Authenticate": "Bearer"},
            )

        context = await self.authenticate_token(credentials.credentials)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz kimlik doğrulama bilgileri",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return context

    async def get_optional_user(
        self,
        credentials: HTTPAuthorizationCredentials
        | None = Depends(HTTPBearer(auto_error=False)),
    ) -> AuthContext | None:
        """FastAPI dependency to get current user (optional)"""
        if not credentials:
            return None

        return await self.authenticate_token(credentials.credentials)

    def require_role(self, required_role: UserRole):
        """Decorator to require specific role"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get current user from dependency injection
                context = kwargs.get("current_user")
                if not context or not self.has_role(context, required_role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Bu işlem için {required_role.value} yetkisi gerekli",
                    )
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def require_permission(self, permission: str):
        """Decorator to require specific permission"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                context = kwargs.get("current_user")
                if not context or not self.has_permission(context, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Bu işlem için '{permission}' yetkisi gerekli",
                    )
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    # Security Utils
    def generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint for session tracking"""
        data = f"{user_agent}:{ip_address}:{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()

    def log_security_event(
        self, event: AuthEvent, context: AuthContext, details: dict | None = None
    ) -> None:
        """Log security-related events"""
        log_data = {
            "event": event.value,
            "user_id": context.user_id,
            "username": context.username,
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

        logger.info(f"Security event: {event.value}", extra=log_data)

    # Health Check
    async def health_check(self) -> dict[str, Any]:
        """Perform health check"""
        return {
            "auth_manager_status": "healthy",
            "active_sessions": len(self.active_sessions),
            "blacklisted_tokens": len(self.blacklisted_tokens),
            "rate_limited_users": len(
                [a for a in self.login_attempts.values() if a.locked_until]
            ),
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_auth_manager: UnifiedAuthManager | None = None


def get_auth_manager() -> UnifiedAuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = UnifiedAuthManager()
    return _auth_manager


# Backward compatibility aliases
AuthenticationManager = UnifiedAuthManager
EnhancedAuthManager = UnifiedAuthManager
AuthMiddleware = UnifiedAuthManager
AuthDependencies = UnifiedAuthManager
SessionAuthCache = UnifiedAuthManager
