"""
Basit 50 Soru Üretimi ve ÖSYM Kalite Değerlendirmesi
Sadece REAL OSYMQuestionGenerator kullanır
"""

import sys
import os
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from datetime import datetime

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv('backend/.env')

# Force reload OPENAI_API_KEY from .env (override shell env)
import os
backend_env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
with open(backend_env_path, 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            key = line.strip().split('=', 1)[1]
            os.environ['OPENAI_API_KEY'] = key
            print(f"[INFO] Loaded OpenAI API key from .env: {key[:20]}...")
            break

# REAL OSYM Generator - NO MOCK
from services.osym_question_generator import OSYMQuestionGenerator
from services.llm.ensemble_manager import MultiLLMEnsembleManager

# Soru konuları
MATEMATIK_KONULAR = [
    {"topic": "Sayılar", "subtopic": "Tam Sayılar"},
    {"topic": "Cebir", "subtopic": "Denklemler"},
    {"topic": "Fonksiyonlar", "subtopic": "Fonksiyon Türleri"},
    {"topic": "Geometri", "subtopic": "Üçgenler"},
    {"topic": "Olasılık", "subtopic": "Olasılık Hesaplama"}
]

async def generate_50_questions():
    """50 soru üret"""
    print("=" * 80)
    print(">>> 50 SORU ÜRETİMİ BAŞLIYOR (REAL OSYM GENERATOR)")
    print("=" * 80)
    print()

    # Initialize REAL generator
    ensemble = MultiLLMEnsembleManager()
    generator = OSYMQuestionGenerator(ensemble)

    questions = []

    # Her konudan 10 soru üret (5 konu x 10 = 50 soru)
    for konu_idx, konu in enumerate(MATEMATIK_KONULAR, 1):
        print(f"\n[{konu_idx}/5] Konu: {konu['topic']} - {konu['subtopic']}")
        print("-" * 80)

        for soru_no in range(1, 11):
            try:
                global_idx = (konu_idx - 1) * 10 + soru_no
                print(f"  [{global_idx}/50] Generating...", end=" ", flush=True)

                # REAL OSYM generator
                question = await generator.generate_question(
                    topic=konu['topic'],
                    subtopic=konu['subtopic'],
                    exam_type="TYT",
                    subject="Matematik",
                    difficulty=0.5 + (soru_no - 1) * 0.04,  # 0.5 to 0.86
                    bloom_level=((soru_no - 1) % 4) + 2,  # 2-5
                    generation_method='ensemble',
                    save_to_db=False
                )

                questions.append(question)
                q_score = question.get('quality_score_total', 0)
                print(f"OK (Quality: {q_score:.3f})")

            except Exception as e:
                print(f"FAILED: {e}")
                continue

    print("\n" + "=" * 80)
    print(f">>> ÜRETİM TAMAMLANDI: {len(questions)}/50 soru")
    print("=" * 80)

    return questions


def evaluate_and_report(questions):
    """Basit kalite değerlendirmesi ve rapor"""
    print("\n" + "=" * 80)
    print(">>> KALİTE DEĞERLENDİRMESİ")
    print("=" * 80)
    print()

    # Kalite skorları
    scores = [q.get('quality_score_total', 0) for q in questions]
    osym_scores = [q.get('osym_compliance_score', 0) for q in questions if 'osym_compliance_score' in q]

    avg_quality = sum(scores) / len(scores) if scores else 0
    avg_osym = sum(osym_scores) / len(osym_scores) if osym_scores else 0

    # Sınıflandırma
    excellent = sum(1 for s in scores if s >= 0.9)
    good = sum(1 for s in scores if 0.8 <= s < 0.9)
    acceptable = sum(1 for s in scores if 0.7 <= s < 0.8)
    poor = sum(1 for s in scores if s < 0.7)

    # Rapor
    report = []
    report.append("=" * 100)
    report.append("   50 SORU ÜRETİMİ ve ÖSYM KALİTE DEĞERLENDİRMESİ RAPORU")
    report.append("=" * 100)
    report.append(f"\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Toplam Soru: {len(questions)}")
    report.append(f"Generator: REAL OSYMQuestionGenerator (Multi-LLM Ensemble - NO MOCK)")

    report.append("\n" + "=" * 100)
    report.append("GENEL KALİTE SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama Skor:  {avg_quality:.4f} / 1.0")
    report.append(f"En Düşük:       {min(scores):.4f}")
    report.append(f"En Yüksek:      {max(scores):.4f}")

    report.append("\nKalite Dağılımı:")
    report.append(f"  Mükemmel (0.9+):     {excellent:3d} soru ({excellent/len(questions)*100:5.1f}%)")
    report.append(f"  İyi (0.8-0.9):       {good:3d} soru ({good/len(questions)*100:5.1f}%)")
    report.append(f"  Kabul Edilebilir:    {acceptable:3d} soru ({acceptable/len(questions)*100:5.1f}%)")
    report.append(f"  Zayıf (<0.7):        {poor:3d} soru ({poor/len(questions)*100:5.1f}%)")

    if osym_scores:
        report.append("\n" + "=" * 100)
        report.append("ÖSYM UYUMLULUK SKORU")
        report.append("=" * 100)
        report.append(f"Ortalama ÖSYM Skoru: {avg_osym:.4f} / 1.0")

    report.append("\n" + "=" * 100)
    report.append("BAŞARI KRİTERLERİ")
    report.append("=" * 100)

    c1 = "[OK]" if avg_quality >= 0.8 else "[FAIL]"
    report.append(f"1. Ortalama Kalite >= 0.8:  {c1} ({avg_quality:.4f})")

    c2 = "[OK]" if avg_osym >= 0.85 else "[FAIL]"
    report.append(f"2. ÖSYM Uyumluluk >= 0.85:  {c2} ({avg_osym:.4f})")

    good_pct = (excellent + good) / len(questions) * 100
    c3 = "[OK]" if good_pct >= 80 else "[FAIL]"
    report.append(f"3. İyi/Mükemmel >= 80%:     {c3} ({good_pct:.1f}%)")

    poor_pct = poor / len(questions) * 100
    c4 = "[OK]" if poor_pct <= 5 else "[FAIL]"
    report.append(f"4. Zayıf Soru <= 5%:        {c4} ({poor_pct:.1f}%)")

    all_pass = all([avg_quality >= 0.8, avg_osym >= 0.85, good_pct >= 80, poor_pct <= 5])

    report.append("\n" + "=" * 100)
    if all_pass:
        report.append("SONUÇ: TÜM KRİTERLER SAĞLANDI - ÖSYM KALİTE STANDARTLARI KARŞILANDI!")
    else:
        report.append("SONUÇ: BAZI KRİTERLER SAĞLANAMADI - İYİLEŞTİRME GEREKLİ")
    report.append("=" * 100)

    # En iyi 5 soru
    sorted_q = sorted(zip(questions, scores), key=lambda x: x[1], reverse=True)[:5]
    report.append("\n" + "=" * 100)
    report.append("EN İYİ 5 SORU")
    report.append("=" * 100)

    for i, (q, score) in enumerate(sorted_q, 1):
        report.append(f"\n{i}. Soru (Skor: {score:.4f}):")
        report.append(f"   Konu: {q.get('topic', 'N/A')} / {q.get('subtopic', 'N/A')}")
        report.append(f"   Zorluk: {q.get('difficulty', 0):.2f}")
        report.append(f"   Bloom: {q.get('bloom_level', 'N/A')}")

    report.append("\n" + "=" * 100)

    report_text = "\n".join(report)
    print(report_text)

    return {
        'questions': questions,
        'avg_quality': avg_quality,
        'avg_osym': avg_osym,
        'excellent': excellent,
        'good': good,
        'acceptable': acceptable,
        'poor': poor,
        'report': report_text
    }


async def main():
    try:
        # Step 1: Generate 50 questions
        questions = await generate_50_questions()

        if len(questions) < 10:
            print(f"\n[ERROR] Only {len(questions)} questions generated. Minimum 10 required.")
            return

        # Step 2: Evaluate and report
        results = evaluate_and_report(questions)

        # Step 3: Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        json_file = f'question_results_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            # Remove report from JSON (too large)
            json_data = {k: v for k, v in results.items() if k != 'report'}
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        report_file = f'quality_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(results['report'])

        print(f"\n[SAVE] Results saved to: {json_file}")
        print(f"[SAVE] Report saved to: {report_file}")
        print("\n[OK] Process completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
