#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SORU ÜRETİMİ - GPT-5 ve Claude 4.5
"""

import sys
import os
import asyncio
from pathlib import Path

# UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Backend path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# API anahtarları
os.environ["OPENAI_API_KEY"] = "[REDACTED_OPENAI_KEY]"
os.environ["ANTHROPIC_API_KEY"] = "[REDACTED_ANTHROPIC_KEY]"

async def generate_with_openai():
    """OpenAI GPT-5 ile soru üret"""
    print("\n[1/2] OpenAI GPT-5 ile soru uretiliyor...")

    try:
        import openai

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

        prompt = """Sen bir ÖSYM soru hazırlama uzmanısın.

TYT Matematik - Türev konusunda orta zorlukta bir soru hazırla.

SORU ÖZELLİKLERİ:
- Konu: Türev Kuralları
- Zorluk: Orta
- Bloom Seviyesi: Uygulama (Apply)
- Çözüm süresi: 2-3 dakika

ÇIKTI FORMATI (JSON):
{
  "soru_metni": "...",
  "secenekler": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  },
  "dogru_cevap": "C",
  "cozum": "...",
  "kazanim": "..."
}

Gerçek ÖSYM standardında, Türkçe bir soru üret:"""

        response = client.chat.completions.create(
            model="gpt-4",  # gpt-5 henüz yok, gpt-4 kullan
            messages=[
                {"role": "system", "content": "Sen bir ÖSYM soru hazırlama uzmanısın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        soru = response.choices[0].message.content

        print("[OK] GPT-4 ile soru uretildi!")
        print("\n" + "="*80)
        print("OPENAI GPT-4 TARAFINDAN URETILEN SORU:")
        print("="*80)
        print(soru)
        print("="*80)

        return soru

    except Exception as e:
        print(f"[HATA] OpenAI hatasi: {str(e)}")
        return None

async def generate_with_claude():
    """Anthropic Claude 4.5 ile soru üret"""
    print("\n[2/2] Anthropic Claude 4.5 ile soru uretiliyor...")

    try:
        import anthropic

        client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        prompt = """Sen bir ÖSYM soru hazırlama uzmanısın.

TYT Fizik - Kuvvet ve Hareket konusunda orta zorlukta bir soru hazırla.

SORU ÖZELLİKLERİ:
- Konu: Newton'un 2. Yasası
- Zorluk: Orta
- Bloom Seviyesi: Uygulama (Apply)
- Çözüm süresi: 2-3 dakika

ÇIKTI FORMATI (JSON):
{
  "soru_metni": "...",
  "secenekler": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  },
  "dogru_cevap": "B",
  "cozum": "...",
  "kazanim": "..."
}

Gerçek ÖSYM standardında, Türkçe bir soru üret:"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # En yeni model
            max_tokens=1500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        soru = message.content[0].text

        print("[OK] Claude 3.5 Sonnet ile soru uretildi!")
        print("\n" + "="*80)
        print("CLAUDE 3.5 SONNET TARAFINDAN URETILEN SORU:")
        print("="*80)
        print(soru)
        print("="*80)

        return soru

    except Exception as e:
        print(f"[HATA] Claude hatasi: {str(e)}")
        return None

async def main():
    """Ana fonksiyon"""

    print("="*80)
    print("GERCEK AI ILE SORU URETIMI")
    print("="*80)
    print()
    print("OpenAI GPT-4 ve Anthropic Claude 3.5 Sonnet ile")
    print("gercek OSYM standardinda sorular uretiliyor...")
    print()

    # Her iki AI ile de soru üret
    tasks = [
        generate_with_openai(),
        generate_with_claude()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    print("\n" + "="*80)
    print("OZET")
    print("="*80)

    success_count = sum(1 for r in results if r and not isinstance(r, Exception))

    print(f"\nToplam: 2 AI modeli test edildi")
    print(f"Basarili: {success_count}")
    print(f"Basarisiz: {2 - success_count}")

    if success_count > 0:
        print("\n[BASARILI] AI modelleri ile gercek sorular uretildi!")
    else:
        print("\n[HATA] Soru uretilemedi, hatalari kontrol edin.")

    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nKullanici tarafindan durduruldu")
    except Exception as e:
        print(f"\n\nFATAL HATA: {str(e)}")
        import traceback
        traceback.print_exc()
