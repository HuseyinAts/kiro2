# -*- coding: utf-8 -*-
import asyncio
import sys

print("=" * 60)
print("LEARNING STYLE SERVICE - HIZLI TEST")
print("=" * 60)

try:
    from services.learning_style_service import LearningStyleService

    print("\nOK Service import edildi")

    service = LearningStyleService()
    print("OK Service instance olusturuldu")

    # Test 1: 64 hibrit kod
    print("\nTest 1: 64 Hibrit Kod Uretimi")
    codes = asyncio.run(service.get_all_hybrid_codes())
    print(f"   Uretilen kod sayisi: {len(codes)}")

    if len(codes) == 64:
        print("   OK BASARILI: 64 kod dogru!")
    else:
        print(f"   HATA: {len(codes)} kod, 64 olmali")

    # Test 2: Ornek kodlar
    print("\nTest 2: Ornek Hibrit Kodlar")
    samples = ["V-ASVS", "A-RIVG", "R-ASBG", "K-RIVS"]
    code_list = [c["kod"] for c in codes]
    for sample in samples:
        if sample in code_list:
            print(f"   OK {sample} bulundu")
        else:
            print(f"   HATA {sample} bulunamadi")

    # Test 3: Profil tespiti
    print("\nTest 3: Profil Tespiti")

    async def test_detection():
        result = await service.detect_learning_style(
            student_id="test_001", behavioral_data={"video_watch_time": 3600}
        )
        return result

    result = asyncio.run(test_detection())

    if result and "hibrit_kod" in result:
        print(f"   OK Profil tespit edildi: {result['hibrit_kod']}")
        print(f"   Guven seviyesi: {result['guven_seviyesi']:.2f}")
    else:
        print("   HATA Profil tespit edilemedi")

    # Test 4: VARK yapisi
    print("\nTest 4: VARK Profil Yapisi")
    vark = result.get("vark_profili", {})
    for dim in ["visual", "auditory", "reading", "kinesthetic"]:
        if dim in vark:
            print(f"   OK {dim}: {vark[dim]:.2f}")
        else:
            print(f"   HATA {dim} eksik")

    # Test 5: Istatistikler
    print("\nTest 5: Servis Istatistikleri")
    stats = service.get_service_stats()
    print(f"   Profil sayisi: {stats.get('toplam_profil_sayisi', 0)}")
    print(f"   Toplam kombinasyon: {stats.get('toplam_kombinasyon', 0)}")

    print("\n" + "=" * 60)
    print("TUM TESTLER TAMAMLANDI!")
    print("=" * 60)

except ImportError as e:
    print(f"\nHATA IMPORT: {e}")
    print("\nLutfen kontrol edin:")
    print("  - services/learning_style_service.py dosyasi var mi?")
    print("  - services/__init__.py dosyasi var mi?")

except Exception as e:
    print(f"\nHATA: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
