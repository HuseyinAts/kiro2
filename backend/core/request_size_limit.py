"""
Request Size Limiting Middleware
SECURITY FIX: Prevent DoS attacks via large payloads
"""

import logging

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size

    Prevents DoS attacks via excessively large request payloads
    """

    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10 MB default
        max_file_upload_size: int | None = None,  # Can be different for file uploads
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.max_file_upload_size = max_file_upload_size or max_request_size
        logger.info(
            f"[SECURITY] Request size limiting enabled: "
            f"max_request={max_request_size / 1024 / 1024:.1f}MB, "
            f"max_file_upload={self.max_file_upload_size / 1024 / 1024:.1f}MB"
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check request size before processing"""

        # Get content length from headers
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)

            # Determine size limit based on content type
            is_file_upload = self._is_file_upload(request)
            size_limit = (
                self.max_file_upload_size if is_file_upload else self.max_request_size
            )

            # Check if request exceeds limit
            if content_length > size_limit:
                logger.warning(
                    f"[SECURITY] Request too large: {content_length} bytes "
                    f"(limit: {size_limit} bytes) from {request.client.host} "
                    f"to {request.url.path}"
                )

                # S179 (B-P0-10 / GF99): middleware Response, not raise.
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": (
                            f"Request body too large. "
                            f"Maximum allowed size is {size_limit / 1024 / 1024:.1f}MB"
                        )
                    },
                )

        # Process request
        response = await call_next(request)
        return response

    @staticmethod
    def _is_file_upload(request: Request) -> bool:
        """Detect if request is a file upload"""
        content_type = request.headers.get("content-type", "")

        # Check for multipart/form-data (file uploads)
        if "multipart/form-data" in content_type:
            return True

        # Check for common file upload endpoints
        path = request.url.path.lower()
        file_upload_paths = ["/upload", "/file", "/media", "/attachment"]
        if any(upload_path in path for upload_path in file_upload_paths):
            return True

        return False


# Convenience function for adding to FastAPI app
def add_request_size_limit(
    app,
    max_request_size: int = 10 * 1024 * 1024,
    max_file_upload_size: int | None = None,
) -> None:
    """
    Add request size limiting middleware to FastAPI app

    Usage:
        from core.request_size_limit import add_request_size_limit

        app = FastAPI()
        add_request_size_limit(app, max_request_size=10*1024*1024)  # 10 MB
    """
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_request_size=max_request_size,
        max_file_upload_size=max_file_upload_size,
    )
