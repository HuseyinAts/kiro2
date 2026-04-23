"""
Sensitive Data Logging Filter
SECURITY FIX: Redact sensitive information from logs
"""

import logging
import re
from re import Pattern
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter to redact sensitive data from log messages

    Automatically redacts:
    - Passwords
    - API keys
    - Tokens (JWT, Bearer, etc.)
    - Secret keys
    - Credit card numbers
    - Email addresses (optional)
    - Phone numbers (optional)
    """

    def __init__(
        self,
        redact_email: bool = False,
        redact_phone: bool = False,
        custom_patterns: list[Pattern] = None,
    ):
        super().__init__()
        self.redact_email = redact_email
        self.redact_phone = redact_phone
        self.custom_patterns = custom_patterns or []

        # Compile regex patterns for performance
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for sensitive data detection"""

        # Password patterns
        self.password_patterns = [
            (
                re.compile(r'password["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "password=***REDACTED***",
            ),
            (
                re.compile(r'passwd["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "passwd=***REDACTED***",
            ),
            (
                re.compile(r'pwd["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "pwd=***REDACTED***",
            ),
            (
                re.compile(r'sifre["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "sifre=***REDACTED***",
            ),
        ]

        # API key patterns
        self.api_key_patterns = [
            (
                re.compile(r'api[_\s-]?key["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "api_key=***REDACTED***",
            ),
            (
                re.compile(r'apikey["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "apikey=***REDACTED***",
            ),
            (
                re.compile(r'api[_\s-]?secret["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "api_secret=***REDACTED***",
            ),
        ]

        # Token patterns
        self.token_patterns = [
            (
                re.compile(r'token["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "token=***REDACTED***",
            ),
            (
                re.compile(r"bearer\s+([A-Za-z0-9\-._~+/]+=*)", re.IGNORECASE),
                "bearer ***REDACTED***",
            ),
            (
                re.compile(r'jwt["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "jwt=***REDACTED***",
            ),
            (
                re.compile(r'access[_\s-]?token["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "access_token=***REDACTED***",
            ),
            (
                re.compile(r'refresh[_\s-]?token["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "refresh_token=***REDACTED***",
            ),
        ]

        # Secret key patterns
        self.secret_patterns = [
            (
                re.compile(r'secret["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "secret=***REDACTED***",
            ),
            (
                re.compile(r'secret[_\s-]?key["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "secret_key=***REDACTED***",
            ),
            (
                re.compile(r'private[_\s-]?key["\s:=]+([^\s,}"]+)', re.IGNORECASE),
                "private_key=***REDACTED***",
            ),
        ]

        # Credit card pattern (Luhn algorithm not validated, just format)
        self.credit_card_pattern = (
            re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
            "****-****-****-REDACTED",
        )

        # Email pattern (optional)
        if self.redact_email:
            self.email_pattern = (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "***@***.***",
            )
        else:
            self.email_pattern = None

        # Phone pattern (optional, Turkish format)
        if self.redact_phone:
            self.phone_pattern = (
                re.compile(r"\b0?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b"),
                "***-***-**-**",
            )
        else:
            self.phone_pattern = None

    def _redact_message(self, message: str) -> str:
        """Redact sensitive data from message"""

        # Redact passwords
        for pattern, replacement in self.password_patterns:
            message = pattern.sub(replacement, message)

        # Redact API keys
        for pattern, replacement in self.api_key_patterns:
            message = pattern.sub(replacement, message)

        # Redact tokens
        for pattern, replacement in self.token_patterns:
            message = pattern.sub(replacement, message)

        # Redact secrets
        for pattern, replacement in self.secret_patterns:
            message = pattern.sub(replacement, message)

        # Redact credit cards
        message = self.credit_card_pattern[0].sub(self.credit_card_pattern[1], message)

        # Redact email (if enabled)
        if self.email_pattern:
            message = self.email_pattern[0].sub(self.email_pattern[1], message)

        # Redact phone (if enabled)
        if self.phone_pattern:
            message = self.phone_pattern[0].sub(self.phone_pattern[1], message)

        # Apply custom patterns
        for pattern in self.custom_patterns:
            if isinstance(pattern, tuple):
                regex, replacement = pattern
                message = regex.sub(replacement, message)
            else:
                # Assume Pattern object, use default replacement
                message = pattern.sub("***REDACTED***", message)

        return message

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive data from dictionary"""
        redacted = {}

        sensitive_keys = {
            "password",
            "passwd",
            "pwd",
            "sifre",
            "api_key",
            "apikey",
            "api_secret",
            "token",
            "access_token",
            "refresh_token",
            "jwt",
            "secret",
            "secret_key",
            "private_key",
            "authorization",
            "auth",
        }

        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, str):
                redacted[key] = self._redact_message(value)
            else:
                redacted[key] = value

        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to redact sensitive data

        Args:
            record: Log record to filter

        Returns:
            True (always pass the record, just redacted)
        """
        # Redact message
        if isinstance(record.msg, str):
            record.msg = self._redact_message(record.msg)

        # Redact args
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self._redact_message(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        # Redact extra fields
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            record.extra_data = self._redact_dict(record.extra_data)

        return True


def setup_sensitive_data_filter(
    logger: logging.Logger = None,
    redact_email: bool = False,
    redact_phone: bool = False,
    custom_patterns: list[Pattern] = None,
) -> SensitiveDataFilter:
    """
    Setup sensitive data filter for logger

    Args:
        logger: Logger to add filter to (default: root logger)
        redact_email: Whether to redact email addresses
        redact_phone: Whether to redact phone numbers
        custom_patterns: Custom regex patterns to redact

    Returns:
        SensitiveDataFilter instance

    Example:
        >>> import logging
        >>> from core.sensitive_data_filter import setup_sensitive_data_filter
        >>> logger = logging.getLogger(__name__)
        >>> setup_sensitive_data_filter(logger)
        >>> logger.info("User password: secret123")  # Logs: "User password=***REDACTED***"
    """
    if logger is None:
        logger = logging.getLogger()

    sensitive_filter = SensitiveDataFilter(
        redact_email=redact_email,
        redact_phone=redact_phone,
        custom_patterns=custom_patterns,
    )

    logger.addFilter(sensitive_filter)
    return sensitive_filter


def setup_global_sensitive_data_filter(
    redact_email: bool = False,
    redact_phone: bool = False,
    custom_patterns: list[Pattern] = None,
):
    """
    Setup sensitive data filter for ALL loggers globally

    Args:
        redact_email: Whether to redact email addresses
        redact_phone: Whether to redact phone numbers
        custom_patterns: Custom regex patterns to redact

    Example:
        >>> from core.sensitive_data_filter import setup_global_sensitive_data_filter
        >>> setup_global_sensitive_data_filter()
    """
    # Add filter to root logger (affects all loggers)
    root_logger = logging.getLogger()
    setup_sensitive_data_filter(
        root_logger,
        redact_email=redact_email,
        redact_phone=redact_phone,
        custom_patterns=custom_patterns,
    )

    # Also add to common loggers
    common_loggers = ["uvicorn", "fastapi", "sqlalchemy", "asyncio"]
    for logger_name in common_loggers:
        logger = logging.getLogger(logger_name)
        setup_sensitive_data_filter(
            logger,
            redact_email=redact_email,
            redact_phone=redact_phone,
            custom_patterns=custom_patterns,
        )
