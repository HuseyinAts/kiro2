"""
Audit Middleware (Task 48.5)
Automatically logs all HTTP requests for security and compliance

Features:
- Automatic request/response logging
- Performance tracking (response time)
- Error tracking
- User action correlation
- IP/User-Agent tracking
- Configurable exclusion patterns

Author: Claude
Date: 2025-10-27
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.audit_logger import (
    AuditAction,
    AuditResourceType,
    get_audit_logger,
)
from core.structured_logger import get_logger

logger = get_logger("audit_middleware")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Audit Middleware for automatic request logging (Task 48.5)

    Logs all HTTP requests with:
    - Request method, path, headers
    - Response status code, time
    - User ID (if authenticated)
    - IP address, user agent
    - Error details (if failed)
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """
        Initialize audit middleware

        Args:
            app: ASGI application
            exclude_paths: Paths to exclude from audit (e.g., /health, /metrics)
            log_request_body: Log request body (default: False for performance)
            log_response_body: Log response body (default: False for performance)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit trail

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        # Check if path should be excluded
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Extract request metadata
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Extract user ID from token (if available)
        user_id = await self._extract_user_id(request)

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            logger.error(
                f"[AUDIT] Request failed: {method} {path}",
                extra_data={
                    "method": method,
                    "path": path,
                    "error": error,
                    "user_id": user_id,
                    "ip_address": ip_address,
                },
            )
            raise

        # Calculate response time
        response_time = time.time() - start_time

        # Log audit trail (async in background)
        try:
            await self._log_audit(
                request=request,
                method=method,
                path=path,
                status_code=status_code,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error=error,
            )
        except Exception as e:
            # Don't fail request if audit logging fails
            logger.error(
                f"[AUDIT ERROR] Failed to log request: {e}",
                extra_data={"error": str(e), "path": path},
            )

        return response

    def _should_exclude(self, path: str) -> bool:
        """
        Check if path should be excluded from audit

        Args:
            path: Request path

        Returns:
            True if should be excluded
        """
        return any(excluded in path for excluded in self.exclude_paths)

    async def _extract_user_id(self, request: Request) -> str | None:
        """
        Extract user ID from authorization token

        Args:
            request: FastAPI request

        Returns:
            User ID or None
        """
        try:
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.replace("Bearer ", "")

            # Verify token and extract user ID
            from core.jwt_auth import get_jwt_manager

            jwt_manager = get_jwt_manager()
            payload = jwt_manager.verify_token(token)

            return payload.sub
        except Exception:
            return None

    async def _log_audit(
        self,
        request: Request,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        error: str | None = None,
    ):
        """
        Log audit entry to database

        Args:
            request: FastAPI request
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User ID (if authenticated)
            ip_address: Request IP address
            user_agent: Request user agent
            error: Error message (if failed)
        """
        try:
            # Get database session (sync - audit logging is synchronous)
            from core.database import SessionLocal

            db = SessionLocal()

            try:
                audit_logger = get_audit_logger(db)

                # Determine action based on method and path
                action = self._determine_action(method, path, status_code)

                # Determine resource type
                resource_type = self._determine_resource_type(path)

                # Extract resource ID from path (if available)
                resource_id = self._extract_resource_id(path)

                # Extra data
                extra_data = {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "response_time_ms": round(response_time * 1000, 2),
                    "query_params": dict(request.query_params),
                }

                if error:
                    extra_data["error"] = error

                # Log API request
                audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,
                    resource_id=resource_id,
                    new_values=extra_data,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                # Log security events
                if status_code == 401:
                    audit_logger.log_security_event(
                        event_type=AuditAction.LOGIN_FAILED,
                        description=f"Unauthorized access attempt: {method} {path}",
                        severity="medium",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                elif status_code == 403:
                    audit_logger.log_security_event(
                        event_type=AuditAction.PERMISSION_DENIED,
                        description=f"Permission denied: {method} {path}",
                        severity="medium",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                elif status_code == 429:
                    audit_logger.log_security_event(
                        event_type=AuditAction.RATE_LIMIT_EXCEEDED,
                        description=f"Rate limit exceeded: {method} {path}",
                        severity="low",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"[AUDIT ERROR] Failed to log audit entry: {e}",
                extra_data={"error": str(e), "path": path},
            )

    def _determine_action(
        self, method: str, path: str, status_code: int
    ) -> AuditAction:
        """
        Determine audit action based on request

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code

        Returns:
            AuditAction
        """
        # Authentication endpoints
        if "/auth/login" in path:
            return AuditAction.LOGIN if status_code < 400 else AuditAction.LOGIN_FAILED
        elif "/auth/logout" in path:
            return AuditAction.LOGOUT
        elif "/auth/logout-all" in path:
            return AuditAction.LOGOUT_ALL
        elif "/auth/refresh" in path:
            return AuditAction.TOKEN_REFRESH

        # User management
        elif "/user" in path:
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
            else:
                return AuditAction.USER_VIEW

        # Exam operations
        elif "/exam" in path:
            if method == "POST" and "/submit" in path:
                return AuditAction.EXAM_SUBMIT
            elif method == "POST" and "/start" in path:
                return AuditAction.EXAM_START
            elif method == "POST":
                return AuditAction.EXAM_CREATE
            elif method == "DELETE":
                return AuditAction.EXAM_DELETE
            else:
                return AuditAction.EXAM_RESULT_VIEW

        # Content operations
        elif "/content" in path:
            if method == "POST":
                return AuditAction.CONTENT_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.CONTENT_UPDATE
            elif method == "DELETE":
                return AuditAction.CONTENT_DELETE
            else:
                return AuditAction.CONTENT_VIEW

        # API key operations
        elif "/api-key" in path:
            if method == "POST":
                return AuditAction.API_KEY_CREATE
            elif method == "DELETE":
                return AuditAction.API_KEY_REVOKE
            else:
                return AuditAction.API_REQUEST

        # Default: API request
        return AuditAction.API_REQUEST

    def _determine_resource_type(self, path: str) -> AuditResourceType:
        """
        Determine resource type from path

        Args:
            path: Request path

        Returns:
            AuditResourceType
        """
        if "/user" in path or "/auth" in path:
            return AuditResourceType.USER
        elif "/student" in path:
            return AuditResourceType.STUDENT
        elif "/teacher" in path:
            return AuditResourceType.TEACHER
        elif "/exam" in path:
            return AuditResourceType.EXAM
        elif "/question" in path:
            return AuditResourceType.QUESTION
        elif "/content" in path:
            return AuditResourceType.CONTENT
        elif "/api-key" in path:
            return AuditResourceType.API_KEY
        else:
            return AuditResourceType.SYSTEM

    def _extract_resource_id(self, path: str) -> str | None:
        """
        Extract resource ID from path (e.g., /user/123 -> 123)

        Args:
            path: Request path

        Returns:
            Resource ID or None
        """
        try:
            parts = path.split("/")
            # Look for UUID-like patterns or numeric IDs
            for part in parts:
                if len(part) > 10 and ("-" in part or part.isdigit()):
                    return part
            return None
        except Exception:
            return None
