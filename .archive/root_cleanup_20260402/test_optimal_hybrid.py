"""
Optimal Hybrid System Test
Gerçek API entegrasyonu testi
"""

import asyncio
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Backend path'i ekle
import sys
sys.path.insert(0, "backend")

from optimal_hybrid_system import OptimalHybridSystem


async def test_system():
    """Sistemi test et"""

    print("=" * 80)
    print("🚀 OPTIMAL HYBRID SYSTEM TEST")
    print("=" * 80)

    # API key kontrolü
    gemini_key = os.getenv("GOOGLE_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")

    print("\n📋 API Key Kontrolü:")
    print(f"  Gemini: {'✅ Mevcut' if gemini_key else '❌ Eksik'}")
    print(f"  Claude: {'✅ Mevcut' if claude_key and claude_key != 'your_anthropic_api_key_here' else '❌ Eksik'}")

    if not gemini_key:
        print("\n❌ GOOGLE_API_KEY bulunamadı!")
        return

    if not claude_key or claude_key == "your_anthropic_api_key_here":
        print("\n⚠️  ANTHROPIC_API_KEY eksik veya placeholder değerde!")
        print("   .env dosyasına gerçek API key ekleyin")
        return

    # Sistemi başlat
    print("\n🔧 Sistem başlatılıyor...")
    system = OptimalHybridSystem()

    # Test sorguları
    test_queries = [
        {
            "query": "Python'da liste nedir?",
            "description": "Basit soru (Claude Only bekleniyor)"
        },
        {
            "query": "Bu kodu analiz et: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "description": "Orta seviye (Gemini Assist bekleniyor)"
        },
        {
            "query": "Bir e-ticaret platformu için mikroservis mimarisi tasarla. Ödeme, envanter, kullanıcı yönetimi ve bildirim servislerini içermeli.",
            "description": "Karmaşık analiz (Gemini Thinking bekleniyor)"
        }
    ]

    print("\n" + "=" * 80)
    print("📝 TEST SORULARI")
    print("=" * 80)

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {test['description']}")
        print(f"{'─' * 80}")
        print(f"Soru: {test['query'][:100]}...")

        try:
            result = await system.process_query(
                query=test['query'],
                use_cache=True
            )

            print(f"\n✅ Sonuç:")
            print(f"  Model: {result['model']}")
            print(f"  Süre: {result['duration']:.2f}s")
            print(f"  Maliyet: ${result['cost']:.4f}")
            print(f"  Cache: {'Evet' if result['cached'] else 'Hayır'}")
            print(f"  Karmaşıklık: {result['routing_info']['complexity']}/10")
            print(f"\n  Yanıt (ilk 200 karakter):")
            print(f"  {result['response'][:200]}...")

        except Exception as e:
            print(f"\n❌ Hata: {str(e)}")

    # Sistem metrikleri
    print("\n" + "=" * 80)
    print("📊 SİSTEM METRİKLERİ")
    print("=" * 80)

    metrics = system.get_metrics()
    print(f"\nToplam İstek: {metrics['total_requests']}")
    print(f"Toplam Süre: {metrics['total_time']:.2f}s")
    print(f"Ortalama Süre: {metrics['avg_time']:.2f}s")
    print(f"Toplam Maliyet: ${metrics['total_cost']:.4f}")
    print(f"Ortalama Maliyet: ${metrics['avg_cost']:.4f}")

    cache_hit_rate = metrics['cache_hit_rate']
    print(f"\nCache Hit Rate:")
    print(f"  L1 (Memory): {cache_hit_rate['l1']:.1%}")
    print(f"  L2 (Redis Hot): {cache_hit_rate['l2']:.1%}")
    print(f"  L3 (Redis Cold): {cache_hit_rate['l3']:.1%}")
    print(f"  Toplam: {cache_hit_rate['total']:.1%}")

    print("\n" + "=" * 80)
    print("✅ TEST TAMAMLANDI")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_system())
