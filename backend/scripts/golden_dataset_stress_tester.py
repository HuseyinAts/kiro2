import asyncio
import json
import statistics
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.fsrs_v6_service import FSRSService
from services.irt_calibration_service import IRTCalibrationService

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


async def run_stress_test():
    print(
        "🚀 Başlatılıyor: Golden Dataset Stres Testi (10K Soru, 50K Etkileşim)...",
        flush=True,
    )

    irt_service = IRTCalibrationService()

    # 1. Aşama: IRT Çıpa Dağılımı Testi
    print("\n--- 1. IRT Bell Curve Kalibrasyon Testi ---", flush=True)
    start_time = time.time()

    difficulties = []
    discriminations = []

    question_template = (
        "Bu bir matematik sorusudur. Ali'nin {n} elması var. {k} tanesini yedi."
    )

    num_questions = 10000

    async def process_batch(start, size):
        tasks = []
        for i in range(start, start + size):
            q_text = question_template.format(n=i, k=i % 5)
            diff_level = ["Kolay", "Orta", "Zor"][i % 3]
            subj = ["Matematik", "Fizik", "Türkçe"][i % 3]
            tasks.append(
                irt_service.calibrate_question_irt(
                    question_text=q_text,
                    options=["A", "B", "C", "D", "E"],
                    subject=subj,
                    initial_difficulty=diff_level,
                )
            )
        results = await asyncio.gather(*tasks)
        for r in results:
            difficulties.append(r.difficulty)
            discriminations.append(r.discrimination)

    batch_size = 500
    for i in range(0, num_questions, batch_size):
        await process_batch(i, min(batch_size, num_questions - i))
        if i % 2000 == 0 and i > 0:
            print(f"  [{i}/{num_questions}] kalibre edildi...", flush=True)

    irt_time = time.time() - start_time

    mean_diff = statistics.mean(difficulties)
    stdev_diff = statistics.stdev(difficulties)

    print(f"\n✅ IRT Testi Tamamlandı ({irt_time:.2f} saniye)", flush=True)
    print(f"📊 Ortalama Zorluk (Expected ~0.0): {mean_diff:.4f}", flush=True)
    print(f"📊 Zorluk StSapma (Expected ~1.0): {stdev_diff:.4f}", flush=True)

    # 2. Aşama: FSRS Time Travel Simülasyonu
    print("\n--- 2. FSRS Zihin Aralığı (Spacing) Büyüme Testi ---", flush=True)
    start_time = time.time()

    fsrs_intervals = []

    for i in range(10000):
        s1, d1 = FSRSService.first_review(3)  # Good

        review_date_2 = datetime.now(UTC) + timedelta(days=1)
        res2 = FSRSService.review_card(s1, d1, review_date_2, 3, reps=1)

        review_date_3 = review_date_2 + timedelta(days=3)
        res3 = FSRSService.review_card(
            res2["stability"], res2["difficulty"], review_date_3, 3, reps=2
        )

        review_date_4 = review_date_3 + timedelta(days=10)
        res4 = FSRSService.review_card(
            res3["stability"], res3["difficulty"], review_date_4, 3, reps=3
        )

        review_date_5 = review_date_4 + timedelta(days=21)
        res5 = FSRSService.review_card(
            res4["stability"], res4["difficulty"], review_date_5, 3, reps=4
        )

        if res5["due_date"]:
            interval_days = (res5["due_date"] - review_date_5).days
            fsrs_intervals.append(interval_days)

        if i % 2000 == 0 and i > 0:
            print(f"  [{i}/10000] öğrenci simüle edildi...", flush=True)

    fsrs_time = time.time() - start_time
    mean_interval = statistics.mean(fsrs_intervals) if fsrs_intervals else 0.0

    print(f"\n✅ FSRS Simülasyonu Tamamlandı ({fsrs_time:.2f} saniye)", flush=True)
    print(
        f"🧠 5 Başarılı Tekrar Sonrası Ortalama Bekleme Süresi: {mean_interval:.1f} gün",
        flush=True,
    )
    print(
        f"⚡ Genel Performans: {50000 / fsrs_time:.0f} FSRS hesaplaması / sn",
        flush=True,
    )

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "irt_metrics": {
            "questions_processed": num_questions,
            "time_seconds": irt_time,
            "mean_difficulty": mean_diff,
            "stdev_difficulty": stdev_diff,
        },
        "fsrs_metrics": {
            "simulated_interactions": 50000,
            "time_seconds": fsrs_time,
            "final_mean_interval_days": mean_interval,
        },
    }

    with Path("golden_dataset_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\n💾 Rapor 'golden_dataset_report.json' dosyasına kaydedildi.", flush=True)


if __name__ == "__main__":
    asyncio.run(run_stress_test())
    print("FINISHED EXECUTING", flush=True)
