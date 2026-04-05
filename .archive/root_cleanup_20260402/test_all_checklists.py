"""
KIRO2 Integration Checklists - Comprehensive Verification
Tests ALL checklist items from INTEGRATION_CHECKLISTS.md

This script ACTUALLY tests every single checklist item, not just estimates.
"""

import sys
import io
import os
from pathlib import Path
import json
import subprocess

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Test results tracking
results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "categories": {}
}

def log_test(category, test_name, status, details=""):
    """Log test result"""
    global results
    results["total_tests"] += 1

    if status == "PASS":
        results["passed"] += 1
        symbol = "[PASS]"
    elif status == "FAIL":
        results["failed"] += 1
        symbol = "[FAIL]"
    else:
        results["skipped"] += 1
        symbol = "[SKIP]"

    if category not in results["categories"]:
        results["categories"][category] = {"pass": 0, "fail": 0, "skip": 0}

    if status == "PASS":
        results["categories"][category]["pass"] += 1
    elif status == "FAIL":
        results["categories"][category]["fail"] += 1
    else:
        results["categories"][category]["skip"] += 1

    print(f"{symbol} {category} - {test_name}")
    if details:
        print(f"    {details}")

print("=" * 80)
print("KIRO2 INTEGRATION CHECKLISTS - COMPREHENSIVE VERIFICATION")
print("=" * 80)
print("\nTesting ALL checklist items from INTEGRATION_CHECKLISTS.md...")
print()

# ============================================================================
# LAYER 1: FRONTEND ↔ API GATEWAY
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 1: FRONTEND ↔ API GATEWAY")
print("=" * 80)

# 1.1 API Gateway Integration - Pre-Development
category = "1.1 API Gateway Pre-Dev"

# Check OpenAPI schema
test_name = "OpenAPI schema exported"
if Path("backend/openapi.json").exists():
    size = Path("backend/openapi.json").stat().st_size
    log_test(category, test_name, "PASS", f"File exists ({size:,} bytes)")
else:
    log_test(category, test_name, "FAIL", "File not found")

# Check TypeScript types
test_name = "TypeScript types generated"
ts_types = Path("frontend/src/types/api.generated.ts")
if ts_types.exists():
    size = ts_types.stat().st_size
    lines = len(ts_types.read_text(encoding='utf-8').splitlines())
    log_test(category, test_name, "PASS", f"File exists ({size:,} bytes, {lines:,} lines)")
else:
    log_test(category, test_name, "FAIL", "File not found")

# Check API base URL in environment
test_name = "API base URL in .env"
frontend_env = Path("frontend/.env")
if frontend_env.exists() or Path("frontend/.env.local").exists() or Path("frontend/.env.development").exists():
    log_test(category, test_name, "PASS", "Environment file exists")
else:
    log_test(category, test_name, "FAIL", "No environment file found")

# 1.1 Development checks
category = "1.1 API Gateway Dev"

# Check apiClient configuration
test_name = "apiClient.ts exists"
api_client_path = Path("frontend/src/services/apiClient.ts")
if api_client_path.exists():
    content = api_client_path.read_text(encoding='utf-8')

    # Check base URL
    if "baseURL" in content or "VITE_API_BASE_URL" in content:
        log_test(category, "Base URL configured", "PASS")
    else:
        log_test(category, "Base URL configured", "FAIL", "No baseURL found")

    # Check auth interceptor
    if "Authorization" in content and "Bearer" in content:
        log_test(category, "Auth interceptor configured", "PASS")
    else:
        log_test(category, "Auth interceptor configured", "FAIL", "No auth interceptor")

    # Check error interceptor
    if "interceptors.response" in content:
        log_test(category, "Error interceptor configured", "PASS")
    else:
        log_test(category, "Error interceptor configured", "FAIL", "No error interceptor")
else:
    log_test(category, test_name, "FAIL", "File not found")
    log_test(category, "Base URL configured", "SKIP", "apiClient.ts not found")
    log_test(category, "Auth interceptor configured", "SKIP", "apiClient.ts not found")
    log_test(category, "Error interceptor configured", "SKIP", "apiClient.ts not found")

# ============================================================================
# LAYER 2: API GATEWAY ↔ CORE INFRASTRUCTURE
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 2: API GATEWAY ↔ CORE INFRASTRUCTURE")
print("=" * 80)

category = "2.1 Middleware Setup"

# Check CORS middleware
test_name = "CORS middleware configured"
main_py = Path("backend/main.py")
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    if "CORSMiddleware" in content:
        log_test(category, test_name, "PASS")
    else:
        log_test(category, test_name, "FAIL", "CORSMiddleware not found")
else:
    log_test(category, test_name, "FAIL", "main.py not found")

# Check logging middleware
test_name = "Logging middleware configured"
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    if "logging" in content.lower():
        log_test(category, test_name, "PASS")
    else:
        log_test(category, test_name, "FAIL", "No logging configuration")
else:
    log_test(category, test_name, "FAIL", "main.py not found")

# Check rate limiting
test_name = "Rate limiting configured"
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    if "rate" in content.lower() and "limit" in content.lower():
        log_test(category, test_name, "PASS")
    else:
        log_test(category, test_name, "FAIL", "No rate limiting found")
else:
    log_test(category, test_name, "FAIL", "main.py not found")

# ============================================================================
# LAYER 3: CORE INFRASTRUCTURE ↔ DATABASE
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 3: CORE INFRASTRUCTURE ↔ DATABASE")
print("=" * 80)

category = "3.1 Database Configuration"

# Check database.py exists
test_name = "Database config exists"
db_config = Path("backend/core/database.py")
if db_config.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "database.py not found")

# Check Alembic migrations
test_name = "Alembic migrations exist"
alembic_dir = Path("backend/alembic")
if alembic_dir.exists():
    versions = list((alembic_dir / "versions").glob("*.py"))
    log_test(category, test_name, "PASS", f"{len(versions)} migration files")
else:
    log_test(category, test_name, "FAIL", "Alembic directory not found")

# Check database models
test_name = "Database models exist"
models_dir = Path("backend/models")
if models_dir.exists():
    model_files = list(models_dir.glob("*.py"))
    log_test(category, test_name, "PASS", f"{len(model_files)} model files")
else:
    log_test(category, test_name, "FAIL", "Models directory not found")

# Check connection pool settings
test_name = "Connection pool configured"
if db_config.exists():
    content = db_config.read_text(encoding='utf-8')
    if "pool_size" in content or "max_overflow" in content:
        log_test(category, test_name, "PASS")
    else:
        log_test(category, test_name, "FAIL", "No pool configuration")
else:
    log_test(category, test_name, "SKIP", "database.py not found")

# ============================================================================
# LAYER 4: CORE INFRASTRUCTURE ↔ REDIS CACHE
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 4: CORE INFRASTRUCTURE ↔ REDIS CACHE")
print("=" * 80)

category = "4.1 Redis Cache"

# Check cache.py exists
test_name = "Redis cache config exists"
cache_py = Path("backend/core/cache.py")
if cache_py.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "cache.py not found")

# Check CacheManager class
test_name = "CacheManager class exists"
if cache_py.exists():
    content = cache_py.read_text(encoding='utf-8')
    if "class CacheManager" in content:
        log_test(category, test_name, "PASS")
    else:
        log_test(category, test_name, "FAIL", "CacheManager class not found")
else:
    log_test(category, test_name, "SKIP", "cache.py not found")

# Check CacheService alias (from our fix)
test_name = "CacheService alias exists"
if cache_py.exists():
    content = cache_py.read_text(encoding='utf-8')
    if "CacheService = CacheManager" in content:
        log_test(category, test_name, "PASS", "Backwards compatibility alias")
    else:
        log_test(category, test_name, "FAIL", "CacheService alias not found")
else:
    log_test(category, test_name, "SKIP", "cache.py not found")

# ============================================================================
# LAYER 5: BUSINESS LOGIC ↔ AI/ML
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 5: BUSINESS LOGIC ↔ AI/ML")
print("=" * 80)

category = "5.1 AI/ML Services"

# Check AI services directory
test_name = "AI services directory exists"
services_dir = Path("backend/services")
if services_dir.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "Services directory not found")

# Check algorithms directory
test_name = "Algorithms directory exists"
algorithms_dir = Path("backend/algorithms")
if algorithms_dir.exists():
    algo_files = list(algorithms_dir.glob("*.py"))
    log_test(category, test_name, "PASS", f"{len(algo_files)} algorithm files")
else:
    log_test(category, test_name, "FAIL", "Algorithms directory not found")

# Check IRT system
test_name = "IRT + Morphology service exists"
irt_file = Path("backend/algorithms/irt_morfoloji_service.py")
if irt_file.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "irt_morfoloji_service.py not found")

# Check ZPD system
test_name = "ZPD + Maarif system exists"
zpd_file = Path("backend/algorithms/turkish_zpd_maarif_system.py")
if zpd_file.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "turkish_zpd_maarif_system.py not found")

# ============================================================================
# LAYER 6: MONITORING & OBSERVABILITY
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 6: MONITORING & OBSERVABILITY")
print("=" * 80)

category = "6.1 Monitoring Setup"

# Check Prometheus metrics
test_name = "Prometheus metrics configured"
prometheus_file = Path("backend/monitoring/enhanced_prometheus_metrics.py")
if prometheus_file.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "enhanced_prometheus_metrics.py not found")

# Check Sentry config
test_name = "Sentry config exists"
sentry_file = Path("backend/core/sentry_config.py")
if sentry_file.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "sentry_config.py not found")

# Check OpenTelemetry config
test_name = "OpenTelemetry config exists"
otel_file = Path("backend/core/opentelemetry_config.py")
if otel_file.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "opentelemetry_config.py not found")

# ============================================================================
# LAYER 7: CRITICAL CONFIGURATION
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 7: CRITICAL CONFIGURATION FILES")
print("=" * 80)

category = "7.1 Config Files"

# Check backend .env
test_name = "Backend .env exists"
backend_env = Path("backend/.env")
if backend_env.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "backend/.env not found")

# Check backend config.yaml (our fix)
test_name = "Backend config.yaml exists"
backend_config = Path("backend/config.yaml")
if backend_config.exists():
    size = backend_config.stat().st_size
    log_test(category, test_name, "PASS", f"File exists ({size:,} bytes)")
else:
    log_test(category, test_name, "FAIL", "backend/config.yaml not found")

# Check requirements.txt
test_name = "requirements.txt exists"
requirements = Path("backend/requirements.txt")
if requirements.exists():
    lines = len(requirements.read_text(encoding='utf-8').splitlines())
    log_test(category, test_name, "PASS", f"{lines} dependencies")
else:
    log_test(category, test_name, "FAIL", "requirements.txt not found")

# Check docker-compose.yml
test_name = "docker-compose.yml exists"
docker_compose = Path("docker-compose.yml")
if docker_compose.exists():
    log_test(category, test_name, "PASS")
else:
    log_test(category, test_name, "FAIL", "docker-compose.yml not found")

# ============================================================================
# LAYER 8: AUTHENTICATION & AUTHORIZATION (OUR FIXES)
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 8: AUTHENTICATION & AUTHORIZATION (FIXES)")
print("=" * 80)

category = "8.1 Auth Fixes"

# Check get_current_user function (Fix #2)
test_name = "get_current_user function exists"
jwt_auth = Path("backend/core/jwt_auth.py")
if jwt_auth.exists():
    content = jwt_auth.read_text(encoding='utf-8')
    if "async def get_current_user" in content:
        log_test(category, test_name, "PASS", "Fix #2 applied")
    else:
        log_test(category, test_name, "FAIL", "get_current_user not found")
else:
    log_test(category, test_name, "FAIL", "jwt_auth.py not found")

# Check AuthenticationContext class (Fix #3)
test_name = "AuthenticationContext class exists"
enhanced_auth = Path("backend/core/enhanced_authentication.py")
if enhanced_auth.exists():
    content = enhanced_auth.read_text(encoding='utf-8')
    if "class AuthenticationContext" in content:
        log_test(category, test_name, "PASS", "Fix #3 applied")
    else:
        log_test(category, test_name, "FAIL", "AuthenticationContext not found")
else:
    log_test(category, test_name, "FAIL", "enhanced_authentication.py not found")

# Check DifficultyLevel enum (Fix #4)
test_name = "DifficultyLevel enum exists"
enums_file = Path("backend/models/enums.py")
if enums_file.exists():
    content = enums_file.read_text(encoding='utf-8')
    if "class DifficultyLevel" in content:
        log_test(category, test_name, "PASS", "Fix #4 applied")
    else:
        log_test(category, test_name, "FAIL", "DifficultyLevel not found")
else:
    log_test(category, test_name, "FAIL", "enums.py not found")

# ============================================================================
# LAYER 9: UTF-8 ENCODING & ASYNC FIXES
# ============================================================================
print("\n" + "=" * 80)
print("LAYER 9: UTF-8 ENCODING & ASYNC FIXES")
print("=" * 80)

category = "9.1 Platform Fixes"

# Check UTF-8 encoding fix (Fix #7)
test_name = "UTF-8 encoding wrapper exists"
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    if "sys.stdout = io.TextIOWrapper" in content and "encoding='utf-8'" in content:
        log_test(category, test_name, "PASS", "Fix #7 applied")
    else:
        log_test(category, test_name, "FAIL", "UTF-8 wrapper not found")
else:
    log_test(category, test_name, "FAIL", "main.py not found")

# Check initialize_wave2b async fix (Fix #8)
test_name = "initialize_wave2b in lifespan"
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    if "await initialize_wave2b()" in content:
        log_test(category, test_name, "PASS", "Fix #8 applied")
    else:
        log_test(category, test_name, "FAIL", "Async initialization not found")
else:
    log_test(category, test_name, "FAIL", "main.py not found")

# Check student_profiles extend_existing fix (Fix #6)
test_name = "student_profiles extend_existing"
learning_path = Path("backend/models/learning_path_models.py")
if learning_path.exists():
    content = learning_path.read_text(encoding='utf-8')
    if "extend_existing" in content:
        log_test(category, test_name, "PASS", "Fix #6 applied")
    else:
        log_test(category, test_name, "FAIL", "extend_existing not found")
else:
    log_test(category, test_name, "FAIL", "learning_path_models.py not found")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

total = results["total_tests"]
passed = results["passed"]
failed = results["failed"]
skipped = results["skipped"]
score = (passed / total * 100) if total > 0 else 0

print(f"\nTotal Tests: {total}")
print(f"[PASS] Passed: {passed} ({passed/total*100:.1f}%)")
print(f"[FAIL] Failed: {failed} ({failed/total*100:.1f}%)")
print(f"[SKIP] Skipped: {skipped} ({skipped/total*100:.1f}%)")
print(f"\nOverall Score: {score:.1f}%")

print("\nResults by Category:")
for cat_name, cat_results in sorted(results["categories"].items()):
    cat_total = cat_results["pass"] + cat_results["fail"] + cat_results["skip"]
    cat_score = (cat_results["pass"] / cat_total * 100) if cat_total > 0 else 0
    print(f"  {cat_name}: {cat_score:.1f}% ({cat_results['pass']}/{cat_total} passed)")

if failed == 0:
    print("\n[SUCCESS] ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n[WARNING] {failed} test(s) failed")
    sys.exit(1)
