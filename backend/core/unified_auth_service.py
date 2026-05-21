"""
Unified Authentication & Authorization Service
FAZ 3.4: User/Auth Service Optimization
Consolidates JWT, RBAC, 2FA, and session management
"""

import hashlib
import logging
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================


class UserRole(str, Enum):
    """User roles in the system"""

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TokenType(str, Enum):
    """JWT token types"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    TWO_FACTOR = "two_factor"


class Permission(str, Enum):
    """System permissions"""

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Exam management
    EXAM_CREATE = "exam:create"
    EXAM_READ = "exam:read"
    EXAM_UPDATE = "exam:update"
    EXAM_DELETE = "exam:delete"
    EXAM_TAKE = "exam:take"
    EXAM_GRADE = "exam:grade"

    # Question management
    QUESTION_CREATE = "question:create"
    QUESTION_READ = "question:read"
    QUESTION_UPDATE = "question:update"
    QUESTION_DELETE = "question:delete"
    QUESTION_APPROVE = "question:approve"

    # Content management
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"

    # Analytics
    ANALYTICS_VIEW_OWN = "analytics:view_own"
    ANALYTICS_VIEW_CLASS = "analytics:view_class"
    ANALYTICS_VIEW_ALL = "analytics:view_all"
    ANALYTICS_EXPORT = "analytics:export"

    # Admin
    ADMIN_ACCESS = "admin:access"
    ADMIN_USERS = "admin:users"
    ADMIN_CONTENT = "admin:content"
    ADMIN_SYSTEM = "admin:system"


class AuthEvent(str, Enum):
    """Authentication events for audit logging"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    TWO_FACTOR_ENABLED = "2fa_enabled"
    TWO_FACTOR_DISABLED = "2fa_disabled"
    TWO_FACTOR_VERIFIED = "2fa_verified"
    TWO_FACTOR_FAILED = "2fa_failed"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    PERMISSION_DENIED = "permission_denied"


# ==================== DATA CLASSES ====================


@dataclass
class TokenPayload:
    """JWT token payload"""

    sub: str  # user_id
    email: str
    role: UserRole
    exp: datetime
    iat: datetime
    type: TokenType
    jti: str  # JWT ID
    permissions: list[str] = field(default_factory=list)
    device_id: str | None = None
    session_id: str | None = None


@dataclass
class TokenPair:
    """Access and refresh token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    refresh_expires_in: int = 604800  # 7 days


@dataclass
class UserSession:
    """User session information"""

    session_id: str
    user_id: int
    device_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True


@dataclass
class AuthAuditLog:
    """Authentication audit log entry"""

    id: str
    user_id: int | None
    event: AuthEvent
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitInfo:
    """Rate limiting information"""

    attempts: int
    first_attempt: datetime
    locked_until: datetime | None = None


@dataclass
class SessionContext:
    """
    Oturum bağlam bilgileri.

    Session hijacking tespiti için IP ve User-Agent binding bilgilerini saklar.
    REQ-6.4 uyumlu.

    Attributes:
        ip_address: Oturum açıldığındaki IP adresi
        user_agent: Oturum açıldığındaki tarayıcı bilgisi
        created_at: Bağlam oluşturulma zamanı
        fingerprint: IP + User-Agent hash'i
    """

    ip_address: str
    user_agent: str
    created_at: datetime
    fingerprint: str


@dataclass
class HijackingResult:
    """
    Session hijacking tespit sonucu.

    Attributes:
        is_hijacked: Oturum ele geçirilmiş mi?
        reason: Tespit nedeni
        severity: Önem derecesi (low, medium, high, critical)
        ip_changed: IP adresi değişti mi?
        user_agent_changed: User-Agent değişti mi?
        original_ip: Orijinal IP adresi
        current_ip: Mevcut IP adresi
        original_user_agent: Orijinal User-Agent
        current_user_agent: Mevcut User-Agent
    """

    is_hijacked: bool
    reason: str | None = None
    severity: Literal["low", "medium", "high", "critical"] = "low"
    ip_changed: bool = False
    user_agent_changed: bool = False
    original_ip: str | None = None
    current_ip: str | None = None
    original_user_agent: str | None = None
    current_user_agent: str | None = None


# ==================== ROLE PERMISSIONS ====================

ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.STUDENT: [
        Permission.EXAM_READ,
        Permission.EXAM_TAKE,
        Permission.QUESTION_READ,
        Permission.CONTENT_READ,
        Permission.ANALYTICS_VIEW_OWN,
        Permission.USER_READ,
        Permission.USER_UPDATE,  # Own profile only
    ],
    UserRole.TEACHER: [
        # Student permissions
        Permission.EXAM_READ,
        Permission.EXAM_TAKE,
        Permission.QUESTION_READ,
        Permission.CONTENT_READ,
        Permission.ANALYTICS_VIEW_OWN,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        # Teacher-specific
        Permission.EXAM_CREATE,
        Permission.EXAM_UPDATE,
        Permission.EXAM_GRADE,
        Permission.QUESTION_CREATE,
        Permission.QUESTION_UPDATE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
        Permission.ANALYTICS_VIEW_CLASS,
    ],
    UserRole.PARENT: [
        Permission.CONTENT_READ,
        Permission.ANALYTICS_VIEW_OWN,  # View children's progress
        Permission.USER_READ,
    ],
    UserRole.ADMIN: [
        # All teacher permissions
        Permission.EXAM_CREATE,
        Permission.EXAM_READ,
        Permission.EXAM_UPDATE,
        Permission.EXAM_DELETE,
        Permission.EXAM_TAKE,
        Permission.EXAM_GRADE,
        Permission.QUESTION_CREATE,
        Permission.QUESTION_READ,
        Permission.QUESTION_UPDATE,
        Permission.QUESTION_DELETE,
        Permission.QUESTION_APPROVE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH,
        Permission.ANALYTICS_VIEW_OWN,
        Permission.ANALYTICS_VIEW_CLASS,
        Permission.ANALYTICS_VIEW_ALL,
        Permission.ANALYTICS_EXPORT,
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_CONTENT,
    ],
    UserRole.SUPER_ADMIN: [
        # All permissions
        *[p for p in Permission],
    ],
}


# ==================== UNIFIED AUTH SERVICE ====================


class UnifiedAuthService:
    """
    Unified Authentication and Authorization Service

    Features:
    - JWT token management (access + refresh)
    - Password hashing with bcrypt
    - Role-based access control (RBAC)
    - Session management
    - Rate limiting for brute force protection
    - Audit logging
    - 2FA support (TOTP)
    """

    # Configuration
    SECRET_KEY = os.getenv("JWT_SECRET", "kiro2-super-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def __init__(self):
        # S180 fix (login latency P0): bcrypt cost env-tunable, default 10
        # (was implicit 12 = 250-350ms per verify). 10 rounds is safe with
        # rate-limit (30/min) + Redis brute-force protection.
        _cost = int(os.environ.get("BCRYPT_COST", "10") or 10)
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=_cost,
        )

        # In-memory stores (use Redis in production)
        self._blacklisted_tokens: set[str] = set()
        self._rate_limits: dict[str, RateLimitInfo] = {}
        self._sessions: dict[str, UserSession] = {}
        self._audit_logs: list[AuthAuditLog] = []
        self._2fa_secrets: dict[int, str] = {}
        self._session_contexts: dict[
            str, SessionContext
        ] = {}  # Session hijacking prevention

    # ==================== PASSWORD MANAGEMENT ====================

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_password_reset_token(self) -> str:
        """Generate a secure password reset token"""
        return secrets.token_urlsafe(32)

    # ==================== JWT TOKEN MANAGEMENT ====================

    def create_access_token(
        self,
        user_id: int,
        email: str,
        role: UserRole,
        permissions: list[str] | None = None,
        device_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Create an access token"""
        if permissions is None:
            permissions = [p.value for p in ROLE_PERMISSIONS.get(role, [])]

        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": now,
            "type": TokenType.ACCESS.value,
            "jti": jti,
            "permissions": permissions,
            "device_id": device_id,
            "session_id": session_id,
        }

        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(
        self,
        user_id: int,
        email: str,
        role: UserRole,
        device_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Create a refresh token"""
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": now,
            "type": TokenType.REFRESH.value,
            "jti": jti,
            "device_id": device_id,
            "session_id": session_id,
        }

        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_token_pair(
        self,
        user_id: int,
        email: str,
        role: UserRole,
        permissions: list[str] | None = None,
        device_id: str | None = None,
    ) -> TokenPair:
        """Create both access and refresh tokens"""
        session_id = str(uuid.uuid4())

        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            permissions=permissions,
            device_id=device_id,
            session_id=session_id,
        )

        refresh_token = self.create_refresh_token(
            user_id=user_id,
            email=email,
            role=role,
            device_id=device_id,
            session_id=session_id,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    def decode_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
            )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and jti in self._blacklisted_tokens:
                raise ValueError("Token has been revoked")

            return TokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
                iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
                type=TokenType(payload["type"]),
                jti=payload["jti"],
                permissions=payload.get("permissions", []),
                device_id=payload.get("device_id"),
                session_id=payload.get("session_id"),
            )

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding its JTI to blacklist"""
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
                options={"verify_exp": False},  # Allow expired tokens to be revoked
            )
            jti = payload.get("jti")
            if jti:
                self._blacklisted_tokens.add(jti)
                return True
        except jwt.InvalidTokenError:
            pass
        return False

    def refresh_tokens(self, refresh_token: str) -> TokenPair | None:
        """Refresh tokens using a refresh token"""
        try:
            payload = self.decode_token(refresh_token)

            if payload.type != TokenType.REFRESH:
                return None

            # Revoke old refresh token
            self.revoke_token(refresh_token)

            # Create new token pair
            return self.create_token_pair(
                user_id=int(payload.sub),
                email=payload.email,
                role=payload.role,
                device_id=payload.device_id,
            )

        except ValueError:
            return None

    # ==================== RBAC ====================

    def get_role_permissions(self, role: UserRole) -> list[Permission]:
        """Get all permissions for a role"""
        return ROLE_PERMISSIONS.get(role, [])

    def has_permission(
        self,
        user_role: UserRole,
        permission: Permission,
        user_permissions: list[str] | None = None,
    ) -> bool:
        """Check if a role or user has a specific permission"""
        # Super admin has all permissions
        if user_role == UserRole.SUPER_ADMIN:
            return True

        # Check custom permissions first
        if user_permissions and permission.value in user_permissions:
            return True

        # Check role permissions
        role_perms = self.get_role_permissions(user_role)
        return permission in role_perms

    def check_resource_access(
        self,
        user_id: int,
        user_role: UserRole,
        resource_type: str,
        resource_id: str,
        action: str,
        resource_owner_id: int | None = None,
    ) -> bool:
        """Check if user can access a specific resource"""
        permission_str = f"{resource_type}:{action}"

        try:
            permission = Permission(permission_str)
        except ValueError:
            # Unknown permission, deny by default
            return False

        # Check base permission
        if not self.has_permission(user_role, permission):
            return False

        # Check ownership for update/delete actions
        if action in ["update", "delete"] and resource_owner_id:
            if user_role in [UserRole.STUDENT, UserRole.PARENT]:
                return user_id == resource_owner_id

        return True

    # ==================== RATE LIMITING ====================

    def check_rate_limit(self, identifier: str) -> tuple[bool, int | None]:
        """
        Check if rate limit is exceeded

        Returns:
            (allowed, retry_after_seconds)
        """
        now = datetime.now(UTC)

        if identifier not in self._rate_limits:
            self._rate_limits[identifier] = RateLimitInfo(
                attempts=1,
                first_attempt=now,
            )
            return True, None

        info = self._rate_limits[identifier]

        # Check if locked
        if info.locked_until and now < info.locked_until:
            retry_after = int((info.locked_until - now).total_seconds())
            return False, retry_after

        # Reset if window expired (1 hour)
        if now - info.first_attempt > timedelta(hours=1):
            self._rate_limits[identifier] = RateLimitInfo(
                attempts=1,
                first_attempt=now,
            )
            return True, None

        # Increment attempts
        info.attempts += 1

        # Check if exceeded
        if info.attempts > self.MAX_LOGIN_ATTEMPTS:
            info.locked_until = now + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            return False, self.LOCKOUT_DURATION_MINUTES * 60

        return True, None

    def reset_rate_limit(self, identifier: str) -> None:
        """Reset rate limit for an identifier"""
        self._rate_limits.pop(identifier, None)

    # ==================== SESSION MANAGEMENT ====================

    def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        device_id: str | None = None,
    ) -> UserSession:
        """Create a new user session"""
        now = datetime.now(UTC)
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            device_id=device_id or str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> UserSession | None:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        if session and session.is_active:
            now = datetime.now(UTC)
            if now > session.expires_at:
                session.is_active = False
                return None
            return session
        return None

    def update_session_activity(self, session_id: str) -> None:
        """Update last activity timestamp"""
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.last_activity = datetime.now(UTC)

    def end_session(self, session_id: str) -> bool:
        """End a session"""
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False

    def get_user_sessions(self, user_id: int) -> list[UserSession]:
        """Get all active sessions for a user"""
        return [
            s for s in self._sessions.values() if s.user_id == user_id and s.is_active
        ]

    def end_all_user_sessions(self, user_id: int) -> int:
        """End all sessions for a user"""
        count = 0
        for session in self._sessions.values():
            if session.user_id == user_id and session.is_active:
                session.is_active = False
                count += 1
        return count

    # ==================== SESSION HIJACKING PREVENTION (REQ-6.4) ====================

    def _generate_context_fingerprint(self, ip: str, user_agent: str) -> str:
        """
        IP ve User-Agent bilgilerinden benzersiz fingerprint olusturur.

        Args:
            ip: IP adresi
            user_agent: Tarayici User-Agent stringi

        Returns:
            SHA-256 hash fingerprint
        """
        data = f"{ip}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()

    def bind_session_to_context(
        self,
        session_id: str,
        ip: str,
        user_agent: str,
    ) -> SessionContext:
        """
        Oturumu IP ve User-Agent bilgilerine baglar.

        Session hijacking onlemi icin oturum baglam bilgilerini saklar.
        REQ-6.4 uyumlu.

        Args:
            session_id: Oturum kimlik numarasi
            ip: Kullanicinin IP adresi
            user_agent: Tarayici User-Agent stringi

        Returns:
            SessionContext: Olusturulan oturum baglami

        Example:
            >>> auth_service.bind_session_to_context(
            ...     session_id="abc123",
            ...     ip="192.168.1.1",
            ...     user_agent="Mozilla/5.0..."
            ... )
        """
        now = datetime.now(UTC)
        fingerprint = self._generate_context_fingerprint(ip, user_agent)

        context = SessionContext(
            ip_address=ip,
            user_agent=user_agent,
            created_at=now,
            fingerprint=fingerprint,
        )

        self._session_contexts[session_id] = context

        logger.info(
            f"Session context bound | Session: {session_id[:8]}... | "
            f"IP: {ip} | Fingerprint: {fingerprint[:16]}..."
        )

        return context

    def verify_session_context(
        self,
        session_id: str,
        ip: str,
        user_agent: str,
    ) -> bool:
        """
        Oturum baglam bilgilerini dogrular.

        Mevcut IP ve User-Agent bilgilerinin oturum acildigindaki
        bilgilerle eslesip eslesmedigini kontrol eder.

        Args:
            session_id: Oturum kimlik numarasi
            ip: Mevcut IP adresi
            user_agent: Mevcut User-Agent

        Returns:
            bool: Baglamlar eslesiyor mu?

        Example:
            >>> is_valid = auth_service.verify_session_context(
            ...     session_id="abc123",
            ...     ip="192.168.1.1",
            ...     user_agent="Mozilla/5.0..."
            ... )
        """
        context = self._session_contexts.get(session_id)

        if not context:
            logger.warning(f"Session context not found | Session: {session_id[:8]}...")
            return False

        current_fingerprint = self._generate_context_fingerprint(ip, user_agent)

        if context.fingerprint != current_fingerprint:
            logger.warning(
                f"Session context mismatch | Session: {session_id[:8]}... | "
                f"Original IP: {context.ip_address} | Current IP: {ip}"
            )
            return False

        return True

    def detect_session_hijacking(
        self,
        session_id: str,
        ip: str,
        user_agent: str,
    ) -> HijackingResult:
        """
        Session hijacking tespit eder.

        IP ve User-Agent degisikliklerini analiz ederek oturum
        ele gecirilme girisimlerini tespit eder.

        Args:
            session_id: Oturum kimlik numarasi
            ip: Mevcut IP adresi
            user_agent: Mevcut User-Agent

        Returns:
            HijackingResult: Tespit sonucu

        Severity levels:
            - low: Kucuk User-Agent degisikligi
            - medium: IP degisikligi (ayni agda)
            - high: Farkli ag/bolge IP degisikligi
            - critical: Hem IP hem User-Agent degisti

        Example:
            >>> result = auth_service.detect_session_hijacking(
            ...     session_id="abc123",
            ...     ip="10.0.0.5",
            ...     user_agent="Different browser"
            ... )
            >>> if result.is_hijacked:
            ...     print(f"Hijacking detected: {result.reason}")
        """
        context = self._session_contexts.get(session_id)

        # Baglam bulunamadi - yeni oturum veya temizlenmis
        if not context:
            return HijackingResult(
                is_hijacked=False,
                reason="Oturum baglami bulunamadi",
                severity="low",
            )

        ip_changed = context.ip_address != ip
        user_agent_changed = context.user_agent != user_agent

        # Hicbir sey degismediyse guvenli
        if not ip_changed and not user_agent_changed:
            return HijackingResult(
                is_hijacked=False,
                severity="low",
                original_ip=context.ip_address,
                current_ip=ip,
                original_user_agent=context.user_agent,
                current_user_agent=user_agent,
            )

        # Severity belirleme
        severity: Literal["low", "medium", "high", "critical"]
        reason: str

        if ip_changed and user_agent_changed:
            # En yuksek risk: Hem IP hem User-Agent degisti
            severity = "critical"
            reason = "Hem IP adresi hem User-Agent degisti - muhtemel session hijacking"
            is_hijacked = True
        elif ip_changed:
            # IP degisikligi - orta/yuksek risk
            # Ayni subnet kontrolu
            original_subnet = ".".join(context.ip_address.split(".")[:3])
            current_subnet = ".".join(ip.split(".")[:3])

            if original_subnet == current_subnet:
                severity = "medium"
                reason = "IP adresi ayni ag icinde degisti - dikkatli olunmali"
                is_hijacked = False  # Ayni agda mobil cihazlar icin normal olabilir
            else:
                severity = "high"
                reason = "IP adresi farkli bir aga degisti - suphelil aktivite"
                is_hijacked = True
        else:
            # Sadece User-Agent degisti - dusuk risk (tarayici guncelleme olabilir)
            severity = "low"
            reason = "User-Agent degisti - tarayici guncelleme olabilir"
            is_hijacked = False

        # Suphelil aktivite logla
        if is_hijacked:
            logger.warning(
                f"SESSION HIJACKING DETECTED | Session: {session_id[:8]}... | "
                f"Severity: {severity} | Reason: {reason} | "
                f"Original IP: {context.ip_address} -> Current IP: {ip}"
            )

        return HijackingResult(
            is_hijacked=is_hijacked,
            reason=reason,
            severity=severity,
            ip_changed=ip_changed,
            user_agent_changed=user_agent_changed,
            original_ip=context.ip_address,
            current_ip=ip,
            original_user_agent=context.user_agent,
            current_user_agent=user_agent,
        )

    def remove_session_context(self, session_id: str) -> bool:
        """
        Oturum baglam bilgilerini siler.

        Oturum sonlandirildiginda cagrilmalidir.

        Args:
            session_id: Oturum kimlik numarasi

        Returns:
            bool: Basariyla silindi mi?
        """
        if session_id in self._session_contexts:
            del self._session_contexts[session_id]
            logger.info(f"Session context removed | Session: {session_id[:8]}...")
            return True
        return False

    def get_session_context(self, session_id: str) -> SessionContext | None:
        """
        Oturum baglam bilgilerini getirir.

        Args:
            session_id: Oturum kimlik numarasi

        Returns:
            SessionContext veya None
        """
        return self._session_contexts.get(session_id)

    # ==================== AUDIT LOGGING ====================

    def log_auth_event(
        self,
        event: AuthEvent,
        user_id: int | None,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> AuthAuditLog:
        """Log an authentication event"""
        log = AuthAuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event=event,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(UTC),
            success=success,
            details=details or {},
        )
        self._audit_logs.append(log)

        # Keep only last 10000 logs in memory
        if len(self._audit_logs) > 10000:
            self._audit_logs = self._audit_logs[-10000:]

        # Log to file/service as well
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Auth Event: {event.value} | User: {user_id} | IP: {ip_address} | Success: {success}",
        )

        return log

    def get_recent_auth_events(
        self,
        user_id: int | None = None,
        event_type: AuthEvent | None = None,
        limit: int = 100,
    ) -> list[AuthAuditLog]:
        """Get recent authentication events"""
        logs = self._audit_logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]

        if event_type:
            logs = [l for l in logs if l.event == event_type]

        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]

    # ==================== 2FA (TOTP) ====================

    def generate_2fa_secret(self, user_id: int) -> str:
        """Generate a 2FA secret for a user"""
        secret = secrets.token_hex(20)
        self._2fa_secrets[user_id] = secret
        return secret

    def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """
        Verify a 2FA code

        Note: This is a simplified implementation.
        In production, use pyotp for proper TOTP validation.
        """
        secret = self._2fa_secrets.get(user_id)
        if not secret:
            return False

        # Simplified verification (use pyotp in production)
        # This generates a time-based code for demo purposes
        import time

        counter = int(time.time()) // 30
        expected = hashlib.sha1(f"{secret}{counter}".encode()).hexdigest()[:6]

        return code == expected

    def disable_2fa(self, user_id: int) -> bool:
        """Disable 2FA for a user"""
        if user_id in self._2fa_secrets:
            del self._2fa_secrets[user_id]
            return True
        return False

    def has_2fa_enabled(self, user_id: int) -> bool:
        """Check if user has 2FA enabled"""
        return user_id in self._2fa_secrets

    # ==================== UTILITY METHODS ====================

    def generate_device_id(self, user_agent: str, ip_address: str) -> str:
        """Generate a device identifier"""
        data = f"{user_agent}:{ip_address}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength

        Returns:
            (is_valid, list of issues)
        """
        issues = []

        if len(password) < 8:
            issues.append("Şifre en az 8 karakter olmalıdır")

        if not any(c.isupper() for c in password):
            issues.append("Şifre en az bir büyük harf içermelidir")

        if not any(c.islower() for c in password):
            issues.append("Şifre en az bir küçük harf içermelidir")

        if not any(c.isdigit() for c in password):
            issues.append("Şifre en az bir rakam içermelidir")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Şifre en az bir özel karakter içermelidir")

        # Check for Turkish characters
        turkish_chars = "ıİğĞüÜşŞöÖçÇ"
        has_turkish = any(c in turkish_chars for c in password)
        if has_turkish:
            issues.append("Şifre Türkçe karakterler içermemelidir")

        return len(issues) == 0, issues

    def get_auth_stats(self) -> dict[str, Any]:
        """Get authentication statistics"""
        now = datetime.now(UTC)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        recent_logs = [l for l in self._audit_logs if l.timestamp > last_hour]
        daily_logs = [l for l in self._audit_logs if l.timestamp > last_day]

        return {
            "active_sessions": sum(1 for s in self._sessions.values() if s.is_active),
            "blacklisted_tokens": len(self._blacklisted_tokens),
            "rate_limited_ips": sum(
                1
                for r in self._rate_limits.values()
                if r.locked_until and r.locked_until > now
            ),
            "users_with_2fa": len(self._2fa_secrets),
            "events_last_hour": len(recent_logs),
            "events_last_day": len(daily_logs),
            "failed_logins_last_hour": sum(
                1 for l in recent_logs if l.event == AuthEvent.LOGIN_FAILED
            ),
            "successful_logins_last_hour": sum(
                1 for l in recent_logs if l.event == AuthEvent.LOGIN_SUCCESS
            ),
        }


# Global service instance
_auth_service: UnifiedAuthService | None = None


def get_auth_service() -> UnifiedAuthService:
    """Get global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = UnifiedAuthService()
    return _auth_service
