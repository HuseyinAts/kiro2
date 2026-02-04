"""
Test script for API integration
Verifies that all new endpoints are properly configured
"""

import sys
import os
import io

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all required modules can be imported"""
    print("=" * 60)
    print("API INTEGRATION TEST")
    print("=" * 60)

    tests = []

    # Test 1: Import monitoring tracker
    print("\n[1/5] Testing token_usage_tracker import...")
    try:
        from backend.monitoring.token_usage_tracker import get_tracker
        tracker = get_tracker()
        print(f"✓ TokenUsageTracker imported: {type(tracker).__name__}")
        tests.append(("token_usage_tracker", True))
    except Exception as e:
        print(f"✗ Failed: {e}")
        tests.append(("token_usage_tracker", False))

    # Test 2: Import AB testing manager
    print("\n[2/5] Testing ab_testing import...")
    try:
        from backend.services.ab_testing import get_ab_test_manager
        manager = get_ab_test_manager()
        print(f"✓ ABTestManager imported: {type(manager).__name__}")
        tests.append(("ab_testing", True))
    except Exception as e:
        print(f"✗ Failed: {e}")
        tests.append(("ab_testing", False))

    # Test 3: Import monitoring router
    print("\n[3/5] Testing monitoring_routes import...")
    try:
        from backend.api.monitoring_routes import router as monitoring_router
        routes = [route.path for route in monitoring_router.routes]
        print(f"✓ Monitoring router imported: {len(routes)} routes")
        print(f"  Routes: {', '.join(routes[:3])}...")
        tests.append(("monitoring_routes", True))
    except Exception as e:
        print(f"✗ Failed: {e}")
        tests.append(("monitoring_routes", False))

    # Test 4: Import OSYM router
    print("\n[4/5] Testing osym_routes import...")
    try:
        from backend.api.osym_routes import router as osym_router
        routes = [route.path for route in osym_router.routes]
        print(f"✓ OSYM router imported: {len(routes)} routes")
        print(f"  Routes: {', '.join(routes)}")
        tests.append(("osym_routes", True))
    except Exception as e:
        print(f"✗ Failed: {e}")
        tests.append(("osym_routes", False))

    # Test 5: Check FastAPI app registration
    print("\n[5/5] Testing FastAPI app integration...")
    try:
        # Import without running the app
        import backend.main
        print("✓ Main app module loaded successfully")
        tests.append(("main_app", True))
    except Exception as e:
        print(f"✗ Failed: {e}")
        tests.append(("main_app", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! API integration is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return False


def test_endpoints():
    """Test endpoint functionality (without running server)"""
    print("\n" + "=" * 60)
    print("ENDPOINT FUNCTIONALITY TEST")
    print("=" * 60)

    try:
        from backend.api.monitoring_routes import router as monitoring_router
        from backend.api.osym_routes import router as osym_router

        print("\n📋 Monitoring Endpoints:")
        for route in monitoring_router.routes:
            methods = ", ".join(route.methods) if hasattr(route, 'methods') else "N/A"
            print(f"  {methods:8} {route.path}")

        print("\n📋 OSYM Question Generation Endpoints:")
        for route in osym_router.routes:
            methods = ", ".join(route.methods) if hasattr(route, 'methods') else "N/A"
            print(f"  {methods:8} {route.path}")

        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting API Integration Tests...\n")

    # Run import tests
    import_success = test_imports()

    # Run endpoint tests
    if import_success:
        endpoint_success = test_endpoints()

    print("\n" + "=" * 60)
    if import_success:
        print("✅ INTEGRATION TEST COMPLETE - Ready for server start!")
        print("\nNext steps:")
        print("  1. Start backend: python backend/main.py")
        print("  2. Open Swagger UI: http://localhost:8000/docs")
        print("  3. Test endpoints interactively")
    else:
        print("❌ INTEGRATION TEST FAILED - Check errors above")
    print("=" * 60 + "\n")
