"""
Test single request performance with PostgreSQL
"""
import requests
import time

def test_single_request(url):
    """Test single request latency"""
    start = time.time()
    try:
        response = requests.get(url, timeout=10)
        latency = (time.time() - start) * 1000
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        print(f"Latency: {latency:.0f}ms")
        print(f"Content length: {len(response.content)} bytes")
        return latency
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("SINGLE REQUEST LATENCY TEST - PostgreSQL")
    print("=" * 70)
    print()

    # Test health endpoint
    print("[1/4] Testing /health...")
    test_single_request("http://localhost:8000/health")
    print()

    # Test hybrid-codes endpoint
    print("[2/4] Testing /api/v1/learning-style/hybrid-codes...")
    test_single_request("http://localhost:8000/api/v1/learning-style/hybrid-codes")
    print()

    # Test statistics endpoint
    print("[3/4] Testing /api/v1/learning-style/statistics...")
    test_single_request("http://localhost:8000/api/v1/learning-style/statistics")
    print()

    # Test root endpoint
    print("[4/4] Testing /...")
    test_single_request("http://localhost:8000/")
    print()

    print("=" * 70)
    print("[OK] Single request test completed!")
