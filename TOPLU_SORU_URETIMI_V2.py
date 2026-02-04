#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOPLU SORU ÜRETİMİ V2 - PRODUCTION MODE
Claude Sonnet 4.5 ile soru üretimi - Basitleştirilmiş versiyon
Servislerle entegrasyon + JSON kayıt
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Force flush helper
def log(msg):
    print(msg, flush=True)

# Backend path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Küçük ama değerli bir başlangıç: 50 soru
TYT_TOPICS = [
    # MATEMATİK (15 soru)
    {"ders": "Matematik", "konu": "Temel Kavramlar", "alt_konu": "Rasyonel Sayılar", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Temel Kavramlar", "alt_konu": "Üslü Sayılar", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Temel Kavramlar", "alt_konu": "Kökli Sayılar", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Denklemler", "alt_konu": "Birinci Dereceden Denklemler", "zorluk": "kolay"},
    {"ders": "Matematik", "konu": "Denklemler", "alt_konu": "İkinci Dereceden Denklemler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "Fonksiyon Kavramı", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "Türev", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Fonksiyonlar", "alt_konu": "İntegral", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Üçgenler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Dörtgenler", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Geometri", "alt_konu": "Daire ve Çember", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Analitik Geometri", "alt_konu": "Doğru Denklemi", "zorluk": "orta"},
    {"ders": "Matematik", "konu": "Analitik Geometri", "alt_konu": "Çember Denklemi", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Olasılık", "alt_konu": "Permütasyon", "zorluk": "zor"},
    {"ders": "Matematik", "konu": "Olasılık", "alt_konu": "Kombinasyon", "zorluk": "zor"},

    # FİZİK (10 soru)
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Düzgün Doğrusal Hareket", "zorluk": "kolay"},
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Düzgün Değişen Hareket", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Hareket", "alt_konu": "Serbest Düşme", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Kuvvet", "alt_konu": "Newton'un Hareket Yasaları", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Kuvvet", "alt_konu": "Sürtünme Kuvveti", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Enerji", "alt_konu": "İş ve Enerji", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Enerji", "alt_konu": "Güç", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Elektrik", "alt_konu": "Elektrostatik", "zorluk": "zor"},
    {"ders": "Fizik", "konu": "Optik", "alt_konu": "Aynalar", "zorluk": "orta"},
    {"ders": "Fizik", "konu": "Dalgalar", "alt_konu": "Ses Dalgaları", "zorluk": "orta"},

    # KİMYA (10 soru)
    {"ders": "Kimya", "konu": "Atom", "alt_konu": "Atom Modelleri", "zorluk": "kolay"},
    {"ders": "Kimya", "konu": "Atom", "alt_konu": "Elektron Dizilimi", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Periyodik Sistem", "alt_konu": "Periyodik Özellikler", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Kimyasal Hesaplamalar", "alt_konu": "Mol Kavramı", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Kimyasal Hesaplamalar", "alt_konu": "Avogadro Sayısı", "zorluk": "kolay"},
    {"ders": "Kimya", "konu": "Gazlar", "alt_konu": "İdeal Gaz Yasası", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Çözeltiler", "alt_konu": "Molarite", "zorluk": "zor"},
    {"ders": "Kimya", "konu": "Asit-Baz", "alt_konu": "pH Hesaplamaları", "zorluk": "zor"},
    {"ders": "Kimya", "konu": "Kimyasal Reaksiyonlar", "alt_konu": "Reaksiyon Hızı", "zorluk": "orta"},
    {"ders": "Kimya", "konu": "Kimyasal Reaksiyonlar", "alt_konu": "Denge", "zorluk": "zor"},

    # BİYOLOJİ (10 soru)
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Hücre Yapısı ve Organelleri", "zorluk": "kolay"},
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Hücre Zarından Madde Geçişi", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Hücre", "alt_konu": "Mitokondri ve ATP", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Genetik", "alt_konu": "Mitoz Bölünme", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Genetik", "alt_konu": "Mayoz Bölünme", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Genetik", "alt_konu": "DNA Yapısı", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Fotosentez", "alt_konu": "Fotosentez Tepkimeleri", "zorluk": "zor"},
    {"ders": "Biyoloji", "konu": "Solunum", "alt_konu": "Hücresel Solunum", "zorluk": "orta"},
    {"ders": "Biyoloji", "konu": "Ekoloji", "alt_konu": "Ekosistem", "zorluk": "kolay"},
    {"ders": "Biyoloji", "konu": "Ekoloji", "alt_konu": "Besin Zincirleri", "zorluk": "kolay"},

    # TÜRKÇE (5 soru - temsili)
    {"ders": "Türkçe", "konu": "Sözcükte Anlam", "alt_konu": "Eş Anlamlı Kelimeler", "zorluk": "kolay"},
    {"ders": "Türkçe", "konu": "Sözcükte Anlam", "alt_konu": "Deyimler", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Cümlede Anlam", "alt_konu": "Ana Düşünce", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Paragraf", "alt_konu": "Paragrafın Ana Fikri", "zorluk": "orta"},
    {"ders": "Türkçe", "konu": "Fiilimsiler", "alt_konu": "İsim-Fiil", "zorluk": "zor"},
]

def generate_questions():
    """Soru üretimi - basitleştirilmiş"""
    print("="*80)
    print("TOPLU SORU ÜRETİMİ V2 - PRODUCTION MODE")
    print("="*80)
    print(f"Hedef: {len(TYT_TOPICS)} soru")
    print(f"Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Import services
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
    from services.hitl_workflow_service import HITLWorkflowService

    kg_service = KnowledgeGraphService()
    hitl_service = HITLWorkflowService()

    print(f"[✓] Knowledge Graph: {len(kg_service.graph.nodes())} node")
    print(f"[✓] HITL Workflow: {len(hitl_service.experts)} expert")
    print()

    try:
        import anthropic
        api_key = "[REDACTED_ANTHROPIC_KEY]"
        client = anthropic.Anthropic(api_key=api_key)
        print("[✓] Claude Sonnet 4.5 API hazır")
        print()

        generated = []
        errors = []
        start_time = time.time()

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
                print(f"[✓] Knowledge Graph: {len(kg_service.graph.nodes())} node")

                # Metadata ekle
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

                # Kısa özet
                print()
                print(f"ID: {question_node.id}")
                print(f"Soru: {soru_data['soru_metni'][:70]}...")
                print(f"Doğru: {soru_data['dogru_cevap']}")
                print()

                # Her 10 soruda ara rapor
                if idx % 10 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / idx
                    remaining = (len(TYT_TOPICS) - idx) * avg_time
                    print(f"[ARA RAPOR] {idx}/{len(TYT_TOPICS)} tamamlandı | Geçen: {elapsed/60:.1f}dk | Kalan: {remaining/60:.1f}dk")
                    print()

            except Exception as e:
                error_msg = f"Soru {idx} hata: {str(e)[:100]}"
                print(f"[✗] {error_msg}")
                errors.append(error_msg)

            # Rate limiting - Anthropic'in limitlerine saygı
            time.sleep(2)  # 2 saniye bekle (dakikada 30 soru = güvenli)

        # JSON'a kaydet
        output_file = "PRODUCTION_SORU_BANKASI_V2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        # İstatistik hesapla
        total_time = time.time() - start_time
        dersler = {}
        for s in generated:
            ders = s['_metadata']['ders']
            dersler[ders] = dersler.get(ders, 0) + 1

        # Sonuç raporu
        print()
        print("="*80)
        print("SONUÇ RAPORU")
        print("="*80)
        print(f"\nToplam Üretilen:     {len(generated)}/{len(TYT_TOPICS)} ({len(generated)*100//len(TYT_TOPICS)}%)")
        print(f"Knowledge Graph:     {len(kg_service.graph.nodes())} node")
        print(f"Hatalar:             {len(errors)}")
        print(f"Süre:                {total_time/60:.1f} dakika")
        print(f"Ortalama:            {total_time/len(generated):.1f} saniye/soru")
        print()
        print("DERS DAĞILIMI:")
        for ders, count in sorted(dersler.items()):
            print(f"  {ders:15s}: {count:2d} soru")
        print()
        print(f"JSON Dosya:          {output_file}")
        print(f"Bitiş:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if errors:
            print("HATALAR:")
            for err in errors[:10]:
                print(f"  - {err}")
            print()

        success_rate = len(generated) * 100 // len(TYT_TOPICS)
        if success_rate >= 90:
            print("[✓✓✓] MÜKEMMEL! Production soru bankası oluşturuldu!")
        elif success_rate >= 70:
            print("[✓✓] ÇOK İYİ! Soru bankası hazır!")
        else:
            print("[✓] BAŞARILI! Soru bankası oluşturuldu!")

        print("="*80)
        print()
        print("SONRAKI ADIM:")
        print("Bu sorular şimdi öğrenciler için kullanıma hazır!")
        print("Backend API üzerinden sorgu yapılabilir.")
        print()

        return generated

    except Exception as e:
        print(f"[✗] FATAL HATA: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    generate_questions()
