"""
API Versioning System
ARCHITECTURE FIX: Version management and deprecation strategy
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional

from fastapi import Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .structured_logger import get_logger

logger = get_logger("api_versioning")


class APIVersion(Enum):
    """Supported API versions"""

    V1 = "v1"
    V2 = "v2"  # Future version


@dataclass
class VersionInfo:
    """API version information"""

    version: str
    status: str  # "stable", "deprecated", "sunset"
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    successor: Optional[str] = None
    description: str = ""


# Version catalog
API_VERSIONS = {
    "v1": VersionInfo(
        version="v1",
        status="stable",
        description="Current stable API version",
    ),
    # Wave 2B: Advanced Quality Evaluation API
    "v2": VersionInfo(
        version="v2",
        status="stable",
        description="Wave 2B Quality Evaluation - BERTScore + Bloom + ÖSYM Benchmark",
    ),
}


class VersionNegotiator:
    """
    API version negotiation and validation

    Supports:
    - URL path versioning (/api/v1/...)
    - Header-based versioning (Accept: application/vnd.turkiye-sinav.v1+json)
    - Query parameter versioning (?version=v1)
    """

    @staticmethod
    def extract_version_from_path(path: str) -> Optional[str]:
        """Extract version from URL path"""
        # Pattern: /api/v1/... or /api/v2/...
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "api" and i + 1 < len(parts):
                version_part = parts[i + 1]
                if version_part.startswith("v") and version_part[1:].isdigit():
                    return version_part
        return None

    @staticmethod
    def extract_version_from_header(accept_header: Optional[str]) -> Optional[str]:
        """Extract version from Accept header"""
        if not accept_header:
            return None

        # Pattern: application/vnd.turkiye-sinav.v1+json
        if "vnd.turkiye-sinav" in accept_header:
            parts = accept_header.split(".")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    return part.split("+")[0]  # Remove +json
        return None

    @staticmethod
    def extract_version_from_query(query_params: dict) -> Optional[str]:
        """Extract version from query parameters"""
        return query_params.get("version") or query_params.get("api_version")

    @staticmethod
    def negotiate_version(request: Request, accept: Optional[str] = None) -> str:
        """
        Negotiate API version from request

        Priority:
        1. URL path (/api/v1/...)
        2. Accept header (application/vnd.turkiye-sinav.v1+json)
        3. Query parameter (?version=v1)
        4. Default (v1)
        """
        # 1. URL path (highest priority)
        path_version = VersionNegotiator.extract_version_from_path(request.url.path)
        if path_version:
            return path_version

        # 2. Accept header
        header_version = VersionNegotiator.extract_version_from_header(accept)
        if header_version:
            return header_version

        # 3. Query parameter
        query_version = VersionNegotiator.extract_version_from_query(
            dict(request.query_params)
        )
        if query_version:
            return query_version

        # 4. Default version
        return "v1"

    @staticmethod
    def validate_version(version: str) -> VersionInfo:
        """
        Validate API version

        Raises:
            HTTPException: If version is invalid or sunset
        """
        if version not in API_VERSIONS:
            logger.warning(
                f"Invalid API version requested: {version}",
                extra_data={"version": version},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_api_version",
                    "message": f"API version '{version}' is not supported",
                    "supported_versions": list(API_VERSIONS.keys()),
                },
            )

        version_info = API_VERSIONS[version]

        # Check if sunset
        if version_info.status == "sunset":
            logger.error(
                f"Sunset API version accessed: {version}",
                extra_data={"version": version},
            )
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "error": "api_version_sunset",
                    "message": f"API version '{version}' has been sunset and is no longer available",
                    "sunset_date": version_info.sunset_date.isoformat()
                    if version_info.sunset_date
                    else None,
                    "successor": version_info.successor,
                },
            )

        # Log deprecation warning
        if version_info.status == "deprecated":
            logger.warning(
                f"Deprecated API version accessed: {version}",
                extra_data={
                    "version": version,
                    "deprecation_date": version_info.deprecation_date.isoformat()
                    if version_info.deprecation_date
                    else None,
                    "sunset_date": version_info.sunset_date.isoformat()
                    if version_info.sunset_date
                    else None,
                },
            )

        return version_info


class VersionMiddleware:
    """
    Middleware for API version handling

    Adds to FastAPI:
        app.add_middleware(VersionMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        path = scope["path"]
        headers = dict(scope.get("headers", []))
        accept_header = headers.get(b"accept", b"").decode()

        # Create request object for version negotiation
        from fastapi import Request

        request = Request(scope, receive=receive)

        try:
            # Negotiate version
            version = VersionNegotiator.negotiate_version(request, accept_header)

            # Validate version
            version_info = VersionNegotiator.validate_version(version)

            # Add version info to request state
            scope["state"] = scope.get("state", {})
            scope["state"]["api_version"] = version
            scope["state"]["api_version_info"] = version_info

            # Add deprecation headers if needed
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))

                    # Add version header
                    headers.append((b"x-api-version", version.encode()))

                    # Add deprecation headers
                    if version_info.status == "deprecated":
                        headers.append((b"deprecation", b"true"))
                        if version_info.sunset_date:
                            headers.append(
                                (
                                    b"sunset",
                                    version_info.sunset_date.strftime(
                                        "%a, %d %b %Y %H:%M:%S GMT"
                                    ).encode(),
                                )
                            )
                        if version_info.successor:
                            headers.append(
                                (
                                    b"link",
                                    f'<{version_info.successor}>; rel="successor-version"'.encode(),
                                )
                            )

                    message["headers"] = headers

                await send(message)

            await self.app(scope, receive, send_wrapper)

        except HTTPException as e:
            # Return error response
            response = JSONResponse(status_code=e.status_code, content=e.detail)
            await response(scope, receive, send)


# Dependency for route handlers
async def get_api_version(
    request: Request, accept: Optional[str] = Header(None)
) -> str:
    """
    Dependency to get API version in route handlers

    Usage:
        @router.get("/endpoint")
        async def endpoint(version: str = Depends(get_api_version)):
            if version == "v1":
                # v1 logic
            elif version == "v2":
                # v2 logic
    """
    version = VersionNegotiator.negotiate_version(request, accept)
    VersionNegotiator.validate_version(version)
    return version


# Decorator for version-specific endpoints
def version_endpoint(min_version: str = "v1", max_version: Optional[str] = None):
    """
    Decorator to restrict endpoint to specific API versions

    Usage:
        @router.get("/endpoint")
        @version_endpoint(min_version="v1", max_version="v2")
        async def endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Get version from request
            request = kwargs.get("request")
            if request:
                version = VersionNegotiator.negotiate_version(request)

                # Check version range
                version_num = int(version[1:])
                min_num = int(min_version[1:])
                max_num = int(max_version[1:]) if max_version else 999

                if version_num < min_num or version_num > max_num:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error": "endpoint_not_available",
                            "message": f"This endpoint is not available in API version {version}",
                            "min_version": min_version,
                            "max_version": max_version,
                        },
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Helper to deprecate specific endpoints
def deprecated_endpoint(
    deprecation_date: datetime, sunset_date: datetime, successor: str, message: str = ""
):
    """
    Decorator to mark endpoint as deprecated

    Usage:
        @router.get("/old-endpoint")
        @deprecated_endpoint(
            deprecation_date=datetime(2025, 6, 1),
            sunset_date=datetime(2025, 12, 1),
            successor="/api/v2/new-endpoint",
            message="Use the new endpoint for better performance"
        )
        async def old_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            now = datetime.now(timezone.utc)

            # Check if sunset
            if now >= sunset_date:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail={
                        "error": "endpoint_sunset",
                        "message": f"This endpoint has been sunset. {message}",
                        "sunset_date": sunset_date.isoformat(),
                        "successor": successor,
                    },
                )

            # Log deprecation warning
            if now >= deprecation_date:
                logger.warning(
                    f"Deprecated endpoint accessed: {func.__name__}",
                    extra_data={
                        "endpoint": func.__name__,
                        "deprecation_date": deprecation_date.isoformat(),
                        "sunset_date": sunset_date.isoformat(),
                        "successor": successor,
                    },
                )

            # Call original function
            result = await func(*args, **kwargs)

            # Add deprecation headers (if response is dict, wrap it)
            if isinstance(result, dict):
                result["_deprecation"] = {
                    "deprecated": True,
                    "deprecation_date": deprecation_date.isoformat(),
                    "sunset_date": sunset_date.isoformat(),
                    "successor": successor,
                    "message": message,
                }

            return result

        return wrapper

    return decorator
