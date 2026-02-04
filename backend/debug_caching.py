"""Debug caching issue"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import asyncio
import requests
from core.redis_cache import get_cache


async def test_redis_directly():
    print("=" * 70)
    print("TEST 1: Direct Redis Testing")
    print("=" * 70)

    cache = get_cache()
    print(f"Cache connected: {cache.is_connected()}")

    # Test SET
    result = cache.set("test:direct", {"message": "Hello from test"}, ttl=60)
    print(f"SET result: {result}")

    # Test GET
    value = cache.get("test:direct")
    print(f"GET result: {value}")

    # Check all keys
    keys = cache.client.keys("*")
    print(f"\nAll keys in Redis: {len(keys)}")
    for key in keys:
        print(f"  - {key}")


async def test_health_endpoint():
    print("\n" + "=" * 70)
    print("TEST 2: Health Endpoint Testing")
    print("=" * 70)

    # Call health endpoint
    print("Calling http://localhost:9000/health...")
    response = requests.get("http://localhost:9000/health")
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")

    # Check if key was created
    cache = get_cache()
    keys = cache.client.keys("health:*")
    print(f"\nHealth keys in Redis: {len(keys)}")
    for key in keys:
        value = cache.get(key)
        print(f"  - {key}: {value}")


async def main():
    await test_redis_directly()
    await test_health_endpoint()

    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)

    cache = get_cache()
    all_keys = cache.client.keys("*")
    print(f"Total keys: {len(all_keys)}")

    if "test:direct" in [k for k in all_keys]:
        print("PASS: Direct Redis SET/GET works")
    else:
        print("ERROR: Direct Redis SET/GET not working!")

    health_keys = [k for k in all_keys if b"health" in k or "health" in k]
    if health_keys:
        print(f"PASS: Health endpoint caching works ({len(health_keys)} keys)")
    else:
        print("ERROR: Health endpoint caching NOT working!")
        print("  Possible causes:")
        print("    - cache.set() is not being called")
        print("    - cache.set() is failing silently")
        print("    - Multi-worker issue")


if __name__ == "__main__":
    asyncio.run(main())
