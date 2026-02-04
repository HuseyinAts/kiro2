#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20 SORU ÜRETİMİ - Her dersten farklı konular
Hızlı başlangıç için optimize edilmiş
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Unbuffered output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def log(msg):
    print(msg, flush=True)

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# 20 çeşitli soru - TYT'yi temsil eden
TOPICS = [
    # Matematik (5)
    {"ders": "Matematik", "konu": "Sayılar", "alt_konu": "Rasyonel Sayılar", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Denklemler", "alt_konu": "İkinci Dereceden Denklemler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "Türev", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Üçgenler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Olasılık", "alt_konu": "Kombinasyon", "zorluk": "zor"},

    # Fizik (4)
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Düzgün Değişen Hareket", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Kuvvet", "alt_konu": "Newton'un Hareket Yasaları", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Enerji", "alt_konu": "İş ve Enerji", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Elektrik", "alt_konu": "Elektrostatik", "zorluk": "zor"},

    # Kimya (4)
    {"ders": "Kimya", "konu": "Atom", "alt_konu": "Atom Modelleri", "zorluk": "kolay"},
    {"ders": "Kimya", "konu": "Mol", "alt_konu": "Mol Hesaplamaları", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Gazlar", "alt_konu": "İdeal Gaz Yasası", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Asit-Baz", "alt_konu": "pH Hesaplamaları", "zorluk": "zor"},

    # Biyoloji (4)
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Hücre Yapısı", "zorluk": "kolay"},
    {"ders": "Biyoloji", "konu": "Genetik", "alt_konu": "Mitoz Bölünme", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Fotosentez", "alt_konu": "Fotosentez Tepkimeleri", "zorluk": "zor"},
    {"ders": "Biyoloji", "konu": "Solunum", "alt_konu": "Hücresel Solunum", "zorluk": "orta"},

    # Türkçe (3)
    {"ders": "Türkçe", "konu": "Sözcükte Anlam", "alt_konu": "Deyimler", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Cümlede Anlam", "alt_konu": "Ana Düşünce", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Fiilimsiler", "alt_konu": "İsim-Fiil", "zorluk": "zor"},
]

def main():
    log("="*80)
    log("20 SORU ÜRETİMİ - PRODUCTION")
    log("="*80)
    log(f"Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("")

    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode

    kg_service = KnowledgeGraphService()
    log(f"[✓] Knowledge Graph: {len(kg_service.graph.nodes())} node")
    log("")

    try:
        import anthropic
        api_key = "[REDACTED_ANTHROPIC_KEY]"
        client = anthropic.Anthropic(api_key=api_key)
        log("[✓] Claude Sonnet 4.5 hazır")
        log("")

        generated = []
        errors = []
        start_time = time.time()

        for idx, topic in enumerate(TOPICS, 1):
            log(f"\n{'='*70}")
            log(f"SORU {idx}/20: {topic['ders']} - {topic['konu']}")
            log(f"{'='*70}")
            log(f"Alt Konu: {topic['alt_konu']} | Zorluk: {topic['zorluk']}")

            try:
                prompt = f"""TYT {topic['ders']} sınavı için '{topic['alt_konu']}' konusunda {topic['zorluk']} zorlukta bir çoktan seçmeli soru hazırla.

Soru özellikleri:
- Ders: {topic['ders']}
- Konu: {topic['konu']} - {topic['alt_konu']}
- Zorluk: {topic['zorluk']}
- Format: 5 şıklı çoktan seçmeli (A, B, C, D, E)
- Dil: Türkçe
- Standart: ÖSYM TYT

JSON formatında döndür:
{{
  "soru_metni": "...",
  "secenekler": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
  "dogru_cevap": "C",
  "cozum": "...",
  "kazanim": "..."
}}"""

                log("[AI] Claude çağrılıyor...")

                msg = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=1200,
                    temperature=0.7,
                    messages=[{'role': 'user', 'content': prompt}]
                )

                response_text = msg.content[0].text
                log(f"[✓] Yanıt alındı ({len(response_text)} karakter)")

                # JSON parse
                if '```json' in response_text:
                    start = response_text.find('```json') + 7
                    end = response_text.find('```', start)
                    json_text = response_text[start:end].strip()
                elif '{' in response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    json_text = response_text[start:end]
                else:
                    json_text = response_text

                soru_data = json.loads(json_text)

                # Knowledge Graph
                question_node = QuestionNode(
                    id=f"PROD_{topic['ders'][:3].upper()}_Q{idx:03d}",
                    konu=f"{topic['ders']} - {topic['konu']}",
                    kazanim=soru_data.get('kazanim', topic['alt_konu']),
                    bloom_level='apply' if topic['zorluk'] == 'orta' else ('remember' if topic['zorluk'] == 'kolay' else 'analyze'),
                    irt_difficulty={'kolay': -0.5, 'orta': 0.0, 'zor': 0.8}[topic['zorluk']],
                    cognitive_skills=['problem_solving']
                )
                kg_service.add_question_node(question_node)

                # Metadata
                soru_data['_metadata'] = {
                    'id': question_node.id,
                    'ders': topic['ders'],
                    'konu': topic['konu'],
                    'alt_konu': topic['alt_konu'],
                    'zorluk': topic['zorluk'],
                    'ai_model': 'claude-sonnet-4-20250514',
                    'irt_difficulty': question_node.irt_difficulty,
                    'bloom_level': question_node.bloom_level,
                    'created_at': datetime.now().isoformat()
                }

                generated.append(soru_data)

                log(f"[✓] ID: {question_node.id}")
                log(f"[✓] Soru: {soru_data['soru_metni'][:60]}...")
                log(f"[✓] Doğru: {soru_data['dogru_cevap']}")

                # Her 5 soruda rapor
                if idx % 5 == 0:
                    elapsed = time.time() - start_time
                    remaining = (20 - idx) * (elapsed / idx)
                    log(f"\n[İLERLEME] {idx}/20 ({idx*100//20}%) | Geçen: {elapsed/60:.1f}dk | Kalan: ~{remaining/60:.1f}dk\n")

            except Exception as e:
                err_msg = f"Soru {idx} hata: {str(e)[:80]}"
                log(f"[✗] {err_msg}")
                errors.append(err_msg)

            # Rate limit
            time.sleep(1.5)

        # Kaydet
        output_file = "URETILEN_20_SORU.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        # Rapor
        total_time = time.time() - start_time
        dersler = {}
        for s in generated:
            ders = s['_metadata']['ders']
            dersler[ders] = dersler.get(ders, 0) + 1

        log("")
        log("="*80)
        log("SONUÇ RAPORU")
        log("="*80)
        log(f"\nÜretilen:            {len(generated)}/20 ({len(generated)*100//20}%)")
        log(f"Knowledge Graph:     {len(kg_service.graph.nodes())} node")
        log(f"Hatalar:             {len(errors)}")
        log(f"Süre:                {total_time/60:.1f} dakika")
        log(f"Ortalama:            {total_time/len(generated):.1f} sn/soru")
        log("")
        log("DERS DAĞILIMI:")
        for ders, count in sorted(dersler.items()):
            log(f"  {ders:12s}: {count:2d} soru")
        log("")
        log(f"Kaydedildi:          {output_file}")
        log(f"Bitiş:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("")

        if len(generated) >= 18:
            log("[✓✓✓] MÜKEMMEL! 20 soruluk soru bankası oluşturuldu!")
        elif len(generated) >= 15:
            log("[✓✓] ÇOK İYİ! Soru bankası hazır!")
        else:
            log("[✓] Soru bankası oluşturuldu!")

        log("="*80)

        return generated

    except Exception as e:
        log(f"[✗] FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    main()
