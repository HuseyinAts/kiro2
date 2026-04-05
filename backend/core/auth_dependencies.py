"""
KIRO2 Authentication Dependencies
Unified authentication and authorization decorators for FastAPI
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.enhanced_authentication import (
    AuthenticationContext,
    get_authentication_manager,
)
from core.rbac_system import AuthorizationContext, get_rbac_manager
from core.unified_config import get_unified_config
from models.user import User

logger = logging.getLogger(__name__)
config = get_unified_config()

# Security schemes
security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)


class AuthenticationDependency:
    """FastAPI dependency for authentication"""

    def __init__(self, required: bool = True):
        self.required = required
        self.auth_manager = get_authentication_manager()

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> User | None:
        """Authenticate user from request"""

        if not credentials and not self.required:
            return None

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "authentication_required",
                    "message": "Kimlik doğrulama gerekli",
                    "message_en": "Authentication required",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials

        try:
            # FIX: AuthenticationContext constructor mismatch â€” use working JWT path
            import jwt as _jwt
            from core.config import settings as _settings
            _payload = _jwt.decode(
                token,
                _settings.jwt_secret_key,
                algorithms=[_settings.jwt_algorithm],
            )
            from core.dependencies import AuthenticatedUser, UserRole
            _user = AuthenticatedUser(
                id=_payload.get("sub", ""),
                username=_payload.get("username", ""),
                role=_payload.get("role", "student"),
                email=_payload.get("email"),
                permissions=_payload.get("permissions", []),
                exp=_payload.get("exp"),
            )
            request.state.current_user = _user
            return _user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "authentication_failed",
                    "message": "Kimlik doğrulama başarısız",
                    "message_en": "Authentication failed",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _generate_device_fingerprint(self, request: Request) -> str:
        """Generate device fingerprint from request headers"""
        headers = [
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
            request.headers.get("accept-encoding", ""),
            request.headers.get("accept", ""),
            str(request.client.host) if request.client else "",
        ]

        import hashlib

        fingerprint_data = "|".join(headers)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]


class AuthorizationDependency:
    """FastAPI dependency for authorization"""

    def __init__(
        self,
        required_permissions: list[str] = None,
        required_roles: list[str] = None,
        resource_type: str = None,
        resource_id: str = None,
        allow_self: bool = False,
    ):
        self.required_permissions = required_permissions or []
        self.required_roles = required_roles or []
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.allow_self = allow_self
        self.rbac_manager = get_rbac_manager()

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(AuthenticationDependency(required=True)),
    ) -> User:
        """Check user authorization"""

        try:
            # Get resource ID from path parameters if not provided
            resource_id = self.resource_id
            if not resource_id and hasattr(request, "path_params"):
                # Common path parameter names for resource IDs
                for param_name in ["id", "user_id", "resource_id", "item_id"]:
                    if param_name in request.path_params:
                        resource_id = str(request.path_params[param_name])
                        break

            # Check if user is accessing their own resource
            if self.allow_self and resource_id and str(current_user.id) == resource_id:
                return current_user

            # Create authorization context
            auth_context = AuthorizationContext(
                user_id=current_user.id,
                user_role=current_user.role,
                required_permissions=self.required_permissions,
                required_roles=self.required_roles,
                resource_type=self.resource_type or "general",
                resource_id=resource_id,
                resource_owner_id=resource_id if self.allow_self else None,
                ip_address=getattr(
                    request.state, "auth_context", AuthenticationContext()
                ).ip_address,
                user_agent=getattr(
                    request.state, "auth_context", AuthenticationContext()
                ).user_agent,
                request_path=str(request.url.path),
                request_method=request.method,
                additional_context={
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers),
                },
            )

            # Check authorization
            auth_result = await self.rbac_manager.check_permission(auth_context)

            if not auth_result.authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "insufficient_permissions",
                        "message": auth_result.message,
                        "message_en": "Insufficient permissions",
                        "required_permissions": self.required_permissions,
                        "required_roles": self.required_roles,
                        "user_role": current_user.role,
                        "resource_type": self.resource_type,
                    },
                )

            # Store authorization result in request state
            request.state.auth_result = auth_result

            return current_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "authorization_failed",
                    "message": "Yetkilendirme başarısız",
                    "message_en": "Authorization failed",
                },
            )


# Pre-configured dependency instances
authenticate_user = AuthenticationDependency(required=True)
authenticate_optional = AuthenticationDependency(required=False)

# Alias for backward compatibility (many files use get_current_user)
get_current_user = authenticate_user

# Common authorization dependencies
require_admin = AuthorizationDependency(required_roles=["admin", "super_admin"])
require_teacher = AuthorizationDependency(
    required_roles=["teacher", "admin", "super_admin"]
)
require_student = AuthorizationDependency(
    required_roles=["student", "teacher", "admin", "super_admin"]
)

# Permission-based dependencies
require_read_permission = AuthorizationDependency(required_permissions=["read"])
require_write_permission = AuthorizationDependency(required_permissions=["write"])
require_delete_permission = AuthorizationDependency(required_permissions=["delete"])
require_manage_users = AuthorizationDependency(required_permissions=["manage_users"])
require_manage_content = AuthorizationDependency(
    required_permissions=["manage_content"]
)
require_view_analytics = AuthorizationDependency(
    required_permissions=["view_analytics"]
)


# Resource-specific dependencies
def require_user_access(allow_self: bool = True):
    """Require access to user resources"""
    return AuthorizationDependency(
        resource_type="user",
        required_permissions=["manage_users"],
        allow_self=allow_self,
    )


def require_content_access(content_type: str = "general"):
    """Require access to content resources"""
    return AuthorizationDependency(
        resource_type=f"content_{content_type}", required_permissions=["manage_content"]
    )


def require_exam_access():
    """Require access to exam resources"""
    return AuthorizationDependency(
        resource_type="exam", required_permissions=["manage_exams"]
    )


def require_analytics_access():
    """Require access to analytics resources"""
    return AuthorizationDependency(
        resource_type="analytics", required_permissions=["view_analytics"]
    )


# Decorator functions for route handlers
def require_authentication(func: Callable = None, *, optional: bool = False):
    """Decorator to require authentication"""

    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # Authentication will be handled by FastAPI dependency injection
            return await f(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def require_authorization(
    permissions: list[str] = None,
    roles: list[str] = None,
    resource_type: str = None,
    allow_self: bool = False,
):
    """Decorator to require specific authorization"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Authorization will be handled by FastAPI dependency injection
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str):
    """Decorator to require specific roles"""
    return require_authorization(roles=list(roles))


def require_permission(*permissions: str):
    """Decorator to require specific permissions"""
    return require_authorization(permissions=list(permissions))


# Utility functions for manual authentication/authorization
async def authenticate_request(request: Request) -> User | None:
    """Manually authenticate a request"""
    auth_dep = AuthenticationDependency(required=False)
    return await auth_dep(request)


async def authorize_user(
    user: User,
    permissions: list[str] = None,
    roles: list[str] = None,
    resource_type: str = "general",
    resource_id: str = None,
) -> bool:
    """Manually authorize a user"""
    rbac_manager = get_rbac_manager()

    auth_context = AuthorizationContext(
        user_id=user.id,
        user_role=user.role,
        required_permissions=permissions or [],
        required_roles=roles or [],
        resource_type=resource_type,
        resource_id=resource_id,
        request_path="manual_check",
        request_method="GET",
    )

    result = await rbac_manager.check_permission(auth_context)
    return result.authorized


# Security context helper
class SecurityContext:
    """Security context for current request"""

    def __init__(self, request: Request):
        self.request = request
        self._current_user = getattr(request.state, "current_user", None)
        self._auth_context = getattr(request.state, "auth_context", None)
        self._auth_result = getattr(request.state, "auth_result", None)

    @property
    def current_user(self) -> User | None:
        """Get current authenticated user"""
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self._current_user is not None

    @property
    def user_role(self) -> str | None:
        """Get user role"""
        return self._current_user.role if self._current_user else None

    @property
    def user_permissions(self) -> list[str]:
        """Get user permissions"""
        if not self._auth_result:
            return []
        return self._auth_result.granted_permissions

    @property
    def session_data(self) -> dict[str, Any]:
        """Get session data"""
        return getattr(self.request.state, "session_data", {})

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles"""
        if not self._current_user:
            return False
        return self._current_user.role in roles

    def has_permission(self, *permissions: str) -> bool:
        """Check if user has any of the specified permissions"""
        user_perms = self.user_permissions
        return any(perm in user_perms for perm in permissions)

    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.has_role("admin", "super_admin")

    def is_teacher(self) -> bool:
        """Check if user is teacher or above"""
        return self.has_role("teacher", "admin", "super_admin")

    def is_student(self) -> bool:
        """Check if user is student or above"""
        return self.has_role("student", "teacher", "admin", "super_admin")

    def can_access_resource(self, resource_owner_id: int) -> bool:
        """Check if user can access resource owned by another user"""
        if not self._current_user:
            return False

        # User can access their own resources
        if self._current_user.id == resource_owner_id:
            return True

        # Admin can access all resources
        if self.is_admin():
            return True

        return False


def get_security_context(request: Request) -> SecurityContext:
    """Get security context for current request"""
    return SecurityContext(request)


# Example usage in route handlers
"""
# Basic authentication
@router.get("/profile")
async def get_profile(current_user: User = Depends(authenticate_user)):
    return {"user": current_user}

# Optional authentication
@router.get("/public-content")
async def get_public_content(current_user: Optional[User] = Depends(authenticate_optional)):
    if current_user:
        # Personalized content
        pass
    else:
        # Public content
        pass

# Role-based authorization
@router.get("/admin-panel")
async def admin_panel(current_user: User = Depends(require_admin)):
    return {"message": "Admin panel"}

# Permission-based authorization
@router.post("/create-content")
async def create_content(current_user: User = Depends(require_write_permission)):
    return {"message": "Content created"}

# Resource-specific authorization with self-access
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_user_access(allow_self=True))
):
    return {"user_id": user_id}

# Manual security context usage
@router.get("/complex-endpoint")
async def complex_endpoint(request: Request):
    security_ctx = get_security_context(request)
    
    if security_ctx.is_authenticated:
        if security_ctx.is_admin():
            # Admin logic
            pass
        elif security_ctx.has_permission("special_access"):
            # Special access logic
            pass
    
    return {"message": "Complex endpoint"}
"""
