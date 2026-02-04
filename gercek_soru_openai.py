#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SORU ÜRETİMİ - OpenAI GPT-4
"""

import sys
import json
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def generate_with_openai():
    print("="*80)
    print("OPENAI GPT-4 ILE GERCEK SORU URETIMI")
    print("="*80)
    print()

    try:
        import openai

        api_key = "[REDACTED_OPENAI_KEY]"

        client = openai.OpenAI(api_key=api_key)

        # 3 farklı soru üret
        topics = [
            {
                "konu": "TYT Matematik - Türev",
                "prompt": """TYT Matematik sınavı için Türev konusunda orta zorlukta bir soru hazırla.

Soru özellikleri:
- Konu: Türev kuralları (toplam, çarpım, bölüm)
- Zorluk: Orta (2-3 dakika)
- Format: 5 şıklı çoktan seçmeli
- Dil: Türkçe
- Standart: ÖSYM TYT

JSON formatında döndür:
{
  "soru_metni": "...",
  "secenekler": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "dogru_cevap": "B",
  "cozum": "..."
}"""
            },
            {
                "konu": "TYT Fizik - Newton Yasaları",
                "prompt": """TYT Fizik sınavı için Newton'un 2. Yasası konusunda orta zorlukta bir soru hazırla.

Soru özellikleri:
- Konu: F = m·a formülü
- Zorluk: Orta (2-3 dakika)
- Format: 5 şıklı çoktan seçmeli
- Dil: Türkçe
- Standart: ÖSYM TYT

JSON formatında döndür."""
            },
            {
                "konu": "TYT Kimya - Mol Kavramı",
                "prompt": """TYT Kimya sınavı için Mol Kavramı konusunda kolay bir soru hazırla.

Soru özellikleri:
- Konu: Mol hesaplamaları
- Zorluk: Kolay (1-2 dakika)
- Format: 5 şıklı çoktan seçmeli
- Dil: Türkçe
- Standart: ÖSYM TYT

JSON formatında döndür."""
            }
        ]

        generated = []

        for idx, topic in enumerate(topics, 1):
            print(f"\n[{idx}/3] {topic['konu']} icin soru uretiliyor...")

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Sen bir ÖSYM soru hazırlama uzmanısın. Türkçe, standart ÖSYM formatında sorular üretirsin."},
                        {"role": "user", "content": topic['prompt']}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )

                soru_text = response.choices[0].message.content

                print(f"      [OK] Soru uretildi! ({len(soru_text)} karakter)")

                # JSON parse
                try:
                    if '```json' in soru_text:
                        json_start = soru_text.find('```json') + 7
                        json_end = soru_text.find('```', json_start)
                        json_text = soru_text[json_start:json_end].strip()
                    elif '{' in soru_text:
                        json_start = soru_text.find('{')
                        json_end = soru_text.rfind('}') + 1
                        json_text = soru_text[json_start:json_end]
                    else:
                        json_text = soru_text

                    soru_data = json.loads(json_text)
                    soru_data['_metadata'] = {
                        'konu': topic['konu'],
                        'ai_model': 'gpt-4'
                    }
                    generated.append(soru_data)
                    print(f"      [OK] JSON parse basarili")

                except:
                    generated.append({'_raw': soru_text, '_metadata': {'konu': topic['konu']}})
                    print(f"      [UYARI] JSON parse basarisiz, ham metin kaydedildi")

            except Exception as e:
                print(f"      [HATA] {str(e)[:100]}")

        # Sonuçları göster
        print()
        print("="*80)
        print("URETILEN SORULAR")
        print("="*80)

        for idx, soru in enumerate(generated, 1):
            print(f"\n{'='*70}")
            print(f"SORU {idx}")
            print(f"{'='*70}")

            if '_raw' in soru:
                print("\n[HAM METIN]")
                print(soru['_raw'])
            else:
                print(f"\nKonu: {soru['_metadata']['konu']}")
                print(f"\nSORU:")
                print(soru.get('soru_metni', 'N/A'))
                print(f"\nSECENEKLER:")
                for k, v in soru.get('secenekler', {}).items():
                    marker = " <-- DOGRU" if k == soru.get('dogru_cevap') else ""
                    print(f"  {k}) {v}{marker}")
                print(f"\nCOZUM:")
                print(soru.get('cozum', 'N/A'))

        # Kaydet
        with open('openai_uretilen_sorular.json', 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        print()
        print("="*80)
        print("OZET")
        print("="*80)
        print(f"\nToplam: {len(generated)} soru uretildi")
        print(f"Basarili: {sum(1 for s in generated if '_raw' not in s)}")
        print(f"Kaydedildi: openai_uretilen_sorular.json")
        print()
        print("[BASARILI] OpenAI GPT-4 ile gercek sorular uretildi!")
        print("="*80)

    except Exception as e:
        print(f"[HATA] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_with_openai()
