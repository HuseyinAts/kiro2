"""
Mevcut API performansini test et
Konum: C:/Users/husey/kiro2/
"""

import asyncio
import time
import httpx
from typing import List, Dict
import statistics

async def test_endpoint_performance(url: str, method: str = "GET", data: dict = None) -> Dict:
    """Endpoint performans testi"""
    times = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 5 kez test et
        for i in range(5):
            start = time.time()
            try:
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url, json=data)

                duration = (time.time() - start) * 1000  # ms
                times.append(duration)

                print(f"  Test {i+1}: {duration:.0f}ms - Status: {response.status_code}")

                await asyncio.sleep(0.5)  # Rate limit için bekle

            except Exception as e:
                print(f"  Test {i+1}: HATA - {str(e)}")
                continue

    if times:
        return {
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times)
        }
    return None

async def main():
    """Ana test fonksiyonu"""
    print("="*60)
    print("API PERFORMANS ANALİZİ - BAŞLANGIÇ")
    print("="*60)

    # Test edilecek endpoint'ler
    endpoints = [
        {"url": "http://localhost:8000/health", "method": "GET", "name": "Health Check"},
        {"url": "http://localhost:8000/", "method": "GET", "name": "Root Endpoint"},
    ]

    results = {}

    for endpoint in endpoints:
        print(f"\n[*] {endpoint['name']} testi...")
        print(f"   URL: {endpoint['url']}")

        result = await test_endpoint_performance(
            endpoint['url'],
            endpoint['method']
        )

        if result:
            results[endpoint['name']] = result
            print(f"\n   [OK] Sonuclar:")
            print(f"      Min: {result['min']:.0f}ms")
            print(f"      Max: {result['max']:.0f}ms")
            print(f"      Avg: {result['avg']:.0f}ms")
            print(f"      Median: {result['median']:.0f}ms")
        else:
            print(f"   [ERROR] Test basarisiz!")

    print("\n" + "="*60)
    print("ÖZET")
    print("="*60)

    for name, result in results.items():
        status = "[SLOW]" if result['avg'] > 200 else "[FAST]"
        print(f"{status} {name}: {result['avg']:.0f}ms (ortalama)")

    print("\n[OK] Analiz tamamlandi!")
    print("Sonuclari buraya yapistirin...")

if __name__ == "__main__":
    asyncio.run(main())
