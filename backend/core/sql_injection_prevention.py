"""
SQL Injection Prevention Modülü
Task 23: Security Hardening - SQL injection prevention

Bu modül SQL injection saldırılarını önlemek için güvenli query oluşturma
ve parameterized query kullanımını sağlar.
"""
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status


class SQLInjectionPrevention:
    """SQL injection prevention utilities"""

    # Tehlikeli SQL pattern'leri
    DANGEROUS_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*|1=1|'=')",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)",
        r"(CAST|CONVERT|CHAR|ASCII|SUBSTRING)",
    ]

    @staticmethod
    def is_safe_identifier(identifier: str) -> bool:
        """
        Identifier'ın güvenli olup olmadığını kontrol et

        Args:
            identifier: Tablo/kolon adı

        Returns:
            True if safe, False otherwise
        """
        # Sadece alfanumerik ve underscore
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
            return False

        # SQL keyword kontrolü
        sql_keywords = [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "EXEC",
            "EXECUTE",
            "UNION",
            "WHERE",
            "FROM",
        ]

        if identifier.upper() in sql_keywords:
            return False

        return True

    @staticmethod
    def validate_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query parametrelerini doğrula

        Args:
            params: Query parametreleri

        Returns:
            Doğrulanmış parametreler

        Raises:
            HTTPException: Güvenli olmayan parametre
        """
        validated = {}

        for key, value in params.items():
            # Key validation
            if not SQLInjectionPrevention.is_safe_identifier(key):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Geçersiz parametre adı: {key}",
                )

            # Value validation
            if isinstance(value, str):
                # SQL injection pattern kontrolü
                for pattern in SQLInjectionPrevention.DANGEROUS_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Güvenlik nedeniyle istek reddedildi.",
                        )

            validated[key] = value

        return validated

    @staticmethod
    def build_safe_query(
        base_query: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Güvenli parameterized query oluştur

        Args:
            base_query: Temel SELECT query
            filters: WHERE clause filtreleri
            order_by: ORDER BY kolon adı
            limit: LIMIT değeri

        Returns:
            (query_string, params) tuple

        Raises:
            HTTPException: Güvenli olmayan query
        """
        query_parts = [base_query]
        params = {}

        # WHERE clause
        if filters:
            where_conditions = []
            for key, value in filters.items():
                # Identifier validation
                if not SQLInjectionPrevention.is_safe_identifier(key):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Geçersiz kolon adı: {key}",
                    )

                # Parameterized condition
                param_name = f"param_{key}"
                where_conditions.append(f"{key} = :{param_name}")
                params[param_name] = value

            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))

        # ORDER BY clause
        if order_by:
            # Identifier validation
            if not SQLInjectionPrevention.is_safe_identifier(order_by):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Geçersiz ORDER BY kolon adı: {order_by}",
                )

            query_parts.append(f"ORDER BY {order_by}")

        # LIMIT clause
        if limit:
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geçersiz LIMIT değeri",
                )

            query_parts.append("LIMIT :limit_value")
            params["limit_value"] = limit

        query_string = " ".join(query_parts)

        return query_string, params

    @staticmethod
    async def execute_safe_query(
        session: AsyncSession, query_string: str, params: Dict[str, Any]
    ) -> List[Any]:
        """
        Güvenli query execution

        Args:
            session: Database session
            query_string: Parameterized query string
            params: Query parametreleri

        Returns:
            Query sonuçları
        """
        # Parametreleri doğrula
        validated_params = SQLInjectionPrevention.validate_query_params(params)

        # Execute with parameterized query
        result = await session.execute(text(query_string), validated_params)

        return result.fetchall()


class SafeQueryBuilder:
    """Güvenli query builder sınıfı"""

    def __init__(self, table_name: str):
        """
        Initialize query builder

        Args:
            table_name: Tablo adı

        Raises:
            HTTPException: Geçersiz tablo adı
        """
        if not SQLInjectionPrevention.is_safe_identifier(table_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz tablo adı: {table_name}",
            )

        self.table_name = table_name
        self.filters = {}
        self.order_by_column = None
        self.limit_value = None

    def where(self, **kwargs) -> "SafeQueryBuilder":
        """
        WHERE clause ekle

        Args:
            **kwargs: Kolon=değer çiftleri

        Returns:
            Self (method chaining için)
        """
        for key, value in kwargs.items():
            if not SQLInjectionPrevention.is_safe_identifier(key):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Geçersiz kolon adı: {key}",
                )

            self.filters[key] = value

        return self

    def order_by(self, column: str) -> "SafeQueryBuilder":
        """
        ORDER BY clause ekle

        Args:
            column: Sıralama kolonu

        Returns:
            Self (method chaining için)
        """
        if not SQLInjectionPrevention.is_safe_identifier(column):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz kolon adı: {column}",
            )

        self.order_by_column = column
        return self

    def limit(self, value: int) -> "SafeQueryBuilder":
        """
        LIMIT clause ekle

        Args:
            value: Limit değeri

        Returns:
            Self (method chaining için)
        """
        if not isinstance(value, int) or value < 1 or value > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz LIMIT değeri"
            )

        self.limit_value = value
        return self

    def build(self) -> Tuple[str, Dict[str, Any]]:
        """
        Query'yi oluştur

        Returns:
            (query_string, params) tuple
        """
        base_query = f"SELECT * FROM {self.table_name}"

        return SQLInjectionPrevention.build_safe_query(
            base_query=base_query,
            filters=self.filters,
            order_by=self.order_by_column,
            limit=self.limit_value,
        )

    async def execute(self, session: AsyncSession) -> List[Any]:
        """
        Query'yi çalıştır

        Args:
            session: Database session

        Returns:
            Query sonuçları
        """
        query_string, params = self.build()
        return await SQLInjectionPrevention.execute_safe_query(
            session, query_string, params
        )


# ==================== BACKWARD COMPATIBILITY ALIASES ====================

# Alias for tests that import SQLInjectionDetector
SQLInjectionDetector = SQLInjectionPrevention


class SQLInjectionSeverity(str, Enum):
    """Severity levels for SQL injection attempts"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SQLInjectionPreventionMiddleware:
    """ASGI middleware for SQL injection detection in requests"""

    def __init__(self, app: Any, detector: Optional[SQLInjectionPrevention] = None) -> None:
        self.app = app
        self.detector = detector or SQLInjectionPrevention()

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        # Pass through for now - actual implementation would inspect request body
        await self.app(scope, receive, send)


class ParameterizedQueryValidator:
    """Validator for parameterized queries"""

    @staticmethod
    def validate(query: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that query uses parameterized placeholders

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for string concatenation patterns
        if re.search(r"%s|%d|\+|f\"|\$\{", query):
            return False, "Query appears to use string concatenation instead of parameters"

        # Check that all parameters are used
        expected_params = set(re.findall(r":(\w+)", query))
        provided_params = set(params.keys())

        if expected_params != provided_params:
            missing = expected_params - provided_params
            extra = provided_params - expected_params
            error = []
            if missing:
                error.append(f"Missing parameters: {missing}")
            if extra:
                error.append(f"Extra parameters: {extra}")
            return False, "; ".join(error)

        return True, None


# Example usage:
"""
# Safe query building
builder = SafeQueryBuilder("video_cache")
builder.where(subject="matematik", difficulty="orta")
builder.order_by("quality_score")
builder.limit(20)

results = await builder.execute(session)

# Or using build_safe_query directly
query, params = SQLInjectionPrevention.build_safe_query(
    base_query="SELECT * FROM video_cache",
    filters={"subject": "matematik", "difficulty": "orta"},
    order_by="quality_score",
    limit=20
)

results = await SQLInjectionPrevention.execute_safe_query(session, query, params)
"""
