"""
Wave 2B ile Kaliteli Soru Üretimi
Mevcut soru üretim sistemine Wave 2B kalite kontrolü ekler
"""

import asyncio
import io
import json
import sys
from datetime import datetime
from pathlib import Path

# UTF-8 kodlama
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from core.database import get_db_session
from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator
from services.soru_bankasi_service import SoruBankasiServisi


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
                AND LENGTH(metin) > 50
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


async def generate_questions_with_quality_control(count: int = 5):
    """
    Mevcut sistemle soru üret ve Wave 2B ile kalite kontrolü yap
    """
    print("\n" + "=" * 80)
    print(" " * 20 + "WAVE 2B KALİTE KONTROLÜ İLE SORU ÜRETİMİ")
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

    # Soru bankası servisi
    service = SoruBankasiServisi()

    # Farklı konulardan sorular
    topics = [
        {
            "subject": "Matematik",
            "topic": "İkinci Dereceden Denklemler",
            "difficulty": "orta",
        },
        {"subject": "Fizik", "topic": "Hareket", "difficulty": "kolay"},
        {"subject": "Kimya", "topic": "Mol Kavramı", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Türev", "difficulty": "zor"},
        {"subject": "Biyoloji", "topic": "Hücre", "difficulty": "orta"},
    ]

    generated_questions = []
    quality_stats = {
        "total": 0,
        "approved": 0,
        "review": 0,
        "rejected": 0,
        "scores": [],
    }

    print(
        f"\n📝 {min(count, len(topics))} soru üretiliyor ve kalite kontrolünden geçiriliyor...\n"
    )

    for i, req in enumerate(topics[:count], 1):
        print(f"\n{'='*80}")
        print(
            f"SORU {i}/{min(count, len(topics))}: {req['subject']} - {req['topic']} ({req['difficulty']})"
        )
        print("=" * 80)

        try:
            # 1. Soru üret (mevcut sistem)
            print("📝 Soru üretiliyor...")
            questions = await service.get_random_questions(
                exam_type="TYT", subject=req["subject"], question_count=1
            )

            if not questions or len(questions) == 0:
                print("❌ Soru üretilemedi\n")
                quality_stats["total"] += 1
                continue

            question = questions[0]
            print("✓ Soru üretildi")
            print(f"   {question.get('soru_metni', '')[:100]}...")

            # 2. Wave 2B kalite kontrolü
            print("\n🔍 Wave 2B kalite kontrolü yapılıyor...")

            # Kalite değerlendirme için format dönüştür
            eval_question = {
                "question_text": question.get("soru_metni", ""),
                "choices": [
                    question.get("A", ""),
                    question.get("B", ""),
                    question.get("C", ""),
                    question.get("D", ""),
                    question.get("E", ""),
                ],
                "correct_answer": question.get("dogru_cevap", ""),
                "difficulty": req["difficulty"],
                "subject": req["subject"],
            }

            # Standard değerlendirme yap
            evaluation = evaluator.evaluate(eval_question, stage="standard")

            quality_stats["total"] += 1
            quality_stats["scores"].append(evaluation.overall_score)

            # Sonuçları göster
            print("\n📊 KALİTE RAPORU:")
            print(f"   Genel Skor: {evaluation.overall_score:.3f}")
            print(f"   Derece: {evaluation.overall_grade}")
            print(f"   Karar: {evaluation.decision}")

            if evaluation.decision == "APPROVE":
                quality_stats["approved"] += 1
                print("   Durum: ✅ ONAYLANDI")
            elif evaluation.decision == "REVIEW":
                quality_stats["review"] += 1
                print("   Durum: ⚠️  İNCELENMELİ")
            else:
                quality_stats["rejected"] += 1
                print("   Durum: ❌ REDDEDİLDİ")

            if evaluation.bloom_level:
                print(
                    f"   Bloom Seviyesi: {evaluation.bloom_level} (güven={evaluation.bloom_confidence:.2f})"
                )

            if evaluation.strengths:
                print("\n   ✓ Güçlü Yönler:")
                for s in evaluation.strengths[:2]:
                    print(f"      - {s}")

            if evaluation.weaknesses:
                print("\n   ⚠️  İyileştirme Alanları:")
                for w in evaluation.weaknesses[:2]:
                    print(f"      - {w}")

            # Soruyu kaydet
            question["wave2b_quality"] = {
                "overall_score": evaluation.overall_score,
                "decision": evaluation.decision,
                "bloom_level": evaluation.bloom_level,
                "bloom_confidence": evaluation.bloom_confidence,
            }
            generated_questions.append(question)

        except Exception as e:
            print(f"\n❌ Hata: {e}")
            import traceback

            traceback.print_exc()
            quality_stats["total"] += 1

    # Özet rapor
    print("\n" + "=" * 80)
    print(" " * 30 + "ÖZET RAPOR")
    print("=" * 80)

    print("\n📊 KALİTE İSTATİSTİKLERİ:")
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

    # Sonuçları kaydet
    output = {
        "timestamp": datetime.now().isoformat(),
        "statistics": quality_stats,
        "questions": generated_questions,
    }

    output_file = (
        Path(__file__).parent
        / f"wave2b_quality_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Sonuçlar kaydedildi: {output_file.name}")

    return quality_stats


async def main():
    """Ana fonksiyon"""
    try:
        stats = await generate_questions_with_quality_control(count=5)

        print("\n" + "=" * 80)
        print("\n✅ Wave 2B kalite kontrolü başarıyla tamamlandı!")
        print(f"\nOnay oranı: {stats['approved']/max(stats['total'],1):.1%}")
        print(
            f"Ortalama kalite: {sum(stats['scores'])/len(stats['scores']):.3f}"
            if stats["scores"]
            else "N/A"
        )

        return 0 if stats["approved"] > 0 else 1

    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
