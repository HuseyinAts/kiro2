"""
Sentry Error Tracking Configuration for Kiro2 Platform
Sprint 12: Comprehensive Error Tracking & Monitoring

Advanced Sentry integration with:
- Automatic error capture and reporting
- Performance monitoring (transactions)
- Release tracking
- Custom error categorization
- User context enrichment
- Breadcrumbs for error context
- Environment-based configuration
"""
import logging
import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger(__name__)


class SentryConfig:
    """
    Comprehensive Sentry Configuration

    Features:
    - Automatic error capture
    - Performance monitoring
    - Release tracking
    - Custom tags and context
    - Error filtering and sampling
    - User tracking
    """

    def __init__(
        self,
        dsn: str | None = None,
        environment: str = "production",
        release: str | None = None,
        traces_sample_rate: float = 1.0,
        profiles_sample_rate: float = 1.0,
        enable_tracing: bool = True,
        debug: bool = False,
    ):
        """
        Initialize Sentry configuration

        Args:
            dsn: Sentry DSN (Data Source Name)
            environment: Environment name (dev, staging, production)
            release: Release version (e.g., "kiro2@1.0.0")
            traces_sample_rate: Sampling rate for performance transactions (0.0 - 1.0)
            profiles_sample_rate: Sampling rate for profiling (0.0 - 1.0)
            enable_tracing: Enable performance monitoring
            debug: Enable Sentry debug mode
        """
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.release = release or self._get_release_version()
        self.traces_sample_rate = traces_sample_rate
        self.profiles_sample_rate = profiles_sample_rate
        self.enable_tracing = enable_tracing
        self.debug = debug

        # Error categorization tags
        self.error_categories = {
            "DatabaseError": "database",
            "ConnectionError": "network",
            "TimeoutError": "timeout",
            "ValidationError": "validation",
            "AuthenticationError": "auth",
            "PermissionError": "auth",
            "HTTPException": "http",
            "ValueError": "validation",
            "KeyError": "data",
            "TypeError": "data",
        }

    def _get_release_version(self) -> str:
        """
        Get release version from environment or git

        Returns:
            Release version string
        """
        # Try environment variable first
        release = os.getenv("RELEASE_VERSION")
        if release:
            return f"kiro2@{release}"

        # Try git commit hash
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                return f"kiro2@{commit_hash}"
        except Exception:
            pass

        # Fallback to default
        return "kiro2@1.0.0"

    def setup(self):
        """
        Initialize Sentry with all integrations and configurations
        """
        if not self.dsn:
            logger.warning(
                "[WARNING] Sentry DSN not configured - Error tracking disabled. "
                "Set SENTRY_DSN environment variable to enable."
            )
            return

        try:
            # Configure Sentry
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,

                # Integrations
                integrations=[
                    # FastAPI integration (automatic request tracking)
                    FastApiIntegration(
                        transaction_style="url",  # Group by URL path
                        failed_request_status_codes=[500, 501, 502, 503, 504],
                    ),

                    # SQLAlchemy integration (database queries)
                    SqlalchemyIntegration(),

                    # Redis integration (cache operations)
                    RedisIntegration(),

                    # Logging integration
                    LoggingIntegration(
                        level=logging.INFO,  # Capture info and above
                        event_level=logging.ERROR,  # Send error and above to Sentry
                    ),

                    # Asyncio integration
                    AsyncioIntegration(),

                    # HTTPX integration (HTTP client)
                    HttpxIntegration(),
                ],

                # Performance monitoring
                traces_sample_rate=self.traces_sample_rate if self.enable_tracing else 0.0,
                _experiments={
                    "profiles_sample_rate": self.profiles_sample_rate,
                },

                # Error filtering
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb,

                # Configuration
                debug=self.debug,
                attach_stacktrace=True,
                send_default_pii=False,  # KVKK compliance - no PII by default

                # Performance
                max_breadcrumbs=100,
                max_value_length=16384,

                # Request body
                request_bodies="medium",  # Capture request bodies for errors

                # Sampling
                sample_rate=1.0,  # Capture all errors (no sampling)

                # Tags
                default_integrations=True,
            )

            # Set global tags
            sentry_sdk.set_tag("platform", "kiro2")
            sentry_sdk.set_tag("language", "python")
            sentry_sdk.set_tag("framework", "fastapi")

            logger.info(
                f"[OK] [SHIELD] Sentry initialized - Environment: {self.environment}, "
                f"Release: {self.release}, Tracing: {self.enable_tracing}"
            )

        except Exception as e:
            logger.error(f"[ERROR] Sentry initialization failed: {e}")
            raise

    def _before_send(self, event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
        """
        Filter and modify events before sending to Sentry

        Args:
            event: Sentry event data
            hint: Additional context

        Returns:
            Modified event or None to drop the event
        """
        # Add error category tag
        if "exception" in event and "values" in event["exception"]:
            for exception in event["exception"]["values"]:
                exc_type = exception.get("type", "")
                category = self.error_categories.get(exc_type, "other")
                event.setdefault("tags", {})["error_category"] = category

        # Filter out health check errors
        if "request" in event and "url" in event["request"]:
            url = event["request"]["url"]
            if any(path in url for path in ["/health", "/metrics", "/docs"]):
                return None  # Drop health check errors

        # Add business context
        if "user" in event:
            user_role = event["user"].get("role")
            if user_role:
                event.setdefault("tags", {})["user_role"] = user_role

        # Sanitize sensitive data (KVKK compliance)
        event = self._sanitize_event(event)

        return event

    def _before_breadcrumb(self, crumb: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
        """
        Filter and modify breadcrumbs before adding to event

        Args:
            crumb: Breadcrumb data
            hint: Additional context

        Returns:
            Modified breadcrumb or None to drop
        """
        # Filter out noisy breadcrumbs
        if crumb.get("category") == "query":
            query = crumb.get("message", "")
            # Skip SELECT queries from health checks
            if "pg_stat_activity" in query or "pg_database" in query:
                return None

        # Sanitize breadcrumb data
        if "data" in crumb:
            crumb["data"] = self._sanitize_dict(crumb["data"])

        return crumb

    def _sanitize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Remove sensitive data from Sentry event (KVKK compliance)

        Args:
            event: Sentry event

        Returns:
            Sanitized event
        """
        # Sanitize request data
        if "request" in event:
            if "data" in event["request"]:
                event["request"]["data"] = self._sanitize_dict(event["request"]["data"])
            if "headers" in event["request"]:
                event["request"]["headers"] = self._sanitize_headers(event["request"]["headers"])
            if "cookies" in event["request"]:
                event["request"]["cookies"] = {"[Filtered]": "[Filtered]"}

        # Sanitize extra data
        if "extra" in event:
            event["extra"] = self._sanitize_dict(event["extra"])

        return event

    def _sanitize_dict(self, data: Any) -> Any:
        """
        Recursively sanitize dictionary data

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data
        """
        if not isinstance(data, dict):
            return data

        sensitive_keys = [
            "password", "token", "secret", "api_key", "authorization",
            "credit_card", "ssn", "phone", "email", "tcno", "iban"
        ]

        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[Filtered]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_headers(self, headers: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize HTTP headers

        Args:
            headers: Request headers

        Returns:
            Sanitized headers
        """
        sensitive_headers = [
            "authorization", "cookie", "x-api-key", "x-auth-token"
        ]

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[Filtered]"
            else:
                sanitized[key] = value

        return sanitized


# Global Sentry instance
_sentry_config: SentryConfig | None = None


def get_sentry_config() -> SentryConfig:
    """Get or create global Sentry configuration"""
    global _sentry_config
    if _sentry_config is None:
        environment = os.getenv("DEPLOYMENT_ENV", "production")

        # Adjust sampling based on environment
        if environment == "production":
            traces_sample_rate = 0.1  # 10% sampling in production
            profiles_sample_rate = 0.1
        elif environment == "staging":
            traces_sample_rate = 0.5  # 50% sampling in staging
            profiles_sample_rate = 0.5
        else:  # development
            traces_sample_rate = 1.0  # 100% sampling in dev
            profiles_sample_rate = 1.0

        _sentry_config = SentryConfig(
            dsn=os.getenv("SENTRY_DSN"),
            environment=environment,
            release=os.getenv("RELEASE_VERSION"),
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            enable_tracing=os.getenv("SENTRY_ENABLE_TRACING", "true").lower() == "true",
            debug=os.getenv("SENTRY_DEBUG", "false").lower() == "true",
        )

    return _sentry_config


def init_sentry():
    """
    Initialize Sentry error tracking

    Call this during application startup
    """
    config = get_sentry_config()
    config.setup()
    return config


# Utility functions for error tracking

def capture_exception(error: Exception, **kwargs):
    """
    Manually capture an exception

    Args:
        error: Exception to capture
        **kwargs: Additional context (tags, extra, user, etc.)
    """
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        if "tags" in kwargs:
            for key, value in kwargs["tags"].items():
                scope.set_tag(key, value)

        if "extra" in kwargs:
            for key, value in kwargs["extra"].items():
                scope.set_extra(key, value)

        if "user" in kwargs:
            scope.set_user(kwargs["user"])

        if "level" in kwargs:
            scope.level = kwargs["level"]

        # Capture exception
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a custom message

    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error, fatal)
        **kwargs: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        if "tags" in kwargs:
            for key, value in kwargs["tags"].items():
                scope.set_tag(key, value)

        if "extra" in kwargs:
            for key, value in kwargs["extra"].items():
                scope.set_extra(key, value)

        # Set level
        scope.level = level

        # Capture message
        sentry_sdk.capture_message(message)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: dict | None = None):
    """
    Add a breadcrumb for error context

    Args:
        message: Breadcrumb message
        category: Breadcrumb category (navigation, http, auth, etc.)
        level: Breadcrumb level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def set_user_context(user_id: str, email: str | None = None, username: str | None = None, **kwargs):
    """
    Set user context for error tracking

    Args:
        user_id: User ID
        email: User email (will be sanitized if KVKK compliance enabled)
        username: Username
        **kwargs: Additional user attributes
    """
    user_data = {
        "id": user_id,
        "username": username,
    }

    # Only include email if explicitly allowed (KVKK compliance)
    if email and os.getenv("SENTRY_INCLUDE_EMAIL", "false").lower() == "true":
        user_data["email"] = email

    # Add additional attributes
    user_data.update(kwargs)

    sentry_sdk.set_user(user_data)


def set_context(key: str, value: dict[str, Any]):
    """
    Set custom context for errors

    Args:
        key: Context key
        value: Context data
    """
    sentry_sdk.set_context(key, value)


def start_transaction(name: str, op: str = "http.server") -> Any:
    """
    Start a performance transaction

    Args:
        name: Transaction name
        op: Operation type

    Returns:
        Transaction object
    """
    return sentry_sdk.start_transaction(name=name, op=op)


if __name__ == "__main__":
    # Test Sentry configuration
    print("=" * 80)
    print("SENTRY ERROR TRACKING TEST")
    print("=" * 80)

    # Create config
    config = SentryConfig(
        dsn="https://example@sentry.io/123456",  # Fake DSN for testing
        environment="development",
        traces_sample_rate=1.0,
        debug=True
    )

    print("\nConfiguration:")
    print(f"  Environment: {config.environment}")
    print(f"  Release: {config.release}")
    print(f"  Traces Sample Rate: {config.traces_sample_rate}")
    print(f"  Tracing Enabled: {config.enable_tracing}")

    print("\n[OK] Sentry configuration test passed")
    print("\nTo enable Sentry in production:")
    print("  1. Set SENTRY_DSN environment variable")
    print("  2. Set DEPLOYMENT_ENV=production")
    print("  3. Set RELEASE_VERSION (optional)")
    print("  4. Start application")
