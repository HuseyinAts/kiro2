# load_test.py
"""
Load testing - Yuk altinda performans testi
"""

import asyncio
import time
import httpx
from typing import List, Dict
import statistics
from datetime import datetime
import json

class LoadTester:
    """Load testing sınıfı"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []

    async def single_request(
        self,
        endpoint: str,
        method: str = "GET",
        request_id: int = 0
    ) -> Dict:
        """Tek bir request gönder"""
        url = f"{self.base_url}{endpoint}"

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url, json={})

                duration = (time.time() - start) * 1000  # ms

                return {
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "duration": duration,
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            duration = (time.time() - start) * 1000
            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)[:100],
                "timestamp": datetime.now().isoformat()
            }

    async def load_test(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        requests_per_user: int = 5,
        method: str = "GET"
    ) -> Dict:
        """Load test çalıştır"""

        print(f"\nLOAD TEST: {endpoint}")
        print(f"   Concurrent Users: {concurrent_users}")
        print(f"   Requests per User: {requests_per_user}")
        print(f"   Total Requests: {concurrent_users * requests_per_user}")
        print("-"*70)

        start_time = time.time()

        # Tüm request'leri hazırla
        tasks = []
        request_id = 0

        for user in range(concurrent_users):
            for req in range(requests_per_user):
                task = self.single_request(endpoint, method, request_id)
                tasks.append(task)
                request_id += 1

        # Tüm request'leri paralel çalıştır
        print(f"Sending {len(tasks)} requests...")
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # İstatistikleri hesapla
        durations = [r['duration'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count

        stats = {
            "endpoint": endpoint,
            "total_requests": len(results),
            "successful_requests": success_count,
            "failed_requests": error_count,
            "success_rate": f"{(success_count / len(results) * 100):.1f}%",
            "total_time": f"{total_time:.2f}s",
            "requests_per_second": f"{len(results) / total_time:.2f}",
            "avg_response_time": f"{statistics.mean(durations):.0f}ms" if durations else "N/A",
            "min_response_time": f"{min(durations):.0f}ms" if durations else "N/A",
            "max_response_time": f"{max(durations):.0f}ms" if durations else "N/A",
            "median_response_time": f"{statistics.median(durations):.0f}ms" if durations else "N/A",
            "p95_response_time": f"{sorted(durations)[int(len(durations) * 0.95)]:.0f}ms" if len(durations) > 20 else "N/A",
            "p99_response_time": f"{sorted(durations)[int(len(durations) * 0.99)]:.0f}ms" if len(durations) > 20 else "N/A"
        }

        return stats, results

async def run_load_tests():
    """Tüm load testleri çalıştır"""

    print("="*70)
    print("LOAD TESTING - YUK ALTINDA PERFORMANS TESTI")
    print("="*70)
    print(f"Baslangic: {datetime.now().strftime('%H:%M:%S')}")

    tester = LoadTester()

    # Test senaryoları
    test_scenarios = [
        {
            "name": "Light Load (10 kullanici)",
            "endpoint": "/api/v1/learning-style/hybrid-codes",
            "concurrent_users": 10,
            "requests_per_user": 5
        },
        {
            "name": "Medium Load (25 kullanici)",
            "endpoint": "/api/v1/learning-style/statistics",
            "concurrent_users": 25,
            "requests_per_user": 4
        },
        {
            "name": "Heavy Load (50 kullanici)",
            "endpoint": "/health",
            "concurrent_users": 50,
            "requests_per_user": 3
        },
        {
            "name": "Stress Test (100 kullanici)",
            "endpoint": "/",
            "concurrent_users": 100,
            "requests_per_user": 2
        }
    ]

    all_results = []

    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"[TEST] {scenario['name']}")
        print("="*70)

        stats, results = await tester.load_test(
            endpoint=scenario['endpoint'],
            concurrent_users=scenario['concurrent_users'],
            requests_per_user=scenario['requests_per_user']
        )

        all_results.append({
            "scenario": scenario['name'],
            "stats": stats
        })

        # Sonuçları göster
        print(f"\n[OK] Test Tamamlandi!")
        print(f"   Total Requests: {stats['total_requests']}")
        print(f"   Success Rate: {stats['success_rate']}")
        print(f"   Avg Response: {stats['avg_response_time']}")
        print(f"   Min Response: {stats['min_response_time']}")
        print(f"   Max Response: {stats['max_response_time']}")
        print(f"   Median Response: {stats['median_response_time']}")
        print(f"   P95: {stats['p95_response_time']}")
        print(f"   P99: {stats['p99_response_time']}")
        print(f"   Total Time: {stats['total_time']}")
        print(f"   RPS: {stats['requests_per_second']}")

        # Performans değerlendirmesi
        avg_ms = float(stats['avg_response_time'].replace('ms', ''))

        if avg_ms < 100:
            grade = "[EXCELLENT]"
        elif avg_ms < 200:
            grade = "[GOOD]"
        elif avg_ms < 500:
            grade = "[MEDIUM]"
        else:
            grade = "[SLOW]"

        print(f"\n   Performance: {grade}")

        # Request'ler arasında bekleme
        await asyncio.sleep(2)

    # GENEL ÖZET
    print("\n\n" + "="*70)
    print("LOAD TEST GENEL OZETI")
    print("="*70)

    print("\nSenaryo Karsilastirmasi:\n")

    for result in all_results:
        scenario = result['scenario']
        stats = result['stats']

        avg_ms = float(stats['avg_response_time'].replace('ms', ''))
        success_rate = float(stats['success_rate'].replace('%', ''))

        # Grade
        if avg_ms < 200 and success_rate > 95:
            grade = "[OK] BASARILI"
        elif avg_ms < 500 and success_rate > 90:
            grade = "[WARN] KABUL EDILEBILIR"
        else:
            grade = "[FAIL] SORUNLU"

        print(f"{grade} {scenario}")
        print(f"   Avg: {stats['avg_response_time']}, Success: {stats['success_rate']}")

    # Cache ihtiyacı analizi
    print("\n\nCACHE IHTIYACI ANALIZI:")
    print("-"*70)

    # En yavaş senaryo
    slowest = max(all_results, key=lambda x: float(x['stats']['avg_response_time'].replace('ms', '')))
    slowest_avg = float(slowest['stats']['avg_response_time'].replace('ms', ''))

    if slowest_avg < 200:
        print("[OK] Performans mukemmel - Cache opsiyonel")
        print("   Mevcut performans yuk altinda bile hedefin altinda")
        print("   Cache daha cok hit rate iyilestirmesi icin eklenebilir")
    elif slowest_avg < 500:
        print("[WARN] Performans kabul edilebilir ama cache eklenebilir")
        print("   Cache ile response time %30-50 daha dusebilir")
    else:
        print("[FAIL] Performans iyilestirme gerekli!")
        print("   Cache zorunlu - response time'i dusurmek icin")

    # Recommendations
    print("\n\nONERILER:")
    print("-"*70)

    for i, result in enumerate(all_results, 1):
        stats = result['stats']
        avg_ms = float(stats['avg_response_time'].replace('ms', ''))

        if avg_ms > 200:
            print(f"{i}. {result['scenario']} icin optimizasyon onerileri:")
            print(f"   - Redis cache ekle (response time %40-60 duser)")
            print(f"   - Database connection pool optimize et")
            print(f"   - Async islemleri paralelize et")

    print("\n[OK] Load testing tamamlandi!")
    print("Sonuclari buraya yapistirin...")

if __name__ == "__main__":
    asyncio.run(run_load_tests())
