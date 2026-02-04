"""
Wave 2B ile Mevcut Soruları Değerlendirme
Veritabanındaki mevcut soruları Wave 2B kalite kontrolünden geçirir
"""

import sys
import json
import asyncio
from pathlib import Path
import io
from datetime import datetime

# UTF-8 kodlama
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator
from core.database import get_db_session
from sqlalchemy import text


async def load_osym_reference():
    """ÖSYM referans sorularını yükle"""
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

            questions = []
            for row in rows:
                questions.append(
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                    }
                )

            print(f"✓ {len(questions)} ÖSYM referans sorusu yüklendi")
            return questions

        except Exception as e:
            print(f"⚠️  Referans yüklenemedi: {e}")
            return []


async def load_test_questions(count: int = 10):
    """Test edilecek soruları yükle"""
    async for db in get_db_session():
        try:
            query = text(
                """
                SELECT
                    metin as question_text,
                    zorluk as difficulty,
                    konu as subject,
                    dogru_cevap as correct_answer,
                    LENGTH(metin) as length
                FROM sorular
                WHERE dogru_cevap IS NOT NULL
                AND metin IS NOT NULL
                AND LENGTH(metin) BETWEEN 80 AND 600
                ORDER BY RANDOM()
                LIMIT :count
            """
            )

            result = await db.execute(query, {"count": count})
            rows = result.fetchall()

            questions = []
            for row in rows:
                questions.append(
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                        "length": row[4],
                    }
                )

            print(f"✓ {len(questions)} test sorusu yüklendi")
            return questions

        except Exception as e:
            print(f"❌ Soru yüklenemedi: {e}")
            return []


async def evaluate_questions():
    """
    Mevcut soruları Wave 2B ile değerlendir
    """
    print("\n" + "=" * 80)
    print(" " * 15 + "WAVE 2B İLE MEVCUT SORULARI DEĞERLENDİRME")
    print("=" * 80)

    # ÖSYM referans sorularını yükle
    print("\n🔄 ÖSYM referans soruları yükleniyor...")
    osym_ref = await load_osym_reference()

    # Kalite değerlendirici başlat
    print("🔧 Wave 2B kalite değerlendirici başlatılıyor...")
    evaluator = ComprehensiveQualityEvaluator(
        osym_reference_questions=osym_ref if osym_ref else None
    )
    print("✓ Değerlendirici hazır")

    # Test sorularını yükle
    print("\n📚 Test sorular yükleniyor...")
    test_questions = await load_test_questions(count=10)

    if not test_questions:
        print("❌ Test soruları yüklenemedi")
        return None

    quality_stats = {
        "total": 0,
        "approved": 0,
        "review": 0,
        "rejected": 0,
        "scores": [],
        "bloom_levels": {},
    }

    evaluated_questions = []

    print(
        f"\n🔍 {len(test_questions)} soru Wave 2B kalite kontrolünden geçiriliyor...\n"
    )

    for i, q in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"SORU {i}/{len(test_questions)}")
        print("=" * 80)

        print(f"📝 {q['question_text'][:150]}...")
        print(f"   Konu: {q.get('subject', 'N/A')}")
        print(f"   Zorluk: {q.get('difficulty', 'N/A')}")
        print(f"   Uzunluk: {q['length']} karakter")

        try:
            # Wave 2B kalite kontrolü
            print("\n🔍 Wave 2B kalite değerlendirmesi...")

            # Standard değerlendirme
            evaluation = evaluator.evaluate(q, stage="standard")

            quality_stats["total"] += 1
            quality_stats["scores"].append(evaluation.overall_score)

            # Bloom seviye istatistiği
            if evaluation.bloom_level:
                level = f"Seviye {evaluation.bloom_level}"
                quality_stats["bloom_levels"][level] = (
                    quality_stats["bloom_levels"].get(level, 0) + 1
                )

            # Sonuçları göster
            print(f"\n📊 KALİTE RAPORU:")
            print(f"   Genel Skor: {evaluation.overall_score:.3f}")
            print(f"   Derece: {evaluation.overall_grade}")
            print(f"   Karar: {evaluation.decision}")

            if evaluation.decision == "APPROVE":
                quality_stats["approved"] += 1
                print(f"   Durum: ✅ ONAYLANDI")
            elif evaluation.decision == "REVIEW":
                quality_stats["review"] += 1
                print(f"   Durum: ⚠️  İNCELENMELİ")
            else:
                quality_stats["rejected"] += 1
                print(f"   Durum: ❌ REDDEDİLDİ")

            if evaluation.bloom_level:
                print(
                    f"   Bloom Seviyesi: {evaluation.bloom_level} (güven={evaluation.bloom_confidence:.2f})"
                )

            if evaluation.strengths:
                print(f"\n   ✓ Güçlü Yönler:")
                for s in evaluation.strengths[:2]:
                    print(f"      - {s}")

            if evaluation.weaknesses:
                print(f"\n   ⚠️  İyileştirme Alanları:")
                for w in evaluation.weaknesses[:2]:
                    print(f"      - {w}")

            # Soruyu kaydet
            q["wave2b_evaluation"] = {
                "overall_score": evaluation.overall_score,
                "overall_grade": evaluation.overall_grade,
                "decision": evaluation.decision,
                "bloom_level": evaluation.bloom_level,
                "bloom_confidence": evaluation.bloom_confidence,
                "strengths": evaluation.strengths[:3] if evaluation.strengths else [],
                "weaknesses": evaluation.weaknesses[:3]
                if evaluation.weaknesses
                else [],
            }
            evaluated_questions.append(q)

        except Exception as e:
            print(f"\n❌ Değerlendirme hatası: {e}")
            import traceback

            traceback.print_exc()
            quality_stats["total"] += 1

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
        min_score = min(quality_stats["scores"])
        max_score = max(quality_stats["scores"])
        print(f"\n   Ortalama Kalite: {avg_score:.3f}")
        print(f"   En Düşük: {min_score:.3f}")
        print(f"   En Yüksek: {max_score:.3f}")

    if quality_stats["bloom_levels"]:
        print(f"\n📚 BLOOM SEVİYE DAĞILIMI:")
        for level, count in sorted(quality_stats["bloom_levels"].items()):
            print(f"   {level}: {count} soru ({count/quality_stats['total']:.1%})")

    # Sonuçları kaydet
    output = {
        "timestamp": datetime.now().isoformat(),
        "statistics": quality_stats,
        "questions": evaluated_questions,
    }

    output_file = (
        Path(__file__).parent
        / f"wave2b_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Sonuçlar kaydedildi: {output_file.name}")

    return quality_stats


async def main():
    """Ana fonksiyon"""
    try:
        stats = await evaluate_questions()

        if stats and stats["total"] > 0:
            print("\n" + "=" * 80)
            print("\n✅ Wave 2B kalite değerlendirmesi tamamlandı!")
            print(f"\nOnay oranı: {stats['approved']/stats['total']:.1%}")
            print(
                f"Ortalama kalite: {sum(stats['scores'])/len(stats['scores']):.3f}"
                if stats["scores"]
                else "N/A"
            )
            print(f"\nWave 2B başarıyla çalışıyor! 🎉")
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
