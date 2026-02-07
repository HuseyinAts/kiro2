"""
Optimal Hybrid System - Başlatma ve Test Scripti
Gemini 3 Pro + Claude Sonnet 4.5 Hibrit Sistemi

Kullanım:
    python backend/start_hybrid_system.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Backend path'i ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.optimal_hybrid_system import OptimalHybridSystem
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


def check_api_keys():
    """API key'lerini kontrol et"""
    print("\n" + "="*80)
    print("🔑 API KEY KONTROLÜ")
    print("="*80)
    
    gemini_key = os.getenv("GOOGLE_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    
    gemini_ok = gemini_key and len(gemini_key) > 20
    claude_ok = claude_key and claude_key != "your_anthropic_api_key_here" and len(claude_key) > 20
    
    print(f"\n✅ Gemini API Key: {'Ayarlanmış' if gemini_ok else '❌ Eksik'}")
    if gemini_ok:
        print(f"   Key: {gemini_key[:20]}...")
    else:
        print("   ⚠️  .env dosyasında GOOGLE_API_KEY değerini ayarlayın")
    
    print(f"\n{'✅' if claude_ok else '⚠️ '} Claude API Key: {'Ayarlanmış' if claude_ok else 'Eksik (opsiyonel)'}")
    if claude_ok:
        print(f"   Key: {claude_key[:20]}...")
    else:
        print("   ℹ️  Claude kullanmak için .env dosyasında ANTHROPIC_API_KEY değerini ayarlayın")
    
    print("\n" + "="*80)
    
    return gemini_ok or claude_ok


async def test_simple_query(system: OptimalHybridSystem):
    """Basit sorgu testi"""
    print("\n" + "="*80)
    print("📝 TEST 1: Basit Sorgu (Claude Only)")
    print("="*80)
    
    result = await system.process_query(
        query="Python'da liste nedir? Kısaca açıkla.",
        use_cache=True
    )
    
    print(f"\n🤖 Model: {result['model']}")
    print(f"⏱️  Süre: {result['duration']:.2f}s")
    print(f"💰 Maliyet: ${result['cost']:.4f}")
    print(f"📦 Cache: {'Evet' if result['cached'] else 'Hayır'}")
    print(f"\n📄 Yanıt:\n{result['response'][:500]}...")


async def test_medium_query(system: OptimalHybridSystem):
    """Orta seviye sorgu testi"""
    print("\n" + "="*80)
    print("📝 TEST 2: Orta Seviye Sorgu (Gemini Assist)")
    print("="*80)
    
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = await system.process_query(
        query=f"Bu kodu analiz et ve optimize et:\n{code}",
        context={"language": "python", "type": "optimization"},
        use_cache=True
    )
    
    print(f"\n🤖 Model: {result['model']}")
    print(f"⏱️  Süre: {result['duration']:.2f}s")
    print(f"💰 Maliyet: ${result['cost']:.4f}")
    print(f"📦 Cache: {'Evet' if result['cached'] else 'Hayır'}")
    print(f"\n📄 Yanıt:\n{result['response'][:500]}...")


async def test_complex_query(system: OptimalHybridSystem):
    """Karmaşık sorgu testi"""
    print("\n" + "="*80)
    print("📝 TEST 3: Karmaşık Sorgu (Gemini Thinking)")
    print("="*80)
    
    result = await system.process_query(
        query="""
        Bir e-ticaret platformu için mikroservis mimarisi tasarla.
        Şunları içermeli:
        - Kullanıcı yönetimi
        - Ürün kataloğu
        - Sipariş yönetimi
        - Ödeme sistemi
        
        Her servisin sorumluluklarını ve aralarındaki iletişimi detaylı açıkla.
        """,
        context={"type": "system_design", "complexity": "high"},
        use_cache=True
    )
    
    print(f"\n🤖 Model: {result['model']}")
    print(f"⏱️  Süre: {result['duration']:.2f}s")
    print(f"💰 Maliyet: ${result['cost']:.4f}")
    print(f"📦 Cache: {'Evet' if result['cached'] else 'Hayır'}")
    print(f"\n📄 Yanıt:\n{result['response'][:500]}...")


async def test_cache_performance(system: OptimalHybridSystem):
    """Cache performans testi"""
    print("\n" + "="*80)
    print("📝 TEST 4: Cache Performansı")
    print("="*80)
    
    query = "Python'da liste nedir?"
    
    # İlk çağrı (cache miss)
    print("\n1️⃣  İlk çağrı (cache miss)...")
    result1 = await system.process_query(query, use_cache=True)
    print(f"   Süre: {result1['duration']:.2f}s | Cache: {result1['cached']}")
    
    # İkinci çağrı (cache hit)
    print("\n2️⃣  İkinci çağrı (cache hit)...")
    result2 = await system.process_query(query, use_cache=True)
    print(f"   Süre: {result2['duration']:.2f}s | Cache: {result2['cached']}")
    
    speedup = result1['duration'] / result2['duration'] if result2['duration'] > 0 else 0
    print(f"\n⚡ Hızlanma: {speedup:.1f}x")


async def show_metrics(system: OptimalHybridSystem):
    """Sistem metriklerini göster"""
    print("\n" + "="*80)
    print("📊 SİSTEM METRİKLERİ")
    print("="*80)
    
    metrics = system.get_metrics()
    
    print(f"\n📈 Toplam İstek: {metrics['total_requests']}")
    print(f"💰 Toplam Maliyet: ${metrics['total_cost']:.4f}")
    print(f"⏱️  Toplam Süre: {metrics['total_time']:.2f}s")
    print(f"📊 Ortalama Süre: {metrics['avg_time']:.2f}s")
    print(f"💵 Ortalama Maliyet: ${metrics['avg_cost']:.4f}")
    
    cache_rates = metrics['cache_hit_rate']
    print("\n📦 Cache Hit Rate:")
    print(f"   L1 (Memory): {cache_rates['l1']:.1%}")
    print(f"   L2 (Redis Hot): {cache_rates['l2']:.1%}")
    print(f"   L3 (Redis Cold): {cache_rates['l3']:.1%}")
    print(f"   Toplam: {cache_rates['total']:.1%}")


async def interactive_mode(system: OptimalHybridSystem):
    """İnteraktif mod"""
    print("\n" + "="*80)
    print("💬 İNTERAKTİF MOD")
    print("="*80)
    print("\nSorularınızı yazın (çıkmak için 'exit' yazın)")
    print("Komutlar:")
    print("  - 'metrics': Sistem metriklerini göster")
    print("  - 'clear': Ekranı temizle")
    print("  - 'exit': Çık")
    
    while True:
        try:
            query = input("\n❓ Soru: ").strip()
            
            if not query:
                continue
            
            if query.lower() == 'exit':
                print("\n👋 Görüşmek üzere!")
                break
            
            if query.lower() == 'metrics':
                await show_metrics(system)
                continue
            
            if query.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            # Routing bilgisini göster
            routing = system.router.get_routing_info(query)
            print(f"\n🎯 Routing: {routing['model_type']} (karmaşıklık: {routing['complexity']}/10)")
            print(f"⏱️  Tahmini süre: {routing['estimated_time']:.1f}s")
            
            # Sorguyu işle
            result = await system.process_query(query, use_cache=True)
            
            print(f"\n🤖 Model: {result['model']}")
            print(f"⏱️  Süre: {result['duration']:.2f}s")
            print(f"💰 Maliyet: ${result['cost']:.4f}")
            print(f"📦 Cache: {'Evet' if result['cached'] else 'Hayır'}")
            print(f"\n📄 Yanıt:\n{result['response']}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"\n❌ Hata: {e}")


async def main():
    """Ana fonksiyon"""
    print("\n" + "="*80)
    print("🚀 OPTIMAL HYBRID SYSTEM")
    print("Gemini 3 Pro + Claude Sonnet 4.5")
    print("="*80)
    
    # API key kontrolü
    if not check_api_keys():
        print("\n❌ En az bir API key gerekli!")
        print("\n📝 Kurulum:")
        print("   1. .env dosyasını açın")
        print("   2. GOOGLE_API_KEY değerini ayarlayın")
        print("   3. (Opsiyonel) ANTHROPIC_API_KEY değerini ayarlayın")
        return
    
    # Sistemi başlat
    print("\n⚙️  Sistem başlatılıyor...")
    system = OptimalHybridSystem()
    print("✅ Sistem hazır!\n")
    
    # Menü
    print("\n" + "="*80)
    print("📋 MENÜ")
    print("="*80)
    print("\n1. Otomatik testleri çalıştır")
    print("2. İnteraktif mod (soru-cevap)")
    print("3. Çıkış")
    
    choice = input("\nSeçiminiz (1-3): ").strip()
    
    if choice == "1":
        # Otomatik testler
        await test_simple_query(system)
        await asyncio.sleep(1)
        
        await test_medium_query(system)
        await asyncio.sleep(1)
        
        await test_complex_query(system)
        await asyncio.sleep(1)
        
        await test_cache_performance(system)
        await asyncio.sleep(1)
        
        await show_metrics(system)
        
    elif choice == "2":
        # İnteraktif mod
        await interactive_mode(system)
    
    else:
        print("\n👋 Görüşmek üzere!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Program sonlandırıldı.")
