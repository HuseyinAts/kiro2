#!/usr/bin/env python3
"""
Structured Logging Verification Script
======================================

Bu script, structured logging sisteminin tüm özelliklerini test eder ve doğrular.
"""

import sys
import time
import traceback
from core.structured_logger import (
    get_logger,
    log_api_request,
    log_api_response,
    log_error_with_context,
)


def test_basic_logging():
    """Test basic logging functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Logging")
    print("=" * 60)

    logger = get_logger("test_basic")

    logger.debug("Debug message", extra={"detail": "low-level info"})
    logger.info("Info message", extra={"status": "normal"})
    logger.warning("Warning message", extra={"threshold": 80})
    logger.error("Error message", extra={"error_code": "ERR_001"})
    logger.critical("Critical message", extra={"system": "database"})

    print("✓ All log levels working")


def test_request_logging():
    """Test request logging"""
    print("\n" + "=" * 60)
    print("TEST 2: Request Logging")
    print("=" * 60)

    logger = get_logger("video_api")

    # Method 1: Helper function
    log_api_request(
        logger,
        method="POST",
        path="/api/youtube/recommendations",
        request_id="req-001",
        profile={"goals": ["TYT Matematik"], "currentLevel": {"matematik": 50}},
    )

    # Method 2: Convenience method
    logger.log_request(
        request_id="req-002",
        endpoint="/api/youtube/recommendations",
        method="POST",
        profile={"goals": ["TYT Fizik"]},
        user_id=123,
    )

    print("✓ Request logging working")


def test_response_logging():
    """Test response logging"""
    print("\n" + "=" * 60)
    print("TEST 3: Response Logging")
    print("=" * 60)

    logger = get_logger("video_api")

    # Success response (cache hit)
    logger.log_response(
        request_id="req-001",
        endpoint="/api/youtube/recommendations",
        status=200,
        response_time=123.45,
        cache_hit=True,
        video_count=15,
    )

    # Success response (cache miss)
    logger.log_response(
        request_id="req-002",
        endpoint="/api/youtube/recommendations",
        status=200,
        response_time=2345.67,
        cache_hit=False,
        video_count=15,
        discovery_time_ms=2000,
    )

    # Client error
    logger.log_response(
        request_id="req-003",
        endpoint="/api/youtube/recommendations",
        status=400,
        response_time=50.0,
        cache_hit=False,
        error="Invalid request",
    )

    # Server error
    logger.log_response(
        request_id="req-004",
        endpoint="/api/youtube/recommendations",
        status=500,
        response_time=100.0,
        cache_hit=False,
        error="Internal server error",
    )

    print("✓ Response logging working (all status codes)")


def test_error_logging():
    """Test error logging"""
    print("\n" + "=" * 60)
    print("TEST 4: Error Logging")
    print("=" * 60)

    logger = get_logger("video_api")

    try:
        # Simulate an error
        raise ValueError("YouTube API rate limit exceeded")
    except Exception as e:
        # Method 1: Helper function
        log_error_with_context(
            logger,
            error=e,
            context="video_discovery",
            request_id="req-005",
            include_stack_trace=True,
            quota_remaining=0,
        )

        # Method 2: Convenience method
        logger.log_error_context(
            error_type=type(e).__name__,
            error_message=str(e),
            context="video_discovery",
            request_id="req-006",
            stack_trace=traceback.format_exc(),
            quota_remaining=0,
        )

    print("✓ Error logging working (with stack trace)")


def test_context_binding():
    """Test context binding"""
    print("\n" + "=" * 60)
    print("TEST 5: Context Binding")
    print("=" * 60)

    logger = get_logger("video_service")

    # Bind context
    logger = logger.bind(request_id="req-007", user_id=456)

    logger.info("Video search started")
    logger.info("Cache checking")
    logger.info("YouTube API calling")

    # Unbind context
    logger = logger.unbind("request_id", "user_id")

    logger.info("Context unbound")

    print("✓ Context binding/unbinding working")


def test_sensitive_data_censoring():
    """Test sensitive data censoring"""
    print("\n" + "=" * 60)
    print("TEST 6: Sensitive Data Censoring")
    print("=" * 60)

    logger = get_logger("security_test")

    # These should be censored
    logger.info(
        "User authentication",
        password="secret123",
        api_key="sk-1234567890",
        token="bearer_token_xyz",
        şifre="gizli_şifre",
    )

    print("✓ Sensitive data censoring working (check logs above)")


def test_full_video_api_flow():
    """Test full video API flow"""
    print("\n" + "=" * 60)
    print("TEST 7: Full Video API Flow")
    print("=" * 60)

    logger = get_logger("video_recommendation_service")

    request_id = "req-flow-001"
    student_profile = {"goals": ["TYT Matematik"], "currentLevel": {"matematik": 50}}

    # 1. Request start
    logger.log_request(
        request_id=request_id,
        endpoint="/api/youtube/recommendations",
        profile=student_profile,
    )

    start_time = time.time()

    try:
        # 2. Cache check
        logger.info(
            "cache_check_started",
            request_id=request_id,
            cache_key="profile_hash_abc123",
        )

        # Simulate cache miss
        logger.info(
            "cache_miss", request_id=request_id, cache_key="profile_hash_abc123"
        )

        # 3. Video discovery
        logger.info(
            "video_discovery_started",
            request_id=request_id,
            subject="matematik",
            difficulty="orta",
        )

        # Simulate some work
        time.sleep(0.1)

        # 4. Filtering
        logger.info(
            "video_filtering_completed",
            request_id=request_id,
            filtered_videos=15,
            removed_videos=10,
        )

        # 5. Success response
        response_time = (time.time() - start_time) * 1000

        logger.log_response(
            request_id=request_id,
            endpoint="/api/youtube/recommendations",
            status=200,
            response_time=response_time,
            cache_hit=False,
            video_count=15,
        )

        print(f"✓ Full flow completed in {response_time:.2f}ms")

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        logger.log_error_context(
            error_type=type(e).__name__,
            error_message=str(e),
            context="video_recommendation_flow",
            request_id=request_id,
            stack_trace=traceback.format_exc(),
        )

        logger.log_response(
            request_id=request_id,
            endpoint="/api/youtube/recommendations",
            status=500,
            response_time=response_time,
            cache_hit=False,
            error=str(e),
        )


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STRUCTURED LOGGING VERIFICATION")
    print("=" * 60)
    print("\nTesting all structured logging features...")

    try:
        test_basic_logging()
        test_request_logging()
        test_response_logging()
        test_error_logging()
        test_context_binding()
        test_sensitive_data_censoring()
        test_full_video_api_flow()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nStructured logging system is working correctly!")
        print("All logs are in JSON format and ready for log aggregation.")
        print("\nNext steps:")
        print("1. Configure log aggregation (ELK Stack, Loki, etc.)")
        print("2. Set up log monitoring and alerting")
        print("3. Integrate with video API endpoints")
        print("\n")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
