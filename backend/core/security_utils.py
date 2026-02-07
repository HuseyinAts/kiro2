"""
Security Utilities - XSS & SQL Injection Protection
Comprehensive security utilities for input sanitization and validation

Features:
- XSS protection with bleach
- SQL Injection detection and prevention
- HTML sanitization
- Path traversal protection
- Command injection prevention
- LDAP injection protection
"""
import html
import re
import unicodedata
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import bleach
from fastapi import HTTPException, status

# ==================== CONFIGURATION ====================

# Allowed HTML tags for rich text (very restrictive)
ALLOWED_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "ol",
    "ul",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "blockquote",
    "code",
    "pre",
]

# Allowed HTML attributes
ALLOWED_HTML_ATTRIBUTES = {"a": ["href", "title"], "code": ["class"], "pre": ["class"]}

# Allowed URL protocols
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# ==================== XSS PROTECTION ====================


class XSSProtection:
    """XSS attack prevention utilities"""

    # Dangerous XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"onmouseout\s*=",
        r"onfocus\s*=",
        r"onblur\s*=",
        r"onchange\s*=",
        r"onsubmit\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<applet[^>]*>",
        r"<meta[^>]*>",
        r"<link[^>]*>",
        r"<style[^>]*>",
        r"<base[^>]*>",
        r"<form[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
        r"import\s*\(",
        r"document\.",
        r"window\.",
        r"<svg[^>]*onload",
        r"<img[^>]*onerror",
        r"<body[^>]*onload",
    ]

    @classmethod
    def sanitize_html(
        cls,
        html_content: str,
        strip: bool = True,
        tags: Optional[List[str]] = None,
        attributes: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """
        Sanitize HTML content using bleach

        Args:
            html_content: Raw HTML content
            strip: Strip disallowed tags instead of escaping
            tags: Allowed tags (default: ALLOWED_HTML_TAGS)
            attributes: Allowed attributes (default: ALLOWED_HTML_ATTRIBUTES)

        Returns:
            Sanitized HTML content
        """
        if not html_content:
            return ""

        # Use defaults if not provided
        tags = tags or ALLOWED_HTML_TAGS
        attributes = attributes or ALLOWED_HTML_ATTRIBUTES

        # Clean with bleach
        cleaned = bleach.clean(
            html_content,
            tags=tags,
            attributes=attributes,
            protocols=ALLOWED_PROTOCOLS,
            strip=strip,
        )

        # Additional pattern-based validation
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                # If dangerous pattern found after cleaning, reject
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Potentially malicious content detected: {pattern}",
                )

        return cleaned

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize plain text (no HTML allowed)

        Args:
            text: Raw text input

        Returns:
            HTML-escaped safe text
        """
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Remove control characters (except tab, newline, carriage return)
        text = "".join(
            char
            for char in text
            if not unicodedata.category(char).startswith("C") or char in "\t\n\r"
        )

        # HTML escape
        text = html.escape(text)

        # Check for XSS patterns even in escaped text
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Potentially malicious content detected",
                )

        return text

    @classmethod
    def linkify_safe(cls, text: str) -> str:
        """
        Convert URLs to safe links

        Args:
            text: Text with URLs

        Returns:
            Text with safe HTML links
        """
        return bleach.linkify(
            text,
            protocols=ALLOWED_PROTOCOLS,
            parse_email=False,  # Disable email parsing for security
        )


# ==================== SQL INJECTION PROTECTION ====================


class SQLInjectionProtection:
    """SQL Injection attack prevention utilities"""

    # SQL injection patterns (comprehensive)
    SQL_PATTERNS = [
        # Basic SQL keywords
        r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b",
        # UNION attacks
        r"\bUNION\b.*\bSELECT\b",
        # Boolean-based blind SQL injection
        r'\b(OR|AND)\b\s*[\'"]?\d+[\'"]?\s*=\s*[\'"]?\d+[\'"]?',
        r'\b(OR|AND)\b\s*[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?',
        # Time-based blind SQL injection
        r"\bWAITFOR\b.*\bDELAY\b",
        r"\bSLEEP\s*\(",
        r"\bBENCHMARK\s*\(",
        r"\bPG_SLEEP\s*\(",
        # Stacked queries
        r";.*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b",
        # Comments (used to bypass filters)
        r"--[^\r\n]*",
        r"/\*.*?\*/",
        r"#[^\r\n]*",
        # String concatenation
        r'\+.*[\'"].*\+',
        r'\|\|.*[\'"].*\|\|',
        r"CONCAT\s*\(",
        # System tables and functions
        r"\b(information_schema|mysql|pg_catalog|sys|sysobjects|syscolumns)\b",
        r"\b(xp_cmdshell|sp_executesql|xp_regread)\b",
        # Data exfiltration
        r"\bINTO\s+OUTFILE\b",
        r"\bLOAD_FILE\s*\(",
        r"\bINTO\s+DUMPFILE\b",
        # Authentication bypass
        r"['\"]?\s*OR\s*['\"]?1['\"]?\s*=\s*['\"]?1",
        r"['\"]?\s*OR\s*['\"]?[a-z]\s*=\s*['\"]?[a-z]",
        r"admin['\"]?\s*--",
        r"admin['\"]?\s*#",
        # Hex encoding
        r"0x[0-9a-fA-F]+",
        # Database fingerprinting
        r"@@version",
        r"@@servername",
        r"\bVERSION\s*\(",
        r"\bDATABASE\s*\(",
        r"\bUSER\s*\(",
    ]

    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        Detect potential SQL injection attempts

        Args:
            value: Input string to check

        Returns:
            True if SQL injection pattern detected
        """
        if not value:
            return False

        # Check each pattern
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
                return True

        return False

    @classmethod
    def validate_input(cls, value: str, param_name: str = "input") -> str:
        """
        Validate input for SQL injection

        Args:
            value: Input string
            param_name: Parameter name for error message

        Returns:
            Validated input

        Raises:
            HTTPException: If SQL injection detected
        """
        if not value:
            return value

        if cls.detect_sql_injection(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {param_name}: potential SQL injection detected",
            )

        return value

    @classmethod
    def sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitize database identifier (table/column name)

        Args:
            identifier: Database identifier

        Returns:
            Sanitized identifier

        Raises:
            HTTPException: If invalid characters detected
        """
        # Only allow alphanumeric and underscore
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid database identifier",
            )

        # Check against SQL keywords
        sql_keywords = {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TABLE",
            "DATABASE",
            "INDEX",
            "VIEW",
            "TRIGGER",
            "PROCEDURE",
            "FUNCTION",
            "EXEC",
            "EXECUTE",
        }

        if identifier.upper() in sql_keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identifier cannot be a SQL keyword",
            )

        return identifier


# ==================== PATH TRAVERSAL PROTECTION ====================


class PathTraversalProtection:
    """Path traversal attack prevention"""

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"%2e%2e",
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"..%2f",
        r"..%5c",
        r"..%c0%af",
        r"..%c1%9c",
    ]

    @classmethod
    def validate_path(cls, path: str) -> str:
        """
        Validate file path

        Args:
            path: File path to validate

        Returns:
            Validated path

        Raises:
            HTTPException: If path traversal detected
        """
        if not path:
            return path

        # Check for path traversal patterns
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid path: path traversal detected",
                )

        # Ensure no absolute paths
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Absolute paths not allowed",
            )

        return path


# ==================== COMMAND INJECTION PROTECTION ====================


class CommandInjectionProtection:
    """Command injection attack prevention"""

    COMMAND_INJECTION_PATTERNS = [
        r"[;\|\&\$\`]",
        r"\$\([^)]*\)",
        r"`[^`]*`",
        r"\$\{[^}]*\}",
        r"\n",
        r"\r",
        r"&&",
        r"\|\|",
        r">>",
        r"<<",
        r"<\(",
        r">\(",
    ]

    @classmethod
    def validate_input(cls, value: str) -> str:
        """
        Validate input for command injection

        Args:
            value: Input to validate

        Returns:
            Validated input

        Raises:
            HTTPException: If command injection detected
        """
        if not value:
            return value

        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential command injection detected",
                )

        return value


# ==================== LDAP INJECTION PROTECTION ====================


class LDAPInjectionProtection:
    """LDAP injection attack prevention"""

    LDAP_SPECIAL_CHARS = ["*", "(", ")", "\\", "\x00", "/"]

    @classmethod
    def escape_ldap(cls, value: str) -> str:
        """
        Escape LDAP special characters

        Args:
            value: Input string

        Returns:
            Escaped string
        """
        if not value:
            return value

        # Escape special characters
        for char in cls.LDAP_SPECIAL_CHARS:
            value = value.replace(char, f"\\{char}")

        return value


# ==================== COMPREHENSIVE INPUT SANITIZER ====================


class ComprehensiveInputSanitizer:
    """All-in-one input sanitizer"""

    @classmethod
    def sanitize(
        cls,
        value: Any,
        allow_html: bool = False,
        check_sql: bool = True,
        check_xss: bool = True,
        check_path: bool = False,
        check_command: bool = False,
        max_length: Optional[int] = None,
    ) -> Any:
        """
        Comprehensive input sanitization

        Args:
            value: Input value
            allow_html: Allow HTML content
            check_sql: Check for SQL injection
            check_xss: Check for XSS
            check_path: Check for path traversal
            check_command: Check for command injection
            max_length: Maximum length

        Returns:
            Sanitized value
        """
        if value is None:
            return None

        # Handle non-string types
        if not isinstance(value, str):
            if isinstance(value, (int, float, bool)):
                return value
            if isinstance(value, (list, dict)):
                return value
            return str(value)

        # Null byte check
        if "\x00" in value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Null bytes not allowed"
            )

        # Length check
        if max_length and len(value) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long (max {max_length} characters)",
            )

        # SQL injection check
        if check_sql:
            SQLInjectionProtection.validate_input(value)

        # Path traversal check
        if check_path:
            PathTraversalProtection.validate_path(value)

        # Command injection check
        if check_command:
            CommandInjectionProtection.validate_input(value)

        # XSS protection
        if check_xss:
            if allow_html:
                value = XSSProtection.sanitize_html(value)
            else:
                value = XSSProtection.sanitize_text(value)

        return value


# ==================== UTILITY FUNCTIONS ====================


def sanitize_input(
    value: str, allow_html: bool = False, max_length: Optional[int] = None
) -> str:
    """
    Quick sanitize function

    Args:
        value: Input string
        allow_html: Allow HTML
        max_length: Max length

    Returns:
        Sanitized string
    """
    return ComprehensiveInputSanitizer.sanitize(
        value, allow_html=allow_html, max_length=max_length
    )


def validate_email(email: str) -> str:
    """
    Validate and sanitize email

    Args:
        email: Email address

    Returns:
        Validated email
    """
    email = email.strip().lower()

    # Basic email regex
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
        )

    # Check for SQL injection in email
    SQLInjectionProtection.validate_input(email, "email")

    return email


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Validate URL

    Args:
        url: URL to validate
        allowed_schemes: Allowed URL schemes

    Returns:
        Validated URL
    """
    allowed_schemes = allowed_schemes or ["http", "https"]

    try:
        parsed = urlparse(url)

        if parsed.scheme not in allowed_schemes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL scheme must be one of: {', '.join(allowed_schemes)}",
            )

        # Check for XSS in URL
        if any(char in url for char in ["<", ">", '"', "'"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters in URL",
            )

        return url

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL format"
        )


# ==================== EXPORT ====================

__all__ = [
    "XSSProtection",
    "SQLInjectionProtection",
    "PathTraversalProtection",
    "CommandInjectionProtection",
    "LDAPInjectionProtection",
    "ComprehensiveInputSanitizer",
    "sanitize_input",
    "validate_email",
    "validate_url",
]
