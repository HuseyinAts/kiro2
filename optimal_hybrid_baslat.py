"""
Optimal Hybrid System - Hızlı Başlangıç
"""

import asyncio
import os
from dotenv import load_dotenv

# .env yükle
load_dotenv()

# Backend path
import sys
sys.path.insert(0, "backend")

from optimal_hybrid_system import OptimalHybridSystem


async def main():
    """Hızlı başlangıç"""
    
    print("=" * 80)
    print("🚀 OPTIMAL HYBRID SYSTEM")
    print("   Gemini 3 Pro + Claude Sonnet 4.5")
    print("=" * 80)
    
    # API key kontrolü
    gemini_key = os.getenv("GOOGLE_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    
    print("\n📋 Yapılandırma:")
    print(f"  Gemini API: {'✅ Yapılandırıldı' if gemini_key else '❌ Eksik'}")
    print(f"  Claude API: {'✅ Yapılandırıldı' if claude_key and claude_key != 'your_anthropic_api_key_here' else '❌ Eksik'}")
    
    if not gemini_key:
        print("\n❌ HATA: GOOGLE_API_KEY bulunamadı!")
        print("   .env dosyasına ekleyin:")
        print("   GOOGLE_API_KEY=your_key_here")
        return
    
    if not claude_key or claude_key == "your_anthropic_api_key_here":
        print("\n❌ HATA: ANTHROPIC_API_KEY eksik veya placeholder!")
        print("   .env dosyasına gerçek API key ekleyin:")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        print("\n   API key almak için: https://console.anthropic.com/")
        return
    
    # Sistemi başlat
    print("\n🔧 Sistem başlatılıyor...")
    system = OptimalHybridSystem()
    print("✅ Sistem hazır!")
    
    # İnteraktif mod
    print("\n" + "=" * 80)
    print("💬 İNTERAKTİF MOD")
    print("=" * 80)
    print("\nSoru sorun (çıkmak için 'q' yazın):")
    
    while True:
        print("\n" + "─" * 80)
        query = input("Soru: ").strip()
        
        if query.lower() in ['q', 'quit', 'exit', 'çık']:
            break
        
        if not query:
            continue
        
        try:
            print("\n⏳ İşleniyor...")
            result = await system.process_query(query, use_cache=True)
            
            print(f"\n✅ Yanıt ({result['model']}):")
            print("─" * 80)
            print(result['response'])
            print("─" * 80)
            print(f"Süre: {result['duration']:.2f}s | Maliyet: ${result['cost']:.4f} | Cache: {'Evet' if result['cached'] else 'Hayır'}")
            
        except Exception as e:
            print(f"\n❌ Hata: {str(e)}")
    
    # Özet
    print("\n" + "=" * 80)
    print("📊 OTURUM ÖZETİ")
    print("=" * 80)
    
    metrics = system.get_metrics()
    print(f"\nToplam Soru: {metrics['total_requests']}")
    print(f"Toplam Süre: {metrics['total_time']:.2f}s")
    print(f"Toplam Maliyet: ${metrics['total_cost']:.4f}")
    print(f"Cache Hit Rate: {metrics['cache_hit_rate']['total']:.1%}")
    
    print("\n👋 Görüşmek üzere!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Çıkılıyor...")
