"""
Wave 2B - Tam Veritabanı Değerlendirmesi
Tüm soruları BERTScore ile tara, benzer soruları tespit et, kalite raporu oluştur
"""

import sys
import json
import asyncio
from pathlib import Path
import io
from datetime import datetime
from collections import defaultdict

# UTF-8 kodlama
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# .env yükle
from dotenv import load_dotenv

load_dotenv()

from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator
from services.bertscore_evaluator import BERTScoreEvaluator
from core.database import get_db_session
from sqlalchemy import text


async def load_all_questions(limit: int = 100):
    """Veritabanından soruları yükle"""
    async for db in get_db_session():
        try:
            query = text(
                """
                SELECT
                    id,
                    metin as question_text,
                    zorluk as difficulty,
                    konu as subject,
                    dogru_cevap as correct_answer,
                    LENGTH(metin) as length
                FROM sorular
                WHERE dogru_cevap IS NOT NULL
                AND metin IS NOT NULL
                AND LENGTH(metin) BETWEEN 50 AND 600
                ORDER BY RANDOM()
                LIMIT :limit
            """
            )

            result = await db.execute(query, {"limit": limit})
            rows = result.fetchall()

            questions = []
            for row in rows:
                questions.append(
                    {
                        "id": str(row[0]),  # UUID'yi string'e çevir
                        "question_text": row[1],
                        "difficulty": row[2],
                        "subject": row[3],
                        "correct_answer": row[4],
                        "length": row[5],
                    }
                )

            print(f"✓ {len(questions)} soru yüklendi")
            return questions

        except Exception as e:
            print(f"❌ Soru yüklenemedi: {e}")
            return []


async def find_similar_questions(questions, threshold=0.85):
    """Benzer soruları tespit et (BERTScore ile)"""
    print("\n🔍 Benzer/kopya sorular aranıyor (BERTScore)...")

    evaluator = BERTScoreEvaluator()
    if not evaluator.is_available():
        print("⚠️  BERTScore mevcut değil, benzerlik tespiti atlanıyor")
        return []

    similar_pairs = []
    total_comparisons = (len(questions) * (len(questions) - 1)) // 2

    print(f"   Toplam {total_comparisons} karşılaştırma yapılacak...")

    count = 0
    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            q1 = questions[i]
            q2 = questions[j]

            result = evaluator.evaluate_single(q1["question_text"], q2["question_text"])

            if result and result["f1"] >= threshold:
                similar_pairs.append(
                    {
                        "question1_id": q1["id"],
                        "question2_id": q2["id"],
                        "question1": q1["question_text"][:100],
                        "question2": q2["question_text"][:100],
                        "similarity": result["f1"],
                        "subject1": q1["subject"],
                        "subject2": q2["subject"],
                    }
                )

            count += 1
            if count % 100 == 0:
                print(
                    f"   İlerleme: {count}/{total_comparisons} ({count/total_comparisons*100:.1f}%)"
                )

    return similar_pairs


async def full_evaluation():
    """Tam veritabanı değerlendirmesi"""
    print("\n" + "=" * 80)
    print(" " * 15 + "WAVE 2B - TAM VERİTABANI DEĞERLENDİRMESİ")
    print("=" * 80)

    # ÖSYM referans sorularını yükle
    print("\n🔄 ÖSYM referans soruları yükleniyor...")
    async for db in get_db_session():
        try:
            query = text(
                """
                SELECT
                    metin as question_text,
                    zorluk as difficulty,
                    konu as subject,
                    dogru_cevap as correct_answer
                FROM sorular
                WHERE dogru_cevap IS NOT NULL
                AND metin IS NOT NULL
                AND LENGTH(metin) > 100
                ORDER BY RANDOM()
                LIMIT 30
            """
            )

            result = await db.execute(query, {})
            rows = result.fetchall()

            osym_ref = []
            for row in rows:
                osym_ref.append(
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                    }
                )

            print(f"✓ {len(osym_ref)} ÖSYM referans sorusu yüklendi")
            break
        except Exception as e:
            print(f"⚠️  Referans yüklenemedi: {e}")
            osym_ref = []

    # Kalite değerlendirici başlat
    print("🔧 Wave 2B değerlendirici başlatılıyor...")
    evaluator = ComprehensiveQualityEvaluator(
        osym_reference_questions=osym_ref if osym_ref else None
    )
    print("✓ Değerlendirici hazır")

    # Tüm soruları yükle
    print("\n📚 Sorular veritabanından yükleniyor...")
    questions = await load_all_questions(limit=100)  # 100 soru ile kapsamlı tarama

    if not questions:
        print("❌ Soru bulunamadı")
        return None

    # İstatistikler
    quality_stats = {
        "total": 0,
        "approved": 0,
        "review": 0,
        "rejected": 0,
        "scores": [],
        "bloom_levels": defaultdict(int),
        "by_subject": defaultdict(lambda: {"total": 0, "approved": 0, "scores": []}),
    }

    evaluated_questions = []

    print(f"\n🔍 {len(questions)} soru Wave 2B ile değerlendiriliyor...\n")

    # Değerlendirme
    for i, q in enumerate(questions, 1):
        if i % 10 == 0:
            print(f"İlerleme: {i}/{len(questions)} ({i/len(questions)*100:.0f}%)")

        try:
            # Standard değerlendirme
            evaluation = evaluator.evaluate(q, stage="standard")

            quality_stats["total"] += 1
            quality_stats["scores"].append(evaluation.overall_score)

            # Bloom seviye
            if evaluation.bloom_level:
                quality_stats["bloom_levels"][f"Seviye {evaluation.bloom_level}"] += 1

            # Konu bazlı
            subject = q.get("subject", "Bilinmeyen")
            quality_stats["by_subject"][subject]["total"] += 1
            quality_stats["by_subject"][subject]["scores"].append(
                evaluation.overall_score
            )

            # Karar
            if evaluation.decision == "APPROVE":
                quality_stats["approved"] += 1
                quality_stats["by_subject"][subject]["approved"] += 1
            elif evaluation.decision == "REVIEW":
                quality_stats["review"] += 1
            else:
                quality_stats["rejected"] += 1

            # Soruyu kaydet
            q["wave2b_evaluation"] = {
                "overall_score": evaluation.overall_score,
                "decision": evaluation.decision,
                "bloom_level": evaluation.bloom_level,
            }
            evaluated_questions.append(q)

        except Exception as e:
            print(f"⚠️  Soru {i} değerlendirme hatası: {e}")
            quality_stats["total"] += 1

    # Benzer soruları tespit et (sadece küçük veri setleri için - çok fazla karşılaştırma gerekir)
    approved_questions = [
        q
        for q in evaluated_questions
        if q.get("wave2b_evaluation", {}).get("decision") == "APPROVE"
    ]

    similar_pairs = []
    if len(approved_questions) > 1 and len(approved_questions) <= 30:
        print(
            f"\n🔍 Benzerlik analizi yapılıyor ({len(approved_questions)} onaylı soru)..."
        )
        similar_pairs = await find_similar_questions(approved_questions, threshold=0.85)
    else:
        print(
            f"\n⚠️  Benzerlik analizi atlandı (çok fazla soru: {len(approved_questions)})"
        )

    # Özet rapor
    print("\n" + "=" * 80)
    print(" " * 30 + "ÖZET RAPOR")
    print("=" * 80)

    print(f"\n📊 KALİTE İSTATİSTİKLERİ:")
    print(f"   Toplam Soru: {quality_stats['total']}")
    print(
        f"   ✅ Onaylanan: {quality_stats['approved']} ({quality_stats['approved']/max(quality_stats['total'],1):.1%})"
    )
    print(
        f"   ⚠️  İncelenmeli: {quality_stats['review']} ({quality_stats['review']/max(quality_stats['total'],1):.1%})"
    )
    print(
        f"   ❌ Reddedilen: {quality_stats['rejected']} ({quality_stats['rejected']/max(quality_stats['total'],1):.1%})"
    )

    if quality_stats["scores"]:
        avg_score = sum(quality_stats["scores"]) / len(quality_stats["scores"])
        print(f"\n   Ortalama Kalite: {avg_score:.3f}")
        print(f"   En Düşük: {min(quality_stats['scores']):.3f}")
        print(f"   En Yüksek: {max(quality_stats['scores']):.3f}")

    if quality_stats["bloom_levels"]:
        print(f"\n📚 BLOOM SEVİYE DAĞILIMI:")
        for level, count in sorted(quality_stats["bloom_levels"].items()):
            print(f"   {level}: {count} soru ({count/quality_stats['total']:.1%})")

    if quality_stats["by_subject"]:
        print(f"\n📖 KONU BAZINDA ANALİZ:")
        for subject, stats in sorted(
            quality_stats["by_subject"].items(),
            key=lambda x: x[1]["total"],
            reverse=True,
        )[:10]:
            avg = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            print(f"   {subject}:")
            print(
                f"      Toplam: {stats['total']}, Onaylanan: {stats['approved']} ({stats['approved']/max(stats['total'],1):.0%}), Ort. Kalite: {avg:.3f}"
            )

    if similar_pairs:
        print(f"\n🔍 BENZERLİK ANALİZİ:")
        print(f"   Tespit edilen benzer soru çifti: {len(similar_pairs)}")
        print(f"\n   En benzer 5 çift:")
        for i, pair in enumerate(
            sorted(similar_pairs, key=lambda x: x["similarity"], reverse=True)[:5], 1
        ):
            print(f"   {i}. F1={pair['similarity']:.3f}")
            print(f"      Soru 1 (ID={pair['question1_id']}): {pair['question1']}...")
            print(f"      Soru 2 (ID={pair['question2_id']}): {pair['question2']}...")

    # Sonuçları kaydet
    output = {
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total": quality_stats["total"],
            "approved": quality_stats["approved"],
            "review": quality_stats["review"],
            "rejected": quality_stats["rejected"],
            "bloom_levels": dict(quality_stats["bloom_levels"]),
            "by_subject": {
                k: {
                    "total": v["total"],
                    "approved": v["approved"],
                    "avg_score": sum(v["scores"]) / len(v["scores"])
                    if v["scores"]
                    else 0,
                }
                for k, v in quality_stats["by_subject"].items()
            },
        },
        "similar_pairs": similar_pairs,
        "questions": evaluated_questions[:20],  # İlk 20 soruyu kaydet
    }

    output_file = (
        Path(__file__).parent
        / f"full_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Tam rapor kaydedildi: {output_file.name}")

    return quality_stats


async def main():
    """Ana fonksiyon"""
    try:
        stats = await full_evaluation()

        if stats and stats["total"] > 0:
            print("\n" + "=" * 80)
            print("\n✅ Wave 2B tam veritabanı değerlendirmesi tamamlandı!")
            print(f"\nOnay oranı: {stats['approved']/stats['total']:.1%}")
            print(
                f"Ortalama kalite: {sum(stats['scores'])/len(stats['scores']):.3f}"
                if stats["scores"]
                else "N/A"
            )
            print(f"\n🎉 Wave 2B tüm özelliklerle çalışıyor!")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
