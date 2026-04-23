"""
Structured Logging Examples
Demonstrates migration from primitive to structured logging
"""

from core.structured_logger import (
    get_logger,
    log_api_request,
    log_api_response,
    log_cache_operation,
    log_database_query,
    log_error_with_context,
    log_exam_event,
)

# Initialize logger
logger = get_logger(__name__)


# ==================== EXAMPLE 1: Basic Logging ====================


def example_basic_logging():
    """Basic logging examples"""

    print("\n=== Example 1: Basic Logging ===\n")

    # Old way ❌
    print("Starting application...")
    user_id = 123
    print(f"User {user_id} logged in")

    # New way ✅
    logger.info("application_starting")
    logger.info("user_login", user_id=user_id, success=True)


# ==================== EXAMPLE 2: Error Logging ====================


def example_error_logging():
    """Error logging with context"""

    print("\n=== Example 2: Error Logging ===\n")

    try:
        # Simulate an error
        result = 10 / 0
    except Exception:
        # Old way ❌
        # print(f"Error: {e}")

        # New way ✅
        logger.exception(
            "division_error", operation="divide", numerator=10, denominator=0
        )


# ==================== EXAMPLE 3: Exam Events ====================


def example_exam_events():
    """Exam-related event logging"""

    print("\n=== Example 3: Exam Events ===\n")

    # Example 1: Exam created
    log_exam_event(
        logger,
        event_type="sinav_olusturuldu",
        sinav_id=456,
        ogrenci_id=123,
        sinav_tipi="tyt",
        soru_sayisi=40,
        sure_dakika=120,
    )

    # Example 2: Exam started
    log_exam_event(logger, event_type="sinav_basladi", sinav_id=456, ogrenci_id=123)

    # Example 3: Exam completed
    log_exam_event(
        logger,
        event_type="sinav_tamamlandi",
        sinav_id=456,
        ogrenci_id=123,
        dogru_sayisi=32,
        yanlis_sayisi=8,
        puan=85.5,
    )


# ==================== EXAMPLE 4: API Request/Response ====================


def example_api_logging():
    """API request and response logging"""

    print("\n=== Example 4: API Request/Response ===\n")

    import time

    # Log request
    log_api_request(
        logger,
        method="POST",
        path="/api/v1/exams",
        user_id=123,
        ip_address="192.168.1.100",
    )

    # Simulate processing
    start_time = time.time()
    time.sleep(0.05)  # Simulate 50ms processing
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    log_api_response(
        logger,
        method="POST",
        path="/api/v1/exams",
        status_code=201,
        duration_ms=duration_ms,
        exam_id=456,
    )


# ==================== EXAMPLE 5: Database Operations ====================


def example_database_logging():
    """Database operation logging"""

    print("\n=== Example 5: Database Operations ===\n")

    import time

    # Simulate query
    start = time.time()
    time.sleep(0.02)  # Simulate 20ms query
    duration_ms = (time.time() - start) * 1000

    log_database_query(
        logger,
        operation="SELECT",
        table="kullanicilar",
        duration_ms=duration_ms,
        row_count=150,
        filters={"sinif": "12", "aktif": True},
    )

    # Slow query warning
    start = time.time()
    time.sleep(0.5)  # Simulate 500ms slow query
    duration_ms = (time.time() - start) * 1000

    if duration_ms > 100:
        logger.warning(
            "slow_query_detected",
            operation="SELECT",
            table="sinav_sonuclari",
            duration_ms=duration_ms,
            threshold_ms=100,
        )


# ==================== EXAMPLE 6: Cache Operations ====================


def example_cache_logging():
    """Cache operation logging"""

    print("\n=== Example 6: Cache Operations ===\n")

    # Cache hit
    log_cache_operation(
        logger, operation="get", cache_key="user:123", hit=True, ttl_seconds=3600
    )

    # Cache miss
    log_cache_operation(logger, operation="get", cache_key="exam:456", hit=False)

    # Cache set
    log_cache_operation(
        logger, operation="set", cache_key="exam:456", size_bytes=2048, ttl_seconds=1800
    )


# ==================== EXAMPLE 7: Contextual Logging ====================


def example_contextual_logging():
    """Using bound logger for consistent context"""

    print("\n=== Example 7: Contextual Logging ===\n")

    # Bind context once
    request_logger = logger.bind(
        request_id="req-abc123", user_id=123, session_id="sess-xyz789"
    )

    # All logs now include the context automatically
    request_logger.info("request_received", method="POST", path="/api/exams")
    request_logger.info("validation_passed", field_count=5)
    request_logger.info("data_processed", record_count=10)
    request_logger.info("request_complete", duration_ms=45.2)


# ==================== EXAMPLE 8: Structured Data ====================


def example_structured_data():
    """Logging with rich structured data"""

    print("\n=== Example 8: Rich Structured Data ===\n")

    logger.info(
        "exam_analysis_complete",
        exam_id=456,
        statistics={
            "total_students": 150,
            "average_score": 75.5,
            "pass_rate": 0.82,
            "duration_minutes": 120,
        },
        distribution={"0-50": 15, "51-70": 45, "71-85": 60, "86-100": 30},
        metadata={"exam_type": "tyt", "school_id": 789, "teacher_id": 321},
    )


# ==================== EXAMPLE 9: Performance Monitoring ====================


def example_performance_monitoring():
    """Monitor function performance"""

    print("\n=== Example 9: Performance Monitoring ===\n")

    import time

    def monitored_operation():
        logger.info("operation_start", operation="data_processing")

        start = time.time()
        try:
            # Simulate work
            time.sleep(0.1)
            processed_items = 100

            duration_ms = (time.time() - start) * 1000
            logger.info(
                "operation_complete",
                operation="data_processing",
                duration_ms=duration_ms,
                items_processed=processed_items,
                items_per_second=processed_items / (duration_ms / 1000),
            )

        except Exception:
            duration_ms = (time.time() - start) * 1000
            logger.exception(
                "operation_failed", operation="data_processing", duration_ms=duration_ms
            )
            raise

    monitored_operation()


# ==================== EXAMPLE 10: Security Events ====================


def example_security_logging():
    """Security-related event logging"""

    print("\n=== Example 10: Security Events ===\n")

    # Successful login
    logger.info(
        "authentication_success",
        user_id=123,
        auth_method="password",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
    )

    # Failed login attempt
    logger.warning(
        "authentication_failed",
        email="user@example.com",
        ip_address="192.168.1.100",
        reason="invalid_password",
        attempt_count=3,
    )

    # Suspicious activity
    logger.error(
        "suspicious_activity_detected",
        user_id=123,
        activity="multiple_failed_logins",
        count=5,
        time_window_minutes=5,
        ip_address="192.168.1.100",
        action="account_locked",
    )

    # Password automatically censored
    logger.debug(
        "auth_attempt",
        email="user@example.com",
        password="secret123",  # This will be ***REDACTED***
        token="abc123xyz",  # This will be ***REDACTED***
    )


# ==================== RUN ALL EXAMPLES ====================


def run_all_examples():
    """Run all examples"""

    print("\n" + "=" * 70)
    print("STRUCTURED LOGGING EXAMPLES")
    print("=" * 70)

    try:
        example_basic_logging()
        example_error_logging()
        example_exam_events()
        example_api_logging()
        example_database_logging()
        example_cache_logging()
        example_contextual_logging()
        example_structured_data()
        example_performance_monitoring()
        example_security_logging()

        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")

    except Exception as e:
        log_error_with_context(logger, e, "running_examples")
        raise


if __name__ == "__main__":
    run_all_examples()
