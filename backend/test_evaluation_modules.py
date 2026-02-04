"""
Test Script for Wave 2B Evaluation Modules

Tests:
1. BERTScore evaluator
2. ÖSYM Benchmark comparator
3. Enhanced Bloom classifier
4. Comprehensive quality evaluator pipeline

Usage:
    cd backend
    py test_evaluation_modules.py
"""

import sys
import json
from pathlib import Path

# Set UTF-8 encoding for console
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def test_bertscore_evaluator():
    """Test BERTScore semantic similarity evaluator"""
    print("\n" + "=" * 70)
    print("TEST 1: BERTScore Semantic Similarity Evaluator")
    print("=" * 70)

    from services.bertscore_evaluator import BERTScoreEvaluator

    evaluator = BERTScoreEvaluator()

    if not evaluator.is_available():
        print("❌ BERTScore not available (bert-score not installed)")
        print("   Install with: pip install bert-score")
        return False

    # Test cases
    test_pairs = [
        {
            "name": "High similarity (same concept)",
            "ai": "Bir maddenin mol kütlesi 40 g/mol'dür. 20 gram bu maddede kaç mol madde vardır?",
            "osym": "Mol kütlesi 32 g/mol olan bir elementin 16 gramında kaç mol element vardır?",
            "expected": "high",
        },
        {
            "name": "Medium similarity (related concept)",
            "ai": "Fotosentez olayında hangi gaz açığa çıkar?",
            "osym": "Bitkilerin fotosentez yapması sırasında atmosfere hangi gaz verilir?",
            "expected": "very_high",
        },
        {
            "name": "Low similarity (different concept)",
            "ai": "Newton'un ikinci yasası kuvvet ve ivme arasındaki ilişkiyi nasıl tanımlar?",
            "osym": "Fotosentez olayında hangi gaz açığa çıkar?",
            "expected": "low",
        },
    ]

    print(f"\nRunning {len(test_pairs)} test pairs...\n")

    success_count = 0
    for i, test in enumerate(test_pairs, 1):
        print(f"{i}. {test['name']}")
        print(f"   AI:   {test['ai'][:60]}...")
        print(f"   ÖSYM: {test['osym'][:60]}...")

        result = evaluator.evaluate_single(test["ai"], test["osym"])

        if result:
            f1 = result["f1"]
            interp = result["interpretation"]
            print(f"   ✓ F1 Score: {f1:.3f} ({interp})")

            # Validate expectation
            if test["expected"] == "very_high" and f1 >= 0.85:
                success_count += 1
            elif test["expected"] == "high" and f1 >= 0.75:
                success_count += 1
            elif test["expected"] == "low" and f1 < 0.75:
                success_count += 1
            else:
                print(f"   ⚠️  Expected {test['expected']}, got F1={f1:.3f}")
        else:
            print(f"   ✗ Evaluation failed")

        print()

    print(f"Results: {success_count}/{len(test_pairs)} tests passed")
    return success_count == len(test_pairs)


def test_benchmark_comparator():
    """Test ÖSYM Benchmark comparator"""
    print("\n" + "=" * 70)
    print("TEST 2: ÖSYM Benchmark Comparator")
    print("=" * 70)

    from services.osym_benchmark_comparator import OSYMBenchmarkComparator

    comparator = OSYMBenchmarkComparator()

    # Sample ÖSYM questions (reference)
    osym_questions = [
        {
            "question_text": "Bir elementin atom numarası 17'dir. Bu elementin değerlik elektron sayısı kaçtır?",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
        {
            "question_text": "25 gramındaki bir maddenin mol sayısı 0.5 mol ise, bu maddenin mol kütlesi kaç g/mol'dür?",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
        {
            "question_text": "Fotosentez olayında bitkilerin kullandığı gaz hangisidir?",
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
            "subject": "Biyoloji",
        },
        {
            "question_text": "İki vektörün skaler çarpımı için hangi formül kullanılır?",
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
            "subject": "Matematik",
        },
        {
            "question_text": "Newton'un ikinci yasasına göre, bir cisme etki eden net kuvvet ile ivme arasındaki bağıntı nedir?",
            "difficulty": "Orta",
            "bloom_level": "Anlama",
            "subject": "Fizik",
        },
    ]

    print(f"\nSetting reference benchmark: {len(osym_questions)} ÖSYM questions")
    ref_stats = comparator.set_reference_benchmark(osym_questions)
    print(f"✓ Reference statistics:")
    print(f"  Mean length: {ref_stats.mean_length:.0f} chars")
    print(f"  Difficulty distribution: {ref_stats.difficulty_percentages}")

    # Sample AI questions
    ai_questions = [
        {
            "question_text": "20 gram H₂O molekülünde kaç mol H₂O vardır? (H=1, O=16)",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
        {
            "question_text": "Atom numarası 8 olan elementin adı nedir?",
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
            "subject": "Kimya",
        },
        {
            "question_text": "İki kuvvetin bileşkesi nasıl bulunur?",
            "difficulty": "Orta",
            "bloom_level": "Anlama",
            "subject": "Fizik",
        },
    ]

    print(
        f"\nComparing {len(ai_questions)} AI-generated questions against benchmark..."
    )
    comparison = comparator.compare_against_benchmark(ai_questions)

    print(f"\n✓ Comparison Results:")
    print(
        f"  Overall similarity: {comparison.overall_similarity:.3f} ({comparison.interpretation})"
    )
    print(f"  Length similarity: {comparison.length_similarity:.3f}")
    print(f"  Difficulty similarity: {comparison.difficulty_similarity:.3f}")
    print(f"  Bloom similarity: {comparison.bloom_similarity:.3f}")

    if comparison.issues:
        print(f"\n⚠️  Issues found:")
        for issue in comparison.issues:
            print(f"  - {issue}")

    if comparison.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in comparison.recommendations[:3]:
            print(f"  - {rec}")

    # Test passes if overall similarity > 0.70
    passed = comparison.overall_similarity >= 0.70
    print(f"\nTest result: {'✓ PASSED' if passed else '✗ FAILED'}")
    return passed


def test_bloom_classifier():
    """Test Enhanced Bloom classifier"""
    print("\n" + "=" * 70)
    print("TEST 3: Enhanced Bloom Classifier")
    print("=" * 70)

    from services.enhanced_bloom_classifier import EnhancedBloomClassifier

    classifier = EnhancedBloomClassifier()

    # Test questions with expected levels
    test_questions = [
        ("Türkiye'nin başkenti neresidir?", 1, "Hatırlama"),
        ("Fotosentez olayını açıklayınız.", 2, "Anlama"),
        ("15 × 8 işleminin sonucunu bulunuz.", 3, "Uygulama"),
        ("Mitoz ve mayoz bölünme arasındaki farkları analiz ediniz.", 4, "Analiz"),
        ("Bu argümanın güçlü ve zayıf yönlerini değerlendiriniz.", 5, "Değerlendirme"),
        (
            "Yenilenebilir enerji kaynakları için yeni bir tasarım öneriniz.",
            6,
            "Yaratma",
        ),
    ]

    print(
        f"\nTesting keyword-based classification on {len(test_questions)} questions:\n"
    )

    correct = 0
    for question, expected_level, expected_name in test_questions:
        result = classifier.classify(question, method="keyword")

        match = "✓" if result.level == expected_level else "✗"
        print(f"{match} Question: {question[:60]}...")
        print(f"   Expected: [{expected_level}] {expected_name}")
        print(
            f"   Got:      [{result.level}] {result.level_name} (confidence={result.confidence:.2f})"
        )
        print()

        if result.level == expected_level:
            correct += 1

    accuracy = correct / len(test_questions)
    print(f"Accuracy: {correct}/{len(test_questions)} ({accuracy:.1%})")

    # Test training capability (if sklearn available)
    if classifier._sklearn_available:
        print(f"\n✓ Testing TF-IDF model training...")

        # Create synthetic training data
        train_q = [q for q, _, _ in test_questions] * 5
        train_l = [l for _, l, _ in test_questions] * 5

        results = classifier.train_tfidf_model(train_q, train_l)
        print(f"  Training accuracy: {results['train_accuracy']:.3f}")
        print(f"  Training samples: {results['train_samples']}")

        # Test ensemble after training
        print(f"\n✓ Testing ensemble classification:")
        ensemble_correct = 0
        for question, expected_level, expected_name in test_questions[:3]:
            result = classifier.classify(question, method="ensemble")
            match = "✓" if result.level == expected_level else "✗"
            print(
                f"  {match} [{result.level}] {result.level_name} (conf={result.confidence:.2f}): {question[:40]}..."
            )
            if result.level == expected_level:
                ensemble_correct += 1

    # Test passes if accuracy > 60% (keyword-based is imperfect)
    passed = accuracy >= 0.60
    print(f"\nTest result: {'✓ PASSED' if passed else '✗ FAILED'}")
    return passed


def test_comprehensive_evaluator():
    """Test comprehensive quality evaluator pipeline"""
    print("\n" + "=" * 70)
    print("TEST 4: Comprehensive Quality Evaluator Pipeline")
    print("=" * 70)

    from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator

    # Sample ÖSYM questions for reference
    osym_questions = [
        {
            "question_text": "Bir elementin atom numarası 17'dir. Bu elementin değerlik elektron sayısı kaçtır?",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
        {
            "question_text": "25 gramındaki bir maddenin mol sayısı 0.5 mol ise, bu maddenin mol kütlesi kaç g/mol'dür?",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
    ]

    print(f"\nInitializing evaluator with {len(osym_questions)} reference questions...")
    evaluator = ComprehensiveQualityEvaluator(osym_reference_questions=osym_questions)

    # Test question
    test_question = {
        "question_text": "40 gram NaOH'ın mol sayısı kaçtır? (Na=23, O=16, H=1)",
        "choices": ["A) 0.5", "B) 1", "C) 1.5", "D) 2", "E) 2.5"],
        "correct_answer": "B",
        "difficulty": "Orta",
        "bloom_level": "Uygulama",
        "subject": "Kimya",
    }

    # Test at different stages
    stages = ["quick", "standard", "thorough"]

    print(f"\nEvaluating question at {len(stages)} stages:\n")

    results = {}
    for stage in stages:
        print(f"📊 {stage.upper()} evaluation:")
        result = evaluator.evaluate(test_question, stage=stage)

        print(f"   Overall Score: {result.overall_score:.3f} ({result.overall_grade})")
        print(f"   Decision: {result.decision}")
        print(f"   Evaluation Time: {result.evaluation_time_ms:.0f}ms")

        if result.bloom_level:
            print(
                f"   Bloom Level: {result.bloom_level} (confidence={result.bloom_confidence:.2f})"
            )

        if result.strengths:
            print(f"   ✓ Strengths: {result.strengths[0]}")

        if result.weaknesses:
            print(f"   ✗ Weaknesses: {result.weaknesses[0]}")

        print()
        results[stage] = result

    # Batch evaluation test
    print(f"📊 Batch evaluation test:")
    batch_questions = [test_question] * 3  # 3 copies for demo

    batch_results = evaluator.evaluate_batch(batch_questions, stage="quick")
    print(f"   Total questions: {batch_results['total_questions']}")
    print(f"   Mean score: {batch_results['mean_score']:.3f}")
    print(
        f"   Approved: {batch_results['approved']}/{batch_results['total_questions']}"
    )
    print(f"   Approval rate: {batch_results['approval_rate']:.1%}")

    # Test passes if standard evaluation gives reasonable score
    passed = results.get("standard") and results["standard"].overall_score >= 0.70
    print(f"\nTest result: {'✓ PASSED' if passed else '✗ FAILED'}")
    return passed


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" " * 15 + "WAVE 2B EVALUATION MODULES TEST SUITE")
    print("=" * 70)

    tests = [
        ("BERTScore Evaluator", test_bertscore_evaluator),
        ("ÖSYM Benchmark Comparator", test_benchmark_comparator),
        ("Enhanced Bloom Classifier", test_bloom_classifier),
        ("Comprehensive Quality Evaluator", test_comprehensive_evaluator),
    ]

    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "PASSED" if passed else "FAILED"
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed with error: {e}")
            import traceback

            traceback.print_exc()
            results[name] = "ERROR"

    # Summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)

    for name, result in results.items():
        icon = "✓" if result == "PASSED" else ("✗" if result == "FAILED" else "❌")
        print(f"{icon} {name}: {result}")

    passed_count = sum(1 for r in results.values() if r == "PASSED")
    total_count = len(results)

    print(
        f"\nOverall: {passed_count}/{total_count} tests passed ({passed_count/total_count:.0%})"
    )

    if passed_count == total_count:
        print("\n🎉 All tests PASSED! Wave 2B evaluation modules are ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
