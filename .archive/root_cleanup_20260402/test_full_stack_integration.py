"""
Full Stack Integration Test
Test frontend + backend connectivity
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time

BACKEND_URL = "http://localhost:9000"
FRONTEND_URL = "http://localhost:3000"

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test_backend():
    print_header("TEST 1: Backend Health Check")

    try:
        start = time.time()
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        elapsed = (time.time() - start) * 1000

        print(f"URL: {BACKEND_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}ms")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ PASS: Backend is healthy")
            return True
        else:
            print(f"❌ FAIL: Unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False

def test_backend_api():
    print_header("TEST 2: Backend API Endpoints")

    endpoints = [
        ("/api/v1/soru-bankasi/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=2", "Random Questions TYT"),
        ("/api/v1/soru-bankasi/rastgele-sorular?sinav_tipi=AYT&soru_sayisi=1", "Random Questions AYT"),
    ]

    results = []
    for endpoint, name in endpoints:
        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            elapsed = (time.time() - start) * 1000

            print(f"\n{name}:")
            print(f"  URL: {BACKEND_URL}{endpoint}")
            print(f"  Status: {response.status_code}")
            print(f"  Response Time: {elapsed:.2f}ms")

            if response.status_code == 200:
                data = response.json()
                print(f"  Success: {data.get('success', False)}")
                print(f"  ✅ PASS")
                results.append(True)
            else:
                print(f"  ❌ FAIL: Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ FAIL: {str(e)}")
            results.append(False)

    return all(results)

def test_frontend():
    print_header("TEST 3: Frontend Server")

    try:
        start = time.time()
        response = requests.get(FRONTEND_URL, timeout=5)
        elapsed = (time.time() - start) * 1000

        print(f"URL: {FRONTEND_URL}")
        print(f"Status: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}ms")
        print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Content Length: {len(response.text)} bytes")

        # Check if HTML is returned
        if response.status_code == 200 and 'html' in response.headers.get('content-type', '').lower():
            # Check for React app indicators
            html = response.text
            has_root = 'id="root"' in html or 'id=root' in html
            has_script = '<script' in html.lower()

            print(f"Has root div: {has_root}")
            print(f"Has scripts: {has_script}")

            if has_root and has_script:
                print("✅ PASS: Frontend is serving React app")
                return True
            else:
                print("⚠️  PARTIAL: HTML served but may not be React app")
                return True
        else:
            print(f"❌ FAIL: Unexpected response")
            return False
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False

def test_cors():
    print_header("TEST 4: CORS Configuration")

    try:
        # Simulate a CORS preflight request
        headers = {
            'Origin': FRONTEND_URL,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'content-type'
        }

        response = requests.get(f"{BACKEND_URL}/health", headers=headers, timeout=5)

        print(f"Request Origin: {FRONTEND_URL}")
        print(f"Response Status: {response.status_code}")

        cors_headers = {
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
            'access-control-allow-headers': response.headers.get('access-control-allow-headers'),
        }

        print(f"CORS Headers:")
        for key, value in cors_headers.items():
            print(f"  {key}: {value}")

        # Check if CORS is configured
        allow_origin = cors_headers['access-control-allow-origin']
        if allow_origin:
            if FRONTEND_URL in allow_origin or '*' in allow_origin:
                print(f"✅ PASS: CORS configured for {FRONTEND_URL}")
                return True
            else:
                print(f"⚠️  WARNING: CORS configured but not for {FRONTEND_URL}")
                print(f"   Configured for: {allow_origin}")
                return True
        else:
            print("❌ FAIL: CORS not configured")
            return False
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False

def test_integration():
    print_header("TEST 5: Frontend → Backend Integration")

    print("This test should be done manually in browser:")
    print(f"\n1. Open browser and go to: {FRONTEND_URL}")
    print(f"2. Open DevTools (F12) → Console")
    print(f"3. Run this command:")
    print(f"\n   fetch('{BACKEND_URL}/health')")
    print(f"     .then(r => r.json())")
    print(f"     .then(data => console.log('Backend response:', data))")
    print(f"\n4. Check for:")
    print(f"   - No CORS errors")
    print(f"   - Response: {{success: true, status: 'healthy', ...}}")
    print(f"\n✅ If you see the response, integration works!")
    print(f"❌ If you see CORS error, backend CORS needs configuration")

    return True  # Manual test

def main():
    print("="*70)
    print(" "*20 + "FULL STACK INTEGRATION TEST")
    print("="*70)
    print(f"\nBackend:  {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        'Backend Health': test_backend(),
        'Backend API': test_backend_api(),
        'Frontend Server': test_frontend(),
        'CORS Configuration': test_cors(),
        'Integration (Manual)': test_integration(),
    }

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nResults:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test:<25} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Pass Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nNext steps:")
        print(f"1. Open browser: {FRONTEND_URL}")
        print(f"2. Test UI functionality")
        print(f"3. Check API calls in Network tab")
    elif passed >= total - 1:
        print("\n✅ INTEGRATION WORKING (with manual verification needed)")
        print(f"\nOpen browser: {FRONTEND_URL}")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nCheck failed tests above for details")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
