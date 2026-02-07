"""
Startup Configuration Validator
Prevents application startup with invalid production configuration

This module is automatically called on application startup to validate
all critical configuration before accepting requests.
"""

import os
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Raised when startup validation fails"""

    pass


class StartupValidator:
    """Validates configuration on application startup"""

    CRITICAL_VARS = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "DATABASE_URL",
        "ENVIRONMENT",
    ]

    PRODUCTION_ONLY_VARS = [
        "SENTRY_DSN",  # Error tracking required in production
        "CORS_ORIGINS",  # CORS must be explicitly configured
    ]

    def __init__(self, strict_mode: bool = None):
        """
        Initialize validator

        Args:
            strict_mode: If True, enforce all validations strictly.
                        If None, determined by ENVIRONMENT variable.
        """
        env = os.getenv("ENVIRONMENT", "development")
        self.strict_mode = (
            strict_mode if strict_mode is not None else (env == "production")
        )
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Core validations
        self._validate_critical_vars()
        self._validate_secrets()
        self._validate_database()
        self._validate_environment()

        # Production-specific validations
        if self.strict_mode:
            self._validate_production_requirements()
            self._validate_security_settings()
            self._validate_cors()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_critical_vars(self):
        """Validate critical environment variables are set"""
        for var in self.CRITICAL_VARS:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing critical variable: {var}")
            elif value.startswith("<") and value.endswith(">"):
                self.errors.append(f"{var} contains placeholder value: {value}")

    def _validate_secrets(self):
        """Validate secret keys meet security requirements"""
        secret_key = os.getenv("SECRET_KEY", "")
        jwt_key = os.getenv("JWT_SECRET_KEY", "")

        # Check minimum length
        if len(secret_key) < 32:
            self.errors.append(
                f"SECRET_KEY too short: {len(secret_key)} chars (minimum 32)"
            )

        if len(jwt_key) < 32:
            self.errors.append(
                f"JWT_SECRET_KEY too short: {len(jwt_key)} chars (minimum 32)"
            )

        # Check for common insecure values
        insecure_values = ["secret", "password", "123456", "changeme", "default"]
        if any(insecure in secret_key.lower() for insecure in insecure_values):
            self.errors.append("SECRET_KEY appears to be insecure")

        if any(insecure in jwt_key.lower() for insecure in insecure_values):
            self.errors.append("JWT_SECRET_KEY appears to be insecure")

    def _validate_database(self):
        """Validate database configuration"""
        db_url = os.getenv("DATABASE_URL", "")

        if not db_url:
            self.errors.append("DATABASE_URL not set")
            return

        # Check for PostgreSQL async driver
        if not db_url.startswith("postgresql+asyncpg://"):
            self.warnings.append(
                f"DATABASE_URL should use asyncpg driver: {db_url[:30]}..."
            )

        # Warn if using default database
        if "localhost" in db_url and self.strict_mode:
            self.warnings.append("Using localhost database in production mode")

    def _validate_environment(self):
        """Validate ENVIRONMENT setting"""
        env = os.getenv("ENVIRONMENT", "")

        if not env:
            self.errors.append("ENVIRONMENT not set")
            return

        valid_envs = ["development", "staging", "production"]
        if env not in valid_envs:
            self.errors.append(
                f"Invalid ENVIRONMENT: {env} (must be one of {valid_envs})"
            )

        # Check DEBUG is disabled in production
        if env == "production":
            debug = os.getenv("DEBUG", "false").lower()
            if debug not in ["false", "0", "no"]:
                self.errors.append("DEBUG must be false in production")

    def _validate_production_requirements(self):
        """Validate production-only requirements"""
        for var in self.PRODUCTION_ONLY_VARS:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Production variable not set: {var}")

        # Check monitoring is configured
        if not os.getenv("SENTRY_DSN"):
            self.warnings.append("SENTRY_DSN not configured - error tracking disabled")

        # Check email is configured
        if not os.getenv("SMTP_HOST"):
            self.warnings.append("SMTP not configured - email notifications disabled")

    def _validate_security_settings(self):
        """Validate security-related settings"""
        # Check session cookie security
        if os.getenv("SESSION_COOKIE_SECURE", "true").lower() != "true":
            self.errors.append("SESSION_COOKIE_SECURE must be true in production")

        # Check rate limiting is configured
        if not os.getenv("RATE_LIMIT_PER_MINUTE"):
            self.warnings.append("Rate limiting not configured")

        # Check KVKK compliance is enabled
        if os.getenv("KVKK_ENABLED", "false").lower() != "true":
            self.warnings.append("KVKK compliance not enabled (required in Turkey)")

    def _validate_cors(self):
        """Validate CORS configuration"""
        cors_origins = os.getenv("CORS_ORIGINS", "")

        if not cors_origins:
            self.errors.append("CORS_ORIGINS not set")
            return

        # Check for wildcard in production
        if "*" in cors_origins:
            self.errors.append("CORS_ORIGINS cannot use wildcard (*) in production")

        # Check for HTTPS
        if cors_origins and not cors_origins.startswith("https://"):
            self.errors.append("CORS_ORIGINS must use HTTPS in production")


def validate_startup_config(strict_mode: bool = None) -> None:
    """
    Validate configuration on startup

    Args:
        strict_mode: If True, enforce strict validation.
                    If None, determined by ENVIRONMENT.

    Raises:
        StartupValidationError: If validation fails in strict mode
    """
    validator = StartupValidator(strict_mode=strict_mode)
    is_valid, errors, warnings = validator.validate_all()

    # Log results
    if warnings:
        logger.warning("Configuration warnings detected:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    if errors:
        logger.error("Configuration errors detected:")
        for error in errors:
            logger.error(f"  - {error}")

    # In strict mode, prevent startup if errors exist
    if validator.strict_mode and not is_valid:
        error_msg = f"Startup validation failed with {len(errors)} error(s)"
        logger.critical(error_msg)
        raise StartupValidationError(error_msg)

    # Log success
    if is_valid:
        mode = "strict" if validator.strict_mode else "relaxed"
        logger.info(f"✓ Startup validation passed ({mode} mode)")
        if warnings:
            logger.info(f"  Note: {len(warnings)} warning(s) detected")


# Auto-validate on import in production
if __name__ != "__main__":
    try:
        # Only auto-validate if ENVIRONMENT is production
        if os.getenv("ENVIRONMENT") == "production":
            validate_startup_config(strict_mode=True)
    except StartupValidationError:
        # Re-raise to prevent startup
        raise
    except Exception as e:
        # Log but don't prevent startup for unexpected errors
        logger.error(f"Startup validation encountered unexpected error: {e}")
