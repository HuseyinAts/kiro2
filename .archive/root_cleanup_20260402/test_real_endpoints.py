"""
Gercek API endpoint'lerinin performansini test et
Konum: C:/Users/husey/kiro2/
"""

import asyncio
import time
import httpx
from typing import List, Dict
import statistics
import json

async def test_endpoint(
    url: str,
    method: str = "GET",
    data: dict = None,
    name: str = ""
) -> Dict:
    """Tek endpoint test"""
    times = []
    errors = []

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

                status_icon = "[OK]" if response.status_code == 200 else "[WARN]"
                print(f"  {status_icon} Test {i+1}: {duration:.0f}ms - Status: {response.status_code}")

                # Ilk basarili response'u kaydet
                if i == 0 and response.status_code == 200:
                    try:
                        response_data = response.json()
                        print(f"     Response keys: {list(response_data.keys())[:5]}")
                    except:
                        pass

                await asyncio.sleep(0.3)

            except Exception as e:
                error_msg = str(e)[:100]
                print(f"  [ERROR] Test {i+1}: {error_msg}")
                errors.append(error_msg)
                continue

    if times:
        return {
            "name": name,
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "tests": len(times),
            "errors": len(errors)
        }
    return None

async def main():
    """Ana test fonksiyonu"""
    print("="*70)
    print("GERCEK API ENDPOINT'LERI PERFORMANS TESTI")
    print("="*70)

    # Test edilecek endpoint'ler (calisan router'lardan)
    endpoints = [
        {
            "name": "Health Check",
            "url": "http://localhost:8000/health",
            "method": "GET"
        },
        {
            "name": "System Root",
            "url": "http://localhost:8000/",
            "method": "GET"
        },
        {
            "name": "Learning Style - Hybrid Codes (64 kombinasyon)",
            "url": "http://localhost:8000/api/v1/learning-style/hybrid-codes",
            "method": "GET"
        },
        {
            "name": "Learning Style - Statistics",
            "url": "http://localhost:8000/api/v1/learning-style/statistics",
            "method": "GET"
        },
        {
            "name": "Learning Style - Detect (Mock Student)",
            "url": "http://localhost:8000/api/v1/learning-style/detect/test_student_123",
            "method": "GET"
        },
        {
            "name": "AI Agents - List",
            "url": "http://localhost:8000/api/agents",
            "method": "GET"
        },
    ]

    results = []

    for endpoint in endpoints:
        print(f"\n[*] {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")

        result = await test_endpoint(
            endpoint['url'],
            endpoint['method'],
            endpoint.get('data'),
            endpoint['name']
        )

        if result:
            results.append(result)

            # Performans degerlendirmesi
            avg = result['avg']
            if avg < 50:
                status = "[PERFECT]"
            elif avg < 200:
                status = "[GOOD]"
            elif avg < 500:
                status = "[MEDIUM]"
            else:
                status = "[SLOW]"

            print(f"\n   {status}")
            print(f"   Min: {result['min']:.0f}ms")
            print(f"   Max: {result['max']:.0f}ms")
            print(f"   Avg: {result['avg']:.0f}ms")
            print(f"   Median: {result['median']:.0f}ms")
            print(f"   Basari: {result['tests']}/{result['tests'] + result['errors']}")
        else:
            print(f"   [ERROR] Tum testler basarisiz!")

    # OZET
    print("\n" + "="*70)
    print("PERFORMANS OZETI")
    print("="*70)

    if results:
        # Sirala (yavasdan hizliya)
        results.sort(key=lambda x: x['avg'], reverse=True)

        print("\nOptimizasyon Oncelikleri (yavasdan hizliya):\n")
        for i, r in enumerate(results, 1):
            avg = r['avg']

            if avg < 50:
                priority = "[OK] Mukemmel"
            elif avg < 200:
                priority = "[GOOD] Hedefte"
            elif avg < 500:
                priority = "[WARN] Iyilestirilebilir"
            else:
                priority = "[URGENT] ACIL OPTIMIZASYON"

            print(f"{i}. {priority} - {r['name']}")
            print(f"   Ortalama: {avg:.0f}ms")

        # Genel istatistik
        all_avgs = [r['avg'] for r in results]
        print(f"\nGENEL ISTATISTIKLER:")
        print(f"   Ortalama Response Time: {statistics.mean(all_avgs):.0f}ms")
        print(f"   En Hizli: {min(all_avgs):.0f}ms")
        print(f"   En Yavas: {max(all_avgs):.0f}ms")

        # Hedef kontrolu
        slow_endpoints = [r for r in results if r['avg'] > 200]
        if slow_endpoints:
            print(f"\n[WARN] {len(slow_endpoints)} endpoint hedefin ustunde (>200ms)")
            print("   Bu endpoint'lere cache ve optimizasyon uygulanacak!")
        else:
            print(f"\n[OK] TUM ENDPOINT'LER HEDEFTE! (<200ms)")

    print("\n" + "="*70)
    print("[OK] Test tamamlandi!")
    print("Sonuclari buraya yapistirin...")

if __name__ == "__main__":
    asyncio.run(main())
