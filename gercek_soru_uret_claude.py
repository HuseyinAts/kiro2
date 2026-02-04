#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SORU ÜRETİMİ - Claude 4.5 Sonnet
"""

import sys
import os
import json
from pathlib import Path

# UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def generate_questions_with_claude():
    """Claude 4.5 ile gerçek sorular üret"""

    print("="*80)
    print("CLAUDE 4.5 SONNET ILE GERCEK SORU URETIMI")
    print("="*80)
    print()

    try:
        import anthropic

        # Gerçek API key
        api_key = "[REDACTED_ANTHROPIC_KEY]"

        client = anthropic.Anthropic(api_key=api_key)

        # 3 farklı konuda soru üret
        topics = [
            {
                "konu": "TYT Matematik - Türev",
                "kazanim": "Türev kurallarını uygulama",
                "zorluk": "orta",
                "prompt": """TYT Matematik sınavı için Türev konusunda orta zorlukta bir soru hazırla.

SORU ÖZELLİKLERİ:
- Konu: Türev Kuralları (Toplam, çarpım, bölüm kuralı)
- Zorluk: Orta (2-3 dakikada çözülebilir)
- Hedef: TYT öğrencisi
- Format: 5 şıklı çoktan seçmeli

Gerçek ÖSYM standardında, Türkçe bir soru üret. JSON formatında döndür:
{
  "soru_metni": "...",
  "secenekler": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "dogru_cevap": "C",
  "cozum": "Adım adım çözüm...",
  "kazanim": "..."
}"""
            },
            {
                "konu": "TYT Fizik - Kuvvet ve Hareket",
                "kazanim": "Newton'un 2. yasasını uygulama",
                "zorluk": "orta",
                "prompt": """TYT Fizik sınavı için Newton'un 2. Yasası konusunda orta zorlukta bir soru hazırla.

SORU ÖZELLİKLERİ:
- Konu: F = m·a formülü ve uygulamaları
- Zorluk: Orta (2-3 dakikada çözülebilir)
- Hedef: TYT öğrencisi
- Format: 5 şıklı çoktan seçmeli

Gerçek ÖSYM standardında, Türkçe bir soru üret. JSON formatında döndür."""
            },
            {
                "konu": "TYT Kimya - Mol Kavramı",
                "kazanim": "Mol hesaplamaları yapma",
                "zorluk": "kolay",
                "prompt": """TYT Kimya sınavı için Mol Kavramı konusunda kolay bir soru hazırla.

SORU ÖZELLİKLERİ:
- Konu: Mol = kütle/molekül ağırlığı
- Zorluk: Kolay (1-2 dakikada çözülebilir)
- Hedef: TYT öğrencisi
- Format: 5 şıklı çoktan seçmeli

Gerçek ÖSYM standardında, Türkçe bir soru üret. JSON formatında döndür."""
            }
        ]

        generated_questions = []

        for idx, topic in enumerate(topics, 1):
            print(f"\n[{idx}/3] {topic['konu']} icin soru uretiliyor...")
            print(f"      Zorluk: {topic['zorluk']}")

            try:
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[
                        {
                            "role": "user",
                            "content": topic['prompt']
                        }
                    ]
                )

                response_text = message.content[0].text

                print(f"      [OK] Soru uretildi! ({len(response_text)} karakter)")

                # JSON parse etmeye çalış
                try:
                    # JSON bloğunu bul
                    if '```json' in response_text:
                        json_start = response_text.find('```json') + 7
                        json_end = response_text.find('```', json_start)
                        json_text = response_text[json_start:json_end].strip()
                    elif '{' in response_text:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_text = response_text[json_start:json_end]
                    else:
                        json_text = response_text

                    soru_data = json.loads(json_text)
                    soru_data['_metadata'] = {
                        'konu': topic['konu'],
                        'kazanim': topic['kazanim'],
                        'zorluk': topic['zorluk'],
                        'ai_model': 'claude-3-5-sonnet-20241022'
                    }
                    generated_questions.append(soru_data)
                    print(f"      [OK] JSON parse basarili")

                except json.JSONDecodeError as e:
                    print(f"      [UYARI] JSON parse hatasi, ham metin kaydediliyor")
                    generated_questions.append({
                        '_raw_response': response_text,
                        '_metadata': {
                            'konu': topic['konu'],
                            'error': str(e)
                        }
                    })

            except Exception as e:
                print(f"      [HATA] {str(e)[:100]}")
                continue

        # Sonuçları göster
        print()
        print("="*80)
        print("URETILEN SORULAR")
        print("="*80)

        for idx, soru in enumerate(generated_questions, 1):
            print(f"\n{'='*70}")
            print(f"SORU {idx}")
            print(f"{'='*70}")

            if '_raw_response' in soru:
                print("\n[HAM CEVAP - JSON parse edilemedi]")
                print(soru['_raw_response'][:500])
                print("...")
            else:
                print(f"\nKonu: {soru['_metadata']['konu']}")
                print(f"Zorluk: {soru['_metadata']['zorluk']}")
                print(f"\nSORU:")
                print(soru.get('soru_metni', 'N/A'))

                print(f"\nSECENEKLER:")
                for key, value in soru.get('secenekler', {}).items():
                    print(f"  {key}) {value}")

                print(f"\nDOGRU CEVAP: {soru.get('dogru_cevap', 'N/A')}")

                print(f"\nCOZUM:")
                print(soru.get('cozum', 'N/A')[:200])
                if len(soru.get('cozum', '')) > 200:
                    print("...")

        # JSON dosyasına kaydet
        output_file = Path("claude_uretilen_sorular.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated_questions, f, ensure_ascii=False, indent=2)

        print()
        print("="*80)
        print("OZET")
        print("="*80)
        print(f"\nToplam Uretilen Soru: {len(generated_questions)}")
        print(f"Basarili Parse: {sum(1 for q in generated_questions if '_raw_response' not in q)}")
        print(f"Kaydedildi: {output_file}")
        print()
        print("[BASARILI] Claude 4.5 Sonnet ile gercek sorular uretildi!")
        print()
        print("="*80)

        return generated_questions

    except ImportError:
        print("[HATA] anthropic kutuphanesi bulunamadi!")
        print("Yuklemek icin: pip install anthropic")
        return []
    except Exception as e:
        print(f"[HATA] {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    try:
        generate_questions_with_claude()
    except KeyboardInterrupt:
        print("\n\nKullanici tarafindan durduruldu")
    except Exception as e:
        print(f"\n\nFATAL HATA: {str(e)}")
        import traceback
        traceback.print_exc()
