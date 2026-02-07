"""
Test Hybrid Question Generation
Generate 10 test questions and measure quality metrics
"""

import asyncio
import os
import json
from datetime import datetime

# Set API keys from environment
os.environ["ANTHROPIC_API_KEY"] = os.getenv(
    "ANTHROPIC_API_KEY", "your-anthropic-key-here"
)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-key-here")

from services.hybrid_question_generator import HybridQuestionGenerator


async def test_single_question():
    """Test 1: Generate a single question"""
    print("\n" + "=" * 80)
    print("TEST 1: Single ÖSYM-Guided Question Generation")
    print("=" * 80 + "\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    try:
        question = await generator.generate_osym_quality_question(
            subject="Matematik",
            topic="Türev Alma Kuralları",
            difficulty="orta",
            exam_type="TYT",
            provider="claude",
            validate=True,
        )

        print(f"✅ QUESTION GENERATED!")
        print(f"\n📝 STEM:")
        print(f"{question['stem']}\n")

        print(f"📋 OPTIONS:")
        for key, value in question["options"].items():
            marker = "✓" if key == question["correct_answer"] else " "
            print(f"{marker} {key}) {value}")

        print(f"\n✅ Correct Answer: {question['correct_answer']}")
        print(f"📖 Explanation: {question['explanation'][:150]}...")

        print(f"\n📊 QUALITY METRICS:")
        print(f"  Overall Quality: {question['quality_score']:.2f}/1.00")
        print(f"  ÖSYM Compliance: {question['osym_compliance_score']:.2f}/1.00")
        print(f"  IRT Difficulty: {question['irt_difficulty']:.2f}")
        print(f"  IRT Discrimination: {question['irt_discrimination']:.2f}")
        print(f"  Morphology Complexity: {question['morphology_complexity']:.2f}")
        print(f"  Readability: {question['readability_score']:.2f}")
        print(f"  Valid: {'✅ YES' if question['is_valid'] else '❌ NO'}")

        if question.get("validation_issues"):
            print(f"\n⚠️ Issues: {', '.join(question['validation_issues'])}")

        return question

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_bulk_generation():
    """Test 2: Generate 10 questions"""
    print("\n" + "=" * 80)
    print("TEST 2: Bulk Question Generation (10 questions)")
    print("=" * 80 + "\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test subjects and topics
    test_cases = [
        {"subject": "Matematik", "topic": "Türev", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Limit", "difficulty": "kolay"},
        {"subject": "Matematik", "topic": "İntegral", "difficulty": "zor"},
        {"subject": "Fizik", "topic": "Newton Kanunları", "difficulty": "orta"},
        {"subject": "Fizik", "topic": "Elektrik", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Asit-Baz", "difficulty": "orta"},
        {"subject": "Türkçe", "topic": "Anlam Bilgisi", "difficulty": "kolay"},
        {"subject": "Türkçe", "topic": "Dil Bilgisi", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Fonksiyonlar", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Geometri", "difficulty": "zor"},
    ]

    generated_questions = []
    success_count = 0
    failed_count = 0

    for i, test_case in enumerate(test_cases, 1):
        print(
            f"\n[{i}/10] Generating: {test_case['subject']} - {test_case['topic']} ({test_case['difficulty']})"
        )

        try:
            question = await generator.generate_osym_quality_question(
                subject=test_case["subject"],
                topic=test_case["topic"],
                difficulty=test_case["difficulty"],
                exam_type="TYT",
                provider="claude",
                validate=True,
            )

            generated_questions.append(question)
            success_count += 1

            print(f"  ✅ Success!")
            print(
                f"     Quality: {question['quality_score']:.2f}, ÖSYM: {question['osym_compliance_score']:.2f}"
            )

        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed: {e}")
            continue

    # Calculate statistics
    if generated_questions:
        avg_quality = sum(q["quality_score"] for q in generated_questions) / len(
            generated_questions
        )
        avg_osym = sum(q["osym_compliance_score"] for q in generated_questions) / len(
            generated_questions
        )
        avg_irt_diff = sum(q["irt_difficulty"] for q in generated_questions) / len(
            generated_questions
        )
        avg_irt_disc = sum(q["irt_discrimination"] for q in generated_questions) / len(
            generated_questions
        )

        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Generated: {success_count}/10")
        print(f"Success Rate: {success_count/10*100:.1f}%")
        print(f"\nQUALITY METRICS (Average):")
        print(f"  Overall Quality: {avg_quality:.3f}/1.00")
        print(f"  ÖSYM Compliance: {avg_osym:.3f}/1.00")
        print(f"  IRT Difficulty: {avg_irt_diff:.3f}")
        print(f"  IRT Discrimination: {avg_irt_disc:.3f}")

        # Save results to file
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_generated": success_count,
            "success_rate": success_count / 10,
            "average_metrics": {
                "quality_score": avg_quality,
                "osym_compliance": avg_osym,
                "irt_difficulty": avg_irt_diff,
                "irt_discrimination": avg_irt_disc,
            },
            "questions": generated_questions,
        }

        output_file = (
            f"hybrid_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Results saved to: {output_file}")

    return generated_questions


async def test_ensemble():
    """Test 3: Ensemble generation (multi-model)"""
    print("\n" + "=" * 80)
    print("TEST 3: Ensemble Generation (Multi-Model)")
    print("=" * 80 + "\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    try:
        question = await generator.generate_ensemble(
            subject="Matematik", topic="Limit", difficulty="orta", exam_type="TYT"
        )

        print(f"✅ ENSEMBLE QUESTION GENERATED!")
        print(f"\n🏆 Winning Provider: {question['winning_provider']}")
        print(f"📊 Candidates Evaluated: {question['candidates_evaluated']}")
        print(f"⭐ Final Quality: {question['quality_score']:.2f}/1.00")

        print(f"\n📝 Question: {question['stem'][:200]}...")

        return question

    except Exception as e:
        print(f"❌ Ensemble failed: {e}")
        return None


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 HYBRID QUESTION GENERATION - TEST SUITE")
    print("=" * 80)
    print("\nTesting ÖSYM-guided AI question generation with quality metrics\n")

    # Check API keys
    if (
        not os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY") == "your-anthropic-key-here"
    ):
        print("⚠️ WARNING: ANTHROPIC_API_KEY not set!")
        print("Please set it in your .env file or environment variables")
        print("\nRunning in demo mode...\n")

    # Test 1: Single question
    print("\n[START] Running Test 1: Single Question")
    single_q = await test_single_question()

    # Wait a bit
    await asyncio.sleep(2)

    # Test 2: Bulk generation (10 questions)
    print("\n[START] Running Test 2: Bulk Generation")
    bulk_q = await test_bulk_generation()

    # Test 3: Ensemble (optional - costs 3x)
    # Uncomment to test ensemble:
    # print("\n[START] Running Test 3: Ensemble")
    # ensemble_q = await test_ensemble()

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 80)

    print("\n📋 NEXT STEPS:")
    print("  1. Review quality metrics in generated questions")
    print("  2. Check JSON output file for details")
    print("  3. Add API endpoint to main.py")
    print("  4. Test via HTTP endpoint")
    print("  5. Generate 1000 questions for production")


if __name__ == "__main__":
    asyncio.run(main())
