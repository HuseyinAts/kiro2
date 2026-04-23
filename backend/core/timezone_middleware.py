"""
Timezone Middleware - Phase 3.0
Automatic timezone handling for FastAPI requests and responses

This middleware automatically:
1. Converts all incoming datetime strings to UTC timezone-aware datetimes
2. Adds Turkish timezone versions of all datetime fields in responses
3. Sets timezone-related headers
4. Handles timezone conversion errors gracefully

Integration with auth_refactored.py and all API endpoints.

Usage:
    from fastapi import FastAPI
    from core.timezone_middleware import add_timezone_middleware

    app = FastAPI()
    add_timezone_middleware(app)
"""

import json
import logging
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from core.timezone_utils import (
    convert_dict_datetimes_to_utc,
    format_datetime_turkish,
    format_datetime_turkish_display,
    format_datetime_utc,
    format_dict_datetimes_for_api,
    parse_datetime,
)

logger = logging.getLogger(__name__)


class TimezoneMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic timezone handling

    Features:
    - Converts all incoming datetimes to UTC
    - Adds Turkish timezone versions to responses
    - Sets X-Timezone headers
    - Logs timezone conversion errors

    Configuration:
    - add_turkish_versions: Add _tr suffix fields with Turkish timezone
    - add_display_formats: Add _display suffix fields with DD.MM.YYYY HH:MM format
    - log_conversions: Log all timezone conversions (debug mode)
    """

    def __init__(
        self,
        app: ASGIApp,
        add_turkish_versions: bool = True,
        add_display_formats: bool = True,
        log_conversions: bool = False,
    ):
        super().__init__(app)
        self.add_turkish_versions = add_turkish_versions
        self.add_display_formats = add_display_formats
        self.log_conversions = log_conversions

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request and response with timezone handling

        Request Processing:
        - Parses request body (if JSON)
        - Converts all datetime strings to UTC timezone-aware
        - Stores original timezone if provided

        Response Processing:
        - Adds Turkish timezone versions of datetime fields
        - Adds user-friendly display formats
        - Sets X-Timezone headers
        """
        try:
            # Process request body for datetime conversion
            if request.method in ["POST", "PUT", "PATCH"]:
                request = await self._process_request_datetimes(request)

            # Set timezone metadata on request
            request.state.timezone_processed = True
            request.state.request_timezone = "UTC"
            request.state.user_timezone = "Europe/Istanbul"  # Turkish timezone

            # Process request
            response = await call_next(request)

            # Process response body for datetime conversion
            response = await self._process_response_datetimes(response, request)

            # Add timezone headers
            response.headers["X-Timezone-Processed"] = "true"
            response.headers["X-Server-Timezone"] = "UTC"
            response.headers["X-User-Timezone"] = "Europe/Istanbul"
            response.headers["X-Timezone-Format"] = "ISO8601"

            return response

        except Exception as e:
            logger.error(f"Timezone middleware error: {e}", exc_info=True)
            # Don't fail the request due to timezone processing errors
            return await call_next(request)

    async def _process_request_datetimes(self, request: Request) -> Request:
        """
        Process request body to convert datetime strings to UTC

        Reads JSON body, finds all datetime-like strings, and converts
        them to UTC timezone-aware datetimes.

        Args:
            request: FastAPI Request object

        Returns:
            Request: Modified request with UTC datetimes
        """
        try:
            # Read request body
            body = await request.body()

            if not body:
                return request

            # Parse JSON
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON or can't decode, skip processing
                return request

            # Convert datetime strings to UTC
            converted_data = self._convert_request_datetimes_to_utc(data)

            if self.log_conversions:
                logger.debug(f"Request datetime conversion: {data} -> {converted_data}")

            # Update request body
            # Note: FastAPI will re-parse this in the endpoint
            request._body = json.dumps(converted_data).encode("utf-8")

            return request

        except Exception as e:
            logger.warning(f"Request datetime processing error: {e}")
            return request

    def _convert_request_datetimes_to_utc(self, data: Any) -> Any:
        """
        Recursively convert datetime strings in request data to UTC

        Args:
            data: Request data (dict, list, or primitive)

        Returns:
            Converted data with UTC datetimes
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Check if field name suggests datetime
                is_datetime_field = any(
                    suffix in key.lower()
                    for suffix in [
                        "_at",
                        "_time",
                        "_date",
                        "timestamp",
                        "created",
                        "updated",
                        "deleted",
                        "started",
                        "completed",
                        "finished",
                    ]
                )

                if isinstance(value, str) and is_datetime_field:
                    # Try to parse as datetime
                    parsed = parse_datetime(value)
                    if parsed:
                        result[key] = format_datetime_utc(parsed)
                    else:
                        result[key] = value
                elif isinstance(value, (dict, list)):
                    result[key] = self._convert_request_datetimes_to_utc(value)
                else:
                    result[key] = value
            return result

        if isinstance(data, list):
            return [self._convert_request_datetimes_to_utc(item) for item in data]

        return data

    async def _process_response_datetimes(
        self, response: Response, request: Request
    ) -> Response:
        """
        Process response body to add Turkish timezone versions

        Adds:
        - {field}_tr: Turkish timezone version (ISO 8601)
        - {field}_display: Turkish user-friendly format (DD.MM.YYYY HH:MM)

        Args:
            response: FastAPI Response object
            request: Original request object

        Returns:
            Response: Modified response with Turkish timezone fields
        """
        try:
            # Only process JSON responses
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return response

            # Read response body
            body = response.body

            if not body:
                return response

            # Parse JSON
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return response

            # Add Turkish timezone versions
            enhanced_data = self._add_turkish_timezone_fields(data)

            if self.log_conversions:
                logger.debug("Response datetime enhancement: added Turkish timezone fields")

            # Update response body
            new_body = json.dumps(enhanced_data, ensure_ascii=False, default=str).encode(
                "utf-8"
            )
            response.headers["content-length"] = str(len(new_body))

            # Create new response with updated body
            return Response(
                content=new_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        except Exception as e:
            logger.warning(f"Response datetime processing error: {e}")
            return response

    def _add_turkish_timezone_fields(self, data: Any) -> Any:
        """
        Recursively add Turkish timezone versions to datetime fields

        For each datetime field, adds:
        - {field}_tr: Turkish timezone (ISO 8601)
        - {field}_display: User-friendly Turkish format

        Args:
            data: Response data

        Returns:
            Enhanced data with Turkish timezone fields
        """
        if isinstance(data, dict):
            result = {}

            for key, value in data.items():
                # Keep original UTC value
                result[key] = value

                # Check if field is a datetime string
                if isinstance(value, str):
                    # Try to parse as datetime
                    parsed = parse_datetime(value)

                    if parsed:
                        # Add Turkish timezone version
                        if self.add_turkish_versions:
                            tr_key = f"{key}_tr"
                            if tr_key not in data:  # Don't overwrite existing
                                result[tr_key] = format_datetime_turkish(parsed)

                        # Add display format
                        if self.add_display_formats:
                            display_key = f"{key}_display"
                            if display_key not in data:
                                result[display_key] = format_datetime_turkish_display(
                                    parsed
                                )

                # Recurse into nested structures
                elif isinstance(value, dict):
                    result[key] = self._add_turkish_timezone_fields(value)

                elif isinstance(value, list):
                    result[key] = [
                        self._add_turkish_timezone_fields(item)
                        if isinstance(item, (dict, list))
                        else item
                        for item in value
                    ]

            return result

        if isinstance(data, list):
            return [
                self._add_turkish_timezone_fields(item)
                if isinstance(item, (dict, list))
                else item
                for item in data
            ]

        return data


# ================================================================
# FASTAPI INTEGRATION HELPERS
# ================================================================

def add_timezone_middleware(
    app,
    add_turkish_versions: bool = True,
    add_display_formats: bool = True,
    log_conversions: bool = False,
):
    """
    Add timezone middleware to FastAPI application

    Args:
        app: FastAPI application instance
        add_turkish_versions: Add _tr suffix fields with Turkish timezone
        add_display_formats: Add _display suffix fields with DD.MM.YYYY HH:MM
        log_conversions: Log all timezone conversions (debug mode)

    Example:
        from fastapi import FastAPI
        from core.timezone_middleware import add_timezone_middleware

        app = FastAPI()
        add_timezone_middleware(app)

        # All datetime fields will automatically get:
        # - UTC normalization on input
        # - Turkish timezone versions in responses
        # - User-friendly display formats
    """
    app.add_middleware(
        TimezoneMiddleware,
        add_turkish_versions=add_turkish_versions,
        add_display_formats=add_display_formats,
        log_conversions=log_conversions,
    )

    logger.info("Timezone middleware added to FastAPI application")
    logger.info(
        f"Configuration: turkish_versions={add_turkish_versions}, "
        f"display_formats={add_display_formats}, log_conversions={log_conversions}"
    )


# ================================================================
# MANUAL TIMEZONE CONVERSION FOR ENDPOINTS
# ================================================================

def ensure_request_datetimes_utc(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Manually ensure all datetimes in request data are UTC

    Use this in endpoints that need explicit timezone handling:

    Example:
        @router.post("/exams")
        async def create_exam(data: ExamCreate):
            data_dict = data.dict()
            data_dict = ensure_request_datetimes_utc(data_dict)
            # Now all datetimes are UTC timezone-aware
    """
    return convert_dict_datetimes_to_utc(request_data)


def add_turkish_timezone_to_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """
    Manually add Turkish timezone versions to response data

    Use this in endpoints that need explicit timezone formatting:

    Example:
        @router.get("/exams/{exam_id}")
        async def get_exam(exam_id: str):
            exam = await get_exam_from_db(exam_id)
            exam_dict = exam.dict()
            exam_dict = add_turkish_timezone_to_response(exam_dict)
            return exam_dict
            # Response will have _tr and _display fields
    """
    middleware = TimezoneMiddleware(app=None)  # Create instance for method access
    return middleware._add_turkish_timezone_fields(response_data)


# ================================================================
# MIGRATION HELPERS FOR EXISTING ENDPOINTS
# ================================================================

class ManualTimezoneConverter:
    """
    Helper class for manual timezone conversion in existing endpoints

    Use this during migration from old timezone-naive code to new
    timezone-aware code.

    Example:
        converter = ManualTimezoneConverter()

        # In old endpoint:
        @router.post("/old-endpoint")
        async def old_endpoint(data: dict):
            # Convert incoming datetimes to UTC
            data = converter.convert_request_to_utc(data)

            # ... process data ...

            # Add Turkish timezone to response
            response = {"created_at": datetime.now(timezone.utc)}
            response = converter.add_turkish_to_response(response)
            return response
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ManualTimezoneConverter")

    def convert_request_to_utc(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert all datetimes in request to UTC"""
        return ensure_request_datetimes_utc(data)

    def add_turkish_to_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add Turkish timezone versions to response"""
        return add_turkish_timezone_to_response(data)

    def format_for_api(
        self, data: dict[str, Any], use_turkish: bool = False
    ) -> dict[str, Any]:
        """Format all datetimes in data for API response"""
        return format_dict_datetimes_for_api(data, use_turkish=use_turkish)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    "ManualTimezoneConverter",
    "TimezoneMiddleware",
    "add_timezone_middleware",
    "add_turkish_timezone_to_response",
    "ensure_request_datetimes_utc",
]
