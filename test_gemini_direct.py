"""
Gemini MCP Doğrudan Test Scripti
Kiro IDE'de Agents bölümü olmadan Gemini'yi kullanmak için
"""

import asyncio
import os
import sys

# Backend path ekle
sys.path.insert(0, ".")

from backend.mcp_servers.gemini_reasoning_mcp import (
    gemini_reasoning_engine,
    gemini_code_review,
    gemini_design_analysis,
    gemini_requirements_analysis,
)


async def test_gemini():
    """Gemini MCP araçlarını test et"""
    
    print("=" * 80)
    print("🤖 GEMINI MCP TEST")
    print("=" * 80)
    print()
    
    # Test 1: Basit soru
    print("📝 Test 1: Basit Soru")
    print("-" * 80)
    result = await gemini_reasoning_engine(
        prompt="Merhaba! Kendini tanıt ve neler yapabileceğini kısaca anlat.",
        thinking_mode=False
    )
    print(result)
    print()
    
    # Test 2: Kod incelemesi
    print("\n💻 Test 2: Kod İncelemesi")
    print("-" * 80)
    code = """
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total
"""
    result = await gemini_code_review(code=code, language="python")
    print(result)
    print()


async def interactive_mode():
    """İnteraktif mod - Gemini ile sohbet"""
    
    print("=" * 80)
    print("🤖 GEMINI İNTERAKTİF MOD")
    print("=" * 80)
    print()
    print("Gemini Mimar'a soru sorabilirsiniz.")
    print("Çıkmak için 'exit' veya 'quit' yazın.")
    print()
    
    while True:
        try:
            # Kullanıcıdan soru al
            question = input("\n💬 Siz: ").strip()
            
            if question.lower() in ["exit", "quit", "çıkış"]:
                print("\n👋 Görüşmek üzere!")
                break
            
            if not question:
                continue
            
            # Gemini'ye gönder
            print("\n🤖 Gemini düşünüyor...")
            result = await gemini_reasoning_engine(
                prompt=question,
                thinking_mode=True
            )
            print(f"\n{result}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"\n❌ Hata: {e}")


def main():
    """Ana fonksiyon"""
    
    # API Key kontrolü
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY environment variable bulunamadı!")
        print("Lütfen .env dosyasını kontrol edin.")
        sys.exit(1)
    
    print("\nGemini MCP Kullanım Seçenekleri:")
    print("1. Test Modu (otomatik testler)")
    print("2. İnteraktif Mod (sohbet)")
    print()
    
    choice = input("Seçiminiz (1 veya 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_gemini())
    elif choice == "2":
        asyncio.run(interactive_mode())
    else:
        print("Geçersiz seçim!")
        sys.exit(1)


if __name__ == "__main__":
    main()
