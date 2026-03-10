"""
Learning Path Authentication & Authorization
Simple JWT-based auth for Learning Path API endpoints

Features:
- JWT token validation
- Ownership verification (students can only access their own paths)
- Role-based access (teachers and admins can access all paths)
"""

import logging
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.jwt_auth import JWTManager, TokenType, UserRole, get_jwt_manager
from models.learning_path_models import LearningPathStudentProfile

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=True)


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
):
    """
    Extract and validate current user from JWT token

    Args:
        credentials: HTTP Bearer token credentials
        jwt_manager: JWT manager instance

    Returns:
        TokenPayload: Validated token payload with user info

    Raises:
        HTTPException: 401 if token is invalid
    """
    try:
        token = credentials.credentials

        # Verify token
        payload = jwt_manager.verify_token(token, TokenType.ACCESS)

        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_student_access(
    student_id: str,
    current_user,
    db: AsyncSession,
    allow_privileged: bool = True,
) -> bool:
    """
    Verify that current user can access student data.

    For students: checks DB ownership (user_id matches in learning_path_student_profiles).
    For teachers/admins: allows access to any student.

    Args:
        student_id: Target student ID (STU_xxx format)
        current_user: Current user token payload
        db: Async database session
        allow_privileged: If True, teachers and admins can access any student

    Returns:
        bool: True if access is allowed

    Raises:
        HTTPException: 403 if access is denied
    """
    # Privileged roles (teacher, admin) can access any student
    if allow_privileged and current_user.role in [
        UserRole.TEACHER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        logger.info(
            f"Privileged access granted: {current_user.role.value} accessing student {student_id}"
        )
        return True

    # Student ownership: verify via DB that user_id owns this student_id
    user_id = getattr(current_user, 'id', None) or getattr(current_user, 'sub', None)

    result = await db.execute(
        select(LearningPathStudentProfile.student_id).where(
            LearningPathStudentProfile.user_id == str(user_id),
            LearningPathStudentProfile.student_id == student_id,
        )
    )
    if not result.scalar_one_or_none():
        logger.warning(
            f"IDOR blocked: user={user_id} attempted access to student={student_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu öğrenci verisine erişim yetkiniz yok",
        )

    logger.info(
        f"Student access verified: user={user_id} owns student={student_id}"
    )
    return True


class RequireStudentOwnership:
    """
    Dependency class to require student ownership or privileged role

    Usage:
        @router.post("/create")
        async def create_path(
            request: LearningPathCreateRequest,
            current_user = Depends(get_current_user_from_token),
            _: bool = Depends(RequireStudentOwnership("student_id"))
        ):
            # Ownership verified, proceed
            ...
    """

    def __init__(self, student_id_param: str = "student_id"):
        """
        Args:
            student_id_param: Name of the parameter containing student_id
        """
        self.student_id_param = student_id_param

    def __call__(
        self,
        student_id: str,  # This will be injected from request
        current_user=Depends(get_current_user_from_token),
    ) -> bool:
        """Verify ownership"""
        return verify_student_access(student_id, current_user, allow_privileged=True)


def require_permission(required_permission: str):
    """
    Dependency factory to require specific permission

    Args:
        required_permission: Permission string (e.g., "exam:create")

    Returns:
        Dependency function

    Usage:
        @router.post("/admin-only")
        async def admin_endpoint(
            current_user = Depends(get_current_user_from_token),
            _: bool = Depends(require_permission("system:monitor"))
        ):
            # Permission verified, proceed
            ...
    """

    async def permission_checker(
        current_user=Depends(get_current_user_from_token),
    ) -> bool:
        # Super admin has all permissions
        if "*" in current_user.permissions:
            return True

        if required_permission not in current_user.permissions:
            logger.warning(
                f"Permission denied: User {getattr(current_user, 'id', getattr(current_user, 'sub', '?'))} lacks '{required_permission}' permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "message": "Bu işlem için yetkiniz yok",
                    "message_en": "Insufficient permissions for this operation",
                    "required_permission": required_permission,
                },
            )

        return True

    return permission_checker


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific role(s)

    Args:
        *allowed_roles: One or more UserRole values

    Returns:
        Dependency function

    Usage:
        @router.get("/teacher-only")
        async def teacher_endpoint(
            current_user = Depends(get_current_user_from_token),
            _: bool = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))
        ):
            # Role verified, proceed
            ...
    """

    async def role_checker(current_user=Depends(get_current_user_from_token)) -> bool:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Role denied: User {getattr(current_user, 'id', getattr(current_user, 'sub', '?'))} has role '{current_user.role.value}', "
                f"required: {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_role",
                    "message": "Bu işlem için yetkiniz yok",
                    "message_en": "Insufficient role for this operation",
                    "required_roles": [r.value for r in allowed_roles],
                },
            )

        return True

    return role_checker


# Optional auth (for public endpoints with optional user context)
optional_security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
):
    """
    Get current user from token if provided, otherwise None

    Usage for public endpoints that want to customize behavior for logged-in users
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token, TokenType.ACCESS)
        return payload
    except Exception as e:
        logger.debug(f"Optional auth failed (ignored): {e}")
        return None
