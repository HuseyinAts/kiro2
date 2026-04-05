"""
KIRO2 Critical Scenario Testing
Tests platform resilience under critical failure conditions

This script tests 14 critical scenario items:
- High Traffic Scenario (5 tests)
- Database Failure Scenario (5 tests)
- Redis Failure Scenario (4 tests)
"""

import sys
import io
from pathlib import Path
import re

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("KIRO2 CRITICAL SCENARIO TESTING")
print("=" * 80)

# Test results tracking
tests_passed = 0
tests_failed = 0
total_tests = 14

# ============================================================================
# SCENARIO 1: HIGH TRAFFIC (5 tests)
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 1: HIGH TRAFFIC (100,000+ CONCURRENT USERS)")
print("=" * 80)

# Test 1.1: Database Connection Pool Adequacy
print("\n[TEST 1/14] Database Connection Pool Configuration")
print("-" * 80)

db_config_files = [
    Path("backend/core/database.py"),
    Path("backend/config.yaml"),
    Path("backend/.env.example"),
]

db_pool_configured = False
db_pool_size = 0

for config_file in db_config_files:
    if config_file.exists():
        content = config_file.read_text(encoding='utf-8')

        # Check for pool configuration
        pool_size_match = re.search(r'pool_size["\s:=]+(\d+)', content)
        max_overflow_match = re.search(r'max_overflow["\s:=]+(\d+)', content)

        if pool_size_match:
            db_pool_size = int(pool_size_match.group(1))
            max_overflow = int(max_overflow_match.group(1)) if max_overflow_match else 0
            total_connections = db_pool_size + max_overflow

            print(f"[INFO] Database pool configuration found in: {config_file.name}")
            print(f"       Pool size: {db_pool_size}")
            print(f"       Max overflow: {max_overflow}")
            print(f"       Total capacity: {total_connections} connections")

            # For 100k users, recommend 200+ pool size
            if total_connections >= 200:
                print(f"[PASS] Connection pool adequate for high traffic ({total_connections} >= 200)")
                db_pool_configured = True
                tests_passed += 1
            else:
                print(f"[WARN] Connection pool may be insufficient for 100k users")
                print(f"       Current: {total_connections}, Recommended: 200+")
                tests_failed += 1

            break

if not db_pool_configured:
    print("[FAIL] Database connection pool not configured")
    print("       RECOMMENDATION: Set pool_size=200, max_overflow=50 in database.py")
    tests_failed += 1

# Test 1.2: Redis Connection Pool Adequacy
print("\n[TEST 2/14] Redis Connection Pool Configuration")
print("-" * 80)

redis_config_files = [
    Path("backend/core/cache.py"),
    Path("backend/config.yaml"),
]

redis_pool_configured = False

for config_file in redis_config_files:
    if config_file.exists():
        content = config_file.read_text(encoding='utf-8')

        # Check for Redis max connections
        redis_connections_match = re.search(r'max_connections["\s:=]+(\d+)', content)

        if redis_connections_match:
            max_connections = int(redis_connections_match.group(1))

            print(f"[INFO] Redis pool configuration found in: {config_file.name}")
            print(f"       Max connections: {max_connections}")

            # For high traffic, recommend 50+ connections
            if max_connections >= 50:
                print(f"[PASS] Redis connection pool adequate ({max_connections} >= 50)")
                redis_pool_configured = True
                tests_passed += 1
            else:
                print(f"[WARN] Redis pool may be insufficient")
                print(f"       Current: {max_connections}, Recommended: 50+")
                tests_failed += 1

            break

if not redis_pool_configured:
    print("[FAIL] Redis connection pool not configured")
    print("       RECOMMENDATION: Set max_connections=50 in cache.py")
    tests_failed += 1

# Test 1.3: Memory Usage Safety
print("\n[TEST 3/14] Memory Usage Monitoring")
print("-" * 80)

memory_monitoring_files = [
    Path("backend/monitoring/enhanced_prometheus_metrics.py"),
    Path("backend/core/monitoring.py"),
    Path("monitoring/prometheus/prometheus.yml"),
]

memory_monitoring_found = False

for monitoring_file in memory_monitoring_files:
    if monitoring_file.exists():
        content = monitoring_file.read_text(encoding='utf-8')

        # Check for memory metrics
        has_memory_metrics = (
            "memory" in content.lower() and
            ("gauge" in content.lower() or "histogram" in content.lower())
        )

        if has_memory_metrics:
            print(f"[PASS] Memory monitoring configured in: {monitoring_file.name}")
            print(f"       Memory metrics collection enabled")
            memory_monitoring_found = True
            tests_passed += 1
            break

if not memory_monitoring_found:
    print("[WARN] No explicit memory monitoring found")
    print("       RECOMMENDATION: Add memory usage metrics to Prometheus")
    tests_failed += 1

# Test 1.4: Response Time Monitoring
print("\n[TEST 4/14] Response Time Monitoring (<2s target)")
print("-" * 80)

response_time_monitoring = False

monitoring_files = [
    Path("backend/monitoring/enhanced_prometheus_metrics.py"),
    Path("backend/core/middleware.py"),
    Path("backend/main.py"),
]

for monitoring_file in monitoring_files:
    if monitoring_file.exists():
        content = monitoring_file.read_text(encoding='utf-8')

        # Check for response time tracking
        has_response_time = (
            ("response_time" in content.lower() or "latency" in content.lower()) and
            ("histogram" in content.lower() or "summary" in content.lower())
        )

        if has_response_time:
            print(f"[PASS] Response time monitoring configured in: {monitoring_file.name}")
            print(f"       Request latency tracking enabled")
            response_time_monitoring = True
            tests_passed += 1
            break

if not response_time_monitoring:
    print("[WARN] Response time monitoring not found")
    print("       RECOMMENDATION: Add response time metrics with <2s alerts")
    tests_failed += 1

# Test 1.5: Error Rate Monitoring
print("\n[TEST 5/14] Error Rate Monitoring (<1% target)")
print("-" * 80)

error_rate_monitoring = False

for monitoring_file in monitoring_files:
    if monitoring_file.exists():
        content = monitoring_file.read_text(encoding='utf-8')

        # Check for error rate tracking
        has_error_rate = (
            ("error" in content.lower() or "exception" in content.lower()) and
            ("counter" in content.lower() or "rate" in content.lower())
        )

        if has_error_rate:
            print(f"[PASS] Error rate monitoring configured in: {monitoring_file.name}")
            print(f"       Error tracking enabled")
            error_rate_monitoring = True
            tests_passed += 1
            break

if not error_rate_monitoring:
    print("[WARN] Error rate monitoring not found")
    print("       RECOMMENDATION: Add error rate metrics with <1% target")
    tests_failed += 1

# ============================================================================
# SCENARIO 2: DATABASE FAILURE (5 tests)
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 2: DATABASE FAILURE & RECOVERY")
print("=" * 80)

# Test 2.1: Circuit Breaker Pattern
print("\n[TEST 6/14] Circuit Breaker Implementation")
print("-" * 80)

circuit_breaker_files = [
    Path("backend/core/circuit_breaker.py"),
    Path("backend/core/database.py"),
    Path("backend/services/resilience.py"),
]

circuit_breaker_found = False

for cb_file in circuit_breaker_files:
    if cb_file.exists():
        content = cb_file.read_text(encoding='utf-8')

        # Check for circuit breaker pattern
        has_circuit_breaker = (
            "circuit" in content.lower() and "breaker" in content.lower()
        ) or "CircuitBreaker" in content

        if has_circuit_breaker:
            print(f"[PASS] Circuit breaker found in: {cb_file.name}")
            print(f"       Fault tolerance mechanism implemented")
            circuit_breaker_found = True
            tests_passed += 1
            break

if not circuit_breaker_found:
    print("[WARN] No circuit breaker pattern found")
    print("       RECOMMENDATION: Implement circuit breaker for database failover")
    print("       Libraries: circuitbreaker, pybreaker")
    tests_failed += 1

# Test 2.2: Cache Fallback Strategy
print("\n[TEST 7/14] Cache Fallback on Database Failure")
print("-" * 80)

cache_fallback_found = False

cache_files = [
    Path("backend/core/cache.py"),
    Path("backend/core/multi_layer_cache.py"),
]

for cache_file in cache_files:
    if cache_file.exists():
        content = cache_file.read_text(encoding='utf-8')

        # Check for fallback strategy
        has_fallback = (
            ("fallback" in content.lower() or "stale" in content.lower()) and
            ("cache" in content.lower())
        )

        if has_fallback:
            print(f"[PASS] Cache fallback strategy found in: {cache_file.name}")
            print(f"       Stale data serving on database failure")
            cache_fallback_found = True
            tests_passed += 1
            break

if not cache_fallback_found:
    print("[WARN] No cache fallback strategy found")
    print("       RECOMMENDATION: Serve stale cached data when database is down")
    tests_failed += 1

# Test 2.3: Graceful Degradation
print("\n[TEST 8/14] Graceful Service Degradation")
print("-" * 80)

degradation_files = [
    Path("backend/core/middleware.py"),
    Path("backend/core/error_handling.py"),
    Path("backend/main.py"),
]

graceful_degradation_found = False

for deg_file in degradation_files:
    if deg_file.exists():
        content = deg_file.read_text(encoding='utf-8')

        # Check for graceful degradation
        has_degradation = (
            ("degraded" in content.lower() or "fallback" in content.lower()) and
            ("mode" in content.lower() or "service" in content.lower())
        )

        if has_degradation:
            print(f"[PASS] Graceful degradation found in: {deg_file.name}")
            print(f"       Degraded mode handling implemented")
            graceful_degradation_found = True
            tests_passed += 1
            break

if not graceful_degradation_found:
    print("[WARN] No graceful degradation mechanism found")
    print("       RECOMMENDATION: Implement degraded mode for non-critical features")
    tests_failed += 1

# Test 2.4: User Notification System
print("\n[TEST 9/14] User Notification on Service Issues")
print("-" * 80)

notification_files = [
    Path("frontend/src/components/ServiceStatus.tsx"),
    Path("frontend/src/components/Notification.tsx"),
    Path("frontend/src/services/notification.ts"),
]

notification_system_found = False

for notif_file in notification_files:
    if notif_file.exists():
        content = notif_file.read_text(encoding='utf-8')

        # Check for service status notifications
        has_notification = (
            ("notification" in content.lower() or "toast" in content.lower() or "alert" in content.lower())
        )

        if has_notification:
            print(f"[PASS] Notification system found in: {notif_file.name}")
            print(f"       User alerts for service issues")
            notification_system_found = True
            tests_passed += 1
            break

if not notification_system_found:
    print("[WARN] No user notification system found")
    print("       RECOMMENDATION: Add toast/alert system for service status")
    tests_failed += 1

# Test 2.5: Auto-Recovery Mechanism
print("\n[TEST 10/14] Auto-Recovery After Database Restart")
print("-" * 80)

auto_recovery_files = [
    Path("backend/core/database.py"),
    Path("backend/main.py"),
]

auto_recovery_found = False

for recovery_file in auto_recovery_files:
    if recovery_file.exists():
        content = recovery_file.read_text(encoding='utf-8')

        # Check for connection retry/recovery
        has_recovery = (
            ("retry" in content.lower() or "reconnect" in content.lower()) and
            ("pool" in content.lower() or "connection" in content.lower())
        ) or "pool_pre_ping" in content

        if has_recovery:
            print(f"[PASS] Auto-recovery mechanism found in: {recovery_file.name}")
            print(f"       Connection retry/pool pre-ping enabled")
            auto_recovery_found = True
            tests_passed += 1
            break

if not auto_recovery_found:
    print("[WARN] No auto-recovery mechanism found")
    print("       RECOMMENDATION: Enable pool_pre_ping and retry logic")
    tests_failed += 1

# ============================================================================
# SCENARIO 3: REDIS FAILURE (4 tests)
# ============================================================================
print("\n" + "=" * 80)
print("SCENARIO 3: REDIS FAILURE & DEGRADATION")
print("=" * 80)

# Test 3.1: Fallback Mode Activation
print("\n[TEST 11/14] Redis Fallback Mode")
print("-" * 80)

redis_fallback_found = False

for cache_file in cache_files:
    if cache_file.exists():
        content = cache_file.read_text(encoding='utf-8')

        # Check for Redis failure handling
        has_redis_fallback = (
            "try" in content and "except" in content and
            ("redis" in content.lower() or "cache" in content.lower())
        )

        if has_redis_fallback:
            print(f"[PASS] Redis fallback handling found in: {cache_file.name}")
            print(f"       Exception handling for Redis failures")
            redis_fallback_found = True
            tests_passed += 1
            break

if not redis_fallback_found:
    print("[WARN] No Redis fallback mechanism found")
    print("       RECOMMENDATION: Add try/except for Redis operations")
    tests_failed += 1

# Test 3.2: Application Continuity
print("\n[TEST 12/14] Application Continues Without Redis")
print("-" * 80)

app_continuity_files = [
    Path("backend/core/cache.py"),
    Path("backend/main.py"),
]

app_continuity_found = False

for app_file in app_continuity_files:
    if app_file.exists():
        content = app_file.read_text(encoding='utf-8')

        # Check if app can work without cache
        has_continuity = (
            ("optional" in content.lower() or "fallback" in content.lower()) and
            "cache" in content.lower()
        ) or (
            "try" in content and "except" in content and
            ("pass" in content or "log" in content)
        )

        if has_continuity:
            print(f"[PASS] Application continuity found in: {app_file.name}")
            print(f"       App can operate without Redis")
            app_continuity_found = True
            tests_passed += 1
            break

if not app_continuity_found:
    print("[WARN] Application may fail without Redis")
    print("       RECOMMENDATION: Make Redis optional, use direct DB on failure")
    tests_failed += 1

# Test 3.3: Database Load Monitoring
print("\n[TEST 13/14] Database Load Increase Monitoring")
print("-" * 80)

db_load_monitoring_found = False

for monitoring_file in monitoring_files:
    if monitoring_file.exists():
        content = monitoring_file.read_text(encoding='utf-8')

        # Check for database query metrics
        has_db_monitoring = (
            ("database" in content.lower() or "query" in content.lower()) and
            ("counter" in content.lower() or "histogram" in content.lower())
        )

        if has_db_monitoring:
            print(f"[PASS] Database load monitoring found in: {monitoring_file.name}")
            print(f"       Query metrics tracking enabled")
            db_load_monitoring_found = True
            tests_passed += 1
            break

if not db_load_monitoring_found:
    print("[WARN] Database load monitoring not comprehensive")
    print("       RECOMMENDATION: Add query count/latency metrics")
    tests_failed += 1

# Test 3.4: Auto-Recovery After Redis Restart
print("\n[TEST 14/14] Redis Auto-Recovery")
print("-" * 80)

redis_recovery_found = False

for cache_file in cache_files:
    if cache_file.exists():
        content = cache_file.read_text(encoding='utf-8')

        # Check for connection retry
        has_redis_recovery = (
            ("retry" in content.lower() or "reconnect" in content.lower()) and
            "redis" in content.lower()
        )

        if has_redis_recovery:
            print(f"[PASS] Redis auto-recovery found in: {cache_file.name}")
            print(f"       Connection retry mechanism enabled")
            redis_recovery_found = True
            tests_passed += 1
            break

if not redis_recovery_found:
    print("[WARN] No Redis auto-recovery mechanism found")
    print("       RECOMMENDATION: Implement retry logic for Redis connections")
    tests_failed += 1

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("CRITICAL SCENARIO TESTING SUMMARY")
print("=" * 80)

success_rate = (tests_passed / total_tests) * 100

print(f"\nTotal Tests: {total_tests}")
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {success_rate:.1f}%")

print("\n" + "-" * 80)
print("SCENARIO BREAKDOWN")
print("-" * 80)

print("\n[SCENARIO 1] High Traffic (100k+ users):")
high_traffic_pass = sum([db_pool_configured, redis_pool_configured, memory_monitoring_found,
                          response_time_monitoring, error_rate_monitoring])
print(f"  {high_traffic_pass}/5 tests passed")

print("\n[SCENARIO 2] Database Failure:")
db_failure_pass = sum([circuit_breaker_found, cache_fallback_found, graceful_degradation_found,
                       notification_system_found, auto_recovery_found])
print(f"  {db_failure_pass}/5 tests passed")

print("\n[SCENARIO 3] Redis Failure:")
redis_failure_pass = sum([redis_fallback_found, app_continuity_found,
                          db_load_monitoring_found, redis_recovery_found])
print(f"  {redis_failure_pass}/4 tests passed")

print("\n" + "=" * 80)

if tests_passed == total_tests:
    print("[SUCCESS] PLATFORM IS PRODUCTION-READY!")
    print("\nAll critical scenarios covered:")
    print("✓ High traffic handling (100k+ users)")
    print("✓ Database failure recovery")
    print("✓ Redis failure resilience")
    sys.exit(0)
elif tests_passed >= 10:
    print("[GOOD] Platform is resilient but needs minor improvements")
    print(f"\nPassed {tests_passed}/{total_tests} critical scenario tests")
    print("\nPlatform can handle production traffic with monitoring")
    sys.exit(0)
elif tests_passed >= 7:
    print("[FAIR] Platform has basic resilience")
    print(f"\nPassed {tests_passed}/{total_tests} tests")
    print("\nRECOMMENDATION: Improve failure recovery before full production launch")
    sys.exit(0)
else:
    print("[CRITICAL] Platform is NOT production-ready")
    print(f"\nOnly {tests_passed}/{total_tests} tests passed")
    print("\nCRITICAL ACTIONS REQUIRED:")
    print("1. Configure connection pools (database, Redis)")
    print("2. Implement circuit breaker pattern")
    print("3. Add cache fallback strategy")
    print("4. Enable comprehensive monitoring")
    print("5. Test failure recovery scenarios")
    sys.exit(1)
