"""
SQL Injection Prevention & Security Utilities
SECURITY FIX: Centralized SQL security validation and sanitization
"""

import re
from typing import Any, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ClauseElement

from .structured_logger import get_logger

logger = get_logger("sql_security")


class SQLInjectionError(Exception):
    """SQL Injection attempt detected"""



class SQLSecurityValidator:
    """
    SQL Security validation and sanitization

    Features:
    - SQL injection pattern detection
    - Input sanitization
    - Safe parameter binding
    - Query validation
    """

    # SQL injection patterns (common attack signatures)
    INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",  # UNION SELECT
        r"(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)",  # OR 1=1
        r"(\band\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)",  # AND 1=1
        r"(--\s*$)",  # SQL comments
        r"(/\*.*\*/)",  # Multi-line comments
        r"(\bexec\b|\bexecute\b)\s*\(",  # Execute commands
        r"(\bdrop\b\s+\btable\b)",  # DROP TABLE
        r"(\bdelete\b\s+\bfrom\b\s+\w+\s*(?!.*\bwhere\b))",  # DELETE without WHERE - SECURITY FIX
        r"(\binsert\b\s+\binto\b)",  # INSERT INTO (without proper context)
        r"(\bupdate\b.*\bset\b)",  # UPDATE SET (without proper context)
        r"(;\s*\b(select|insert|update|delete|drop|create|alter)\b)",  # Statement chaining
        r"(\bxp_cmdshell\b)",  # SQL Server command execution
        r"(\binto\b\s+\boutfile\b)",  # MySQL file write
        r"(\bload_file\b\s*\()",  # MySQL file read
    ]

    # Compiled regex patterns for performance
    _compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    @classmethod
    def validate_input(cls, value: str, field_name: str = "input") -> str:
        """
        Validate user input for SQL injection attempts

        Args:
            value: Input value to validate
            field_name: Name of the field (for logging)

        Returns:
            Validated input value

        Raises:
            SQLInjectionError: If injection pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for SQL injection patterns
        for pattern in cls._compiled_patterns:
            if pattern.search(value):
                logger.error(
                    f"SQL Injection attempt detected in {field_name}",
                    extra_data={
                        "field": field_name,
                        "value_preview": value[:100],
                        "pattern_matched": pattern.pattern,
                    },
                )
                raise SQLInjectionError(
                    f"Invalid input detected in {field_name}. "
                    "Please avoid SQL keywords and special characters."
                )

        return value

    @classmethod
    def sanitize_like_pattern(cls, pattern: str) -> str:
        """
        Sanitize LIKE pattern to prevent injection

        Args:
            pattern: User-provided LIKE pattern

        Returns:
            Sanitized pattern
        """
        # Escape SQL LIKE special characters
        pattern = pattern.replace("\\", "\\\\")  # Backslash
        pattern = pattern.replace("%", "\\%")  # Percent
        pattern = pattern.replace("_", "\\_")  # Underscore
        return pattern

    @classmethod
    def validate_table_name(cls, table_name: str) -> str:
        """
        Validate table name (alphanumeric + underscore only)

        Args:
            table_name: Table name to validate

        Returns:
            Validated table name

        Raises:
            SQLInjectionError: If invalid characters found
        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            logger.error(
                f"Invalid table name: {table_name}",
                extra_data={"table_name": table_name},
            )
            raise SQLInjectionError(f"Invalid table name: {table_name}")
        return table_name

    @classmethod
    def validate_column_name(cls, column_name: str) -> str:
        """
        Validate column name (alphanumeric + underscore only)

        Args:
            column_name: Column name to validate

        Returns:
            Validated column name

        Raises:
            SQLInjectionError: If invalid characters found
        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name):
            logger.error(
                f"Invalid column name: {column_name}",
                extra_data={"column_name": column_name},
            )
            raise SQLInjectionError(f"Invalid column name: {column_name}")
        return column_name

    @classmethod
    def validate_order_by(cls, order_by: str, allowed_columns: list[str]) -> str:
        """
        Validate ORDER BY clause

        Args:
            order_by: ORDER BY value
            allowed_columns: List of allowed column names

        Returns:
            Validated ORDER BY value

        Raises:
            SQLInjectionError: If invalid ORDER BY
        """
        # Extract column name and direction
        parts = order_by.strip().split()
        column = parts[0]
        direction = parts[1].upper() if len(parts) > 1 else "ASC"

        # Validate column name
        if column not in allowed_columns:
            raise SQLInjectionError(f"Invalid ORDER BY column: {column}")

        # Validate direction
        if direction not in ("ASC", "DESC"):
            raise SQLInjectionError(f"Invalid ORDER BY direction: {direction}")

        return f"{column} {direction}"


class SafeQueryBuilder:
    """
    Safe query builder with parameter binding

    Usage:
        builder = SafeQueryBuilder()
        query = builder.select('users', ['id', 'name']) \
            .where('age > :min_age') \
            .order_by('created_at', 'DESC') \
            .limit(10) \
            .build()

        results = await session.execute(query, {'min_age': 18})
    """

    def __init__(self):
        self._select_cols: list[str] = []
        self._from_table: str | None = None
        self._where_clauses: list[str] = []
        self._order_by_clause: str | None = None
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def select(self, table: str, columns: list[str] = None):
        """Select columns from table"""
        self._from_table = SQLSecurityValidator.validate_table_name(table)
        if columns:
            self._select_cols = [
                SQLSecurityValidator.validate_column_name(col) for col in columns
            ]
        else:
            self._select_cols = ["*"]
        return self

    def where(self, condition: str):
        """Add WHERE condition (use :param for parameters)"""
        # Condition should use parameter binding (:param_name)
        if not re.search(r":\w+", condition) and re.search(r'[\'"]', condition):
            logger.warning(
                "WHERE clause contains quotes but no parameters - potential SQL injection",
                extra_data={"condition": condition},
            )
        self._where_clauses.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC"):
        """Add ORDER BY clause"""
        column = SQLSecurityValidator.validate_column_name(column)
        direction = direction.upper()
        if direction not in ("ASC", "DESC"):
            raise SQLInjectionError(f"Invalid ORDER BY direction: {direction}")
        self._order_by_clause = f"{column} {direction}"
        return self

    def limit(self, limit: int):
        """Add LIMIT"""
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("LIMIT must be a positive integer")
        self._limit_value = limit
        return self

    def offset(self, offset: int):
        """Add OFFSET"""
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("OFFSET must be a positive integer")
        self._offset_value = offset
        return self

    def build(self) -> text:
        """Build safe SQL query"""
        if not self._from_table:
            raise ValueError("Table not specified")

        parts = []

        # SELECT
        cols = ", ".join(self._select_cols)
        parts.append(f"SELECT {cols} FROM {self._from_table}")

        # WHERE
        if self._where_clauses:
            where = " AND ".join(self._where_clauses)
            parts.append(f"WHERE {where}")

        # ORDER BY
        if self._order_by_clause:
            parts.append(f"ORDER BY {self._order_by_clause}")

        # LIMIT
        if self._limit_value is not None:
            parts.append(f"LIMIT {self._limit_value}")

        # OFFSET
        if self._offset_value is not None:
            parts.append(f"OFFSET {self._offset_value}")

        query_str = " ".join(parts)
        return text(query_str)


async def safe_execute(
    session: AsyncSession,
    query: Union[str, ClauseElement],
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Safely execute query with parameter validation

    Args:
        session: Database session
        query: SQL query (string or SQLAlchemy construct)
        params: Query parameters (will be validated)

    Returns:
        Query result

    Example:
        result = await safe_execute(
            session,
            "SELECT * FROM users WHERE email = :email",
            {"email": user_input}
        )
    """
    # Validate parameters
    if params:
        for key, value in params.items():
            if isinstance(value, str):
                SQLSecurityValidator.validate_input(value, key)

    # Execute with parameter binding
    if isinstance(query, str):
        query = text(query)

    result = await session.execute(query, params or {})
    return result


# Decorator for input validation
def validate_sql_inputs(**field_validators):
    """
    Decorator to validate SQL inputs

    Usage:
        @validate_sql_inputs(email=str, age=int)
        async def get_user(email: str, age: int):
            ...
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Validate kwargs
            for field, field_type in field_validators.items():
                if field in kwargs:
                    value = kwargs[field]
                    if isinstance(value, str):
                        kwargs[field] = SQLSecurityValidator.validate_input(
                            value, field
                        )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
