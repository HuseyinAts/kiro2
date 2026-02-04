"""
Configuration Validation System
Comprehensive validation for unified configuration
"""

import logging
import os
import re
import socket
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .unified_config import Environment, UnifiedConfig

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Configuration validation issue"""

    field: str
    message: str
    severity: ValidationSeverity
    current_value: Any = None
    suggested_value: Any = None
    fix_suggestion: str = ""


class ConfigValidator:
    """
    Comprehensive configuration validator
    """

    def __init__(self):
        self.issues: list[ValidationIssue] = []
        self.validators: dict[str, Callable] = {}
        self._register_default_validators()

    def _register_default_validators(self):
        """Register default validation functions"""
        self.validators.update(
            {
                "database_url": self._validate_database_url,
                "redis_url": self._validate_redis_url,
                "elasticsearch_url": self._validate_elasticsearch_url,
                "secret_key": self._validate_secret_key,
                "ports": self._validate_ports,
                "api_keys": self._validate_api_keys,
                "file_paths": self._validate_file_paths,
                "network_connectivity": self._validate_network_connectivity,
                "environment_consistency": self._validate_environment_consistency,
                "security_settings": self._validate_security_settings,
                "performance_settings": self._validate_performance_settings,
                "turkish_support": self._validate_turkish_support,
            }
        )

    def validate_configuration(self, config: UnifiedConfig) -> list[ValidationIssue]:
        """Validate entire configuration and return issues"""
        self.issues.clear()

        # Run all validators
        for validator_name, validator_func in self.validators.items():
            try:
                validator_func(config)
            except Exception as e:
                self._add_issue(
                    field=f"validator.{validator_name}",
                    message=f"Validator failed: {e!s}",
                    severity=ValidationSeverity.ERROR,
                )

        # Sort issues by severity
        severity_order = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 1,
            ValidationSeverity.WARNING: 2,
            ValidationSeverity.INFO: 3,
        }

        self.issues.sort(key=lambda x: severity_order[x.severity])
        return self.issues

    def _add_issue(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity,
        current_value: Any = None,
        suggested_value: Any = None,
        fix_suggestion: str = "",
    ):
        """Add validation issue"""
        issue = ValidationIssue(
            field=field,
            message=message,
            severity=severity,
            current_value=current_value,
            suggested_value=suggested_value,
            fix_suggestion=fix_suggestion,
        )
        self.issues.append(issue)

    def _validate_database_url(self, config: UnifiedConfig):
        """Validate database configuration"""
        db_url = config.database.url

        if not db_url:
            self._add_issue(
                field="database.url",
                message="Database URL is not configured",
                severity=ValidationSeverity.CRITICAL,
                fix_suggestion="Set DATABASE_URL environment variable",
            )
            return

        # Parse URL
        try:
            parsed = urlparse(db_url)
        except Exception:
            self._add_issue(
                field="database.url",
                message="Invalid database URL format",
                severity=ValidationSeverity.CRITICAL,
                current_value=db_url,
            )
            return

        # Check scheme
        valid_schemes = [
            "postgresql",
            "postgresql+asyncpg",
            "sqlite",
            "sqlite+aiosqlite",
            "mysql+aiomysql",
        ]
        if parsed.scheme not in valid_schemes:
            self._add_issue(
                field="database.url",
                message=f"Unsupported database scheme: {parsed.scheme}",
                severity=ValidationSeverity.ERROR,
                current_value=parsed.scheme,
                suggested_value="postgresql+asyncpg",
            )

        # SQLite-specific checks
        if parsed.scheme.startswith("sqlite"):
            if db_url == "sqlite+aiosqlite:///:memory:":
                if config.environment == Environment.PRODUCTION:
                    self._add_issue(
                        field="database.url",
                        message="In-memory database should not be used in production",
                        severity=ValidationSeverity.CRITICAL,
                        current_value="in-memory",
                        fix_suggestion="Use persistent database for production",
                    )
            else:
                # Check if file path exists for file-based SQLite
                db_path = db_url.replace("sqlite+aiosqlite:///", "")
                if db_path != ":memory:" and not Path(db_path).parent.exists():
                    self._add_issue(
                        field="database.url",
                        message=f"Database directory does not exist: {Path(db_path).parent}",
                        severity=ValidationSeverity.WARNING,
                        fix_suggestion="Create database directory or use existing path",
                    )

        # PostgreSQL-specific checks
        if parsed.scheme.startswith("postgresql"):
            if not parsed.hostname:
                self._add_issue(
                    field="database.url",
                    message="PostgreSQL hostname is missing",
                    severity=ValidationSeverity.ERROR,
                )

            if not parsed.username:
                self._add_issue(
                    field="database.url",
                    message="PostgreSQL username is missing",
                    severity=ValidationSeverity.ERROR,
                )

        # Connection pool validation
        if config.database.pool_size < 5:
            self._add_issue(
                field="database.pool_size",
                message="Database pool size is very low",
                severity=ValidationSeverity.WARNING,
                current_value=config.database.pool_size,
                suggested_value=20,
            )

        if config.database.pool_size > 100:
            self._add_issue(
                field="database.pool_size",
                message="Database pool size is very high",
                severity=ValidationSeverity.WARNING,
                current_value=config.database.pool_size,
                suggested_value=50,
            )

    def _validate_redis_url(self, config: UnifiedConfig):
        """Validate Redis configuration"""
        redis_url = config.redis.url

        if not redis_url.startswith("redis://"):
            self._add_issue(
                field="redis.url",
                message="Redis URL must start with redis://",
                severity=ValidationSeverity.ERROR,
                current_value=redis_url,
            )

        # Parse Redis URL
        try:
            parsed = urlparse(redis_url)

            # Check hostname
            if not parsed.hostname:
                self._add_issue(
                    field="redis.url",
                    message="Redis hostname is missing",
                    severity=ValidationSeverity.ERROR,
                )

            # Check port
            port = parsed.port or 6379
            if not (1 <= port <= 65535):
                self._add_issue(
                    field="redis.url",
                    message=f"Invalid Redis port: {port}",
                    severity=ValidationSeverity.ERROR,
                )

        except Exception as e:
            self._add_issue(
                field="redis.url",
                message=f"Invalid Redis URL: {e!s}",
                severity=ValidationSeverity.ERROR,
            )

        # Connection pool validation
        if config.redis.max_connections < 10:
            self._add_issue(
                field="redis.max_connections",
                message="Redis connection pool is very low",
                severity=ValidationSeverity.WARNING,
                current_value=config.redis.max_connections,
                suggested_value=50,
            )

    def _validate_elasticsearch_url(self, config: UnifiedConfig):
        """Validate Elasticsearch configuration"""
        es_url = config.elasticsearch.url

        if not es_url:
            self._add_issue(
                field="elasticsearch.url",
                message="Elasticsearch URL is not configured",
                severity=ValidationSeverity.WARNING,
                fix_suggestion="Set ELASTICSEARCH_URL if using Elasticsearch features",
            )
            return

        # Parse URL
        try:
            parsed = urlparse(es_url)

            if parsed.scheme not in ["http", "https"]:
                self._add_issue(
                    field="elasticsearch.url",
                    message="Elasticsearch URL must use http or https",
                    severity=ValidationSeverity.ERROR,
                    current_value=parsed.scheme,
                )

            if config.environment == Environment.PRODUCTION and parsed.scheme == "http":
                self._add_issue(
                    field="elasticsearch.url",
                    message="Use HTTPS for Elasticsearch in production",
                    severity=ValidationSeverity.WARNING,
                    current_value="http",
                    suggested_value="https",
                )

        except Exception:
            self._add_issue(
                field="elasticsearch.url",
                message="Invalid Elasticsearch URL format",
                severity=ValidationSeverity.ERROR,
            )

        # Index name validation
        index_name = config.elasticsearch.index
        if not re.match(r"^[a-z0-9_-]+$", index_name):
            self._add_issue(
                field="elasticsearch.index",
                message="Invalid Elasticsearch index name",
                severity=ValidationSeverity.ERROR,
                current_value=index_name,
                fix_suggestion="Use lowercase letters, numbers, hyphens, and underscores only",
            )

    def _validate_secret_key(self, config: UnifiedConfig):
        """Validate security secret key"""
        secret_key = config.security.secret_key

        if not secret_key:
            self._add_issue(
                field="security.secret_key",
                message="Secret key is not configured",
                severity=ValidationSeverity.CRITICAL,
                fix_suggestion="Set SECRET_KEY environment variable",
            )
            return

        if len(secret_key) < 32:
            self._add_issue(
                field="security.secret_key",
                message="Secret key is too short",
                severity=ValidationSeverity.CRITICAL,
                current_value=f"{len(secret_key)} characters",
                suggested_value="At least 32 characters",
                fix_suggestion="Generate a longer, more secure secret key",
            )

        # Check for default values
        default_keys = [
            "your-secret-key-change-in-production",
            "dev-secret-key-not-for-production-use",
            "test-secret-key-for-testing-only",
        ]

        if secret_key in default_keys:
            severity = (
                ValidationSeverity.CRITICAL
                if config.environment == Environment.PRODUCTION
                else ValidationSeverity.WARNING
            )
            self._add_issue(
                field="security.secret_key",
                message="Using default secret key",
                severity=severity,
                fix_suggestion="Generate a unique, secure secret key",
            )

        # Check complexity
        has_upper = any(c.isupper() for c in secret_key)
        has_lower = any(c.islower() for c in secret_key)
        has_digit = any(c.isdigit() for c in secret_key)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret_key)

        complexity_score = sum([has_upper, has_lower, has_digit, has_special])

        if complexity_score < 3:
            self._add_issue(
                field="security.secret_key",
                message="Secret key lacks complexity",
                severity=ValidationSeverity.WARNING,
                fix_suggestion="Use a mix of uppercase, lowercase, digits, and special characters",
            )

    def _validate_ports(self, config: UnifiedConfig):
        """Validate port configurations"""
        ports_to_check = [
            ("server.port", config.server.port),
            ("monitoring.metrics_port", config.monitoring.metrics_port),
        ]

        used_ports = []

        for field, port in ports_to_check:
            if not (1 <= port <= 65535):
                self._add_issue(
                    field=field,
                    message=f"Invalid port number: {port}",
                    severity=ValidationSeverity.ERROR,
                    current_value=port,
                )

            if port in used_ports:
                self._add_issue(
                    field=field,
                    message=f"Port {port} is used by multiple services",
                    severity=ValidationSeverity.ERROR,
                    current_value=port,
                )

            used_ports.append(port)

            # Check if port is in reserved range
            if port < 1024 and os.getuid() != 0 if hasattr(os, "getuid") else False:
                self._add_issue(
                    field=field,
                    message=f"Port {port} requires root privileges",
                    severity=ValidationSeverity.WARNING,
                    fix_suggestion="Use port > 1024 or run with appropriate privileges",
                )

    def _validate_api_keys(self, config: UnifiedConfig):
        """Validate external API keys"""
        api_keys = {
            "external_apis.openai_api_key": config.external_apis.openai_api_key,
            "external_apis.youtube_api_key": config.external_apis.youtube_api_key,
            "external_apis.huggingface_api_key": config.external_apis.huggingface_api_key,
            "external_apis.google_api_key": config.external_apis.google_api_key,
        }

        for field, key in api_keys.items():
            if not key:
                severity = (
                    ValidationSeverity.WARNING
                    if config.environment != Environment.PRODUCTION
                    else ValidationSeverity.ERROR
                )
                self._add_issue(
                    field=field,
                    message="API key is not configured",
                    severity=severity,
                    fix_suggestion=f"Set {field.upper().replace('.', '_')} environment variable",
                )
                continue

            # Check for test/placeholder keys
            if key.startswith(("test-", "sk-test", "demo-")):
                severity = (
                    ValidationSeverity.CRITICAL
                    if config.environment == Environment.PRODUCTION
                    else ValidationSeverity.INFO
                )
                self._add_issue(
                    field=field,
                    message="Using test/placeholder API key",
                    severity=severity,
                    current_value="test key",
                    fix_suggestion="Replace with production API key",
                )

            # Check key length (basic validation)
            if len(key) < 10:
                self._add_issue(
                    field=field,
                    message="API key seems too short",
                    severity=ValidationSeverity.WARNING,
                    current_value=f"{len(key)} characters",
                )

    def _validate_file_paths(self, config: UnifiedConfig):
        """Validate file paths and directories"""
        # Check database file path for SQLite
        if config.database.url.startswith("sqlite"):
            db_path = config.database.url.replace("sqlite+aiosqlite:///", "")
            if db_path != ":memory:":
                db_dir = Path(db_path).parent
                if not db_dir.exists():
                    self._add_issue(
                        field="database.url",
                        message=f"Database directory does not exist: {db_dir}",
                        severity=ValidationSeverity.ERROR,
                        fix_suggestion=f"Create directory: mkdir -p {db_dir}",
                    )
                elif not os.access(db_dir, os.W_OK):
                    self._add_issue(
                        field="database.url",
                        message=f"Database directory is not writable: {db_dir}",
                        severity=ValidationSeverity.ERROR,
                        fix_suggestion="Check directory permissions",
                    )

    def _validate_network_connectivity(self, config: UnifiedConfig):
        """Validate network connectivity to external services"""
        # This is a basic check - in production, you might want more sophisticated checks
        services_to_check = []

        # Redis connectivity
        if config.redis.url:
            try:
                parsed = urlparse(config.redis.url)
                hostname = parsed.hostname or "localhost"
                port = parsed.port or 6379
                services_to_check.append(("Redis", hostname, port))
            except Exception:
                pass

        # Elasticsearch connectivity
        if config.elasticsearch.url:
            try:
                parsed = urlparse(config.elasticsearch.url)
                hostname = parsed.hostname or "localhost"
                port = parsed.port or 9200
                services_to_check.append(("Elasticsearch", hostname, port))
            except Exception:
                pass

        # Check connectivity
        for service_name, hostname, port in services_to_check:
            try:
                with socket.create_connection((hostname, port), timeout=5):
                    pass  # Connection successful
            except (TimeoutError, OSError):
                severity = (
                    ValidationSeverity.WARNING
                    if config.environment != Environment.PRODUCTION
                    else ValidationSeverity.ERROR
                )
                self._add_issue(
                    field=f"network.{service_name.lower()}",
                    message=f"Cannot connect to {service_name} at {hostname}:{port}",
                    severity=severity,
                    fix_suggestion=f"Ensure {service_name} is running and accessible",
                )
            except Exception as e:
                self._add_issue(
                    field=f"network.{service_name.lower()}",
                    message=f"Network check failed for {service_name}: {e!s}",
                    severity=ValidationSeverity.INFO,
                )

    def _validate_environment_consistency(self, config: UnifiedConfig):
        """Validate environment-specific consistency"""
        env = config.environment

        # Production-specific validations
        if env == Environment.PRODUCTION:
            if config.debug:
                self._add_issue(
                    field="debug",
                    message="Debug mode is enabled in production",
                    severity=ValidationSeverity.CRITICAL,
                    current_value=True,
                    suggested_value=False,
                    fix_suggestion="Set DEBUG=false for production",
                )

            if config.enable_swagger:
                self._add_issue(
                    field="enable_swagger",
                    message="Swagger documentation is enabled in production",
                    severity=ValidationSeverity.WARNING,
                    fix_suggestion="Disable Swagger in production for security",
                )

            if not config.enable_rate_limiting:
                self._add_issue(
                    field="enable_rate_limiting",
                    message="Rate limiting is disabled in production",
                    severity=ValidationSeverity.WARNING,
                    fix_suggestion="Enable rate limiting for production",
                )

        # Development-specific validations
        if env == Environment.DEVELOPMENT:
            if not config.debug:
                self._add_issue(
                    field="debug",
                    message="Debug mode is disabled in development",
                    severity=ValidationSeverity.INFO,
                    fix_suggestion="Consider enabling debug mode for development",
                )

        # Testing-specific validations
        if env == Environment.TESTING:
            if not config.database.url.endswith(":memory:"):
                self._add_issue(
                    field="database.url",
                    message="Consider using in-memory database for testing",
                    severity=ValidationSeverity.INFO,
                    fix_suggestion="Use sqlite+aiosqlite:///:memory: for faster tests",
                )

    def _validate_security_settings(self, config: UnifiedConfig):
        """Validate security-related settings"""
        # Token expiry validation
        if config.security.access_token_expire_minutes > 120:
            self._add_issue(
                field="security.access_token_expire_minutes",
                message="Access token expiry time is very long",
                severity=ValidationSeverity.WARNING,
                current_value=config.security.access_token_expire_minutes,
                suggested_value=30,
            )

        if config.security.access_token_expire_minutes < 5:
            self._add_issue(
                field="security.access_token_expire_minutes",
                message="Access token expiry time is very short",
                severity=ValidationSeverity.WARNING,
                current_value=config.security.access_token_expire_minutes,
                suggested_value=30,
            )

        # Password policy validation
        if config.security.password_min_length < 8:
            self._add_issue(
                field="security.password_min_length",
                message="Minimum password length is too short",
                severity=ValidationSeverity.WARNING,
                current_value=config.security.password_min_length,
                suggested_value=8,
                fix_suggestion="Increase minimum password length for better security",
            )

        # CORS validation
        if (
            "*" in config.server.allowed_origins
            and config.environment == Environment.PRODUCTION
        ):
            self._add_issue(
                field="server.allowed_origins",
                message="Wildcard CORS origin in production",
                severity=ValidationSeverity.ERROR,
                current_value="*",
                fix_suggestion="Specify exact allowed origins for production",
            )

    def _validate_performance_settings(self, config: UnifiedConfig):
        """Validate performance-related settings"""
        # Worker count validation
        if config.server.workers > 8:
            self._add_issue(
                field="server.workers",
                message="Very high worker count may cause resource issues",
                severity=ValidationSeverity.WARNING,
                current_value=config.server.workers,
                suggested_value="2-4 workers per CPU core",
            )

        # Request size validation
        max_size_mb = config.server.max_request_size / (1024 * 1024)
        if max_size_mb > 50:
            self._add_issue(
                field="server.max_request_size",
                message="Very large maximum request size",
                severity=ValidationSeverity.WARNING,
                current_value=f"{max_size_mb:.1f}MB",
                fix_suggestion="Consider if large uploads are necessary",
            )

        # API timeout validation
        if config.external_apis.api_timeout > 120:
            self._add_issue(
                field="external_apis.api_timeout",
                message="Very long API timeout",
                severity=ValidationSeverity.WARNING,
                current_value=config.external_apis.api_timeout,
                suggested_value=30,
            )

    def _validate_turkish_support(self, config: UnifiedConfig):
        """Validate Turkish language support settings"""
        # Encoding validation
        if config.encoding.lower() != "utf-8":
            self._add_issue(
                field="encoding",
                message="Encoding should be UTF-8 for Turkish character support",
                severity=ValidationSeverity.WARNING,
                current_value=config.encoding,
                suggested_value="utf-8",
            )

        # Locale validation
        if not config.locale.startswith("tr_TR"):
            self._add_issue(
                field="locale",
                message="Locale should be set for Turkish language support",
                severity=ValidationSeverity.INFO,
                current_value=config.locale,
                suggested_value="tr_TR.UTF-8",
            )

        # Timezone validation
        if config.timezone != "Europe/Istanbul":
            self._add_issue(
                field="timezone",
                message="Consider using Istanbul timezone for Turkish users",
                severity=ValidationSeverity.INFO,
                current_value=config.timezone,
                suggested_value="Europe/Istanbul",
            )

    def get_validation_summary(self) -> dict[str, Any]:
        """Get validation summary statistics"""
        if not self.issues:
            return {"total_issues": 0, "by_severity": {}, "status": "valid"}

        severity_counts = {}
        for issue in self.issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        has_critical = ValidationSeverity.CRITICAL.value in severity_counts
        has_errors = ValidationSeverity.ERROR.value in severity_counts

        if has_critical:
            status = "critical_issues"
        elif has_errors:
            status = "has_errors"
        else:
            status = "warnings_only"

        return {
            "total_issues": len(self.issues),
            "by_severity": severity_counts,
            "status": status,
            "top_issues": [
                {
                    "field": issue.field,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in self.issues[:5]  # Top 5 issues
            ],
        }


def validate_configuration(
    config: UnifiedConfig,
) -> tuple[list[ValidationIssue], dict[str, Any]]:
    """
    Validate configuration and return issues and summary
    """
    validator = ConfigValidator()
    issues = validator.validate_configuration(config)
    summary = validator.get_validation_summary()

    return issues, summary


def print_validation_report(
    issues: list[ValidationIssue], summary: dict[str, Any]
) -> None:
    """
    Print formatted validation report
    """
    print(f"\n{'='*60}")
    print("CONFIGURATION VALIDATION REPORT")
    print(f"{'='*60}")

    print(f"Status: {summary['status'].replace('_', ' ').title()}")
    print(f"Total Issues: {summary['total_issues']}")

    if summary["by_severity"]:
        print("\nIssues by Severity:")
        for severity, count in summary["by_severity"].items():
            print(f"  {severity.title()}: {count}")

    if issues:
        print(f"\n{'─'*60}")
        print("DETAILED ISSUES")
        print(f"{'─'*60}")

        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue.severity.value.upper()}] {issue.field}")
            print(f"   {issue.message}")

            if issue.current_value is not None:
                print(f"   Current: {issue.current_value}")

            if issue.suggested_value is not None:
                print(f"   Suggested: {issue.suggested_value}")

            if issue.fix_suggestion:
                print(f"   Fix: {issue.fix_suggestion}")
    else:
        print("\n[CHECK] Configuration validation passed - no issues found!")

    print(f"\n{'='*60}")
