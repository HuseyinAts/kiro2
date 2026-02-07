"""
Optimal Hybrid System Başlatma Scripti
Claude Code (Kiro) içinde çalıştırılabilir
"""

import asyncio
import os
import sys
from pathlib import Path

# .env dosyasını yükle
from dotenv import load_dotenv
load_dotenv()

# Backend path'i ekle
sys.path.insert(0, str(Path(__file__).parent))

from backend.optimal_hybrid_system import OptimalHybridSystem


async def test_api_keys():
    """API anahtarlarını kontrol et"""
    print("\n" + "="*60)
    print("🔑 API Anahtarları Kontrolü")
    print("="*60)
    
    google_key = os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if google_key:
        print(f"✅ GOOGLE_API_KEY: {google_key[:20]}...")
    else:
        print("❌ GOOGLE_API_KEY: Bulunamadı")
    
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY: {anthropic_key[:20]}...")
    else:
        print("⚠️  ANTHROPIC_API_KEY: Bulunamadı (opsiyonel)")
    
    if not google_key:
        print("\n⚠️  UYARI: GOOGLE_API_KEY bulunamadı!")
        print("   .env dosyasına API anahtarınızı ekleyin:")
        print("   GOOGLE_API_KEY=your-key-here")
        return False
    
    return True


async def interactive_mode():
    """İnteraktif mod - Soru-cevap"""
    print("\n" + "="*60)
    print("🤖 Optimal Hybrid System - İnteraktif Mod")
    print("="*60)
    print("Komutlar:")
    print("  - Soru yazın ve Enter'a basın")
    print("  - 'exit' veya 'quit' yazarak çıkın")
    print("  - 'metrics' yazarak istatistikleri görün")
    print("="*60 + "\n")
    
    system = OptimalHybridSystem()
    
    while True:
        try:
            query = input("\n💬 Soru: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'çık']:
                print("\n👋 Görüşmek üzere!")
                break
            
            if query.lower() == 'metrics':
                metrics = system.get_metrics()
                print("\n📊 Sistem Metrikleri:")
                print(f"   Toplam İstek: {metrics['total_requests']}")
                print(f"   Toplam Maliyet: ${metrics['total_cost']:.4f}")
                print(f"   Ortalama Süre: {metrics['avg_time']:.2f}s")
                print(f"   Cache Hit Rate: {metrics['cache_hit_rate']['total']:.1%}")
                continue
            
            # Routing bilgisi göster
            routing_info = system.router.get_routing_info(query)
            print(f"\n🎯 Routing: {routing_info['model_type']} (karmaşıklık: {routing_info['complexity']}/10)")
            print(f"⏱️  Tahmini süre: {routing_info['estimated_time']:.1f}s")
            print(f"💰 Tahmini maliyet: ${routing_info['estimated_cost']:.4f}")
            
            # İşle
            print("\n⏳ İşleniyor...")
            result = await system.process_query(query, use_cache=True)
            
            # Sonuç
            print(f"\n{'🔄' if result['cached'] else '✨'} Yanıt ({result['model']}):")
            print("-" * 60)
            print(result['response'])
            print("-" * 60)
            print(f"⏱️  Süre: {result['duration']:.2f}s | 💰 Maliyet: ${result['cost']:.4f} | 🔄 Cache: {result['cached']}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"\n❌ Hata: {str(e)}")


async def demo_mode():
    """Demo mod - Örnek sorular"""
    print("\n" + "="*60)
    print("🎬 Optimal Hybrid System - Demo Modu")
    print("="*60 + "\n")
    
    system = OptimalHybridSystem()
    
    # Test soruları
    test_queries = [
        {
            "query": "Python nedir?",
            "description": "Basit soru (Claude Only)"
        },
        {
            "query": "Aşağıdaki kodu analiz et ve optimize et:\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "description": "Orta seviye (Gemini Assist)"
        },
        {
            "query": "Bir e-ticaret platformu için mikroservis mimarisi tasarla. API Gateway, ödeme servisi, envanter yönetimi ve kullanıcı yönetimi olsun. Her servisin sorumluluklarını ve aralarındaki iletişimi detaylı açıkla.",
            "description": "Karmaşık analiz (Gemini Thinking)"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/3: {test['description']}")
        print(f"{'='*60}")
        print(f"Soru: {test['query'][:100]}...")
        
        # Routing bilgisi
        routing_info = system.router.get_routing_info(test['query'])
        print(f"\n🎯 Model: {routing_info['model_type']}")
        print(f"📊 Karmaşıklık: {routing_info['complexity']}/10")
        print(f"⏱️  Tahmini süre: {routing_info['estimated_time']:.1f}s")
        print(f"💰 Tahmini maliyet: ${routing_info['estimated_cost']:.4f}")
        
        # İşle
        print("\n⏳ İşleniyor...")
        result = await system.process_query(test['query'], use_cache=True)
        
        # Sonuç
        print(f"\n{'🔄' if result['cached'] else '✨'} Yanıt:")
        print("-" * 60)
        print(result['response'][:500] + "..." if len(result['response']) > 500 else result['response'])
        print("-" * 60)
        print(f"⏱️  Süre: {result['duration']:.2f}s")
        print(f"💰 Maliyet: ${result['cost']:.4f}")
        print(f"🔄 Cache: {'Evet' if result['cached'] else 'Hayır'}")
        
        if i < len(test_queries):
            await asyncio.sleep(1)
    
    # Final metrikler
    print("\n" + "="*60)
    print("📊 Final Metrikler")
    print("="*60)
    metrics = system.get_metrics()
    print(f"Toplam İstek: {metrics['total_requests']}")
    print(f"Toplam Maliyet: ${metrics['total_cost']:.4f}")
    print(f"Toplam Süre: {metrics['total_time']:.2f}s")
    print(f"Ortalama Süre: {metrics['avg_time']:.2f}s")
    print(f"Ortalama Maliyet: ${metrics['avg_cost']:.4f}")
    print(f"\nCache Hit Rates:")
    print(f"  L1 (Memory): {metrics['cache_hit_rate']['l1']:.1%}")
    print(f"  L2 (Redis Hot): {metrics['cache_hit_rate']['l2']:.1%}")
    print(f"  L3 (Redis Cold): {metrics['cache_hit_rate']['l3']:.1%}")
    print(f"  Toplam: {metrics['cache_hit_rate']['total']:.1%}")


async def main():
    """Ana fonksiyon"""
    print("\n" + "="*60)
    print("🚀 Optimal Hybrid AI System")
    print("   Gemini 3 Pro + Claude Sonnet 4.5")
    print("="*60)
    
    # API anahtarlarını kontrol et
    if not await test_api_keys():
        return
    
    # Mod seçimi
    print("\n📋 Mod Seçin:")
    print("  1. Demo Modu (Otomatik test)")
    print("  2. İnteraktif Mod (Soru-cevap)")
    
    try:
        choice = input("\nSeçim (1 veya 2): ").strip()
        
        if choice == "1":
            await demo_mode()
        elif choice == "2":
            await interactive_mode()
        else:
            print("❌ Geçersiz seçim!")
    
    except KeyboardInterrupt:
        print("\n\n👋 Görüşmek üzere!")


if __name__ == "__main__":
    asyncio.run(main())
