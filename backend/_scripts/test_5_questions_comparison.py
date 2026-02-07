"""
Test 5 Questions - OSYM Compliance Comparison
Generate 5 questions and compare quality metrics
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.hybrid_question_generator import HybridQuestionGenerator


async def generate_5_questions():
    """Generate 5 questions and analyze quality"""

    print("\n" + "=" * 80)
    print("TEST: 5 QUESTIONS - OSYM COMPLIANCE COMPARISON")
    print("=" * 80 + "\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test cases - different topics
    test_cases = [
        {"subject": "Matematik", "topic": "Turev", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Limit", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Fonksiyonlar", "difficulty": "kolay"},
        {"subject": "Fizik", "topic": "Newton Kanunlari", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Asit-Baz", "difficulty": "orta"},
    ]

    questions = []
    metrics_summary = {
        "osym_compliance": [],
        "overall_quality": [],
        "readability": [],
        "stem_length": [],
        "validation_passed": 0,
    }

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/5] Generating: {test_case['subject']} - {test_case['topic']}")
        print("-" * 80)

        try:
            question = await generator.generate_osym_quality_question(
                subject=test_case["subject"],
                topic=test_case["topic"],
                difficulty=test_case["difficulty"],
                exam_type="TYT",
                provider="claude",
                validate=True,
            )

            # Extract metrics
            osym_score = question.get("osym_compliance_score", 0)
            quality_score = question.get("quality_score", 0)
            readability = question.get("readability_score", 0)
            stem_length = len(question.get("stem", ""))
            is_valid = question.get("is_valid", False)

            # Store metrics
            metrics_summary["osym_compliance"].append(osym_score)
            metrics_summary["overall_quality"].append(quality_score)
            metrics_summary["readability"].append(readability)
            metrics_summary["stem_length"].append(stem_length)
            if is_valid:
                metrics_summary["validation_passed"] += 1

            # Print question
            print(f"\nSTEM ({stem_length} chars):")
            print(f"{question['stem']}\n")

            print(f"CORRECT ANSWER: {question['correct_answer']}")

            print(f"\nMETRICS:")
            print(f"  OSYM Compliance: {osym_score:.2f}")
            print(f"  Overall Quality: {quality_score:.2f}")
            print(f"  Readability:     {readability:.2f}")
            print(f"  Valid:           {'YES' if is_valid else 'NO'}")

            if not is_valid:
                issues = question.get("validation_issues", [])
                print(f"  Issues:          {', '.join(issues)}")

            questions.append(question)

            print(
                f"\n{'[OK]' if osym_score >= 0.80 else '[LOW]'} OSYM Compliance: {osym_score:.2f}"
            )

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Calculate averages
    print("\n" + "=" * 80)
    print("SUMMARY - COMPARISON WITH TARGETS")
    print("=" * 80 + "\n")

    if questions:
        avg_osym = sum(metrics_summary["osym_compliance"]) / len(
            metrics_summary["osym_compliance"]
        )
        avg_quality = sum(metrics_summary["overall_quality"]) / len(
            metrics_summary["overall_quality"]
        )
        avg_readability = sum(metrics_summary["readability"]) / len(
            metrics_summary["readability"]
        )
        avg_length = sum(metrics_summary["stem_length"]) / len(
            metrics_summary["stem_length"]
        )

        print(f"Questions Generated: {len(questions)}/5")
        print(f"Validation Passed:   {metrics_summary['validation_passed']}/5")
        print(f"\nAVERAGE METRICS:")
        print(
            f"  OSYM Compliance: {avg_osym:.2f} (target: >0.80) {'[OK]' if avg_osym >= 0.80 else '[LOW]'}"
        )
        print(
            f"  Overall Quality: {avg_quality:.2f} (target: >0.80) {'[OK]' if avg_quality >= 0.80 else '[LOW]'}"
        )
        print(
            f"  Readability:     {avg_readability:.2f} (target: >0.70) {'[OK]' if avg_readability >= 0.70 else '[LOW]'}"
        )
        print(f"  Avg Stem Length: {avg_length:.0f} chars (target: 100-150)")

        # Individual scores
        print(f"\nINDIVIDUAL OSYM COMPLIANCE SCORES:")
        for i, score in enumerate(metrics_summary["osym_compliance"], 1):
            status = "[OK]" if score >= 0.80 else "[LOW]"
            print(f"  Question {i}: {score:.2f} {status}")

        print(f"\nSTEM LENGTHS:")
        for i, length in enumerate(metrics_summary["stem_length"], 1):
            status = (
                "[OK]"
                if 100 <= length <= 150
                else ("[SHORT]" if length < 100 else "[LONG]")
            )
            print(f"  Question {i}: {length} chars {status}")

        # Improvement analysis
        print(f"\n" + "=" * 80)
        print("IMPROVEMENT ANALYSIS")
        print("=" * 80 + "\n")

        if avg_osym >= 0.80:
            print("[SUCCESS] OSYM compliance target achieved!")
            print("  System is ready for production testing.")
        elif avg_osym >= 0.60:
            print("[PROGRESS] OSYM compliance improving but not at target yet.")
            print("  Recommendation: Further prompt refinement needed.")
        else:
            print("[NEEDS WORK] OSYM compliance still low.")
            print("  Recommendation: Major prompt revision required.")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "5_questions_comparison",
            "summary": {
                "total_generated": len(questions),
                "validation_passed": metrics_summary["validation_passed"],
                "avg_osym_compliance": avg_osym,
                "avg_quality": avg_quality,
                "avg_readability": avg_readability,
                "avg_stem_length": avg_length,
            },
            "questions": questions,
            "metrics_by_question": metrics_summary,
        }

        output_file = (
            f"test_5_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] Results saved to: {output_file}")

    else:
        print("[ERROR] No questions were generated successfully.")

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80 + "\n")

    return questions


if __name__ == "__main__":
    asyncio.run(generate_5_questions())
