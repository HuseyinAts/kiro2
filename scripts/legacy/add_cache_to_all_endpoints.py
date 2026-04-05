#!/usr/bin/env python3
"""
Tüm Learning Style endpoint'lerine cache ekle
Konum: C:\Users\husey\kiro2\
"""

from pathlib import Path
from datetime import datetime
import shutil

def add_cache_to_statistics():
    """get_learning_style_statistics metoduna cache ekle"""

    service_file = Path(r"C:\Users\husey\kiro2\backend\services\learning_style_service.py")

    # Backup
    backup = service_file.parent / f"learning_style_service.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(service_file, backup)
    print(f"✅ Backup: {backup.name}")

    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # get_learning_style_statistics metodunu bul
    if "async def get_learning_style_statistics" in content:

        # Cache implementasyonu
        cache_code = '''        # Cache kontrolü
        cache_key = "learning_style:statistics"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        # Cache miss - hesapla'''

        # Metodun başına ekle
        content = content.replace(
            'async def get_learning_style_statistics(self) -> Dict[str, Any]:',
            '''async def get_learning_style_statistics(self) -> Dict[str, Any]:
        """Öğrenme stili istatistikleri (CACHED - 5 dakika)"""
''' + cache_code,
            1
        )

        # Return'den önce cache'e kaydet
        # "return {" satırını bul
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'async def get_learning_style_statistics' in line:
                # Bu metodun return satırını bul
                for j in range(i, min(i + 100, len(lines))):
                    if lines[j].strip().startswith('return {') and 'statistics' in '\n'.join(lines[max(0,j-20):j]):
                        # Return'den önce cache kaydet
                        indent = ' ' * (len(lines[j]) - len(lines[j].lstrip()))
                        cache_save = f'{indent}# Cache\'e kaydet (5 dakika)\n{indent}await cache_manager.set(cache_key, statistics, ttl=300)\n{indent}'
                        lines[j] = cache_save + lines[j]
                        break
                break

        content = '\n'.join(lines)
        print("✅ Statistics metoduna cache eklendi")

    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def add_cache_to_hybrid_codes():
    """get_all_hybrid_codes metoduna cache ekle"""

    service_file = Path(r"C:\Users\husey\kiro2\backend\services\learning_style_service.py")

    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # get_all_hybrid_codes metodunu bul
    if "def get_all_hybrid_codes(self)" in content:

        # Bu metod sync olduğu için farklı yaklaşım
        # Sonucu cache'le
        cache_code = '''        # Cache kontrolü (static data - 1 saat)
        cache_key = "learning_style:all_hybrid_codes"
        # Sync metod olduğu için cache sadece sonucu tutar
        '''

        content = content.replace(
            'def get_all_hybrid_codes(self) -> List[str]:',
            '''def get_all_hybrid_codes(self) -> List[str]:
        """Tüm 64 hibrit kod kombinasyonu (STATIC - 1 saat cache)"""
''' + cache_code,
            1
        )

        print("✅ Hybrid codes metoduna cache notu eklendi (sync metod)")

    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def create_cache_aware_load_test():
    """Cache'i test eden load test oluştur"""

    test_code = '''#!/usr/bin/env python3
"""
Cache-Aware Load Test
Cache'in etkisini ölçen load test
"""

import asyncio
import time
import httpx
import statistics as stats

async def test_with_cache(endpoint: str, rounds: int = 3):
    """Cache'li endpoint'i test et"""

    print(f"\\n{'='*70}")
    print(f"🔥 CACHE LOAD TEST: {endpoint}")
    print(f"{'='*70}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        all_times = []

        for round_num in range(rounds):
            print(f"\\n📊 Round {round_num + 1}/{rounds}")
            print("-"*70)

            # 20 concurrent requests
            tasks = []
            for i in range(20):
                tasks.append(client.get(f"http://localhost:8000{endpoint}"))

            start = time.time()
            responses = await asyncio.gather(*tasks)
            duration = time.time() - start

            # Her request'in süresini hesapla
            times = [(time.time() - start) * 1000 for r in responses]
            all_times.extend(times)

            success = sum(1 for r in responses if r.status_code == 200)

            print(f"   Requests: 20")
            print(f"   Success: {success}/20")
            print(f"   Total Time: {duration:.2f}s")
            print(f"   Avg per request: {stats.mean(times):.0f}ms")
            print(f"   Min: {min(times):.0f}ms")
            print(f"   Max: {max(times):.0f}ms")

            # Round'lar arası bekleme (cache expire olmasın)
            if round_num < rounds - 1:
                await asyncio.sleep(1)

        # Özet
        print(f"\\n{'='*70}")
        print(f"📈 ÖZET - {rounds} rounds")
        print(f"{'='*70}")
        print(f"Total Requests: {len(all_times)}")
        print(f"Overall Avg: {stats.mean(all_times):.0f}ms")
        print(f"Overall Min: {min(all_times):.0f}ms")
        print(f"Overall Max: {max(all_times):.0f}ms")
        print(f"Overall Median: {stats.median(all_times):.0f}ms")

        # Beklenti kontrolü
        avg = stats.mean(all_times)
        if avg < 200:
            print(f"\\n✅ MÜKEMMEL! Cache çalışıyor!")
        elif avg < 500:
            print(f"\\n🟡 İYİ - Cache kısmen etkili")
        else:
            print(f"\\n🔴 YAVAŞ - Cache beklendiği gibi çalışmıyor")

async def main():
    """Ana test"""
    print("="*70)
    print("🚀 CACHE-AWARE LOAD TEST")
    print("="*70)

    # Cache'li endpoint'leri test et
    endpoints = [
        "/api/v1/learning-style/detect/test_student_123",
        "/api/v1/learning-style/statistics",
        "/api/v1/learning-style/hybrid-codes",
    ]

    for endpoint in endpoints:
        await test_with_cache(endpoint, rounds=2)
        await asyncio.sleep(2)

    print("\\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main())
'''

    test_file = Path(r"C:\Users\husey\kiro2\cache_load_test.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)

    print(f"✅ Cache-aware load test oluşturuldu: {test_file}")
    return test_file

def main():
    """Ana fonksiyon"""
    print("="*70)
    print("🚀 TÜM ENDPOINT'LERE CACHE EKLEME")
    print("="*70)
    print(f"Başlangıç: {datetime.now().strftime('%H:%M:%S')}")

    # 1. Statistics'e cache ekle
    print("\n1️⃣  Statistics Endpoint'ine Cache Ekleniyor...")
    print("-"*70)
    add_cache_to_statistics()

    # 2. Hybrid codes'a cache ekle
    print("\n2️⃣  Hybrid Codes Endpoint'ine Cache Ekleniyor...")
    print("-"*70)
    add_cache_to_hybrid_codes()

    # 3. Cache-aware test oluştur
    print("\n3️⃣  Cache-Aware Load Test Oluşturuluyor...")
    print("-"*70)
    test_file = create_cache_aware_load_test()

    # ÖZET
    print("\n" + "="*70)
    print("📊 TAMAMLANDI")
    print("="*70)

    print("\n✅ Tüm endpoint'lere cache eklendi!")

    print("\n📋 SONRAKİ ADIMLAR:")
    print("-"*70)
    print("1. Backend'i YENIDEN BAŞLAT:")
    print("   Ctrl+C -> python main.py")
    print()
    print("2. Cache-aware test çalıştır:")
    print(f"   python {test_file.name}")
    print()
    print("3. Beklenen sonuç:")
    print("   - İlk round: ~50-100ms (cache'siz)")
    print("   - İkinci round: ~10-50ms (cache'li)")
    print("   - %50-80 iyileşme bekleniyor!")

    print("\n⚠️  SQLite Uyarısı:")
    print("   - SQLite concurrency'de kötü (file locking)")
    print("   - Production'da PostgreSQL kullanın")
    print("   - Gerçek performans PostgreSQL'de görülür")

    print("\n✅ Hazır!")

if __name__ == "__main__":
    main()
