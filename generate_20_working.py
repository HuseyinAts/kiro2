"""
20 SORU ÜRETİMİ - CLAUDE AI (WORKING VERSION)
Direkt ClaudeProvider kullanımı
"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.llm.claude_provider import ClaudeProvider
from services.llm.multi_llm_config import MultiLLMConfig

# Matematik konuları
KONULAR = [
    {"topic": "Sayılar", "subtopic": "Tam Sayılar", "diff": 0.4},
    {"topic": "Cebir", "subtopic": "Denklemler", "diff": 0.5},
    {"topic": "Fonksiyonlar", "subtopic": "Doğrusal Fonksiyonlar", "diff": 0.6},
    {"topic": "Geometri", "subtopic": "Üçgenler", "diff": 0.7},
]

async def generate_20():
    print("=" * 80)
    print(">>> 20 SORU ÜRETİMİ (CLAUDE SONNET 4.5)")
    print("=" * 80)
    print()

    provider = ClaudeProvider(MultiLLMConfig.CLAUDE_CONFIG)
    questions = []

    # Her konudan 5 soru
    for konu_idx, konu in enumerate(KONULAR, 1):
        print(f"\n[{konu_idx}/4] {konu['topic']} - {konu['subtopic']}")
        print("-" * 80)

        for soru_no in range(1, 6):
            global_idx = (konu_idx - 1) * 5 + soru_no
            print(f"  [{global_idx}/20] Generating...", end=" ", flush=True)

            try:
                result = await provider.create_osym_question(
                    topic=konu['topic'],
                    subtopic=konu['subtopic'],
                    difficulty=konu['diff'] + (soru_no - 1) * 0.05,
                    bloom_level=2 + (soru_no % 3),
                    exam_type="TYT"
                )

                questions.append(result)
                print(f"OK")

            except Exception as e:
                print(f"FAILED")
                print(f"       Full error: {str(e)}")
                continue

    print("\n" + "=" * 80)
    print(f">>> {len(questions)}/20 soru üretildi")
    print("=" * 80)

    return questions


def evaluate_quality(questions):
    """ÖSYM kalite değerlendirmesi"""
    print("\n" + "=" * 80)
    print(">>> ÖSYM KALİTE DEĞERLENDİRMESİ")
    print("=" * 80)

    scores = []
    for i, q in enumerate(questions, 1):
        # Basit skorlama
        stem_len = len(q.get('stem', ''))
        opt_count = len(q.get('options', []))

        length_ok = 1.0 if 50 <= stem_len <= 500 else 0.7
        options_ok = 1.0 if opt_count == 5 else 0.5

        overall = (length_ok + options_ok) / 2
        scores.append(overall)

        print(f"  [{i}/{len(questions)}] Skor: {overall:.3f} (Uzunluk: {stem_len}, Seçenek: {opt_count})")

    avg = sum(scores) / len(scores) if scores else 0
    print(f"\n>>> Ortalama Kalite: {avg:.3f}")

    return scores


def generate_report(questions, scores):
    """Rapor oluştur"""
    avg = sum(scores) / len(scores) if scores else 0

    excellent = sum(1 for s in scores if s >= 0.9)
    good = sum(1 for s in scores if 0.8 <= s < 0.9)
    acceptable = sum(1 for s in scores if 0.7 <= s < 0.8)
    poor = sum(1 for s in scores if s < 0.7)

    report = []
    report.append("=" * 100)
    report.append("   20 SORU - ÖSYM KALİTE RAPORU")
    report.append("=" * 100)
    report.append(f"\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Toplam: {len(questions)} soru")
    report.append(f"Generator: Claude Sonnet 4.5 (Direct API)")

    report.append("\n" + "=" * 100)
    report.append("KALİTE SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama:   {avg:.4f}")
    report.append(f"En Düşük:   {min(scores):.4f}")
    report.append(f"En Yüksek:  {max(scores):.4f}")

    report.append("\nDağılım:")
    report.append(f"  Mükemmel:      {excellent:2d} ({excellent/len(questions)*100:5.1f}%)")
    report.append(f"  İyi:           {good:2d} ({good/len(questions)*100:5.1f}%)")
    report.append(f"  Kabul Edilir:  {acceptable:2d} ({acceptable/len(questions)*100:5.1f}%)")
    report.append(f"  Zayıf:         {poor:2d} ({poor/len(questions)*100:5.1f}%)")

    report.append("\n" + "=" * 100)
    report.append("ÖRNEK SORULAR (İlk 5)")
    report.append("=" * 100)

    for i, q in enumerate(questions[:5], 1):
        report.append(f"\n{i}. SORU:")
        report.append(f"   Konu: {q.get('topic', 'N/A')} - {q.get('subtopic', 'N/A')}")
        stem = q.get('stem', '')[:200]
        report.append(f"   Soru: {stem}...")
        report.append(f"   Seçenekler: {len(q.get('options', []))} adet")

    report.append("\n" + "=" * 100)

    return "\n".join(report)


async def main():
    # 1. Generate
    questions = await generate_20()

    if len(questions) < 5:
        print(f"\n[ERROR] Sadece {len(questions)} soru. En az 5 gerekli.")
        return

    # 2. Evaluate
    scores = evaluate_quality(questions)

    # 3. Report
    report_text = generate_report(questions, scores)
    print("\n" + report_text)

    # 4. Save
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    json_file = f'20_questions_{ts}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': ts,
            'total': len(questions),
            'avg_score': sum(scores)/len(scores) if scores else 0,
            'questions': questions
        }, f, ensure_ascii=False, indent=2)

    report_file = f'20_questions_report_{ts}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n[SAVE] JSON: {json_file}")
    print(f"[SAVE] Report: {report_file}")
    print("\n[OK] İşlem tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main())
