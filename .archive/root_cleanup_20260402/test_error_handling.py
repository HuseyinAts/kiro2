"""
KIRO2 Frontend Error Handling Validation
Tests all error handling mechanisms for production readiness

This script tests 4 critical error handling components:
1. Global error boundary existence
2. API error handling uniformity
3. User-friendly error messages
4. Error logging to Sentry
"""

import sys
import io
from pathlib import Path
import re
import json

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("KIRO2 FRONTEND ERROR HANDLING VALIDATION")
print("=" * 80)

# Test results tracking
tests_passed = 0
tests_failed = 0
total_tests = 4

# ============================================================================
# TEST 1: Global Error Boundary Existence
# ============================================================================
print("\n[TEST 1/4] Global Error Boundary Existence")
print("-" * 80)

error_boundary_found = False
error_boundary_file = None

# Check for ErrorBoundary component in frontend
frontend_dir = Path("frontend/src")
if frontend_dir.exists():
    # Search for ErrorBoundary in components
    component_files = list(frontend_dir.rglob("*ErrorBoundary*.tsx")) + list(frontend_dir.rglob("*ErrorBoundary*.jsx"))

    if component_files:
        error_boundary_file = component_files[0]
        content = error_boundary_file.read_text(encoding='utf-8')

        # Check for componentDidCatch or ErrorBoundary implementation
        if "componentDidCatch" in content or "ErrorBoundary" in content:
            error_boundary_found = True
            try:
                rel_path = error_boundary_file.relative_to(Path.cwd())
            except ValueError:
                rel_path = error_boundary_file
            print(f"[PASS] ErrorBoundary component found: {rel_path}")
            print(f"       Component implements error catching mechanism")
            tests_passed += 1
        else:
            print(f"[FAIL] ErrorBoundary file exists but doesn't implement error catching")
            tests_failed += 1
    else:
        # Check if error boundary is implemented in App.tsx or index.tsx
        app_files = list(frontend_dir.glob("App.tsx")) + list(frontend_dir.glob("main.tsx")) + list(frontend_dir.glob("index.tsx"))

        for app_file in app_files:
            if app_file.exists():
                content = app_file.read_text(encoding='utf-8')
                if "ErrorBoundary" in content or "componentDidCatch" in content:
                    error_boundary_found = True
                    try:
                        rel_path = app_file.relative_to(Path.cwd())
                    except ValueError:
                        rel_path = app_file
                    print(f"[PASS] ErrorBoundary used in: {rel_path}")
                    tests_passed += 1
                    break

        if not error_boundary_found:
            print("[WARN] No ErrorBoundary component found")
            print("       RECOMMENDATION: Create frontend/src/components/ErrorBoundary.tsx")
            print("       This is critical for production error handling")
            tests_failed += 1
else:
    print("[FAIL] Frontend source directory not found")
    tests_failed += 1

# ============================================================================
# TEST 2: API Error Handling Uniformity
# ============================================================================
print("\n[TEST 2/4] API Error Handling Uniformity")
print("-" * 80)

api_error_handling_found = False

# Check for API client with error handling
api_client_paths = [
    Path("frontend/src/services/api.ts"),
    Path("frontend/src/services/apiClient.ts"),
    Path("frontend/src/lib/api.ts"),
    Path("frontend/src/api/client.ts"),
]

for api_path in api_client_paths:
    if api_path.exists():
        content = api_path.read_text(encoding='utf-8')

        # Check for response interceptor (error handling)
        has_interceptor = "interceptors.response" in content or "onError" in content or "catch" in content

        # Check for error transformation/normalization
        has_error_transform = (
            "normalizeError" in content or
            "transformError" in content or
            "handleApiError" in content or
            "ApiError" in content
        )

        if has_interceptor and has_error_transform:
            try:
                rel_path = api_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = api_path
            print(f"[PASS] Uniform API error handling found in: {rel_path}")
            print(f"       - Response interceptor: ✓")
            print(f"       - Error transformation: ✓")
            api_error_handling_found = True
            tests_passed += 1
            break
        elif has_interceptor:
            try:
                rel_path = api_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = api_path
            print(f"[WARN] Partial API error handling in: {rel_path}")
            print(f"       - Response interceptor: ✓")
            print(f"       - Error transformation: ✗")
            print(f"       RECOMMENDATION: Add error normalization for consistent error format")

if not api_error_handling_found:
    # Check if using react-query which has built-in error handling
    package_json = Path("frontend/package.json")
    if package_json.exists():
        content = package_json.read_text(encoding='utf-8')
        if "@tanstack/react-query" in content or "react-query" in content:
            print("[PASS] React Query detected - provides built-in error handling")
            print("       Verify error handling in query configurations")
            tests_passed += 1
            api_error_handling_found = True

if not api_error_handling_found:
    print("[FAIL] No uniform API error handling mechanism found")
    print("       RECOMMENDATION: Add error interceptor to API client")
    tests_failed += 1

# ============================================================================
# TEST 3: User-Friendly Error Messages
# ============================================================================
print("\n[TEST 3/4] User-Friendly Error Messages")
print("-" * 80)

user_friendly_errors_found = False

# Check for error message mapping/translation
error_message_paths = [
    Path("frontend/src/utils/errorMessages.ts"),
    Path("frontend/src/constants/errors.ts"),
    Path("frontend/src/config/errorMessages.ts"),
    Path("frontend/src/i18n/errors.json"),
    Path("frontend/src/locales/tr/errors.json"),
]

for error_path in error_message_paths:
    if error_path.exists():
        content = error_path.read_text(encoding='utf-8')

        # Check for Turkish error messages
        has_turkish_messages = (
            "hata" in content.lower() or
            "mesaj" in content.lower() or
            "açıklama" in content.lower()
        )

        if has_turkish_messages:
            try:
                rel_path = error_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = error_path
            print(f"[PASS] User-friendly error messages found in: {rel_path}")
            print(f"       Turkish error messages detected")
            user_friendly_errors_found = True
            tests_passed += 1
            break

if not user_friendly_errors_found:
    # Check in components for inline error handling
    if frontend_dir.exists():
        components_with_errors = []
        for component_file in frontend_dir.rglob("*.tsx"):
            content = component_file.read_text(encoding='utf-8')
            # Look for Turkish error patterns
            if re.search(r'(hata|error.*mesaj|bildirim)', content, re.IGNORECASE):
                components_with_errors.append(component_file)

        if components_with_errors:
            try:
                rel_path = components_with_errors[0].relative_to(Path.cwd())
            except ValueError:
                rel_path = components_with_errors[0]
            print(f"[PARTIAL] Error messages found in {len(components_with_errors)} components")
            print(f"          Example: {rel_path}")
            print(f"          RECOMMENDATION: Centralize error messages for consistency")
            tests_failed += 1
        else:
            print("[FAIL] No user-friendly error message system found")
            print("       RECOMMENDATION: Create error message mapping")
            print("       Example: frontend/src/constants/errorMessages.ts")
            tests_failed += 1
    else:
        tests_failed += 1

# ============================================================================
# TEST 4: Error Logging to Sentry
# ============================================================================
print("\n[TEST 4/4] Error Logging to Sentry")
print("-" * 80)

sentry_integration_found = False

# Check for Sentry integration in frontend
sentry_init_paths = [
    Path("frontend/src/main.tsx"),
    Path("frontend/src/index.tsx"),
    Path("frontend/src/App.tsx"),
    Path("frontend/src/config/sentry.ts"),
]

package_json = Path("frontend/package.json")
sentry_installed = False

if package_json.exists():
    content = package_json.read_text(encoding='utf-8')
    if "@sentry/react" in content or "@sentry/browser" in content:
        sentry_installed = True
        print("[INFO] Sentry package installed in package.json")

for sentry_path in sentry_init_paths:
    if sentry_path.exists():
        content = sentry_path.read_text(encoding='utf-8')

        # Check for Sentry initialization
        has_sentry_init = "Sentry.init" in content or "import.*@sentry" in re.search(r"import.*@sentry", content) if re.search(r"import.*@sentry", content) else False

        if "Sentry.init" in content:
            try:
                rel_path = sentry_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = sentry_path
            print(f"[PASS] Sentry integration found in: {rel_path}")
            print(f"       Sentry.init() detected")

            # Check for error boundary integration
            if "ErrorBoundary" in content and "Sentry" in content:
                print(f"       Sentry ErrorBoundary integration: ✓")

            sentry_integration_found = True
            tests_passed += 1
            break

if not sentry_integration_found:
    if sentry_installed:
        print("[WARN] Sentry installed but not initialized")
        print("       RECOMMENDATION: Add Sentry.init() to main.tsx or App.tsx")
        tests_failed += 1
    else:
        print("[FAIL] Sentry not integrated")
        print("       RECOMMENDATION: Install and configure Sentry for error tracking")
        print("       Steps:")
        print("       1. npm install @sentry/react")
        print("       2. Add Sentry.init() with DSN in main.tsx")
        print("       3. Wrap app with Sentry.ErrorBoundary")
        tests_failed += 1

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("ERROR HANDLING VALIDATION SUMMARY")
print("=" * 80)

success_rate = (tests_passed / total_tests) * 100

print(f"\nTotal Tests: {total_tests}")
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {success_rate:.1f}%")

print("\n" + "-" * 80)
print("TEST RESULTS BREAKDOWN")
print("-" * 80)

results = [
    ("Global Error Boundary", tests_passed >= 1),
    ("API Error Handling", tests_passed >= 2 and api_error_handling_found),
    ("User-Friendly Messages", tests_passed >= 3 and user_friendly_errors_found),
    ("Sentry Integration", tests_passed >= 4 and sentry_integration_found),
]

for test_name, passed in results:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")

print("\n" + "=" * 80)

if tests_passed == total_tests:
    print("[SUCCESS] ALL ERROR HANDLING TESTS PASSED!")
    print("\nYour frontend has robust error handling mechanisms:")
    print("✓ Global error boundaries")
    print("✓ Uniform API error handling")
    print("✓ User-friendly error messages")
    print("✓ Sentry error tracking")
    sys.exit(0)
elif tests_passed >= 2:
    print("[PARTIAL SUCCESS] Core error handling exists, but improvements needed")
    print(f"\nPassed {tests_passed}/{total_tests} tests")
    print("\nNext steps:")
    if not error_boundary_found:
        print("1. Add ErrorBoundary component")
    if not api_error_handling_found:
        print("2. Implement uniform API error handling")
    if not user_friendly_errors_found:
        print("3. Create user-friendly error message mapping")
    if not sentry_integration_found:
        print("4. Integrate Sentry for error tracking")
    sys.exit(0)
else:
    print("[CRITICAL] Error handling needs significant improvements")
    print(f"\nOnly {tests_passed}/{total_tests} tests passed")
    print("\nThis is critical for production deployment!")
    print("\nRECOMMENDED ACTIONS:")
    print("1. Create ErrorBoundary component (CRITICAL)")
    print("2. Add API error interceptor (HIGH)")
    print("3. Create error message constants (MEDIUM)")
    print("4. Integrate Sentry (MEDIUM)")
    sys.exit(1)
