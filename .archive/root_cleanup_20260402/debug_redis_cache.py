#!/usr/bin/env python3
"""
Redis cache'in neden çalışmadığını debug et
Konum: C:\Users\husey\kiro2\
"""

import asyncio
import sys
from pathlib import Path

# Backend path ekle
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

async def test_redis_direct():
    """Redis'e direkt bağlan ve test et"""
    print("="*70)
    print("1️⃣  REDIS DİREKT BAĞLANTI TESTİ")
    print("="*70)

    try:
        from redis import asyncio as aioredis

        # Redis'e bağlan
        redis_url = "redis://localhost:6379/0"
        print(f"🔌 Bağlanılıyor: {redis_url}")

        redis = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False
        )

        # Ping test
        print("\n📡 PING testi...")
        pong = await redis.ping()
        print(f"   ✅ PONG alındı: {pong}")

        # Set/Get test
        print("\n💾 SET/GET testi...")
        await redis.set("test_key", "test_value")
        print("   ✅ SET başarılı")

        value = await redis.get("test_key")
        print(f"   ✅ GET başarılı: {value}")

        # Cleanup
        await redis.delete("test_key")
        await redis.close()

        print("\n✅ Redis direkt bağlantı BAŞARILI!")
        return True

    except Exception as e:
        print(f"\n❌ Redis bağlantı hatası: {e}")
        print("\n💡 Redis çalışıyor mu kontrol edin:")
        print("   Windows: docker ps | findstr redis")
        print("   Veya: redis-cli ping")
        return False

async def test_cache_manager():
    """Cache manager'ı test et"""
    print("\n" + "="*70)
    print("2️⃣  CACHE MANAGER TESTİ")
    print("="*70)

    try:
        from core.cache import cache_manager

        # Initialize durumunu kontrol
        print(f"\n📊 Cache Manager Durumu:")
        print(f"   Enabled: {cache_manager.enabled}")
        print(f"   Redis: {cache_manager.redis}")
        print(f"   Hit Count: {cache_manager.hit_count}")
        print(f"   Miss Count: {cache_manager.miss_count}")

        if not cache_manager.enabled:
            print("\n❌ SORUN BULUNDU: cache_manager.enabled = False")
            print("   Cache manager initialize edilmemiş!")
            return False

        if not cache_manager.redis:
            print("\n❌ SORUN BULUNDU: cache_manager.redis = None")
            print("   Redis bağlantısı yok!")
            return False

        print("\n✅ Cache manager durumu iyi görünüyor")
        return True

    except ImportError as e:
        print(f"\n❌ Import hatası: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        return False

async def test_cache_operations():
    """Cache get/set operasyonlarını test et"""
    print("\n" + "="*70)
    print("3️⃣  CACHE GET/SET OPERASYON TESTİ")
    print("="*70)

    try:
        from core.cache import cache_manager

        # Initialize edilmiş mi kontrol et
        if not cache_manager.enabled or not cache_manager.redis:
            print("\n⚠️  Cache manager initialize edilmemiş!")
            print("   Initialize ediliyor...")
            success = await cache_manager.initialize()
            if not success:
                print("   ❌ Initialize başarısız!")
                return False
            print("   ✅ Initialize başarılı!")

        # Test data
        test_key = "test:debug:key"
        test_value = {"test": "data", "number": 123}

        print(f"\n💾 SET testi...")
        print(f"   Key: {test_key}")
        print(f"   Value: {test_value}")

        success = await cache_manager.set(test_key, test_value, ttl=60)
        print(f"   Result: {success}")

        if not success:
            print("   ❌ SET başarısız!")
            return False

        print("   ✅ SET başarılı!")

        # Get test
        print(f"\n📥 GET testi...")
        cached = await cache_manager.get(test_key)
        print(f"   Result: {cached}")

        if cached is None:
            print("   ❌ GET başarısız - None döndü!")
            print("\n🔍 Debug bilgileri:")
            print(f"   cache_manager.enabled: {cache_manager.enabled}")
            print(f"   cache_manager.redis: {cache_manager.redis}")
            return False

        if cached != test_value:
            print(f"   ❌ Veri eşleşmiyor!")
            print(f"   Beklenen: {test_value}")
            print(f"   Alınan: {cached}")
            return False

        print("   ✅ GET başarılı - veri eşleşti!")

        # Cleanup
        if hasattr(cache_manager, 'delete'):
            await cache_manager.delete(test_key)

        print("\n✅ Cache operasyonları BAŞARILI!")
        return True

    except Exception as e:
        print(f"\n❌ Cache operasyon hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pickle_serialization():
    """Pickle serialization'ı test et"""
    print("\n" + "="*70)
    print("4️⃣  PICKLE SERİALİZATION TESTİ")
    print("="*70)

    try:
        import pickle

        # Learning style benzeri kompleks veri
        test_data = {
            "student_id": "test_123",
            "vark_profili": {
                "visual": 0.7,
                "auditory": 0.5,
                "reading": 0.8,
                "kinesthetic": 0.4
            },
            "hibrit_kod": "V-ASVS",
            "timestamp": "2025-10-03T19:00:00"
        }

        print("\n📦 Pickle serialize testi...")
        pickled = pickle.dumps(test_data)
        print(f"   ✅ Pickle başarılı ({len(pickled)} bytes)")

        print("\n📦 Pickle deserialize testi...")
        unpickled = pickle.loads(pickled)
        print(f"   ✅ Unpickle başarılı")

        if unpickled == test_data:
            print("   ✅ Veri eşleşti!")
            return True
        else:
            print("   ❌ Veri eşleşmedi!")
            return False

    except Exception as e:
        print(f"\n❌ Pickle hatası: {e}")
        print("\n💡 JSON'a geçiş önerilir")
        return False

async def test_main_initialization():
    """main.py'de cache initialize edilmiş mi kontrol et"""
    print("\n" + "="*70)
    print("5️⃣  MAIN.PY INITIALİZATION KONTROLÜ")
    print("="*70)

    main_file = Path(r"C:\Users\husey\kiro2\backend\main.py")

    if not main_file.exists():
        print(f"❌ main.py bulunamadı: {main_file}")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Cache import kontrol
    if "from" in content and "cache import cache_manager" in content:
        print("✅ Cache import var")
    else:
        print("❌ Cache import YOK!")
        return False

    # Initialize kontrol
    if "cache_manager.initialize()" in content:
        print("✅ cache_manager.initialize() çağrılıyor")
    else:
        print("❌ cache_manager.initialize() ÇAĞRILMIYOR!")
        print("\n🔧 FIX: main.py'de lifespan fonksiyonuna ekleyin:")
        print("   await cache_manager.initialize()")
        return False

    return True

async def main():
    """Ana debug fonksiyonu"""
    print("="*70)
    print("🔍 REDIS CACHE DEBUG - KÖK NEDEN ANALİZİ")
    print("="*70)
    print()

    results = {}

    # 1. Redis direkt bağlantı
    results['redis_direct'] = await test_redis_direct()

    # 2. Cache manager durumu
    results['cache_manager'] = await test_cache_manager()

    # 3. Cache operasyonları
    results['cache_operations'] = await test_cache_operations()

    # 4. Pickle serialization
    results['pickle'] = await test_pickle_serialization()

    # 5. Main.py initialization
    results['main_init'] = await test_main_initialization()

    # ÖZET
    print("\n" + "="*70)
    print("📊 DEBUG SONUÇLARI")
    print("="*70)

    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    # Sorun tespiti
    print("\n" + "="*70)
    print("🎯 SORUN TESPİTİ")
    print("="*70)

    if not results['redis_direct']:
        print("\n🔴 SORUN: Redis sunucusu çalışmıyor!")
        print("   FIX: docker-compose up -d redis")

    elif not results['main_init']:
        print("\n🔴 SORUN: Cache manager initialize edilmiyor!")
        print("   FIX: main.py'de cache_manager.initialize() ekleyin")

    elif not results['cache_manager']:
        print("\n🔴 SORUN: Cache manager enabled=False veya redis=None!")
        print("   FIX: Backend'i yeniden başlatın")

    elif not results['cache_operations']:
        print("\n🔴 SORUN: Cache get/set operasyonları çalışmıyor!")
        print("   FIX: cache.py'de hata logları kontrol edin")

    elif not results['pickle']:
        print("\n🔴 SORUN: Pickle serialization başarısız!")
        print("   FIX: JSON serialization'a geçin")

    else:
        print("\n✅ TÜM TESTLER BAŞARILI!")
        print("   Cache teorik olarak çalışmalı...")
        print("   Backend loglarını kontrol edin")

    print("\n✅ Debug tamamlandı!")
    print("Sonuçları buraya yapıştırın...")

if __name__ == "__main__":
    asyncio.run(main())
