#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOPLU SORU ÜRETİMİ - PRODUCTION MODE
Claude Sonnet 4.5 ile TYT için kapsamlı soru bankası oluşturma
Tüm servislerle entegre + Database'e kayıt
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Backend path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# TYT Konuları - Kapsamlı Liste
TYT_TOPICS = [
    # MATEMATİK (40 soru)
    {"ders": "Matematik", "konu": "Temel Kavramlar", "alt_konu": "Rasyonel Sayılar", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Temel Kavramlar", "alt_konu": "Üslü Sayılar", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Denklemler", "alt_konu": "Birinci Dereceden Denklemler", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Denklemler", "alt_konu": "İkinci Dereceden Denklemler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "Fonksiyon Kavramı", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "Türev", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Üçgenler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Daire ve Çember", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Analitik Geometri", "alt_konu": "Doğru Denklemi", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Olasılık", "alt_konu": "Permütasyon ve Kombinasyon", "zorluk": "zor"},

    # FİZİK (14 soru)
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Düzgün Doğrusal Hareket", "zorluk": "kolay"},
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Düzgün Değişen Hareket", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Kuvvet", "alt_konu": "Newton'un Hareket Yasaları", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Enerji", "alt_konu": "İş, Güç ve Enerji", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Elektrik", "alt_konu": "Elektrostatik", "zorluk": "zor"},
    {"ders": "Fizik", "konu": "Optik", "alt_konu": "Işık ve Aynalar", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Dalgalar", "alt_konu": "Ses Dalgaları", "zorluk": "orta"},

    # KİMYA (13 soru)
    {"ders": "Kimya", "konu": "Atom", "alt_konu": "Atom Modelleri", "zorluk": "kolay"},
    {"ders": "Kimya", "konu": "Atom", "alt_konu": "Elektron Dizilimi", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Kimyasal Hesaplamalar", "alt_konu": "Mol Kavramı", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Gazlar", "alt_konu": "Gaz Yasaları", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Çözeltiler", "alt_konu": "Derişim Birimleri", "zorluk": "zor"},
    {"ders": "Kimya", "konu": "Asit-Baz", "alt_konu": "pH Hesaplamaları", "zorluk": "zor"},

    # BİYOLOJİ (13 soru)
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Hücre Yapısı ve Organelleri", "zorluk": "kolay"},
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Hücre Zarından Madde Geçişi", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Canlıların Sınıflandırılması", "alt_konu": "Sistematik", "zorluk": "kolay"},
    {"ders": "Biyoloji", "konu": "Genetik", "alt_konu": "Mitoz ve Mayoz", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Fotosentez", "alt_konu": "Işık ve Karanlık Tepkimeleri", "zorluk": "zor"},
    {"ders": "Biyoloji", "konu": "Solunum", "alt_konu": "Hücresel Solunum", "zorluk": "orta"},

    # TÜRKÇE (40 soru)
    {"ders": "Türkçe", "konu": "Sözcükte Anlam", "alt_konu": "Gerçek ve Mecaz Anlam", "zorluk": "kolay"},
    {"ders": "Türkçe", "konu": "Sözcükte Anlam", "alt_konu": "Deyimler ve Atasözleri", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Cümlede Anlam", "alt_konu": "Ana Düşünce ve Yardımcı Düşünce", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Paragraf", "alt_konu": "Paragrafın Ana Fikri", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Fiilimsiler", "alt_konu": "İsim-Fiil", "zorluk": "zor"},
    {"ders": "Türkçe", "konu": "Yapı Bilgisi", "alt_konu": "Ekler ve Görevleri", "zorluk": "orta"},

    # SOSYAL BİLİMLER (20 soru)
    {"ders": "Tarih", "konu": "İlk Çağ", "alt_konu": "İlk Uygarlıklar", "zorluk": "kolay"},
    {"ders": "Tarih", "konu": "Osmanlı Tarihi", "alt_konu": "Kuruluş Dönemi", "zorluk": "orta"},
    {"ders": "Tarih", "konu": "Türkiye Cumhuriyeti", "alt_konu": "Atatürk İlkeleri", "zorluk": "orta"},
    {"ders": "Coğrafya", "konu": "Fiziki Coğrafya", "alt_konu": "İklim Tipleri", "zorluk": "orta"},
    {"ders": "Coğrafya", "konu": "Beşeri Coğrafya", "alt_konu": "Nüfus ve Göç", "zorluk": "orta"},
]

async def generate_questions_async():
    """Async olarak toplu soru üretimi"""
    print("="*80)
    print("TOPLU SORU ÜRETİMİ - PRODUCTION MODE")
    print("="*80)
    print(f"Hedef: {len(TYT_TOPICS)} soru")
    print(f"Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Import services
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
    from services.hitl_workflow_service import HITLWorkflowService
    from services.plagiarism_detection_service import PlagiarismDetectionService
    from core.database import get_db_pool

    kg_service = KnowledgeGraphService()
    hitl_service = HITLWorkflowService()
    plagiarism_service = PlagiarismDetectionService()

    print(f"[✓] Knowledge Graph: {len(kg_service.graph.nodes())} node")
    print(f"[✓] HITL Workflow: {len(hitl_service.experts)} expert")
    print(f"[✓] Plagiarism Detection: Hazır")
    print()

    try:
        import anthropic
        api_key = "[REDACTED_ANTHROPIC_KEY]"
        client = anthropic.Anthropic(api_key=api_key)
        print("[✓] Claude Sonnet 4.5 API hazır")
        print()

        # Database pool
        db_pool = await get_db_pool()
        print("[✓] PostgreSQL bağlantısı hazır")
        print()

        generated = []
        errors = []
        db_saved = 0

        for idx, topic in enumerate(TYT_TOPICS, 1):
            print(f"\n{'='*70}")
            print(f"SORU {idx}/{len(TYT_TOPICS)}: {topic['ders']} - {topic['konu']}")
            print(f"{'='*70}")
            print(f"Alt Konu: {topic['alt_konu']}")
            print(f"Zorluk: {topic['zorluk']}")
            print()

            try:
                # Claude'a prompt
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

                print(f"[AI] Claude'a gönderiliyor...")

                msg = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=1200,
                    temperature=0.7,
                    messages=[{'role': 'user', 'content': prompt}]
                )

                response_text = msg.content[0].text
                print(f"[✓] AI yanıtı alındı ({len(response_text)} karakter)")

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

                # Knowledge Graph'a ekle
                question_node = QuestionNode(
                    id=f"TYT_{topic['ders'][:3].upper()}_Q{idx:03d}",
                    konu=f"{topic['ders']} - {topic['konu']}",
                    kazanim=soru_data.get('kazanim', topic['alt_konu']),
                    bloom_level='apply' if topic['zorluk'] == 'orta' else ('remember' if topic['zorluk'] == 'kolay' else 'analyze'),
                    irt_difficulty={'kolay': -0.5, 'orta': 0.0, 'zor': 0.8}[topic['zorluk']],
                    cognitive_skills=['problem_solving']
                )
                kg_service.add_question_node(question_node)
                print(f"[✓] Knowledge Graph'a eklendi")

                # Plagiarism check
                similarity_score = await plagiarism_service.check_similarity(
                    soru_data['soru_metni'],
                    [s['soru_metni'] for s in generated if 'soru_metni' in s]
                )
                print(f"[✓] Plagiarism: {similarity_score:.2%}")

                # HITL review (eğer gerekirse)
                if similarity_score > 0.7:
                    task = hitl_service.create_review_task(
                        question_id=question_node.id,
                        question_text=soru_data['soru_metni'],
                        priority='high',
                        reason=f"Yüksek benzerlik: {similarity_score:.2%}"
                    )
                    print(f"[!] HITL review oluşturuldu: {task.task_id}")

                # Metadata ekle
                soru_data['_metadata'] = {
                    'id': question_node.id,
                    'ders': topic['ders'],
                    'konu': topic['konu'],
                    'alt_konu': topic['alt_konu'],
                    'zorluk': topic['zorluk'],
                    'ai_model': 'claude-sonnet-4-20250514',
                    'irt_difficulty': question_node.irt_difficulty,
                    'similarity_score': similarity_score,
                    'created_at': datetime.now().isoformat()
                }

                # Database'e kaydet
                async with db_pool.acquire() as conn:
                    try:
                        await conn.execute("""
                            INSERT INTO sorular (
                                soru_id, ders, konu, alt_konu, zorluk,
                                soru_metni, secenekler, dogru_cevap, cozum,
                                irt_difficulty, ai_model, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                        """,
                            question_node.id,
                            topic['ders'],
                            topic['konu'],
                            topic['alt_konu'],
                            topic['zorluk'],
                            soru_data['soru_metni'],
                            json.dumps(soru_data['secenekler'], ensure_ascii=False),
                            soru_data['dogru_cevap'],
                            soru_data['cozum'],
                            question_node.irt_difficulty,
                            'claude-sonnet-4-20250514'
                        )
                        db_saved += 1
                        print(f"[✓] Database'e kaydedildi")
                    except Exception as db_err:
                        print(f"[⚠] Database kayıt hatası: {str(db_err)[:50]}")

                generated.append(soru_data)

                # Kısa özet
                print()
                print(f"Soru: {soru_data['soru_metni'][:60]}...")
                print(f"Doğru Cevap: {soru_data['dogru_cevap']}")
                print()

            except Exception as e:
                error_msg = f"Soru {idx} hata: {str(e)[:100]}"
                print(f"[✗] {error_msg}")
                errors.append(error_msg)

            # Rate limiting - 1 saniye bekle
            await asyncio.sleep(1)

        # JSON'a kaydet
        output_file = "PRODUCTION_SORU_BANKASI.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        # Sonuç raporu
        print()
        print("="*80)
        print("SONUÇ RAPORU")
        print("="*80)
        print(f"\nToplam Üretilen:     {len(generated)}/{len(TYT_TOPICS)}")
        print(f"Database'e Kaydedilen: {db_saved}")
        print(f"Knowledge Graph:     {len(kg_service.graph.nodes())} node")
        print(f"Hatalar:             {len(errors)}")
        print(f"JSON Dosya:          {output_file}")
        print(f"Bitiş:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if errors:
            print("HATALAR:")
            for err in errors[:5]:
                print(f"  - {err}")

        print()
        print("[✓] PRODUCTION SORU BANKASI OLUŞTURULDU!")
        print("="*80)

        await db_pool.close()
        return generated

    except Exception as e:
        print(f"[✗] FATAL HATA: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(generate_questions_async())
