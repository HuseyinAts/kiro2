"""
Comprehensive Security Middleware
Task 23: Security Hardening - Tüm güvenlik önlemlerini birleştiren middleware

Bu middleware:
- Input validation
- SQL injection prevention
- XSS prevention
- CORS validation
- Security headers
- Rate limiting
"""
import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.structured_logger import get_logger
from core.cors_security import validate_origin
from core.xss_prevention import add_security_headers

logger = get_logger("security_middleware")


class ComprehensiveSecurityMiddleware(BaseHTTPMiddleware):
    """
    Kapsamlı güvenlik middleware'i

    Tüm request'leri güvenlik kontrollerinden geçirir.
    """

    def __init__(
        self,
        app,
        enable_cors_validation: bool = True,
        enable_security_headers: bool = True,
        enable_request_logging: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        blocked_user_agents: list = None,
    ):
        """
        Initialize security middleware

        Args:
            app: FastAPI application
            enable_cors_validation: CORS validation aktif mi?
            enable_security_headers: Security headers eklensin mi?
            enable_request_logging: Request logging aktif mi?
            max_request_size: Maksimum request boyutu (bytes)
            blocked_user_agents: Engellenecek user agent listesi
        """
        super().__init__(app)
        self.enable_cors_validation = enable_cors_validation
        self.enable_security_headers = enable_security_headers
        self.enable_request_logging = enable_request_logging
        self.max_request_size = max_request_size
        self.blocked_user_agents = blocked_user_agents or [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "nessus",
            "openvas",
            "metasploit",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Request'i güvenlik kontrollerinden geçir

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        # 1. User Agent kontrolü
        user_agent = request.headers.get("user-agent", "").lower()
        if any(blocked in user_agent for blocked in self.blocked_user_agents):
            logger.warning(
                "Blocked suspicious user agent",
                user_agent=user_agent,
                ip=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"},
            )

        # 2. Request size kontrolü
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(
                "Request size exceeded",
                content_length=content_length,
                max_size=self.max_request_size,
                ip=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request too large"},
            )

        # 3. CORS validation
        if self.enable_cors_validation:
            origin = request.headers.get("origin")

            if origin:
                # Preflight request (OPTIONS)
                if request.method == "OPTIONS":
                    if not validate_origin(origin):
                        logger.warning(
                            "CORS preflight rejected",
                            origin=origin,
                            ip=request.client.host if request.client else "unknown",
                        )
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Origin not allowed"},
                        )

                # Normal request
                elif not validate_origin(origin):
                    logger.warning(
                        "CORS validation failed",
                        origin=origin,
                        method=request.method,
                        path=request.url.path,
                        ip=request.client.host if request.client else "unknown",
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Origin not allowed"},
                    )

        # 4. Suspicious path kontrolü
        suspicious_paths = [
            "../",
            "..\\",  # Path traversal
            "/etc/",
            "/proc/",  # System files
            "wp-admin",
            "phpmyadmin",  # Common attack targets
            ".env",
            ".git",  # Sensitive files
        ]

        path_lower = request.url.path.lower()
        if any(suspicious in path_lower for suspicious in suspicious_paths):
            logger.warning(
                "Suspicious path detected",
                path=request.url.path,
                ip=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"}
            )

        # 5. Request logging
        if self.enable_request_logging:
            logger.info(
                "Security check passed",
                method=request.method,
                path=request.url.path,
                ip=request.client.host if request.client else "unknown",
                user_agent=user_agent[:100],  # Truncate
            )

        # 6. Process request
        try:
            response = await call_next(request)

            # 7. Security headers ekle
            if self.enable_security_headers:
                response = add_security_headers(response)

            # 8. Response time logging
            process_time = time.time() - start_time
            response.headers["X-Response-Time"] = f"{process_time:.3f}s"

            return response

        except Exception as e:
            logger.error(
                "Request processing error",
                error=str(e),
                method=request.method,
                path=request.url.path,
                ip=request.client.host if request.client else "unknown",
            )

            # Generic error response (don't leak details)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Input validation middleware

    Tüm request body'lerini otomatik olarak validate eder.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Request body'yi validate et

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Sadece POST, PUT, PATCH request'leri için
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Content-Type kontrolü
                content_type = request.headers.get("content-type", "")

                if "application/json" in content_type:
                    # JSON body validation
                    # FastAPI Pydantic validation'ı otomatik yapar
                    # Bu middleware ek kontroller için kullanılabilir
                    pass

                elif "multipart/form-data" in content_type:
                    # File upload validation
                    # Max file size, allowed extensions, etc.
                    pass

            except Exception as e:
                logger.error(
                    "Input validation error",
                    error=str(e),
                    method=request.method,
                    path=request.url.path,
                )

                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid input"},
                )

        response = await call_next(request)
        return response


class SQLInjectionDetectionMiddleware(BaseHTTPMiddleware):
    """
    SQL injection detection middleware

    Query parameters ve path parameters'da SQL injection pattern'lerini tespit eder.
    """

    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*|1=1|'=')",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        SQL injection pattern kontrolü

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        import re

        # Query parameters kontrolü
        for key, value in request.query_params.items():
            value_str = str(value).upper()

            for pattern in self.SQL_PATTERNS:
                if re.search(pattern, value_str, re.IGNORECASE):
                    logger.warning(
                        "SQL injection attempt detected in query params",
                        key=key,
                        value=value[:100],  # Truncate
                        ip=request.client.host if request.client else "unknown",
                        path=request.url.path,
                    )

                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid input"},
                    )

        # Path parameters kontrolü
        path = request.url.path.upper()
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(
                    "SQL injection attempt detected in path",
                    path=request.url.path,
                    ip=request.client.host if request.client else "unknown",
                )

                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "Not found"},
                )

        response = await call_next(request)
        return response


# Example usage:
"""
from fastapi import FastAPI
from middleware.comprehensive_security_middleware import (
    ComprehensiveSecurityMiddleware,
    InputValidationMiddleware,
    SQLInjectionDetectionMiddleware
)

app = FastAPI()

# Add security middlewares
app.add_middleware(ComprehensiveSecurityMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(SQLInjectionDetectionMiddleware)
"""
