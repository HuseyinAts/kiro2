#!/usr/bin/env python3
"""
Cache lazy initialization fix uygula
Konum: C:\Users\husey\kiro2\
"""

from pathlib import Path
from datetime import datetime
import shutil

def apply_lazy_init_fix():
    """Cache manager'a lazy initialization ekle"""

    cache_file = Path("backend/core/cache.py")

    if not cache_file.exists():
        print(f"❌ Dosya bulunamadı: {cache_file}")
        return False

    # Backup
    backup = cache_file.parent / f"cache.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(cache_file, backup)
    print(f"✅ Backup: {backup.name}")

    with open(cache_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # __init__ metodunu bul ve lazy init ekle
    for i, line in enumerate(lines):
        if 'def __init__(self' in line and 'CacheManager' in ''.join(lines[max(0,i-5):i]):
            # __init__ sonuna lazy init flag'leri ekle
            j = i + 1
            while j < len(lines) and (lines[j].startswith('        ') or lines[j].strip() == ''):
                j += 1

            # Son satırdan önce ekle
            insert_pos = j - 1
            lines.insert(insert_pos, '        self._initialized = False\n')
            lines.insert(insert_pos + 1, '        self._init_lock = None\n')
            print("✅ Lazy init flags eklendi")
            break

    # _ensure_initialized metodu ekle (initialize metodundan hemen sonra)
    for i, line in enumerate(lines):
        if 'async def initialize(self)' in line:
            # Bu metodun sonunu bul
            j = i + 1
            indent_level = len(line) - len(line.lstrip())
            while j < len(lines):
                if lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 4)):
                    break
                j += 1

            # _ensure_initialized metodunu ekle
            new_method = f'''
    async def _ensure_initialized(self):
        """Lazy initialization - ilk kullanımda initialize et"""
        if self._initialized:
            return

        if self._init_lock is None:
            import asyncio
            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            if self._initialized:
                return
            await self.initialize()
            self._initialized = True

'''
            lines.insert(j, new_method)
            print("✅ _ensure_initialized metodu eklendi")
            break

    # get() metoduna lazy init ekle
    for i, line in enumerate(lines):
        if 'async def get(self, key: str)' in line:
            # İlk satırdan sonra ekle
            lines.insert(i + 1, '        await self._ensure_initialized()\n')
            print("✅ get() metoduna lazy init eklendi")
            break

    # set() metoduna lazy init ekle
    for i, line in enumerate(lines):
        if 'async def set(self, key: str,' in line:
            # İlk satırdan sonra ekle (docstring varsa ondan sonra)
            j = i + 1
            if '"""' in lines[j]:
                # Docstring'i geç
                while j < len(lines) and not (lines[j].count('"""') >= 2 or (j > i + 1 and '"""' in lines[j])):
                    j += 1
                j += 1
            lines.insert(j, '        await self._ensure_initialized()\n')
            print("✅ set() metoduna lazy init eklendi")
            break

    # Dosyayı yaz
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✅ Dosya güncellendi: {cache_file}")
    return True

def verify_fix():
    """Fix'in doğru uygulandığını kontrol et"""

    cache_file = Path("backend/core/cache.py")

    with open(cache_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {
        "_initialized flag": "self._initialized = False" in content,
        "_init_lock flag": "self._init_lock = None" in content,
        "_ensure_initialized metodu": "async def _ensure_initialized" in content,
        "get() lazy init": "await self._ensure_initialized()" in content and "async def get" in content,
        "set() lazy init": content.count("await self._ensure_initialized()") >= 2
    }

    print("\n🔍 Doğrulama:")
    all_ok = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_ok = False

    return all_ok

def main():
    """Ana fonksiyon"""
    print("="*70)
    print("🔧 CACHE LAZY INITIALIZATION FIX")
    print("="*70)
    print(f"Başlangıç: {datetime.now().strftime('%H:%M:%S')}")

    print("\n1️⃣ Lazy Initialization Uygulanıyor...")
    print("-"*70)
    success = apply_lazy_init_fix()

    if not success:
        print("\n❌ Fix uygulanamadı!")
        return

    print("\n2️⃣ Doğrulama...")
    print("-"*70)
    verified = verify_fix()

    if verified:
        print("\n" + "="*70)
        print("✅ FIX BAŞARIYLA UYGULANDI!")
        print("="*70)

        print("\n📋 SONRAKİ ADIMLAR:")
        print("-"*70)
        print("1. Backend'i YENIDEN BAŞLAT:")
        print("   Ctrl+C -> python main.py")
        print()
        print("2. Hızlı test:")
        print("   curl http://localhost:8000/api/v1/learning-style/statistics")
        print("   curl http://localhost:8000/api/v1/learning-style/statistics  # Daha hızlı olmalı!")
        print()
        print("3. Load test çalıştır:")
        print("   python quick_load_test.py")
        print()
        print("📊 BEKLENTİLER:")
        print("   - İlk çağrı: 50-100ms (cache miss)")
        print("   - İkinci çağrı: 5-20ms (cache hit)")
        print("   - Load test avg: 30-80ms (85% improvement)")
        print("   - Cache hit rate: 95%+")
        print()
        print("🎯 BAŞARI KRİTERİ:")
        print("   Backend loglarında 'Cache hit' mesajları görmelisiniz!")
    else:
        print("\n⚠️ Doğrulama başarısız - manuel kontrol gerekiyor")

    print("\n✅ Script tamamlandı!")

if __name__ == "__main__":
    main()
