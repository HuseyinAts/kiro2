"""
Gerçek ÖSYM Verileriyle Wave 2B Modül Testleri

Veritabanından gerçek ÖSYM sorularını kullanarak tüm modülleri test eder.
"""

import sys
import json
from pathlib import Path
import asyncio

# UTF-8 kodlama
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# Veritabanı bağlantısı için
from core.database import get_db_session
from sqlalchemy import text


async def get_osym_questions_from_db(limit=50):
    """Veritabanından gerçek ÖSYM sorularını al"""
    async for db in get_db_session():
        try:
            # Cevaplı soruları al (kaynak kontrolü yok çünkü NULL)
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
                AND LENGTH(metin) > 50
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
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                        "length": row[4],
                    }
                )

            print(f"✓ Veritabanından {len(questions)} ÖSYM sorusu alındı")
            return questions

        except Exception as e:
            print(f"Veritabanı hatası: {e}")
            raise


def test_bertscore_with_real_data(osym_questions):
    """BERTScore'u gerçek verilerle test et"""
    print("\n" + "=" * 70)
    print("TEST 1: BERTScore - Gerçek ÖSYM Verileriyle")
    print("=" * 70)

    from services.bertscore_evaluator import BERTScoreEvaluator

    evaluator = BERTScoreEvaluator()

    if not evaluator.is_available():
        print("✗ BERTScore kullanılamıyor")
        return False

    # İlk 5 soruyu karşılaştır
    if len(osym_questions) < 2:
        print("✗ Yetersiz soru sayısı")
        return False

    print(f"\n{len(osym_questions[:5])} ÖSYM sorusunu karşılaştırıyorum...\n")

    successes = 0
    for i in range(min(5, len(osym_questions) - 1)):
        q1 = osym_questions[i]
        q2 = osym_questions[i + 1]

        result = evaluator.evaluate_single(q1["question_text"], q2["question_text"])

        if result:
            print(f"{i+1}. Karşılaştırma:")
            print(f"   F1: {result['f1']:.3f} ({result['interpretation']})")
            print(f"   Q1: {q1['question_text'][:60]}...")
            print(f"   Q2: {q2['question_text'][:60]}...")
            print()
            successes += 1

    passed = successes >= 3
    print(
        f"Sonuç: {successes}/5 başarılı - {'✓ BAŞARILI' if passed else '✗ BAŞARISIZ'}"
    )
    return passed


def test_benchmark_with_real_data(osym_questions):
    """ÖSYM Benchmark'ı gerçek verilerle test et"""
    print("\n" + "=" * 70)
    print("TEST 2: ÖSYM Benchmark - Gerçek Verilerle")
    print("=" * 70)

    from services.osym_benchmark_comparator import OSYMBenchmarkComparator

    comparator = OSYMBenchmarkComparator()

    # İlk yarısı referans, ikinci yarısı test
    mid = len(osym_questions) // 2
    reference_questions = osym_questions[:mid]
    test_questions = osym_questions[mid:]

    print(f"\nReferans: {len(reference_questions)} soru")
    print(f"Test: {len(test_questions)} soru\n")

    # Referans benchmark'ı ayarla
    ref_stats = comparator.set_reference_benchmark(reference_questions)
    print(f"✓ Referans istatistikleri:")
    print(f"  Ortalama uzunluk: {ref_stats.mean_length:.0f} karakter")
    print(f"  Zorluk dağılımı: {ref_stats.difficulty_percentages}")

    # Test sorularını karşılaştır
    comparison = comparator.compare_against_benchmark(test_questions)

    print(f"\n✓ Karşılaştırma Sonuçları:")
    print(
        f"  Genel benzerlik: {comparison.overall_similarity:.3f} ({comparison.interpretation})"
    )
    print(f"  Uzunluk benzerliği: {comparison.length_similarity:.3f}")
    print(f"  Zorluk benzerliği: {comparison.difficulty_similarity:.3f}")

    if comparison.overall_similarity >= 0.75:
        print(
            f"\n✓ Test BAŞARILI - Aynı kaynaktan gelen sorular benzer dağılım gösteriyor"
        )
        return True
    else:
        print(f"\n⚠️  Benzerlik {comparison.overall_similarity:.3f} - Beklenen ≥0.75")
        if comparison.issues:
            print("Sorunlar:")
            for issue in comparison.issues[:3]:
                print(f"  - {issue}")
        return False


def test_bloom_with_real_data(osym_questions):
    """Bloom sınıflandırıcıyı gerçek verilerle test et"""
    print("\n" + "=" * 70)
    print("TEST 3: Bloom Sınıflandırıcı - Gerçek ÖSYM Soruları")
    print("=" * 70)

    from services.enhanced_bloom_classifier import EnhancedBloomClassifier

    classifier = EnhancedBloomClassifier()

    print(f"\n{min(10, len(osym_questions))} ÖSYM sorusunu sınıflandırıyorum...\n")

    bloom_counts = {}
    for i, q in enumerate(osym_questions[:10], 1):
        result = classifier.classify(q["question_text"], method="keyword")

        level_name = result.level_name
        bloom_counts[level_name] = bloom_counts.get(level_name, 0) + 1

        print(f"{i}. [{result.level}] {level_name} ({result.confidence:.2f})")
        print(f"   {q['question_text'][:60]}...")
        print()

    print(f"Bloom Dağılımı:")
    for level, count in sorted(bloom_counts.items()):
        print(f"  {level}: {count} soru")

    # Başarı kriteri: En az 3 farklı seviye tespit edilmeli
    unique_levels = len(bloom_counts)
    passed = unique_levels >= 3

    print(
        f"\nSonuç: {unique_levels} farklı seviye tespit edildi - {'✓ BAŞARILI' if passed else '✗ BAŞARISIZ'}"
    )
    return passed


def test_comprehensive_with_real_data(osym_questions):
    """Kapsamlı değerlendiriciyi gerçek verilerle test et"""
    print("\n" + "=" * 70)
    print("TEST 4: Kapsamlı Değerlendirici - Gerçek ÖSYM Soruları")
    print("=" * 70)

    from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator

    # Referans sorular
    reference = osym_questions[:20]
    # Test soruları
    test_questions = osym_questions[20:25]

    print(f"\nReferans: {len(reference)} soru")
    print(f"Test: {len(test_questions)} soru\n")

    evaluator = ComprehensiveQualityEvaluator(osym_reference_questions=reference)

    print("Değerlendirme aşamaları:\n")

    results_by_stage = {}
    for stage in ["quick", "standard", "thorough"]:
        print(f"📊 {stage.upper()} değerlendirme:")

        # İlk test sorusunu değerlendir
        if test_questions:
            result = evaluator.evaluate(test_questions[0], stage=stage)

            print(f"   Genel Skor: {result.overall_score:.3f} ({result.overall_grade})")
            print(f"   Karar: {result.decision}")
            print(f"   Süre: {result.evaluation_time_ms:.0f}ms")

            if result.bloom_level:
                print(
                    f"   Bloom: Seviye {result.bloom_level} (güven={result.bloom_confidence:.2f})"
                )

            results_by_stage[stage] = result

        print()

    # Toplu değerlendirme
    batch_results = evaluator.evaluate_batch(test_questions[:3], stage="quick")
    print(f"📊 Toplu değerlendirme:")
    print(f"   Toplam: {batch_results['total_questions']} soru")
    print(f"   Ortalama skor: {batch_results['mean_score']:.3f}")
    print(
        f"   Onaylanan: {batch_results['approved']}/{batch_results['total_questions']}"
    )
    print(f"   Onay oranı: {batch_results['approval_rate']:.1%}")

    # Başarı kriteri: Ortalama skor ≥ 0.70
    passed = batch_results["mean_score"] >= 0.70
    print(f"\nSonuç: {'✓ BAŞARILI' if passed else '✗ BAŞARISIZ'}")
    return passed


async def main():
    """Ana test fonksiyonu"""
    print("\n" + "=" * 70)
    print(" " * 15 + "WAVE 2B - GERÇEK VERİ TESTLERİ")
    print("=" * 70)

    # Veritabanından gerçek ÖSYM sorularını al
    print("\nVeritabanı bağlantısı kuruluyor...")
    try:
        osym_questions = await get_osym_questions_from_db(limit=30)
    except Exception as e:
        print(f"✗ Veritabanı hatası: {e}")
        print("\nTest veritabanı bağlantısı olmadan çalışamaz.")
        return 1

    if len(osym_questions) < 5:
        print(
            f"✗ Yetersiz veri: {len(osym_questions)} soru bulundu (minimum 5 gerekli)"
        )
        return 1

    print(f"✓ {len(osym_questions)} ÖSYM sorusu yüklendi")
    print(
        f"  Ortalama uzunluk: {sum(q['length'] for q in osym_questions) / len(osym_questions):.0f} karakter"
    )

    # Testleri çalıştır
    tests = [
        (
            "BERTScore Değerlendirici",
            lambda: test_bertscore_with_real_data(osym_questions),
        ),
        (
            "ÖSYM Benchmark Karşılaştırıcı",
            lambda: test_benchmark_with_real_data(osym_questions),
        ),
        ("Bloom Sınıflandırıcı", lambda: test_bloom_with_real_data(osym_questions)),
        (
            "Kapsamlı Kalite Değerlendirici",
            lambda: test_comprehensive_with_real_data(osym_questions),
        ),
    ]

    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "BAŞARILI" if passed else "BAŞARISIZ"
        except Exception as e:
            print(f"\n✗ Test '{name}' hata verdi: {e}")
            import traceback

            traceback.print_exc()
            results[name] = "HATA"

    # Özet
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST ÖZETİ")
    print("=" * 70)

    for name, result in results.items():
        icon = "✓" if result == "BAŞARILI" else ("✗" if result == "BAŞARISIZ" else "❌")
        print(f"{icon} {name}: {result}")

    passed_count = sum(1 for r in results.values() if r == "BAŞARILI")
    total_count = len(results)

    print(
        f"\nGenel: {passed_count}/{total_count} test başarılı ({passed_count/total_count:.0%})"
    )

    if passed_count == total_count:
        print(
            "\n🎉 TÜM TESTLER BAŞARILI! Wave 2B modülleri gerçek verilerle doğrulandı."
        )
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test başarısız oldu.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
