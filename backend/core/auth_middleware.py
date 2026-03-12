"""
KIRO2 Authentication & Authorization Middleware
Comprehensive auth middleware for Turkish exam platform API security
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import hashlib
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import jwt

from core.application_metrics import MetricType, get_metrics_collector
from core.session_auth_caching import get_session_auth_cache
from core.structured_logging import LogCategory, get_logger
from core.unified_api_gateway import APIRequest, APIResponse, HTTPMethod
from core.unified_config import get_unified_config
from core.unified_event_bus import EventPriority, EventType, publish_event

config = get_unified_config()
logger = get_logger(__name__, LogCategory.AUTH)


class AuthenticationMethod(Enum):
    """Authentication methods"""

    JWT_TOKEN = "jwt_token"
    SESSION_TOKEN = "session_token"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class UserRole(str, Enum):
    """User roles in Turkish exam system.

    Uses (str, Enum) so UserRole.STUDENT == "student" works correctly.
    Includes all roles from core.dependencies + middleware-specific roles.
    """

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    MODERATOR = "moderator"
    SYSTEM = "system"
    GUEST = "guest"


class Permission(Enum):
    """System permissions"""

    # User permissions
    VIEW_PROFILE = "view_profile"
    EDIT_PROFILE = "edit_profile"
    DELETE_ACCOUNT = "delete_account"

    # Exam permissions
    TAKE_TYT_EXAM = "take_tyt_exam"
    TAKE_AYT_EXAM = "take_ayt_exam"
    VIEW_EXAM_RESULTS = "view_exam_results"
    CREATE_PRACTICE_TEST = "create_practice_test"

    # Content permissions
    VIEW_CONTENT = "view_content"
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_EXAMS = "manage_exams"

    # Turkish exam specific
    ACCESS_YKS_INFO = "access_yks_info"
    REGISTER_YKS = "register_yks"
    VIEW_RANKINGS = "view_rankings"


@dataclass
class AuthUser:
    """Authenticated user information"""

    user_id: int
    username: str
    email: str
    role: UserRole
    permissions: set[Permission]
    session_id: str | None = None
    last_login: datetime | None = None
    is_active: bool = True
    is_verified: bool = True
    profile_data: dict[str, Any] = field(default_factory=dict)
    exam_context: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role"""
        return self.role == role

    def is_student(self) -> bool:
        """Check if user is a student"""
        return self.role == UserRole.STUDENT

    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role in {UserRole.ADMIN, UserRole.SYSTEM}

    def can_take_exam(self, exam_type: str) -> bool:
        """Check if user can take specific exam"""
        exam_permissions = {
            "tyt": Permission.TAKE_TYT_EXAM,
            "ayt": Permission.TAKE_AYT_EXAM,
        }

        required_permission = exam_permissions.get(exam_type.lower())
        return required_permission and self.has_permission(required_permission)


@dataclass
class AuthContext:
    """Authentication context for request"""

    user: AuthUser | None = None
    authentication_method: AuthenticationMethod | None = None
    token: str | None = None
    authenticated: bool = False
    permissions: set[Permission] = field(default_factory=set)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class JWTManager:
    """JWT token management"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.secret_key = config.get("jwt_secret_key", "kiro2-turkish-exam-secret")
        self.algorithm = config.get("jwt_algorithm", "HS256")
        self.access_token_expire = config.get("access_token_expire_minutes", 30)
        self.refresh_token_expire = config.get("refresh_token_expire_days", 30)
        self.issuer = config.get("jwt_issuer", "KIRO2-Turkish-Exam-Platform")

    def generate_access_token(self, user: AuthUser) -> str:
        """Generate JWT access token"""
        try:
            now = datetime.now(UTC)
            expires_at = now + timedelta(minutes=self.access_token_expire)

            payload = {
                "sub": str(user.user_id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions],
                "session_id": user.session_id,
                "iss": self.issuer,
                "iat": now.timestamp(),
                "exp": expires_at.timestamp(),
                "type": "access_token",
            }

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

            logger.debug(f"Access token generated for user {user.user_id}")
            return token

        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            raise ValueError(f"Token generation failed: {e}")

    def generate_refresh_token(self, user: AuthUser) -> str:
        """Generate JWT refresh token"""
        try:
            now = datetime.now(UTC)
            expires_at = now + timedelta(days=self.refresh_token_expire)

            payload = {
                "sub": str(user.user_id),
                "session_id": user.session_id,
                "iss": self.issuer,
                "iat": now.timestamp(),
                "exp": expires_at.timestamp(),
                "type": "refresh_token",
            }

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token

        except Exception as e:
            logger.error(f"Error generating refresh token: {e}")
            raise ValueError(f"Refresh token generation failed: {e}")

    def validate_token(self, token: str) -> dict[str, Any]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm], issuer=self.issuer
            )

            # Check token expiration
            if payload.get("exp", 0) < datetime.now(UTC).timestamp():
                raise jwt.ExpiredSignatureError("Token has expired")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise ValueError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise ValueError(f"Token validation failed: {e}")


class SessionManager:
    """Session management for Turkish exam platform"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.session_cache = None
        self.session_timeout = config.get("session_timeout_minutes", 60)
        self.max_sessions_per_user = config.get("max_sessions_per_user", 5)

    async def _get_session_cache(self):
        """Get session cache instance"""
        if not self.session_cache:
            self.session_cache = await get_session_auth_cache()
        return self.session_cache

    async def create_session(self, user: AuthUser, client_info: dict[str, Any]) -> str:
        """Create new user session"""
        try:
            session_cache = await self._get_session_cache()
            session_id = self._generate_session_id(user.user_id)

            session_data = {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions],
                "created_at": datetime.now(UTC).isoformat(),
                "last_activity": datetime.now(UTC).isoformat(),
                "client_ip": client_info.get("ip", ""),
                "user_agent": client_info.get("user_agent", ""),
                "is_active": True,
                "exam_context": user.exam_context,
            }

            # Store session in cache
            await session_cache.cache_system.set(
                f"session:{session_id}", session_data, ttl=self.session_timeout * 60
            )

            # Track user sessions
            await self._track_user_session(user.user_id, session_id)

            logger.info(f"Session created for user {user.user_id}: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise ValueError(f"Session creation failed: {e}")

    async def validate_session(self, session_id: str) -> dict[str, Any] | None:
        """Validate and retrieve session data"""
        try:
            session_cache = await self._get_session_cache()
            session_data = await session_cache.cache_system.get(f"session:{session_id}")

            if not session_data:
                return None

            if not session_data.get("is_active", True):
                return None

            # Update last activity
            session_data["last_activity"] = datetime.now(UTC).isoformat()
            await session_cache.cache_system.set(
                f"session:{session_id}", session_data, ttl=self.session_timeout * 60
            )

            return session_data

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def invalidate_session(self, session_id: str, reason: str = "logout"):
        """Invalidate user session"""
        try:
            session_cache = await self._get_session_cache()

            # Get session data before deletion
            session_data = await session_cache.cache_system.get(f"session:{session_id}")

            # Remove session
            await session_cache.cache_system.delete(f"session:{session_id}")

            if session_data:
                user_id = session_data.get("user_id")
                await self._remove_user_session(user_id, session_id)

                logger.info(
                    f"Session invalidated for user {user_id}: {session_id}, reason: {reason}"
                )

        except Exception as e:
            logger.error(f"Session invalidation error: {e}")

    async def _track_user_session(self, user_id: int, session_id: str):
        """Track user sessions"""
        try:
            session_cache = await self._get_session_cache()
            user_sessions_key = f"user_sessions:{user_id}"

            # Get current sessions
            current_sessions = (
                await session_cache.cache_system.get(user_sessions_key) or []
            )

            # Add new session
            current_sessions.append(
                {"session_id": session_id, "created_at": datetime.now(UTC).isoformat()}
            )

            # Limit sessions per user
            if len(current_sessions) > self.max_sessions_per_user:
                # Remove oldest sessions
                oldest_sessions = current_sessions[: -self.max_sessions_per_user]
                for old_session in oldest_sessions:
                    await self.invalidate_session(
                        old_session["session_id"], "session_limit"
                    )

                current_sessions = current_sessions[-self.max_sessions_per_user :]

            # Store updated sessions
            await session_cache.cache_system.set(
                user_sessions_key, current_sessions, ttl=24 * 3600  # 24 hours
            )

        except Exception as e:
            logger.error(f"Error tracking user session: {e}")

    async def _remove_user_session(self, user_id: int, session_id: str):
        """Remove session from user sessions list"""
        try:
            session_cache = await self._get_session_cache()
            user_sessions_key = f"user_sessions:{user_id}"

            current_sessions = (
                await session_cache.cache_system.get(user_sessions_key) or []
            )
            updated_sessions = [
                s for s in current_sessions if s.get("session_id") != session_id
            ]

            if updated_sessions:
                await session_cache.cache_system.set(
                    user_sessions_key, updated_sessions, ttl=24 * 3600
                )
            else:
                await session_cache.cache_system.delete(user_sessions_key)

        except Exception as e:
            logger.error(f"Error removing user session: {e}")

    def _generate_session_id(self, user_id: int) -> str:
        """Generate secure session ID"""
        timestamp = str(int(time.time()))
        random_data = secrets.token_hex(16)
        user_data = str(user_id)

        session_string = f"{timestamp}:{user_data}:{random_data}"
        session_id = hashlib.sha256(session_string.encode()).hexdigest()

        return f"kiro2_session_{session_id[:32]}"


class PermissionManager:
    """Permission management for Turkish exam platform"""

    def __init__(self):
        self.role_permissions = self._setup_role_permissions()

    def _setup_role_permissions(self) -> dict[UserRole, set[Permission]]:
        """Setup default role permissions"""
        return {
            UserRole.STUDENT: {
                Permission.VIEW_PROFILE,
                Permission.EDIT_PROFILE,
                Permission.TAKE_TYT_EXAM,
                Permission.TAKE_AYT_EXAM,
                Permission.VIEW_EXAM_RESULTS,
                Permission.CREATE_PRACTICE_TEST,
                Permission.VIEW_CONTENT,
                Permission.ACCESS_YKS_INFO,
                Permission.REGISTER_YKS,
                Permission.VIEW_RANKINGS,
            },
            UserRole.TEACHER: {
                Permission.VIEW_PROFILE,
                Permission.EDIT_PROFILE,
                Permission.VIEW_CONTENT,
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.VIEW_ANALYTICS,
                Permission.ACCESS_YKS_INFO,
                Permission.VIEW_RANKINGS,
            },
            UserRole.MODERATOR: {
                Permission.VIEW_PROFILE,
                Permission.EDIT_PROFILE,
                Permission.VIEW_CONTENT,
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.DELETE_CONTENT,
                Permission.MANAGE_USERS,
                Permission.VIEW_ANALYTICS,
                Permission.ACCESS_YKS_INFO,
                Permission.VIEW_RANKINGS,
            },
            UserRole.ADMIN: {perm for perm in Permission},  # All permissions
            UserRole.SYSTEM: {perm for perm in Permission},  # All permissions
            UserRole.GUEST: {Permission.VIEW_CONTENT, Permission.ACCESS_YKS_INFO},
        }

    def get_user_permissions(self, role: UserRole) -> set[Permission]:
        """Get permissions for user role"""
        return self.role_permissions.get(role, set())

    def check_permission(
        self, user_role: UserRole, required_permission: Permission
    ) -> bool:
        """Check if role has required permission"""
        user_permissions = self.get_user_permissions(user_role)
        return required_permission in user_permissions

    def check_route_permissions(self, user_role: UserRole, route_path: str) -> bool:
        """Check route-specific permissions"""
        route_permissions = {
            "/auth/": {Permission.VIEW_PROFILE},  # Basic auth routes
            "/users/": {Permission.VIEW_PROFILE},
            "/exams/tyt/": {Permission.TAKE_TYT_EXAM},
            "/exams/ayt/": {Permission.TAKE_AYT_EXAM},
            "/admin/": {Permission.MANAGE_SYSTEM},
            "/analytics/": {Permission.VIEW_ANALYTICS},
        }

        user_permissions = self.get_user_permissions(user_role)

        for route_prefix, required_perms in route_permissions.items():
            if route_path.startswith(route_prefix):
                return any(perm in user_permissions for perm in required_perms)

        return True  # Allow access if no specific permissions required


class AuthenticationMiddleware:
    """Authentication middleware for Turkish exam platform"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.jwt_manager = JWTManager(config.get("jwt", {}))
        self.session_manager = SessionManager(config.get("session", {}))
        self.permission_manager = PermissionManager()
        self.metrics_collector = get_metrics_collector()

        # Public routes that don't require authentication
        self.public_routes = {
            "/health",
            "/auth/login",
            "/auth/register",
            "/yks/info",
            "/auth/forgot-password",
            "/auth/reset-password",
        }

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process authentication middleware"""
        start_time = time.time()

        try:
            # Check if route requires authentication
            if self._is_public_route(request.path):
                request.metadata["auth_context"] = AuthContext()
                return await next_handler(request)

            # Extract authentication data
            auth_context = await self._extract_auth_context(request)

            if not auth_context.authenticated:
                return self._create_auth_error(
                    request.id,
                    401,
                    "Authentication Required",
                    "Kimlik doğrulama gerekli",
                    "Bu işlem için giriş yapmalısınız",
                )

            # Add auth context to request
            request.metadata["auth_context"] = auth_context
            request.user_id = auth_context.user.user_id if auth_context.user else None
            request.session_id = (
                auth_context.user.session_id if auth_context.user else None
            )

            # Record successful authentication
            self.metrics_collector.record_metric(
                MetricType.AUTH_SUCCESS,
                1,
                metadata={
                    "method": auth_context.authentication_method.value
                    if auth_context.authentication_method
                    else "unknown",
                    "user_id": request.user_id,
                    "route": request.path,
                },
            )

            # Publish authentication event
            if auth_context.user:
                await publish_event(
                    EventType.AUTH_SUCCESS,
                    {
                        "user_id": auth_context.user.user_id,
                        "username": auth_context.user.username,
                        "method": auth_context.authentication_method.value,
                        "route": request.path,
                        "client_ip": request.client_ip,
                    },
                    user_id=auth_context.user.user_id,
                    priority=EventPriority.NORMAL,
                )

            response = await next_handler(request)

            # Add auth headers to response
            if auth_context.user:
                response.add_header(
                    "X-Authenticated-User", str(auth_context.user.user_id)
                )
                response.add_header("X-User-Role", auth_context.user.role.value)

            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            logger.error(
                f"Authentication middleware error: {e}",
                extra={"request_id": request.id, "processing_time": processing_time},
            )

            # Record auth failure
            self.metrics_collector.record_metric(
                MetricType.AUTH_FAILED,
                1,
                metadata={"error": str(e), "route": request.path},
            )

            return self._create_auth_error(
                request.id,
                500,
                "Authentication Error",
                "Kimlik doğrulama hatası",
                str(e),
            )

    def _is_public_route(self, path: str) -> bool:
        """Check if route is public (no auth required)"""
        return any(path.startswith(public_path) for public_path in self.public_routes)

    async def _extract_auth_context(self, request: APIRequest) -> AuthContext:
        """Extract authentication context from request"""
        try:
            # Try JWT token first
            jwt_token = self._extract_jwt_token(request)
            if jwt_token:
                return await self._authenticate_jwt(jwt_token, request)

            # Try session token
            session_id = self._extract_session_id(request)
            if session_id:
                return await self._authenticate_session(session_id, request)

            # Try API key
            api_key = self._extract_api_key(request)
            if api_key:
                return await self._authenticate_api_key(api_key, request)

            # No authentication found
            return AuthContext()

        except Exception as e:
            logger.error(f"Error extracting auth context: {e}")
            return AuthContext()

    def _extract_jwt_token(self, request: APIRequest) -> str | None:
        """Extract JWT token from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Check X-Access-Token header
        return request.headers.get("X-Access-Token")

    def _extract_session_id(self, request: APIRequest) -> str | None:
        """Extract session ID from request"""
        # Check X-Session-ID header
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id

        # Check session cookie (if cookies are supported)
        cookies = request.headers.get("Cookie", "")
        for cookie in cookies.split(";"):
            if "session_id=" in cookie:
                return cookie.split("session_id=")[1].split(";")[0].strip()

        return None

    def _extract_api_key(self, request: APIRequest) -> str | None:
        """Extract API key from request"""
        return request.headers.get("X-API-Key")

    async def _authenticate_jwt(self, token: str, request: APIRequest) -> AuthContext:
        """Authenticate using JWT token"""
        try:
            payload = self.jwt_manager.validate_token(token)

            user = AuthUser(
                user_id=int(payload["sub"]),
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                role=UserRole(payload.get("role", "student")),
                permissions={Permission(p) for p in payload.get("permissions", [])},
                session_id=payload.get("session_id"),
                is_active=True,
                is_verified=True,
            )

            return AuthContext(
                user=user,
                authentication_method=AuthenticationMethod.JWT_TOKEN,
                token=token,
                authenticated=True,
                permissions=user.permissions,
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), UTC),
            )

        except Exception as e:
            logger.warning(f"JWT authentication failed: {e}")
            return AuthContext()

    async def _authenticate_session(
        self, session_id: str, request: APIRequest
    ) -> AuthContext:
        """Authenticate using session ID"""
        try:
            session_data = await self.session_manager.validate_session(session_id)

            if not session_data:
                return AuthContext()

            user = AuthUser(
                user_id=session_data["user_id"],
                username=session_data.get("username", ""),
                email="",  # Not stored in session
                role=UserRole(session_data.get("role", "student")),
                permissions={
                    Permission(p) for p in session_data.get("permissions", [])
                },
                session_id=session_id,
                is_active=session_data.get("is_active", True),
                is_verified=True,
                exam_context=session_data.get("exam_context", {}),
            )

            return AuthContext(
                user=user,
                authentication_method=AuthenticationMethod.SESSION_TOKEN,
                token=session_id,
                authenticated=True,
                permissions=user.permissions,
            )

        except Exception as e:
            logger.warning(f"Session authentication failed: {e}")
            return AuthContext()

    async def _authenticate_api_key(
        self, api_key: str, request: APIRequest
    ) -> AuthContext:
        """Authenticate using API key"""
        try:
            # This would typically validate against a database
            # For now, placeholder implementation

            if api_key == "kiro2_system_api_key":
                user = AuthUser(
                    user_id=0,
                    username="system",
                    email="system@kiro2.com",
                    role=UserRole.SYSTEM,
                    permissions=self.permission_manager.get_user_permissions(
                        UserRole.SYSTEM
                    ),
                    is_active=True,
                    is_verified=True,
                )

                return AuthContext(
                    user=user,
                    authentication_method=AuthenticationMethod.API_KEY,
                    token=api_key,
                    authenticated=True,
                    permissions=user.permissions,
                )

            return AuthContext()

        except Exception as e:
            logger.warning(f"API key authentication failed: {e}")
            return AuthContext()

    def _create_auth_error(
        self,
        request_id: str,
        status_code: int,
        error: str,
        error_tr: str,
        detail_tr: str,
    ) -> APIResponse:
        """Create authentication error response"""
        return APIResponse(
            request_id=request_id,
            status_code=status_code,
            headers={
                "Content-Type": "application/json",
                "WWW-Authenticate": 'Bearer realm="KIRO2 Turkish Exam Platform"',
            },
            body={
                "error": error,
                "detail": "Authentication is required to access this resource",
                "error_tr": error_tr,
                "detail_tr": detail_tr,
                "login_url": "/auth/login",
            },
            processing_time_ms=1.0,
        )


class AuthorizationMiddleware:
    """Authorization middleware for Turkish exam platform"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.permission_manager = PermissionManager()
        self.metrics_collector = get_metrics_collector()

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process authorization middleware"""
        try:
            # Get auth context from request
            auth_context: AuthContext = request.metadata.get("auth_context")

            if not auth_context or not auth_context.authenticated:
                return await next_handler(request)  # Let auth middleware handle

            # Check route-specific permissions
            if not self._check_route_authorization(auth_context, request):
                logger.warning(
                    f"Authorization denied for user {auth_context.user.user_id} on route {request.path}",
                    extra={
                        "request_id": request.id,
                        "user_role": auth_context.user.role.value,
                    },
                )

                # Record authorization failure
                self.metrics_collector.record_metric(
                    MetricType.AUTH_FAILED,
                    1,
                    metadata={
                        "type": "authorization",
                        "user_id": auth_context.user.user_id,
                        "route": request.path,
                        "role": auth_context.user.role.value,
                    },
                )

                return self._create_authz_error(
                    request.id,
                    "Insufficient permissions",
                    "Bu işlem için yeterli yetkiniz yok",
                )

            # Check exam-specific authorization
            if request.is_exam_route():
                if not await self._check_exam_authorization(auth_context, request):
                    return self._create_authz_error(
                        request.id, "Exam access denied", "Sınav erişimi engellenmiş"
                    )

            return await next_handler(request)

        except Exception as e:
            logger.error(f"Authorization middleware error: {e}")
            return await next_handler(request)  # Continue on error

    def _check_route_authorization(
        self, auth_context: AuthContext, request: APIRequest
    ) -> bool:
        """Check if user is authorized for the route"""
        try:
            user = auth_context.user
            if not user:
                return False

            # Admin and system users have access to everything
            if user.is_admin():
                return True

            # Check route-specific permissions
            route_permissions = self._get_route_permissions(
                request.path, request.method
            )

            if not route_permissions:
                return True  # No specific permissions required

            return any(user.has_permission(perm) for perm in route_permissions)

        except Exception as e:
            logger.error(f"Route authorization check error: {e}")
            return False

    def _get_route_permissions(self, path: str, method: HTTPMethod) -> set[Permission]:
        """Get required permissions for route"""
        route_permissions = {
            # User routes
            "/users/{user_id}/profile": {Permission.VIEW_PROFILE},
            "/users/{user_id}/settings": {Permission.EDIT_PROFILE},
            # Exam routes
            "/exams/tyt/start": {Permission.TAKE_TYT_EXAM},
            "/exams/ayt/start": {Permission.TAKE_AYT_EXAM},
            "/exams/{exam_id}/results": {Permission.VIEW_EXAM_RESULTS},
            # Content routes
            "/content/create": {Permission.CREATE_CONTENT},
            "/content/{content_id}/edit": {Permission.EDIT_CONTENT},
            "/content/{content_id}/delete": {Permission.DELETE_CONTENT},
            # Admin routes
            "/admin/users": {Permission.MANAGE_USERS},
            "/admin/system": {Permission.MANAGE_SYSTEM},
            "/analytics/": {Permission.VIEW_ANALYTICS},
        }

        # Check exact match first
        if path in route_permissions:
            return route_permissions[path]

        # Check pattern match
        for route_pattern, permissions in route_permissions.items():
            if self._path_matches_pattern(path, route_pattern):
                return permissions

        return set()

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches route pattern"""
        import re

        # Convert {param} to regex
        regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", pattern)
        regex_pattern = f"^{regex_pattern}$"
        return re.match(regex_pattern, path) is not None

    async def _check_exam_authorization(
        self, auth_context: AuthContext, request: APIRequest
    ) -> bool:
        """Check exam-specific authorization"""
        try:
            user = auth_context.user
            if not user:
                return False

            # Extract exam type from path
            path = request.path.lower()
            if "tyt" in path:
                exam_type = "tyt"
            elif "ayt" in path:
                exam_type = "ayt"
            else:
                return True  # Not an exam route

            # Check if user can take this exam
            if not user.can_take_exam(exam_type):
                return False

            # Check if user is in exam period (placeholder)
            # This would check against exam schedule, user registration, etc.

            return True

        except Exception as e:
            logger.error(f"Exam authorization check error: {e}")
            return False

    def _create_authz_error(
        self, request_id: str, error: str, error_tr: str
    ) -> APIResponse:
        """Create authorization error response"""
        return APIResponse(
            request_id=request_id,
            status_code=403,
            headers={"Content-Type": "application/json"},
            body={
                "error": "Forbidden",
                "detail": error,
                "error_tr": "Erişim Engellendi",
                "detail_tr": error_tr,
            },
            processing_time_ms=1.0,
        )


# Factory functions


def create_authentication_middleware(
    config: dict[str, Any] = None
) -> AuthenticationMiddleware:
    """Create authentication middleware instance"""
    config = config or {}
    return AuthenticationMiddleware(config)


def create_authorization_middleware(
    config: dict[str, Any] = None
) -> AuthorizationMiddleware:
    """Create authorization middleware instance"""
    config = config or {}
    return AuthorizationMiddleware(config)


# Utility functions


async def authenticate_user_credentials(
    username: str, password: str
) -> AuthUser | None:
    """Authenticate user with credentials.

    NOTE: This function requires proper database integration.
    Use UnifiedAuthService.authenticate() for production authentication.
    """
    # SECURITY: Hardcoded test credentials removed
    # Must use proper database authentication via UnifiedAuthService
    return None


async def generate_auth_tokens(user: AuthUser) -> dict[str, str]:
    """Generate authentication tokens for user"""
    jwt_manager = JWTManager({})
    session_manager = SessionManager({})

    access_token = jwt_manager.generate_access_token(user)
    refresh_token = jwt_manager.generate_refresh_token(user)

    session_id = await session_manager.create_session(
        user, {"ip": "127.0.0.1", "user_agent": "Test Client"}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "session_id": session_id,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 minutes
    }
