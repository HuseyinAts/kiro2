"""
KIRO2 Consolidated Authentication Dependencies
Replaces the old dependencies.py with enhanced authentication patterns
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import logging
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth_dependencies import (
    AuthorizationDependency,
    SecurityContext,
    authenticate_optional,
    authenticate_user,
    get_security_context,
)
from core.auth_security_utils import SecurityLevel, analyze_request_security

# Import our enhanced authentication components
from core.rbac_system import AuthorizationContext, get_rbac_manager
from core.session_management import get_session_manager
from core.token_management import get_token_manager
from models.user import User

logger = logging.getLogger(__name__)

# Security scheme
security_scheme = HTTPBearer(auto_error=False)


# Enhanced authentication function that replaces get_current_user
async def get_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> User:
    """
    Enhanced authentication dependency that replaces the old get_current_user.
    Uses the new authentication pattern with comprehensive security checks.
    """
    return await authenticate_user(request, credentials)


# Optional authentication for endpoints that don't require login
async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials
    | None = Depends(HTTPBearer(auto_error=False)),
) -> User | None:
    """Optional authentication for public endpoints with personalization"""
    return await authenticate_optional(request, credentials)


# Role-based authorization dependencies
class RoleBasedAuth:
    """Role-based authentication class with the new RBAC system"""

    @staticmethod
    async def require_admin(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require admin role"""
        auth_dep = AuthorizationDependency(required_roles=["admin", "super_admin"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def require_teacher(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require teacher role or higher"""
        auth_dep = AuthorizationDependency(
            required_roles=["teacher", "admin", "super_admin"]
        )
        return await auth_dep(request, current_user)

    @staticmethod
    async def require_student(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require student role or higher"""
        auth_dep = AuthorizationDependency(
            required_roles=["student", "teacher", "admin", "super_admin"]
        )
        return await auth_dep(request, current_user)

    @staticmethod
    async def require_content_manager(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require content manager permissions"""
        auth_dep = AuthorizationDependency(required_permissions=["manage_content"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def require_user_manager(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require user management permissions"""
        auth_dep = AuthorizationDependency(required_permissions=["manage_users"])
        return await auth_dep(request, current_user)


# Permission-based authorization dependencies
class PermissionBasedAuth:
    """Permission-based authorization with the new RBAC system"""

    @staticmethod
    async def can_read(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require read permission"""
        auth_dep = AuthorizationDependency(required_permissions=["read"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def can_write(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require write permission"""
        auth_dep = AuthorizationDependency(required_permissions=["write"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def can_delete(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require delete permission"""
        auth_dep = AuthorizationDependency(required_permissions=["delete"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def can_manage_exams(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require exam management permission"""
        auth_dep = AuthorizationDependency(required_permissions=["manage_exams"])
        return await auth_dep(request, current_user)

    @staticmethod
    async def can_view_analytics(
        request: Request, current_user: User = Depends(get_authenticated_user)
    ) -> User:
        """Require analytics view permission"""
        auth_dep = AuthorizationDependency(required_permissions=["view_analytics"])
        return await auth_dep(request, current_user)


# Resource-specific authorization
class ResourceAuth:
    """Resource-specific authorization with ownership checks"""

    @staticmethod
    def require_user_access(allow_self: bool = True):
        """Factory function for user resource access"""

        async def _user_access_dependency(
            request: Request, current_user: User = Depends(get_authenticated_user)
        ) -> User:
            auth_dep = AuthorizationDependency(
                resource_type="user",
                required_permissions=["manage_users"] if not allow_self else [],
                allow_self=allow_self,
            )
            return await auth_dep(request, current_user)

        return _user_access_dependency

    @staticmethod
    def require_exam_access():
        """Require access to exam resources"""

        async def _exam_access_dependency(
            request: Request, current_user: User = Depends(get_authenticated_user)
        ) -> User:
            auth_dep = AuthorizationDependency(
                resource_type="exam", required_permissions=["manage_exams"]
            )
            return await auth_dep(request, current_user)

        return _exam_access_dependency

    @staticmethod
    def require_content_access(content_type: str = "general"):
        """Require access to content resources"""

        async def _content_access_dependency(
            request: Request, current_user: User = Depends(get_authenticated_user)
        ) -> User:
            auth_dep = AuthorizationDependency(
                resource_type=f"content_{content_type}",
                required_permissions=["manage_content"],
            )
            return await auth_dep(request, current_user)

        return _content_access_dependency


# Enhanced security context dependency
async def get_enhanced_security_context(
    request: Request, current_user: User | None = Depends(get_optional_user)
) -> SecurityContext:
    """Get enhanced security context for the request"""
    return get_security_context(request)


# Request security analysis dependency
async def analyze_request(
    request: Request, current_user: User | None = Depends(get_optional_user)
) -> dict[str, Any]:
    """Analyze request for security threats"""

    # Get client information
    ip_address = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()

    user_agent = request.headers.get("user-agent", "")

    # Get request body for analysis (if applicable)
    input_data = {}
    if hasattr(request.state, "json_body"):
        input_data = request.state.json_body
    elif request.query_params:
        input_data = dict(request.query_params)

    # Get user history (simplified - in production, fetch from database)
    user_history = []
    if current_user:
        # This would fetch actual IP history from database
        pass

    # Perform security analysis
    analysis = analyze_request_security(
        ip_address=ip_address,
        user_agent=user_agent,
        input_data=input_data,
        user_history=user_history,
    )

    # Store analysis in request state
    request.state.security_analysis = analysis

    # Log high-risk requests
    if analysis["risk_level"] in [
        SecurityLevel.HIGH.value,
        SecurityLevel.CRITICAL.value,
    ]:
        logger.warning(f"High-risk request detected from {ip_address}: {analysis}")

    return analysis


# Backward compatibility aliases for existing code
get_current_user = get_authenticated_user  # Alias for backward compatibility

# Role dependencies (backward compatibility)
require_admin = RoleBasedAuth.require_admin
require_teacher = RoleBasedAuth.require_teacher
require_student = RoleBasedAuth.require_student

# Permission dependencies
require_read = PermissionBasedAuth.can_read
require_write = PermissionBasedAuth.can_write
require_delete = PermissionBasedAuth.can_delete

# Resource dependencies
require_user_resource = ResourceAuth.require_user_access(allow_self=True)
require_admin_user_resource = ResourceAuth.require_user_access(allow_self=False)
require_exam_resource = ResourceAuth.require_exam_access()
require_content_resource = ResourceAuth.require_content_access()

# Security dependencies
get_security_analysis = analyze_request
get_request_context = get_enhanced_security_context


# Enhanced authorization helpers
class AuthorizationHelpers:
    """Helper functions for manual authorization checks"""

    @staticmethod
    async def check_user_access(
        user: User, resource_owner_id: int, required_permissions: list[str] = None
    ) -> bool:
        """Check if user can access a resource owned by another user"""

        # User can access their own resources
        if user.id == resource_owner_id:
            return True

        # Check permissions through RBAC
        rbac_manager = get_rbac_manager()
        auth_context = AuthorizationContext(
            user_id=user.id,
            user_role=user.role,
            required_permissions=required_permissions or [],
            resource_type="user",
            resource_id=str(resource_owner_id),
            resource_owner_id=resource_owner_id,
            request_path="manual_check",
            request_method="GET",
        )

        result = await rbac_manager.check_permission(auth_context)
        return result.authorized

    @staticmethod
    async def check_role_hierarchy(user_role: str, required_roles: list[str]) -> bool:
        """Check if user role satisfies required roles"""
        rbac_manager = get_rbac_manager()

        # Get role hierarchy
        user_role_obj = await rbac_manager.role_manager.get_role(user_role)
        if not user_role_obj:
            return False

        # Check if user role or its parents match required roles
        for required_role in required_roles:
            if await rbac_manager.role_manager.has_role_or_parent(
                user_role, required_role
            ):
                return True

        return False

    @staticmethod
    async def get_user_permissions(user: User) -> list[str]:
        """Get all permissions for user"""
        rbac_manager = get_rbac_manager()

        auth_context = AuthorizationContext(
            user_id=user.id,
            user_role=user.role,
            required_permissions=[],  # Empty to get all permissions
            resource_type="general",
            request_path="get_permissions",
            request_method="GET",
        )

        result = await rbac_manager.check_permission(auth_context)
        return result.granted_permissions


# Session management helpers
class SessionHelpers:
    """Session management helper functions"""

    @staticmethod
    async def create_user_session(user: User, request: Request) -> dict[str, Any]:
        """Create session for authenticated user"""
        session_manager = get_session_manager()

        ip_address = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        user_agent = request.headers.get("user-agent", "")
        headers = dict(request.headers)

        session_data = await session_manager.create_session(
            user=user, ip_address=ip_address, user_agent=user_agent, headers=headers
        )

        return {
            "session_id": session_data.session_id,
            "csrf_token": session_data.csrf_token,
            "expires_at": session_data.expires_at.isoformat(),
            "device_info": {
                "device_type": session_data.device_info.device_type.value,
                "device_name": session_data.device_info.device_name,
                "is_trusted": session_data.device_info.is_trusted,
            },
        }

    @staticmethod
    async def update_session_activity(session_id: str, request: Request):
        """Update session last activity"""
        session_manager = get_session_manager()

        ip_address = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        await session_manager.update_session_activity(session_id, ip_address)

    @staticmethod
    async def terminate_user_session(session_id: str, reason: str = "user_logout"):
        """Terminate specific user session"""
        session_manager = get_session_manager()
        return await session_manager.terminate_session(session_id, reason)


# Token management helpers
class TokenHelpers:
    """Token management helper functions"""

    @staticmethod
    async def create_auth_tokens(user: User, request: Request) -> dict[str, Any]:
        """Create authentication tokens for user"""
        token_manager = get_token_manager()

        ip_address = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = request.headers.get("x-device-fingerprint", "")

        # Create access token
        access_token, access_metadata = await token_manager.create_access_token(
            user=user,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            scope=["read", "write"],  # Default scope
        )

        # Create refresh token
        refresh_token, refresh_metadata = await token_manager.create_refresh_token(
            user=user,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": token_manager.access_token_expire_minutes * 60,
            "scope": "read write",
        }

    @staticmethod
    async def refresh_tokens(refresh_token: str, request: Request) -> dict[str, Any]:
        """Refresh access token"""
        token_manager = get_token_manager()

        ip_address = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = request.headers.get("x-device-fingerprint", "")

        new_access_token, metadata = await token_manager.refresh_access_token(
            refresh_token=refresh_token,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": token_manager.access_token_expire_minutes * 60,
        }

    @staticmethod
    async def revoke_token(token: str, reason: str = "user_logout"):
        """Revoke specific token"""
        token_manager = get_token_manager()
        await token_manager.revoke_token(token, reason)


# Export commonly used dependencies for easy import
__all__ = [
    # Main authentication dependencies
    "get_authenticated_user",
    "get_optional_user",
    "get_current_user",  # Backward compatibility
    # Role-based dependencies
    "require_admin",
    "require_teacher",
    "require_student",
    # Permission-based dependencies
    "require_read",
    "require_write",
    "require_delete",
    # Resource-based dependencies
    "require_user_resource",
    "require_admin_user_resource",
    "require_exam_resource",
    "require_content_resource",
    # Security dependencies
    "get_security_analysis",
    "get_request_context",
    # Helper classes
    "RoleBasedAuth",
    "PermissionBasedAuth",
    "ResourceAuth",
    "AuthorizationHelpers",
    "SessionHelpers",
    "TokenHelpers",
]
