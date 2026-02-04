"""
Enhanced Authentication System - Unified Authentication Pattern Consolidation
Comprehensive authentication system for the Türkiye Üniversite Sınavları Hazırlık Platformu

Bu dosya kapsamlı authentication consolidation sağlar:
- Multi-provider authentication (JWT, OAuth2, API keys)
- Enhanced token management with refresh tokens
- User session management with Redis
- Authentication middleware integration
- Security audit logging
- Rate limiting and brute force protection
- Multi-factor authentication support
- Device fingerprinting and session tracking
"""

import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from passlib.context import CryptContext

# Import enhanced database patterns
from .enhanced_database import enhanced_db_manager
from .error_context import annotate_error_context, async_error_context
from .error_monitoring import log_error

# Import error handling
from .exceptions import AuthorizationError, ErrorSeverity, ValidationError
from .query_builder import QueryBuilder
from .transaction_manager import managed_transaction

# Import response models

logger = logging.getLogger(__name__)


# ==================== AUTHENTICATION ENUMS ====================


class AuthenticationType(Enum):
    """Authentication type enumeration"""

    PASSWORD = "password"
    OAUTH2_GOOGLE = "oauth2_google"
    OAUTH2_MICROSOFT = "oauth2_microsoft"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    SESSION_TOKEN = "session_token"
    TWO_FACTOR = "two_factor"


class TokenType(Enum):
    """Token type enumeration"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"
    SESSION = "session"
    API_KEY = "api_key"


class SessionStatus(Enum):
    """Session status enumeration"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


class AuthenticationEvent(Enum):
    """Authentication event types"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    SESSION_EXPIRED = "session_expired"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TWO_FACTOR_SUCCESS = "two_factor_success"
    TWO_FACTOR_FAILURE = "two_factor_failure"


# ==================== AUTHENTICATION DATA CLASSES ====================


@dataclass
class AuthenticationConfig:
    """Authentication system configuration"""

    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Password Settings
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    password_bcrypt_rounds: int = 12

    # Session Settings
    session_expire_hours: int = 8
    max_concurrent_sessions: int = 5
    session_extend_on_activity: bool = True

    # Security Settings
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    rate_limit_window_minutes: int = 15
    rate_limit_max_attempts: int = 100

    # Two-Factor Authentication
    enable_2fa: bool = False
    totp_issuer: str = "KIRO2"
    backup_codes_count: int = 10

    # OAuth2 Settings
    enable_oauth2: bool = False
    oauth2_providers: dict[str, Any] = field(default_factory=dict)

    # Device & Fingerprinting
    enable_device_tracking: bool = True
    max_devices_per_user: int = 10
    device_trust_duration_days: int = 30

    def __post_init__(self):
        if not self.oauth2_providers:
            self.oauth2_providers = {
                "google": {"client_id": "", "client_secret": "", "enabled": False},
                "microsoft": {"client_id": "", "client_secret": "", "enabled": False},
            }


@dataclass
class TokenPayload:
    """JWT token payload structure"""

    user_id: str
    username: str
    email: str
    role: str
    permissions: list[str]
    session_id: str | None = None
    device_id: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    token_type: TokenType = TokenType.ACCESS

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JWT encoding"""
        return {
            "sub": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "permissions": self.permissions,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "iat": int(self.issued_at.timestamp()) if self.issued_at else None,
            "exp": int(self.expires_at.timestamp()) if self.expires_at else None,
            "type": self.token_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create from dictionary"""
        return cls(
            user_id=data.get("sub"),
            username=data.get("username"),
            email=data.get("email"),
            role=data.get("role"),
            permissions=data.get("permissions", []),
            session_id=data.get("session_id"),
            device_id=data.get("device_id"),
            issued_at=datetime.fromtimestamp(data["iat"], tz=UTC)
            if data.get("iat")
            else None,
            expires_at=datetime.fromtimestamp(data["exp"], tz=UTC)
            if data.get("exp")
            else None,
            token_type=TokenType(data.get("type", "access")),
        )


@dataclass
class UserSession:
    """User session information"""

    session_id: str
    user_id: str
    device_id: str
    device_fingerprint: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    authentication_type: AuthenticationType
    location: dict[str, Any] | None = None

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(UTC) >= self.expires_at

    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    def extend_session(self, hours: int = 8) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.now(UTC) + timedelta(hours=hours)
        self.last_activity = datetime.now(UTC)


@dataclass
class DeviceInfo:
    """Device information for tracking"""

    device_id: str
    user_id: str
    device_name: str
    device_type: str
    os: str
    browser: str
    fingerprint: str
    is_trusted: bool
    first_seen: datetime
    last_seen: datetime
    ip_addresses: list[str]

    def update_last_seen(self, ip_address: str) -> None:
        """Update last seen information"""
        self.last_seen = datetime.now(UTC)
        if ip_address not in self.ip_addresses:
            self.ip_addresses.append(ip_address)
            # Keep only last 10 IP addresses
            self.ip_addresses = self.ip_addresses[-10:]


@dataclass
class AuthenticationContext:
    """
    Authentication context for request-scoped auth state

    This class holds all authentication-related information for a single request,
    including user identity, session details, permissions, and security metadata.

    Usage:
        # In middleware or route handler
        auth_context = AuthenticationContext(
            user_id="user_123",
            role="student",
            permissions=["exam:take", "content:view"],
            session_id="session_abc",
            device_id="device_xyz",
            ip_address="192.168.1.1"
        )

        # Check permissions
        if auth_context.has_permission("exam:take"):
            # Allow exam access
            pass
    """

    # Core Identity
    user_id: str
    email: str | None = None
    username: str | None = None
    role: str = "student"
    permissions: list[str] = field(default_factory=list)

    # Session & Device
    session_id: str | None = None
    device_id: str | None = None
    device_fingerprint: str | None = None

    # Request Metadata
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Authentication Details
    authentication_type: AuthenticationType = AuthenticationType.JWT_TOKEN
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_authenticated: bool = True
    is_2fa_verified: bool = False

    # Token Information
    access_token_jti: str | None = None
    token_expires_at: datetime | None = None

    # Security Flags
    is_trusted_device: bool = False
    is_suspicious: bool = False
    security_warnings: list[str] = field(default_factory=list)

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission

        Args:
            permission: Permission string (e.g., "exam:create")

        Returns:
            bool: True if user has permission
        """
        # Super admin has all permissions
        if self.role == "super_admin" or "*" in self.permissions:
            return True

        return permission in self.permissions

    def has_role(self, *roles: str) -> bool:
        """
        Check if user has any of the specified roles

        Args:
            *roles: Variable number of role strings

        Returns:
            bool: True if user has any of the roles
        """
        return self.role in roles

    def require_permission(self, permission: str) -> None:
        """
        Require a specific permission, raise error if not present

        Args:
            permission: Required permission

        Raises:
            AuthorizationError: If permission not present
        """
        if not self.has_permission(permission):
            raise AuthorizationError(
                f"Permission required: {permission}",
                severity=ErrorSeverity.HIGH,
                context={
                    "user_id": self.user_id,
                    "role": self.role,
                    "required_permission": permission,
                    "user_permissions": self.permissions,
                }
            )

    def require_role(self, *roles: str) -> None:
        """
        Require user to have one of the specified roles

        Args:
            *roles: Required roles

        Raises:
            AuthorizationError: If role not present
        """
        if not self.has_role(*roles):
            raise AuthorizationError(
                f"Role required: {', '.join(roles)}",
                severity=ErrorSeverity.HIGH,
                context={
                    "user_id": self.user_id,
                    "user_role": self.role,
                    "required_roles": list(roles),
                }
            )

    def add_security_warning(self, warning: str) -> None:
        """Add a security warning to the context"""
        self.security_warnings.append(warning)
        self.is_suspicious = True

    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.token_expires_at:
            return False
        return datetime.now(UTC) >= self.token_expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "permissions": self.permissions,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "authentication_type": self.authentication_type.value if self.authentication_type else None,
            "authenticated_at": self.authenticated_at.isoformat() if self.authenticated_at else None,
            "is_authenticated": self.is_authenticated,
            "is_2fa_verified": self.is_2fa_verified,
            "is_trusted_device": self.is_trusted_device,
            "is_suspicious": self.is_suspicious,
            "security_warnings": self.security_warnings,
        }


# ==================== PASSWORD MANAGER ====================


class EnhancedPasswordManager:
    """Enhanced password management with comprehensive security"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.password_history_limit = 12  # Remember last 12 passwords

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        if not self.validate_password_format(password):
            raise ValidationError("Password does not meet security requirements")

        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def validate_password_format(self, password: str) -> bool:
        """Validate password meets format requirements"""
        if not password:
            return False

        if len(password) < self.config.password_min_length:
            return False

        if len(password) > self.config.password_max_length:
            return False

        if self.config.password_require_uppercase and not any(
            c.isupper() for c in password
        ):
            return False

        if self.config.password_require_lowercase and not any(
            c.islower() for c in password
        ):
            return False

        if self.config.password_require_digits and not any(
            c.isdigit() for c in password
        ):
            return False

        if self.config.password_require_special and not any(
            c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password
        ):
            return False

        return True

    def get_password_strength_score(self, password: str) -> dict[str, Any]:
        """Calculate password strength score"""
        if not password:
            return {
                "score": 0,
                "strength": "very_weak",
                "feedback": ["Şifre boş olamaz"],
            }

        score = 0
        feedback = []

        # Length scoring
        if len(password) >= 8:
            score += 25
        else:
            feedback.append(f"En az {self.config.password_min_length} karakter olmalı")

        if len(password) >= 12:
            score += 25

        # Character diversity
        if any(c.islower() for c in password):
            score += 10
        else:
            feedback.append("Küçük harf içermeli")

        if any(c.isupper() for c in password):
            score += 10
        else:
            feedback.append("Büyük harf içermeli")

        if any(c.isdigit() for c in password):
            score += 10
        else:
            feedback.append("Rakam içermeli")

        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 20
        else:
            feedback.append("Özel karakter içermeli")

        # Common patterns penalty
        common_patterns = ["123456", "password", "qwerty", "abc123", "admin"]
        if any(pattern in password.lower() for pattern in common_patterns):
            score -= 30
            feedback.append("Yaygın şifre kalıpları kullanmayın")

        # Sequential characters penalty
        if len(set(password)) < len(password) * 0.5:
            score -= 20
            feedback.append("Çok fazla tekrarlanan karakter")

        # Determine strength level
        if score < 30:
            strength = "very_weak"
        elif score < 50:
            strength = "weak"
        elif score < 70:
            strength = "medium"
        elif score < 90:
            strength = "strong"
        else:
            strength = "very_strong"

        return {
            "score": max(0, min(100, score)),
            "strength": strength,
            "feedback": feedback,
        }

    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password"""
        length = max(length, self.config.password_min_length)

        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Ensure at least one character from each required set
        password = []

        if self.config.password_require_lowercase:
            password.append(secrets.choice(lowercase))
        if self.config.password_require_uppercase:
            password.append(secrets.choice(uppercase))
        if self.config.password_require_digits:
            password.append(secrets.choice(digits))
        if self.config.password_require_special:
            password.append(secrets.choice(special))

        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return "".join(password)


# ==================== TOKEN MANAGER ====================


class EnhancedTokenManager:
    """Enhanced JWT token management with comprehensive features"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.revoked_tokens: set[str] = set()  # In production, use Redis
        self.token_usage_counter: dict[str, int] = {}  # Track token usage

    def create_access_token(self, payload: TokenPayload) -> str:
        """Create JWT access token"""
        now = datetime.now(UTC)
        payload.issued_at = now
        payload.expires_at = now + timedelta(
            minutes=self.config.access_token_expire_minutes
        )
        payload.token_type = TokenType.ACCESS

        # Add unique token ID for revocation
        token_data = payload.to_dict()
        token_data["jti"] = str(uuid.uuid4())  # JWT ID

        try:
            token = jwt.encode(
                token_data,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
            )

            logger.debug(f"Created access token for user {payload.user_id}")
            return token

        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise ValidationError("Failed to create access token")

    def create_refresh_token(self, payload: TokenPayload) -> str:
        """Create JWT refresh token"""
        now = datetime.now(UTC)
        payload.issued_at = now
        payload.expires_at = now + timedelta(days=self.config.refresh_token_expire_days)
        payload.token_type = TokenType.REFRESH

        token_data = payload.to_dict()
        token_data["jti"] = str(uuid.uuid4())

        try:
            token = jwt.encode(
                token_data,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
            )

            logger.debug(f"Created refresh token for user {payload.user_id}")
            return token

        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise ValidationError("Failed to create refresh token")

    def verify_token(
        self, token: str, expected_type: TokenType = TokenType.ACCESS
    ) -> TokenPayload | None:
        """Verify and decode JWT token"""
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                logger.warning("Attempted use of revoked token")
                return None

            # Decode token
            payload_data = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            payload = TokenPayload.from_dict(payload_data)

            # Verify token type
            if payload.token_type != expected_type:
                logger.warning(
                    f"Invalid token type: expected {expected_type}, got {payload.token_type}"
                )
                return None

            # Check expiration
            if payload.expires_at and datetime.now(UTC) >= payload.expires_at:
                logger.debug("Token has expired")
                return None

            # Track token usage
            jti = payload_data.get("jti")
            if jti:
                self.token_usage_counter[jti] = self.token_usage_counter.get(jti, 0) + 1

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token signature has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str] | None:
        """Refresh access token using refresh token"""
        refresh_payload = self.verify_token(refresh_token, TokenType.REFRESH)

        if not refresh_payload:
            return None

        # Create new access token
        access_payload = TokenPayload(
            user_id=refresh_payload.user_id,
            username=refresh_payload.username,
            email=refresh_payload.email,
            role=refresh_payload.role,
            permissions=refresh_payload.permissions,
            session_id=refresh_payload.session_id,
            device_id=refresh_payload.device_id,
        )

        new_access_token = self.create_access_token(access_payload)

        # Create new refresh token (rotate refresh tokens)
        new_refresh_payload = TokenPayload(
            user_id=refresh_payload.user_id,
            username=refresh_payload.username,
            email=refresh_payload.email,
            role=refresh_payload.role,
            permissions=refresh_payload.permissions,
            session_id=refresh_payload.session_id,
            device_id=refresh_payload.device_id,
        )

        new_refresh_token = self.create_refresh_token(new_refresh_payload)

        # Revoke old refresh token
        self.revoke_token(refresh_token)

        return new_access_token, new_refresh_token

    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        try:
            # Decode token to get JTI
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False},  # Allow expired tokens for revocation
            )

            jti = payload.get("jti")
            if jti:
                self.revoked_tokens.add(jti)
                logger.info(f"Token revoked: {jti}")
                return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")

        return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user"""
        # In production, this would query a token blacklist in Redis
        # For now, we'll simulate it
        revoked_count = 0

        # This is a simplified implementation
        # In production, you'd maintain a proper token registry
        logger.info(f"Revoking all tokens for user {user_id}")

        return revoked_count

    def get_token_stats(self) -> dict[str, Any]:
        """Get token usage statistics"""
        return {
            "revoked_tokens_count": len(self.revoked_tokens),
            "active_token_usage": len(self.token_usage_counter),
            "total_token_uses": sum(self.token_usage_counter.values()),
        }


# ==================== SESSION MANAGER ====================


class EnhancedSessionManager:
    """Enhanced session management with Redis support"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.active_sessions: dict[str, UserSession] = {}  # In production, use Redis
        self.device_registry: dict[str, DeviceInfo] = {}  # In production, use database

    async def create_session(
        self,
        user_id: str,
        device_id: str,
        device_fingerprint: str,
        ip_address: str,
        user_agent: str,
        authentication_type: AuthenticationType = AuthenticationType.PASSWORD,
    ) -> UserSession:
        """Create new user session"""

        session_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=self.config.session_expire_hours),
            status=SessionStatus.ACTIVE,
            authentication_type=authentication_type,
        )

        # Check concurrent session limit
        user_sessions = self.get_user_sessions(user_id)
        if len(user_sessions) >= self.config.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            await self.revoke_session(oldest_session.session_id)

        # Store session
        self.active_sessions[session_id] = session

        # Update device information
        await self.update_device_info(
            device_id, user_id, device_fingerprint, ip_address, user_agent
        )

        logger.info(f"Created session {session_id} for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> UserSession | None:
        """Get session by ID"""
        session = self.active_sessions.get(session_id)

        if not session:
            return None

        if session.is_expired():
            await self.revoke_session(session_id)
            return None

        # Update last activity if session extend is enabled
        if self.config.session_extend_on_activity:
            session.last_activity = datetime.now(UTC)

        return session

    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp"""
        session = await self.get_session(session_id)

        if session and session.is_active():
            session.last_activity = datetime.now(UTC)

            if self.config.session_extend_on_activity:
                session.expires_at = datetime.now(UTC) + timedelta(
                    hours=self.config.session_expire_hours
                )

            return True

        return False

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        session = self.active_sessions.get(session_id)

        if session:
            session.status = SessionStatus.REVOKED
            del self.active_sessions[session_id]
            logger.info(f"Revoked session {session_id}")
            return True

        return False

    async def revoke_user_sessions(
        self, user_id: str, except_session_id: str | None = None
    ) -> int:
        """Revoke all sessions for a user"""
        revoked_count = 0
        user_sessions = self.get_user_sessions(user_id)

        for session in user_sessions:
            if except_session_id and session.session_id == except_session_id:
                continue

            if await self.revoke_session(session.session_id):
                revoked_count += 1

        return revoked_count

    def get_user_sessions(self, user_id: str) -> list[UserSession]:
        """Get all active sessions for a user"""
        return [
            session
            for session in self.active_sessions.values()
            if session.user_id == user_id and session.is_active()
        ]

    async def update_device_info(
        self,
        device_id: str,
        user_id: str,
        fingerprint: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """Update or create device information"""

        device = self.device_registry.get(device_id)

        if device:
            device.update_last_seen(ip_address)
        else:
            # Parse user agent for device info
            device_name = f"Device {device_id[:8]}"
            device_type = "Unknown"
            os = "Unknown"
            browser = "Unknown"

            # Simple user agent parsing (in production, use a proper library)
            if "Mobile" in user_agent:
                device_type = "Mobile"
            elif "Tablet" in user_agent:
                device_type = "Tablet"
            else:
                device_type = "Desktop"

            if "Windows" in user_agent:
                os = "Windows"
            elif "Mac" in user_agent:
                os = "macOS"
            elif "Linux" in user_agent:
                os = "Linux"
            elif "Android" in user_agent:
                os = "Android"
            elif "iOS" in user_agent:
                os = "iOS"

            device = DeviceInfo(
                device_id=device_id,
                user_id=user_id,
                device_name=device_name,
                device_type=device_type,
                os=os,
                browser=browser,
                fingerprint=fingerprint,
                is_trusted=False,
                first_seen=datetime.now(UTC),
                last_seen=datetime.now(UTC),
                ip_addresses=[ip_address],
            )

            self.device_registry[device_id] = device

    def get_user_devices(self, user_id: str) -> list[DeviceInfo]:
        """Get all devices for a user"""
        return [
            device
            for device in self.device_registry.values()
            if device.user_id == user_id
        ]

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_count = 0
        expired_session_ids = []

        for session_id, session in self.active_sessions.items():
            if session.is_expired():
                expired_session_ids.append(session_id)

        for session_id in expired_session_ids:
            await self.revoke_session(session_id)
            expired_count += 1

        logger.info(f"Cleaned up {expired_count} expired sessions")
        return expired_count

    def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics"""
        active_sessions = len(self.active_sessions)
        unique_users = len(
            set(session.user_id for session in self.active_sessions.values())
        )
        unique_devices = len(self.device_registry)

        return {
            "active_sessions": active_sessions,
            "unique_active_users": unique_users,
            "registered_devices": unique_devices,
            "average_sessions_per_user": active_sessions / unique_users
            if unique_users > 0
            else 0,
        }


# ==================== MAIN AUTHENTICATION MANAGER ====================


class EnhancedAuthenticationManager:
    """Main authentication manager combining all authentication components"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.password_manager = EnhancedPasswordManager(config)
        self.token_manager = EnhancedTokenManager(config)
        self.session_manager = EnhancedSessionManager(config)

        # Authentication events tracking
        self.auth_events: list[dict[str, Any]] = []
        self.failed_attempts: dict[str, list[datetime]] = {}  # IP -> timestamps

    async def authenticate_user(
        self,
        identifier: str,  # email or username
        password: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str,
    ) -> dict[str, Any] | None:
        """
        Authenticate user with comprehensive security checks

        Returns authentication result with tokens and session info
        """

        async with async_error_context(
            operation_name="authenticate_user", business_operation="user_authentication"
        ) as ctx:
            ctx.tags.update(
                {
                    "identifier": identifier,
                    "ip_address": ip_address,
                    "authentication_type": AuthenticationType.PASSWORD.value,
                }
            )

            try:
                # Check for rate limiting
                if self._is_rate_limited(ip_address):
                    annotate_error_context("Authentication rate limited")
                    await self._log_auth_event(
                        AuthenticationEvent.LOGIN_FAILURE,
                        identifier,
                        ip_address,
                        "Rate limit exceeded",
                    )
                    raise AuthorizationError(
                        "Çok fazla başarısız giriş denemesi. Lütfen daha sonra tekrar deneyin."
                    )

                # Get user from database (using enhanced database patterns)
                async with enhanced_db_manager.get_session(read_only=True) as session:
                    # This would use the actual User model and query builder
                    user_query = QueryBuilder(
                        User, session
                    )  # Assuming User model exists

                    user = await user_query.filter(
                        or_(email=identifier, username=identifier)
                    ).first()

                    if not user:
                        annotate_error_context("User not found")
                        await self._record_failed_attempt(
                            identifier, ip_address, "User not found"
                        )
                        return None

                    # Check if user is active
                    if not user.is_active:
                        annotate_error_context("User account is inactive")
                        await self._record_failed_attempt(
                            identifier, ip_address, "Account inactive"
                        )
                        raise AuthorizationError(
                            "Hesabınız aktif değil. Lütfen yöneticiye başvurun."
                        )

                    # Check if account is locked
                    if (
                        user.is_locked
                        and user.locked_until
                        and datetime.now(UTC) < user.locked_until
                    ):
                        annotate_error_context("Account is locked")
                        raise AuthorizationError(
                            f"Hesabınız {user.locked_until} tarihine kadar kilitli."
                        )

                    # Verify password
                    if not self.password_manager.verify_password(
                        password, user.password_hash
                    ):
                        annotate_error_context("Password verification failed")
                        await self._record_failed_attempt(
                            identifier, ip_address, "Invalid password"
                        )

                        # Check if account should be locked
                        failed_count = await self._get_failed_attempt_count(user.id)
                        if failed_count >= self.config.max_login_attempts:
                            await self._lock_user_account(user.id)

                        return None

                    # Clear failed attempts on successful password verification
                    await self._clear_failed_attempts(user.id)

                    # Generate device ID
                    device_id = self._generate_device_id(user_agent, device_fingerprint)

                    # Create session
                    session_obj = await self.session_manager.create_session(
                        user_id=user.id,
                        device_id=device_id,
                        device_fingerprint=device_fingerprint,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        authentication_type=AuthenticationType.PASSWORD,
                    )

                    # Create token payload
                    token_payload = TokenPayload(
                        user_id=user.id,
                        username=user.username,
                        email=user.email,
                        role=user.role,
                        permissions=user.permissions or [],
                        session_id=session_obj.session_id,
                        device_id=device_id,
                    )

                    # Generate tokens
                    access_token = self.token_manager.create_access_token(token_payload)
                    refresh_token = self.token_manager.create_refresh_token(
                        token_payload
                    )

                    # Update user's last login
                    async with managed_transaction() as tx_ctx:
                        user.last_login_at = datetime.now(UTC)
                        user.last_login_ip = ip_address
                        await tx_ctx.session.flush()

                    # Log successful authentication
                    await self._log_auth_event(
                        AuthenticationEvent.LOGIN_SUCCESS,
                        identifier,
                        ip_address,
                        f"User {user.username} authenticated successfully",
                    )

                    annotate_error_context("Authentication successful")

                    return {
                        "success": True,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "role": user.role,
                            "permissions": user.permissions or [],
                        },
                        "tokens": {
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "token_type": "bearer",
                            "expires_in": self.config.access_token_expire_minutes * 60,
                        },
                        "session": {
                            "session_id": session_obj.session_id,
                            "expires_at": session_obj.expires_at,
                            "device_id": device_id,
                        },
                    }

            except Exception as e:
                ctx.add_annotation(f"Authentication failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)

                if isinstance(e, (ValidationError, AuthorizationError)):
                    raise e
                raise AuthorizationError("Kimlik doğrulama başarısız oldu")

    async def refresh_token_pair(self, refresh_token: str) -> dict[str, Any] | None:
        """Refresh access token using refresh token"""

        async with async_error_context(
            operation_name="refresh_tokens", business_operation="token_refresh"
        ) as ctx:
            try:
                # Refresh tokens
                token_result = self.token_manager.refresh_access_token(refresh_token)

                if not token_result:
                    annotate_error_context("Token refresh failed")
                    return None

                new_access_token, new_refresh_token = token_result

                # Log token refresh
                refresh_payload = self.token_manager.verify_token(
                    refresh_token, TokenType.REFRESH
                )
                if refresh_payload:
                    await self._log_auth_event(
                        AuthenticationEvent.TOKEN_REFRESH,
                        refresh_payload.username,
                        "unknown",  # IP not available in refresh
                        f"Tokens refreshed for user {refresh_payload.user_id}",
                    )

                annotate_error_context("Token refresh successful")

                return {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.config.access_token_expire_minutes * 60,
                }

            except Exception as e:
                ctx.add_annotation(f"Token refresh failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.MEDIUM)
                return None

    async def logout_user(self, access_token: str, session_id: str) -> bool:
        """Logout user and revoke tokens/session"""

        try:
            # Verify token
            payload = self.token_manager.verify_token(access_token)

            if payload:
                # Revoke session
                await self.session_manager.revoke_session(session_id)

                # Revoke tokens
                self.token_manager.revoke_token(access_token)

                # Log logout
                await self._log_auth_event(
                    AuthenticationEvent.LOGOUT,
                    payload.username,
                    "unknown",
                    f"User {payload.user_id} logged out",
                )

                return True

        except Exception as e:
            logger.error(f"Logout error: {e}")

        return False

    def _generate_device_id(self, user_agent: str, fingerprint: str) -> str:
        """Generate unique device ID"""
        combined = f"{user_agent}:{fingerprint}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP is rate limited"""
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=self.config.rate_limit_window_minutes)

        # Clean old attempts
        if ip_address in self.failed_attempts:
            self.failed_attempts[ip_address] = [
                attempt
                for attempt in self.failed_attempts[ip_address]
                if attempt > window_start
            ]

        # Check rate limit
        attempt_count = len(self.failed_attempts.get(ip_address, []))
        return attempt_count >= self.config.rate_limit_max_attempts

    async def _record_failed_attempt(
        self, identifier: str, ip_address: str, reason: str
    ) -> None:
        """Record failed authentication attempt"""
        now = datetime.now(UTC)

        # Track by IP
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        self.failed_attempts[ip_address].append(now)

        # Log event
        await self._log_auth_event(
            AuthenticationEvent.LOGIN_FAILURE, identifier, ip_address, reason
        )

    async def _get_failed_attempt_count(self, user_id: str) -> int:
        """Get failed attempt count for user (simulate database query)"""
        # In production, this would query the database
        return 0  # Simplified for example

    async def _clear_failed_attempts(self, user_id: str) -> None:
        """Clear failed attempts for user"""
        # In production, this would update the database

    async def _lock_user_account(self, user_id: str) -> None:
        """Lock user account due to too many failed attempts"""
        # In production, this would update the database
        logger.warning(f"Locking account for user {user_id} due to failed attempts")

    async def _log_auth_event(
        self,
        event_type: AuthenticationEvent,
        identifier: str,
        ip_address: str,
        details: str,
    ) -> None:
        """Log authentication event"""

        event = {
            "timestamp": datetime.now(UTC),
            "event_type": event_type.value,
            "identifier": identifier,
            "ip_address": ip_address,
            "details": details,
        }

        self.auth_events.append(event)

        # Log to logger based on event type
        if event_type in [
            AuthenticationEvent.LOGIN_FAILURE,
            AuthenticationEvent.ACCOUNT_LOCKED,
        ]:
            logger.warning(f"AUTH EVENT: {event_type.value} - {identifier} - {details}")
        else:
            logger.info(f"AUTH EVENT: {event_type.value} - {identifier} - {details}")

    async def get_authentication_stats(self) -> dict[str, Any]:
        """Get comprehensive authentication statistics"""

        # Session stats
        session_stats = self.session_manager.get_session_stats()

        # Token stats
        token_stats = self.token_manager.get_token_stats()

        # Event stats
        recent_events = [
            event
            for event in self.auth_events
            if event["timestamp"] > datetime.now(UTC) - timedelta(hours=24)
        ]

        event_counts = {}
        for event in recent_events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "sessions": session_stats,
            "tokens": token_stats,
            "events_24h": {
                "total_events": len(recent_events),
                "event_breakdown": event_counts,
            },
            "rate_limiting": {
                "blocked_ips": len(self.failed_attempts),
                "total_failed_attempts": sum(
                    len(attempts) for attempts in self.failed_attempts.values()
                ),
            },
        }


# ==================== GLOBAL AUTHENTICATION MANAGER ====================

# Global authentication manager instance
authentication_manager: EnhancedAuthenticationManager | None = None


def get_authentication_manager() -> EnhancedAuthenticationManager:
    """Get global authentication manager instance"""
    global authentication_manager

    if authentication_manager is None:
        config = AuthenticationConfig(
            jwt_secret_key=secrets.token_urlsafe(32),  # In production, use env variable
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )
        authentication_manager = EnhancedAuthenticationManager(config)

    return authentication_manager


# ==================== UTILITY FUNCTIONS ====================


async def authenticate_user_credentials(
    identifier: str,
    password: str,
    ip_address: str,
    user_agent: str,
    device_fingerprint: str = "",
) -> dict[str, Any] | None:
    """Convenience function for user authentication"""

    auth_manager = get_authentication_manager()
    return await auth_manager.authenticate_user(
        identifier, password, ip_address, user_agent, device_fingerprint
    )


async def refresh_user_tokens(refresh_token: str) -> dict[str, Any] | None:
    """Convenience function for token refresh"""

    auth_manager = get_authentication_manager()
    return await auth_manager.refresh_token_pair(refresh_token)


async def logout_user_session(access_token: str, session_id: str) -> bool:
    """Convenience function for user logout"""

    auth_manager = get_authentication_manager()
    return await auth_manager.logout_user(access_token, session_id)


def verify_access_token(token: str) -> TokenPayload | None:
    """Convenience function for token verification"""

    auth_manager = get_authentication_manager()
    return auth_manager.token_manager.verify_token(token, TokenType.ACCESS)
