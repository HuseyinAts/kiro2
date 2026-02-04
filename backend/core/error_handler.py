"""
Video API Error Handler
Learning Path Video Yükleme Sorunu için özel hata yönetimi

Requirements: 5.1, 5.2, 5.7, 5.8, 5.9
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, List
from dataclasses import dataclass, field
import logging
import traceback

from .exceptions import (
    EnhancedServiceError,
    ErrorSeverity,
    ExternalServiceError,
    TimeoutError as CustomTimeoutError,
    RateLimitError,
    DatabaseError,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitBreakerHalfOpenError,
    circuit_breaker_manager,
)

logger = logging.getLogger(__name__)


# ==================== CUSTOM VIDEO API EXCEPTIONS ====================


class VideoAPIError(EnhancedServiceError):
    """Base exception for video API errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "VIDEO_API_ERROR",
        details: Dict[str, Any] | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: str | None = None,
        retry_after: int | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            severity=severity,
            user_message=user_message or "Video yükleme sırasında bir hata oluştu",
            retry_after=retry_after,
            **kwargs,
        )


class YouTubeAPIError(VideoAPIError):
    """YouTube API specific errors"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        quota_exceeded: bool = False,
        details: Dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details.update({"status_code": status_code, "quota_exceeded": quota_exceeded})

        user_message = "YouTube servisine erişilemiyor"
        if quota_exceeded:
            user_message = "YouTube API kotası doldu. Lütfen daha sonra tekrar deneyin."

        super().__init__(
            message=message,
            error_code="YOUTUBE_API_ERROR",
            details=details,
            severity=ErrorSeverity.HIGH if quota_exceeded else ErrorSeverity.MEDIUM,
            user_message=user_message,
            retry_after=3600 if quota_exceeded else 60,
            **kwargs,
        )


class CacheError(VideoAPIError):
    """Cache operation errors"""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        cache_type: str | None = None,
        details: Dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details.update({"operation": operation, "cache_type": cache_type})

        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            severity=ErrorSeverity.LOW,
            user_message="Önbellek sistemi geçici olarak kullanılamıyor",
            **kwargs,
        )


class VideoDiscoveryError(VideoAPIError):
    """Video discovery process errors"""

    def __init__(
        self,
        message: str,
        subject: str | None = None,
        search_type: str | None = None,
        details: Dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details.update({"subject": subject, "search_type": search_type})

        super().__init__(
            message=message,
            error_code="VIDEO_DISCOVERY_ERROR",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            user_message="Videolar bulunamadı. Lütfen farklı bir konu deneyin.",
            **kwargs,
        )


class VideoFilterError(VideoAPIError):
    """Video filtering errors"""

    def __init__(
        self,
        message: str,
        filter_type: str | None = None,
        details: Dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details.update({"filter_type": filter_type})

        super().__init__(
            message=message,
            error_code="VIDEO_FILTER_ERROR",
            details=details,
            severity=ErrorSeverity.LOW,
            user_message="Video filtreleme sırasında bir sorun oluştu",
            **kwargs,
        )


class VideoTimeoutError(VideoAPIError):
    """Video API timeout errors"""

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        operation: str | None = None,
        details: Dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details.update({"timeout_seconds": timeout_seconds, "operation": operation})

        super().__init__(
            message=message,
            error_code="VIDEO_TIMEOUT_ERROR",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            user_message="Video yükleme zaman aşımına uğradı. Lütfen tekrar deneyin.",
            retry_after=5,
            **kwargs,
        )


# ==================== ERROR CLASSIFICATION ====================


class ErrorCategory(str, Enum):
    """Error categories for classification"""

    NETWORK = "network"  # Network connectivity issues
    TIMEOUT = "timeout"  # Operation timeout
    RATE_LIMIT = "rate_limit"  # Rate limiting
    QUOTA = "quota"  # API quota exceeded
    AUTHENTICATION = "authentication"  # Auth failures
    AUTHORIZATION = "authorization"  # Permission issues
    VALIDATION = "validation"  # Input validation
    NOT_FOUND = "not_found"  # Resource not found
    SERVER_ERROR = "server_error"  # Server-side errors
    CLIENT_ERROR = "client_error"  # Client-side errors
    CACHE = "cache"  # Cache errors
    DATABASE = "database"  # Database errors
    UNKNOWN = "unknown"  # Unknown errors


@dataclass
class ErrorClassification:
    """Classification result for an error"""

    category: ErrorCategory
    severity: ErrorSeverity
    retryable: bool
    retry_after: int  # Seconds
    user_message: str
    recovery_actions: List[str]
    log_level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL


# ==================== ERROR HANDLER ====================


class ErrorHandler:
    """
    Comprehensive error handler for video API

    Responsibilities:
    - Error classification
    - User-friendly message generation
    - Recovery action determination
    - Structured logging
    - Error metrics collection

    Requirements: 5.1, 5.2, 5.7, 5.8, 5.9
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}

    def classify_error(self, error: Exception) -> ErrorClassification:
        """
        Classify error and determine handling strategy

        Args:
            error: Exception to classify

        Returns:
            ErrorClassification with handling strategy
        """
        # Handle VideoAPIError and subclasses
        if isinstance(error, YouTubeAPIError):
            return self._classify_youtube_error(error)
        elif isinstance(error, CacheError):
            return self._classify_cache_error(error)
        elif isinstance(error, VideoTimeoutError):
            return self._classify_timeout_error(error)
        elif isinstance(error, VideoDiscoveryError):
            return self._classify_discovery_error(error)
        elif isinstance(error, VideoFilterError):
            return self._classify_filter_error(error)

        # Handle standard exceptions
        elif isinstance(error, RateLimitError):
            return self._classify_rate_limit_error(error)
        elif isinstance(error, CustomTimeoutError):
            return self._classify_timeout_error(error)
        elif isinstance(error, DatabaseError):
            return self._classify_database_error(error)
        elif isinstance(error, ExternalServiceError):
            return self._classify_external_service_error(error)

        # Handle generic exceptions
        elif isinstance(error, asyncio.TimeoutError):
            return ErrorClassification(
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                retryable=True,
                retry_after=5,
                user_message="İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.",
                recovery_actions=["retry", "use_cache", "fallback"],
                log_level="WARNING",
            )
        elif isinstance(error, ConnectionError):
            return ErrorClassification(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                retryable=True,
                retry_after=10,
                user_message="Bağlantı hatası. İnternet bağlantınızı kontrol edin.",
                recovery_actions=["retry", "check_network", "use_cache"],
                log_level="ERROR",
            )
        else:
            return self._classify_unknown_error(error)

    def _classify_youtube_error(self, error: YouTubeAPIError) -> ErrorClassification:
        """Classify YouTube API errors"""
        if error.details.get("quota_exceeded"):
            return ErrorClassification(
                category=ErrorCategory.QUOTA,
                severity=ErrorSeverity.CRITICAL,
                retryable=True,
                retry_after=3600,
                user_message="YouTube API kotası doldu. Önbellekteki videolar gösteriliyor.",
                recovery_actions=["use_cache", "fallback", "notify_admin"],
                log_level="CRITICAL",
            )

        status_code = error.details.get("status_code")
        if status_code == 429:
            return ErrorClassification(
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.HIGH,
                retryable=True,
                retry_after=60,
                user_message="Çok fazla istek gönderildi. Lütfen bir dakika bekleyin.",
                recovery_actions=["wait", "use_cache"],
                log_level="WARNING",
            )
        elif status_code and 500 <= status_code < 600:
            return ErrorClassification(
                category=ErrorCategory.SERVER_ERROR,
                severity=ErrorSeverity.HIGH,
                retryable=True,
                retry_after=30,
                user_message="YouTube servisi geçici olarak kullanılamıyor.",
                recovery_actions=["retry", "use_cache", "fallback"],
                log_level="ERROR",
            )
        else:
            return ErrorClassification(
                category=ErrorCategory.CLIENT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                retryable=False,
                retry_after=0,
                user_message="YouTube API isteği başarısız oldu.",
                recovery_actions=["use_cache", "fallback"],
                log_level="WARNING",
            )

    def _classify_cache_error(self, error: CacheError) -> ErrorClassification:
        """Classify cache errors"""
        return ErrorClassification(
            category=ErrorCategory.CACHE,
            severity=ErrorSeverity.LOW,
            retryable=True,
            retry_after=5,
            user_message="Önbellek sistemi geçici olarak kullanılamıyor.",
            recovery_actions=["skip_cache", "retry"],
            log_level="WARNING",
        )

    def _classify_timeout_error(
        self, error: VideoTimeoutError | CustomTimeoutError
    ) -> ErrorClassification:
        """Classify timeout errors"""
        return ErrorClassification(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after=5,
            user_message="İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.",
            recovery_actions=["retry", "increase_timeout", "use_cache"],
            log_level="WARNING",
        )

    def _classify_discovery_error(
        self, error: VideoDiscoveryError
    ) -> ErrorClassification:
        """Classify video discovery errors"""
        return ErrorClassification(
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after=10,
            user_message="İstenen konuda video bulunamadı. Farklı bir konu deneyin.",
            recovery_actions=["retry_different_query", "fallback", "use_cache"],
            log_level="INFO",
        )

    def _classify_filter_error(self, error: VideoFilterError) -> ErrorClassification:
        """Classify video filter errors"""
        return ErrorClassification(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            retryable=True,
            retry_after=0,
            user_message="Video filtreleme sırasında bir sorun oluştu.",
            recovery_actions=["skip_filter", "retry"],
            log_level="WARNING",
        )

    def _classify_rate_limit_error(self, error: RateLimitError) -> ErrorClassification:
        """Classify rate limit errors"""
        retry_after = error.details.get("retry_after", 60)
        return ErrorClassification(
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after=retry_after,
            user_message=f"Çok fazla istek. {retry_after} saniye sonra tekrar deneyin.",
            recovery_actions=["wait", "use_cache"],
            log_level="WARNING",
        )

    def _classify_database_error(self, error: DatabaseError) -> ErrorClassification:
        """Classify database errors"""
        return ErrorClassification(
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            retryable=True,
            retry_after=10,
            user_message="Veritabanı geçici olarak kullanılamıyor.",
            recovery_actions=["retry", "use_cache", "notify_admin"],
            log_level="ERROR",
        )

    def _classify_external_service_error(
        self, error: ExternalServiceError
    ) -> ErrorClassification:
        """Classify external service errors"""
        status_code = error.details.get("status_code")
        if status_code and 500 <= status_code < 600:
            severity = ErrorSeverity.HIGH
            retryable = True
        else:
            severity = ErrorSeverity.MEDIUM
            retryable = False

        return ErrorClassification(
            category=ErrorCategory.SERVER_ERROR,
            severity=severity,
            retryable=retryable,
            retry_after=30 if retryable else 0,
            user_message="Dış servis geçici olarak kullanılamıyor.",
            recovery_actions=["retry", "use_cache"] if retryable else ["use_cache"],
            log_level="ERROR",
        )

    def _classify_unknown_error(self, error: Exception) -> ErrorClassification:
        """Classify unknown errors"""
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            retry_after=0,
            user_message="Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.",
            recovery_actions=["fallback", "notify_admin"],
            log_level="ERROR",
        )

    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> ErrorClassification:
        """
        Handle error with classification, logging, and metrics

        Args:
            error: Exception to handle
            context: Additional context information
            request_id: Request ID for tracing

        Returns:
            ErrorClassification with handling strategy
        """
        # Classify error
        classification = self.classify_error(error)

        # Update error metrics
        self._update_error_metrics(classification.category.value)

        # Log error
        self._log_error(error, classification, context, request_id)

        return classification

    def _update_error_metrics(self, error_type: str) -> None:
        """Update error count metrics"""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        self._last_errors[error_type] = datetime.now()

    def _log_error(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Dict[str, Any] | None,
        request_id: str | None,
    ) -> None:
        """Log error with structured format"""
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": classification.category.value,
            "severity": classification.severity.value,
            "retryable": classification.retryable,
            "retry_after": classification.retry_after,
            "request_id": request_id,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }

        # Add stack trace for high severity errors
        if classification.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log_data["stack_trace"] = traceback.format_exc()

        # Log based on level
        log_level = classification.log_level.upper()
        if log_level == "CRITICAL":
            self.logger.critical(f"Critical error: {log_data}")
        elif log_level == "ERROR":
            self.logger.error(f"Error: {log_data}")
        elif log_level == "WARNING":
            self.logger.warning(f"Warning: {log_data}")
        else:
            self.logger.info(f"Info: {log_data}")

    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message"""
        classification = self.classify_error(error)
        return classification.user_message

    def should_retry(self, error: Exception) -> Tuple[bool, int]:
        """
        Determine if error should be retried

        Returns:
            Tuple of (should_retry, retry_after_seconds)
        """
        classification = self.classify_error(error)
        return classification.retryable, classification.retry_after

    def get_recovery_actions(self, error: Exception) -> List[str]:
        """Get recommended recovery actions"""
        classification = self.classify_error(error)
        return classification.recovery_actions

    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics summary"""
        return {
            "error_counts": dict(self._error_counts),
            "last_errors": {k: v.isoformat() for k, v in self._last_errors.items()},
            "total_errors": sum(self._error_counts.values()),
        }


# ==================== CIRCUIT BREAKER ====================


# Note: CircuitBreaker implementation moved to circuit_breaker.py
# Import from there: from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, etc.
