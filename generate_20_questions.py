"""
20 Soru Üretimi ve ÖSYM Kalite Değerlendirmesi
Claude AI ile REAL soru üretimi
"""
import sys
import os
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from datetime import datetime

# Load API keys
from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.osym_question_generator import OSYMQuestionGenerator
from services.llm.ensemble_manager import MultiLLMEnsembleManager

# Matematik konuları
KONULAR = [
    {"topic": "Sayılar", "subtopic": "Tam Sayılar", "diff": 0.4},
    {"topic": "Cebir", "subtopic": "Denklemler", "diff": 0.5},
    {"topic": "Fonksiyonlar", "subtopic": "Doğrusal Fonksiyonlar", "diff": 0.6},
    {"topic": "Geometri", "subtopic": "Üçgenler", "diff": 0.7},
]


async def generate_20_questions():
    """20 soru üret"""
    print("=" * 80)
    print(">>> 20 SORU ÜRETİMİ (CLAUDE AI)")
    print("=" * 80)
    print()

    ensemble = MultiLLMEnsembleManager(
        enable_openai=False,  # OpenAI quota aşıldı
        enable_claude=True,
        enable_qwen=False
    )

    generator = OSYMQuestionGenerator(ensemble)
    questions = []

    # Her konudan 5 soru (4 konu x 5 = 20 soru)
    for konu_idx, konu in enumerate(KONULAR, 1):
        print(f"\n[{konu_idx}/4] Konu: {konu['topic']} - {konu['subtopic']}")
        print("-" * 80)

        for soru_no in range(1, 6):
            try:
                global_idx = (konu_idx - 1) * 5 + soru_no
                print(f"  [{global_idx}/20] Generating...", end=" ", flush=True)

                question = await generator.generate_question(
                    topic=konu['topic'],
                    subtopic=konu['subtopic'],
                    exam_type="TYT",
                    subject="Matematik",
                    difficulty=konu['diff'] + (soru_no - 1) * 0.05,
                    bloom_level=2 + (soru_no % 3),
                    generation_method='ensemble',
                    save_to_db=False
                )

                questions.append(question)
                q_score = question.get('quality_score_total', 0)
                print(f"OK (Quality: {q_score:.3f})")

            except Exception as e:
                print(f"FAILED")
                print(f"       ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    print("\n" + "=" * 80)
    print(f">>> TAMAMLANDI: {len(questions)}/20 soru üretildi")
    print("=" * 80)

    return questions


def evaluate_osym_quality(questions):
    """ÖSYM standartlarına göre değerlendirme"""
    print("\n" + "=" * 80)
    print(">>> ÖSYM KALİTE DEĞERLENDİRMESİ")
    print("=" * 80)
    print()

    evaluations = []

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Evaluating...", end=" ")

        # Basit kalite değerlendirmesi
        stem_length = len(q.get('stem', ''))
        options_count = len([q.get('correct_answer', '')] +
                          [q.get(f'distractor_{i}', '') for i in range(1, 5)])

        # Kalite skorları
        length_score = 1.0 if 50 <= stem_length <= 500 else 0.7
        option_score = 1.0 if options_count == 5 else 0.5
        quality_score = q.get('quality_score_total', 0.75)
        osym_score = q.get('osym_compliance_score', 0.75)

        overall = (length_score * 0.2 + option_score * 0.2 +
                  quality_score * 0.3 + osym_score * 0.3)

        eval_data = {
            'overall_score': overall,
            'osym_compliance_score': osym_score,
            'quality_score': quality_score,
            'length_score': length_score,
            'option_score': option_score
        }

        evaluations.append(eval_data)
        print(f"Overall: {overall:.3f} | ÖSYM: {osym_score:.3f}")

    print(f"\n[OK] Değerlendirme tamamlandı\n")
    return evaluations


def generate_report(questions, evaluations):
    """Detaylı rapor"""
    scores = [e['overall_score'] for e in evaluations]
    osym_scores = [e['osym_compliance_score'] for e in evaluations]

    avg_score = sum(scores) / len(scores) if scores else 0
    avg_osym = sum(osym_scores) / len(osym_scores) if osym_scores else 0

    excellent = sum(1 for s in scores if s >= 0.9)
    good = sum(1 for s in scores if 0.8 <= s < 0.9)
    acceptable = sum(1 for s in scores if 0.7 <= s < 0.8)
    poor = sum(1 for s in scores if s < 0.7)

    report = []
    report.append("=" * 100)
    report.append("   20 SORU - ÖSYM KALİTE DEĞERLENDİRME RAPORU")
    report.append("=" * 100)
    report.append(f"\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Toplam Soru: {len(questions)}")
    report.append(f"Generator: REAL OSYMQuestionGenerator (Claude Sonnet 4.5)")
    report.append(f"Method: Multi-LLM Ensemble")

    report.append("\n" + "=" * 100)
    report.append("GENEL KALİTE SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama Skor:  {avg_score:.4f} / 1.0")
    report.append(f"En Düşük:       {min(scores):.4f}")
    report.append(f"En Yüksek:      {max(scores):.4f}")

    report.append("\nKalite Dağılımı:")
    report.append(f"  Mükemmel (0.9+):     {excellent:3d} soru ({excellent/len(questions)*100:5.1f}%)")
    report.append(f"  İyi (0.8-0.9):       {good:3d} soru ({good/len(questions)*100:5.1f}%)")
    report.append(f"  Kabul Edilebilir:    {acceptable:3d} soru ({acceptable/len(questions)*100:5.1f}%)")
    report.append(f"  Zayıf (<0.7):        {poor:3d} soru ({poor/len(questions)*100:5.1f}%)")

    report.append("\n" + "=" * 100)
    report.append("ÖSYM UYUMLULUK")
    report.append("=" * 100)
    report.append(f"Ortalama ÖSYM Skoru: {avg_osym:.4f} / 1.0")

    report.append("\n" + "=" * 100)
    report.append("BAŞARI KRİTERLERİ")
    report.append("=" * 100)

    c1 = "[OK]" if avg_score >= 0.8 else "[FAIL]"
    report.append(f"1. Ortalama Kalite >= 0.8:  {c1} ({avg_score:.4f})")

    c2 = "[OK]" if avg_osym >= 0.75 else "[FAIL]"
    report.append(f"2. ÖSYM Uyumluluk >= 0.75:  {c2} ({avg_osym:.4f})")

    good_pct = (excellent + good) / len(questions) * 100
    c3 = "[OK]" if good_pct >= 70 else "[FAIL]"
    report.append(f"3. İyi/Mükemmel >= 70%:     {c3} ({good_pct:.1f}%)")

    poor_pct = poor / len(questions) * 100
    c4 = "[OK]" if poor_pct <= 15 else "[FAIL]"
    report.append(f"4. Zayıf Soru <= 15%:       {c4} ({poor_pct:.1f}%)")

    # En iyi 5 soru
    sorted_q = sorted(zip(questions, scores), key=lambda x: x[1], reverse=True)[:5]
    report.append("\n" + "=" * 100)
    report.append("EN İYİ 5 SORU")
    report.append("=" * 100)

    for i, (q, score) in enumerate(sorted_q, 1):
        report.append(f"\n{i}. Soru (Skor: {score:.4f}):")
        report.append(f"   Konu: {q.get('topic', 'N/A')} / {q.get('subtopic', 'N/A')}")
        stem = q.get('stem', '')[:150]
        report.append(f"   Soru: {stem}...")
        report.append(f"   Zorluk: {q.get('difficulty', 0):.2f}")

    report.append("\n" + "=" * 100)

    report_text = "\n".join(report)
    print(report_text)

    return {
        'questions': questions,
        'evaluations': evaluations,
        'avg_score': avg_score,
        'avg_osym': avg_osym,
        'report': report_text
    }


async def main():
    try:
        # Generate 20 questions
        questions = await generate_20_questions()

        if len(questions) < 5:
            print(f"\n[ERROR] Sadece {len(questions)} soru üretildi. Minimum 5 gerekli.")
            return

        # Evaluate quality
        evaluations = evaluate_osym_quality(questions)

        # Generate report
        results = generate_report(questions, evaluations)

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        json_file = f'20_questions_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total': len(questions),
                'avg_quality': results['avg_score'],
                'avg_osym': results['avg_osym'],
                'questions': questions,
                'evaluations': evaluations
            }, f, ensure_ascii=False, indent=2)

        report_file = f'20_questions_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(results['report'])

        print(f"\n[SAVE] JSON: {json_file}")
        print(f"[SAVE] Report: {report_file}")
        print("\n[OK] İşlem başarıyla tamamlandı!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
