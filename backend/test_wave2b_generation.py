"""
Wave 2B Kaliteli Soru Üretimi - Canlı Test

Wave 2B modüllerini kullanarak kaliteli soru üretir ve kalite kontrolünü gösterir.
"""

import sys
import json
import asyncio
from pathlib import Path
import io

# UTF-8 kodlama
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from services.quality_aware_question_generator import (
    QualityAwareQuestionGenerator,
    generate_single_quality_question,
)
from core.database import get_db_session
from sqlalchemy import text


async def load_osym_reference():
    """Veritabanından ÖSYM referans sorularını yükle"""
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
                LIMIT 20
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
            print(f"Hata: {e}")
            return []


async def test_single_generation():
    """Tek soru üretimi testi"""
    print("\n" + "=" * 80)
    print(" " * 25 + "TEST 1: TEK SORU ÜRETİMİ")
    print("=" * 80)

    print("\n📝 Matematik sorusu üretiliyor...")

    soru = await generate_single_quality_question(
        subject="Matematik", topic="İkinci Dereceden Denklemler", difficulty="orta"
    )

    if soru:
        print("\n✅ SORU ÜRETİLDİ!\n")
        print(f"📌 Soru: {soru.get('question_text', 'N/A')}")
        print(f"\n🎯 Seçenekler:")
        for choice in soru.get("choices", []):
            print(f"   {choice}")
        print(f"\n✓ Doğru Cevap: {soru.get('correct_answer', 'N/A')}")

        eval_result = soru.get("quality_evaluation", {})
        print(f"\n📊 KALİTE DEĞERLENDİRMESİ:")
        print(f"   Genel Skor: {eval_result.get('overall_score', 0):.3f}")
        print(f"   Karar: {eval_result.get('decision', 'N/A')}")
        print(f"   Derece: {eval_result.get('overall_grade', 'N/A')}")

        if eval_result.get("bloom_level"):
            print(
                f"   Bloom Seviyesi: {eval_result['bloom_level']} (güven={eval_result.get('bloom_confidence', 0):.2f})"
            )

        if eval_result.get("strengths"):
            print(f"\n✓ Güçlü Yönler:")
            for s in eval_result["strengths"][:3]:
                print(f"   - {s}")

        if eval_result.get("weaknesses"):
            print(f"\n⚠️  İyileştirme Alanları:")
            for w in eval_result["weaknesses"][:3]:
                print(f"   - {w}")

        return True
    else:
        print("\n❌ Soru üretilemedi")
        return False


async def test_batch_generation():
    """Toplu soru üretimi testi"""
    print("\n" + "=" * 80)
    print(" " * 22 + "TEST 2: TOPLU SORU ÜRETİMİ")
    print("=" * 80)

    # ÖSYM referans sorularını yükle
    print("\n🔄 ÖSYM referans soruları yükleniyor...")
    osym_ref = await load_osym_reference()

    if not osym_ref:
        print("⚠️  ÖSYM referans soruları yüklenemedi, benchmark devre dışı")

    # Generator başlat
    print("\n🔧 Generator başlatılıyor...")
    generator = QualityAwareQuestionGenerator(
        osym_reference_questions=osym_ref if osym_ref else None,
        quality_threshold=0.75,  # Orta eşik
        enable_bertscore=False,  # HF auth olmadan
        enable_benchmark=True if osym_ref else False,
    )

    # Farklı derslerden sorular üret
    requirements = [
        {"subject": "Matematik", "topic": "Türev", "difficulty": "orta"},
        {"subject": "Fizik", "topic": "Hareket", "difficulty": "kolay"},
        {"subject": "Kimya", "topic": "Mol Kavramı", "difficulty": "orta"},
    ]

    print(f"\n📝 {len(requirements)} soru üretiliyor...")
    print("   1. Matematik - Türev (orta)")
    print("   2. Fizik - Hareket (kolay)")
    print("   3. Kimya - Mol Kavramı (orta)")

    results = await generator.generate_batch_with_quality(
        requirements=requirements, evaluation_stage="standard"  # Hızlı ama kaliteli
    )

    # Sonuçları göster
    print("\n" + "=" * 80)
    print(" " * 30 + "SONUÇLAR")
    print("=" * 80)

    stats = results["statistics"]
    print(f"\n📊 İSTATİSTİKLER:")
    print(f"   Toplam Deneme: {stats['total_attempts']}")
    print(f"   Başarılı: {stats['successful']}")
    print(f"   Başarısız: {stats['failed']}")
    print(f"   Başarı Oranı: {stats['success_rate']:.1%}")
    print(f"   Ortalama Kalite: {stats['average_quality']:.3f}")

    if stats.get("average_osym_similarity"):
        print(f"   Ortalama ÖSYM Uyumu: {stats['average_osym_similarity']:.3f}")

    print(f"\n✅ ÜRETİLEN SORULAR:\n")

    for i, q in enumerate(results["questions"], 1):
        print(f"{i}. {q['subject']} - {q['topic']}")
        print(f"   Soru: {q['question_text'][:80]}...")

        eval_res = q.get("quality_evaluation", {})
        print(
            f"   Kalite: {eval_res.get('overall_score', 0):.3f} ({eval_res.get('decision', 'N/A')})"
        )

        if eval_res.get("bloom_level"):
            print(f"   Bloom: Seviye {eval_res['bloom_level']}")

        print()

    # Kaydedilecek dosya
    output_file = Path(__file__).parent / "wave2b_generated_questions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"💾 Sonuçlar kaydedildi: {output_file.name}")

    return stats["success_rate"] > 0.5


async def main():
    """Ana test fonksiyonu"""
    print("\n" + "=" * 80)
    print(" " * 20 + "WAVE 2B KALİTELİ SORU ÜRETİMİ")
    print("=" * 80)
    print("\nBu test Wave 2B modüllerini kullanarak kaliteli soru üretecek.")
    print("Her soru otomatik olarak kalite kontrolünden geçirilecek.\n")

    results = {}

    # Test 1: Tek soru
    try:
        results["single"] = await test_single_generation()
    except Exception as e:
        print(f"\n❌ Tek soru testi hatası: {e}")
        import traceback

        traceback.print_exc()
        results["single"] = False

    # Test 2: Toplu soru
    try:
        results["batch"] = await test_batch_generation()
    except Exception as e:
        print(f"\n❌ Toplu soru testi hatası: {e}")
        import traceback

        traceback.print_exc()
        results["batch"] = False

    # Özet
    print("\n" + "=" * 80)
    print(" " * 30 + "ÖZET")
    print("=" * 80)

    success = sum(1 for r in results.values() if r)
    total = len(results)

    print(
        f"\n{'✓' if results.get('single') else '✗'} Tek soru üretimi: {'BAŞARILI' if results.get('single') else 'BAŞARISIZ'}"
    )
    print(
        f"{'✓' if results.get('batch') else '✗'} Toplu soru üretimi: {'BAŞARILI' if results.get('batch') else 'BAŞARISIZ'}"
    )

    print(f"\nGenel: {success}/{total} test başarılı\n")

    if success == total:
        print("🎉 TÜM TESTLER BAŞARILI! Wave 2B kaliteli soru üretimi çalışıyor.")
        return 0
    else:
        print("⚠️  Bazı testler başarısız oldu.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
