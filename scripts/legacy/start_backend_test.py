"""
Quick backend startup test
Tests if the server can start and endpoints are accessible
"""

import subprocess
import time
import requests
import sys
import io

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_endpoints():
    """Test the new endpoints"""
    base_url = "http://localhost:8000"

    print("\n" + "="*60)
    print("ENDPOINT TESTING")
    print("="*60)

    endpoints = [
        ("GET", "/health", "Main health check"),
        ("GET", "/api/monitoring/health", "Monitoring health check"),
        ("GET", "/api/osym/health", "OSYM health check"),
        ("GET", "/api/monitoring/token-stats?days=7", "Token statistics"),
        ("GET", "/api/monitoring/token-projection", "Token projection"),
    ]

    results = []

    for method, path, description in endpoints:
        url = base_url + path
        print(f"\n[TEST] {description}")
        print(f"  → {method} {path}")

        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)

            status = "✅ PASS" if response.status_code == 200 else f"⚠️  {response.status_code}"
            print(f"  Status: {status}")

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    print(f"  Response keys: {list(data.keys())[:5]}")
                results.append((description, True))
            else:
                print(f"  Error: {response.text[:100]}")
                results.append((description, False))

        except requests.exceptions.ConnectionError:
            print(f"  ❌ FAIL - Connection refused (is server running?)")
            results.append((description, False))
        except Exception as e:
            print(f"  ❌ FAIL - {str(e)}")
            results.append((description, False))

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for desc, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {desc}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")

    return passed == total


if __name__ == "__main__":
    print("🚀 Backend Endpoint Testing")
    print("\nNOTE: Make sure backend is running on http://localhost:8000")
    print("Start with: python backend/main.py\n")

    input("Press Enter when backend is ready...")

    success = test_endpoints()

    if success:
        print("\n🎉 All endpoint tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the backend logs.")
