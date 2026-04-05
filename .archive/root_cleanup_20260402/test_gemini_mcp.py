"""
Gemini MCP Test Script
Gemini Reasoning Engine'i doğrudan test eder
"""

import asyncio
import os
import sys

# Backend path ekle
sys.path.insert(0, '.')

from backend.mcp_servers.gemini_reasoning_mcp import (
    gemini_reasoning_engine,
    gemini_code_review,
    gemini_design_analysis,
)


async def test_gemini():
    """Gemini MCP araçlarını test et"""
    
    print("=" * 60)
    print("🤖 GEMİNİ MCP TEST")
    print("=" * 60)
    
    # Test 1: Basit soru
    print("\n1️⃣ Basit Soru Testi:")
    print("-" * 60)
    
    result = await gemini_reasoning_engine(
        prompt="Merhaba! Kendini tanıt ve neler yapabileceğini anlat.",
        thinking_mode=False
    )
    print(result)
    
    # Test 2: Kod incelemesi
    print("\n\n2️⃣ Kod İncelemesi Testi:")
    print("-" * 60)
    
    sample_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)
"""
    
    result = await gemini_code_review(
        code=sample_code,
        language="python"
    )
    print(result)
    
    print("\n" + "=" * 60)
    print("✅ Test Tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    # API Key kontrolü
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY bulunamadı!")
        print("Lütfen .env dosyasını kontrol edin.")
        sys.exit(1)
    
    # Test çalıştır
    asyncio.run(test_gemini())
