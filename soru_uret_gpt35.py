#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SORU ÜRETİMİ - OpenAI GPT-3.5-Turbo
"""

import sys
import json
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def generate():
    print("="*80)
    print("OPENAI GPT-3.5-TURBO ILE GERCEK SORU URETIMI")
    print("="*80)
    print()

    try:
        import openai

        api_key = "[REDACTED_OPENAI_KEY]"

        client = openai.OpenAI(api_key=api_key)

        prompts = [
            "TYT Matematik Türev konusunda orta zorlukta çoktan seçmeli bir soru hazırla. JSON formatında döndür: {\"soru_metni\": \"...\", \"secenekler\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\", \"E\": \"...\"}, \"dogru_cevap\": \"C\", \"cozum\": \"...\"}",
            "TYT Fizik Newton'un 2. Yasası konusunda orta zorlukta çoktan seçmeli bir soru hazırla. JSON formatında döndür.",
            "TYT Kimya Mol Kavramı konusunda kolay çoktan seçmeli bir soru hazırla. JSON formatında döndür."
        ]

        generated = []

        for idx, prompt in enumerate(prompts, 1):
            print(f"[{idx}/3] Soru uretiliyor...")

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Ücretsiz hesaplarda mevcut
                    messages=[
                        {"role": "system", "content": "Sen ÖSYM soru uzmanısın."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )

                text = response.choices[0].message.content
                print(f"    [OK] Uretildi! ({len(text)} karakter)")

                try:
                    if '```json' in text:
                        start = text.find('```json') + 7
                        end = text.find('```', start)
                        text = text[start:end].strip()
                    elif '{' in text:
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        text = text[start:end]

                    data = json.loads(text)
                    generated.append(data)
                    print(f"    [OK] JSON parse basarili")
                except:
                    generated.append({'_raw': text})
                    print(f"    [UYARI] JSON parse basarisiz")

            except Exception as e:
                print(f"    [HATA] {str(e)[:80]}")

        print()
        print("="*80)
        print("URETILEN SORULAR")
        print("="*80)

        for idx, soru in enumerate(generated, 1):
            print(f"\nSORU {idx}:")
            print("-"*70)
            if '_raw' in soru:
                print(soru['_raw'][:300])
            else:
                print(f"Soru: {soru.get('soru_metni', 'N/A')[:80]}...")
                print(f"Dogru: {soru.get('dogru_cevap', 'N/A')}")
            print()

        with open('gpt35_sorular.json', 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        print("="*80)
        print(f"Toplam: {len(generated)} soru | Basarili: {sum(1 for s in generated if '_raw' not in s)}")
        print("Kaydedildi: gpt35_sorular.json")
        print("="*80)

    except Exception as e:
        print(f"HATA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate()
