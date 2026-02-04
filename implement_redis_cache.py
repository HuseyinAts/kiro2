# implement_redis_cache.py
"""
Redis cache implementasyonu ekle
Konum: C:/Users/husey/kiro2/
"""

import os
from pathlib import Path
from datetime import datetime
import shutil

def create_cache_manager():
    """Cache manager modülü oluştur"""

    cache_code = '''"""
Redis Cache Manager - Performance Optimization
"""

from redis import asyncio as aioredis
import json
import pickle
from typing import Any, Optional
import hashlib
from datetime import datetime

class CacheManager:
    """Gelişmiş Redis cache yönetimi"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = None
        self.redis_url = redis_url
        self.hit_count = 0
        self.miss_count = 0
        self.enabled = True

    async def initialize(self) -> bool:
        """Redis bağlantısı kur"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=50,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            # Bağlantıyı test et
            await self.redis.ping()
            print("[OK] Redis bağlantısı başarılı")
            return True

        except Exception as e:
            print(f"[OK][OK]  Redis bağlantı hatası: {e}")
            print("   Cache devre dışı - sistem normal çalışmaya devam edecek")
            self.enabled = False
            return False

    async def close(self):
        """Redis bağlantısını kapat"""
        if self.redis:
            await self.redis.close()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Cache key oluştur"""
        data = str(args) + str(sorted(kwargs.items()))
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_key}"

    async def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        if not self.enabled or not self.redis:
            return None

        try:
            cached = await self.redis.get(key)
            if cached:
                self.hit_count += 1
                return pickle.loads(cached)

            self.miss_count += 1
            return None

        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Cache'e veri kaydet"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.setex(
                key,
                ttl,
                pickle.dumps(value)
            )
            return True

        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def get_or_set(
        self,
        key: str,
        factory_func: callable,
        ttl: int = 300
    ) -> Any:
        """Cache'den al veya hesapla ve kaydet"""

        # Cache'den kontrol et
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Cache miss - hesapla
        result = await factory_func()

        # Cache'e kaydet
        await self.set(key, result, ttl)

        return result

    async def delete(self, key: str) -> bool:
        """Cache'den sil"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str):
        """Pattern'e uyan tüm cache'leri temizle"""
        if not self.enabled or not self.redis:
            return

        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            print(f"Cache invalidate error: {e}")

    def get_stats(self) -> dict:
        """Cache istatistikleri"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0

        return {
            "enabled": self.enabled,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2f}%",
            "timestamp": datetime.now().isoformat()
        }

    async def clear_all(self):
        """Tüm cache'i temizle"""
        if not self.enabled or not self.redis:
            return

        try:
            await self.redis.flushdb()
            print("[OK] Cache temizlendi")
        except Exception as e:
            print(f"Cache clear error: {e}")

# Global instance
cache_manager = CacheManager()
'''

    # backend/core/cache.py oluştur
    cache_file = Path(r"C:\Users\husey\kiro2\backend\core\cache.py")
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(cache_code)

    print(f"[OK] Cache manager oluşturuldu: {cache_file}")
    return cache_file

def add_cache_to_learning_style_service():
    """Learning style service'e cache ekle"""

    service_file = Path(r"C:\Users\husey\kiro2\backend\services\learning_style_service.py")

    if not service_file.exists():
        print(f"[OK] Service dosyası bulunamadı: {service_file}")
        return False

    # Backup oluştur
    backup_file = service_file.parent / f"learning_style_service.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(service_file, backup_file)
    print(f"[OK] Backup oluşturuldu: {backup_file.name}")

    # Dosyayı oku
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Cache import ekle (eğer yoksa)
    if "from core.cache import cache_manager" not in content:
        # İlk import'tan sonra ekle
        import_line = "from core.cache import cache_manager"

        if "from datetime import datetime" in content:
            content = content.replace(
                "from datetime import datetime",
                f"from datetime import datetime\n{import_line}",
                1
            )
            print("[OK] Cache import eklendi")

    # detect_learning_style metoduna cache ekle
    if "async def detect_learning_style" in content and "cache_key = " not in content:

        # Metod başlangıcını bul
        method_start = content.find("async def detect_learning_style")
        if method_start != -1:

            # Metod sonunu bul (bir sonraki async def'e kadar)
            method_end = content.find("async def", method_start + 1)
            if method_end == -1:
                method_end = len(content)

            method_content = content[method_start:method_end]

            # Cache implementasyonu
            cache_impl = '''
        # Cache key oluştur
        cache_key = f"learning_style:{student_id}"

        # Cache'den kontrol et
        cached_profile = await cache_manager.get(cache_key)
        if cached_profile:
            print(f"[OK] Cache hit: {student_id}")
            return cached_profile

        print(f"[OK][OK]  Cache miss: {student_id}")

        # Profile hesapla (mevcut kod)'''

            # Try bloğunun içine ekle
            if 'try:' in method_content:
                new_method = method_content.replace(
                    'try:',
                    f'try:{cache_impl}',
                    1
                )

                # Return'den önce cache'e kaydet
                if 'self.student_profiles[student_id] = hibrit_profil' in new_method:
                    new_method = new_method.replace(
                        'self.student_profiles[student_id] = hibrit_profil',
                        '''self.student_profiles[student_id] = hibrit_profil

        # Cache'e kaydet (1 saat TTL)
        await cache_manager.set(cache_key, hibrit_profil, ttl=3600)
        print(f"[OK] Cached: {student_id} -> {hibrit_profil['hibrit_kod']}")''',
                        1
                    )

                content = content[:method_start] + new_method + content[method_end:]
                print("[OK] Cache implementasyonu eklendi")

    # Güncellenmiş içeriği yaz
    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] Service güncellendi: {service_file}")
    return True

def add_cache_stats_endpoint():
    """Cache istatistikleri için endpoint ekle"""

    endpoint_code = '''
@router.get("/cache-stats")
async def get_cache_stats():
    """Cache istatistiklerini getir"""
    from core.cache import cache_manager

    return {
        "success": True,
        "data": cache_manager.get_stats()
    }
'''

    # learning_style router'a ekle
    router_file = Path(r"C:\Users\husey\kiro2\backend\api\learning_style.py")

    if not router_file.exists():
        print(f"[OK][OK]  Router dosyası bulunamadı: {router_file}")
        return False

    with open(router_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if "/cache-stats" not in content:
        # Son endpoint'ten sonra ekle
        content += endpoint_code

        with open(router_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print("[OK] Cache stats endpoint eklendi")
        return True
    else:
        print("[OK][OK]  Cache stats endpoint zaten var")
        return True

def main():
    """Ana implementasyon fonksiyonu"""
    print("="*70)
    print("REDIS CACHE IMPLEMENTASYONU")
    print("="*70)
    print(f"Baslangic: {datetime.now().strftime('%H:%M:%S')}")

    steps = []

    # 1. Cache manager oluştur
    print("\n1. Cache Manager Olusturuluyor...")
    print("-"*70)
    cache_file = create_cache_manager()
    steps.append(("Cache Manager", True))

    # 2. Service'e cache ekle
    print("\n2. Learning Style Service'e Cache Ekleniyor...")
    print("-"*70)
    service_updated = add_cache_to_learning_style_service()
    steps.append(("Service Cache", service_updated))

    # 3. Cache stats endpoint ekle
    print("\n3. Cache Stats Endpoint Ekleniyor...")
    print("-"*70)
    endpoint_added = add_cache_stats_endpoint()
    steps.append(("Cache Stats Endpoint", endpoint_added))

    # ÖZET
    print("\n" + "="*70)
    print("IMPLEMENTASYON OZETI")
    print("="*70)

    for step_name, success in steps:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {step_name}")

    success_count = sum(1 for _, s in steps if s)

    if success_count == len(steps):
        print("\nCACHE IMPLEMENTASYONU TAMAMLANDI!")
        print("\nSonraki Adimlar:")
        print("1. Backend'i yeniden baslat:")
        print("   Ctrl+C ile durdur")
        print("   python main.py ile baslat")
        print("\n2. Cache'i test et:")
        print("   Ayni endpoint'i 2 kez cagir")
        print("   Ikinci cagri cok daha hizli olmali!")
        print("\n3. Cache stats kontrol et:")
        print("   GET http://localhost:8000/api/v1/learning-style/cache-stats")
    else:
        print("\nBazi adimlar basarisiz")

    print("\nImplementasyon tamamlandi!")
    print("Ciktiyi buraya yapistirin...")

if __name__ == "__main__":
    main()
