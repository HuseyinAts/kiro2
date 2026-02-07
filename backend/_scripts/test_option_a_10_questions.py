"""
Test Option A: Database Average Length
Generate 10 questions with Option A implementation and compare with baseline (0.49)

Expected Improvement: +30% (0.49 -> 0.65)
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.hybrid_question_generator import HybridQuestionGenerator


async def test_option_a():
    """
    Test Option A: Use database average length instead of example average

    Baseline (without Option A): 0.49 ÖSYM compliance
    Expected (with Option A): 0.65 ÖSYM compliance (+30% improvement)
    """

    print("\n" + "=" * 80)
    print("TEST: OPTION A - DATABASE AVERAGE LENGTH")
    print("=" * 80 + "\n")
    print("BASELINE: 0.49 ÖSYM compliance (example-based length)")
    print("TARGET:   0.65 ÖSYM compliance (database-based length)")
    print("EXPECTED: +30% improvement\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test cases - 10 questions across different subjects
    # Prioritize subjects with known target lengths
    test_cases = [
        # Kimya (shortest: 202 chars)
        {"subject": "Kimya", "topic": "Asit-Baz Tepkimeleri", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Mol Kavrami", "difficulty": "kolay"},
        # Matematik (medium: 388 chars)
        {"subject": "Matematik", "topic": "Turev Alma Kurallari", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Limit", "difficulty": "kolay"},
        # Fizik (long: 453 chars)
        {"subject": "Fizik", "topic": "Newton Kanunlari", "difficulty": "orta"},
        {"subject": "Fizik", "topic": "Hareket", "difficulty": "kolay"},
        # Biyoloji (291 chars)
        {"subject": "Biyoloji", "topic": "Fotosentez", "difficulty": "orta"},
        # Mixed subjects
        {"subject": "Matematik", "topic": "Fonksiyonlar", "difficulty": "zor"},
        {"subject": "Fizik", "topic": "Kuvvet ve Hareket", "difficulty": "zor"},
        {"subject": "Kimya", "topic": "Kimyasal Denge", "difficulty": "orta"},
    ]

    questions = []
    metrics_summary = {
        "osym_compliance": [],
        "overall_quality": [],
        "readability": [],
        "stem_length": [],
        "target_length": [],
        "length_deviation": [],
        "validation_passed": 0,
    }

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/10] Generating: {test_case['subject']} - {test_case['topic']}")
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

            # Get target length from research
            from services.osym_inspired_generator import SUBJECT_TARGET_LENGTHS

            target_length = SUBJECT_TARGET_LENGTHS.get(
                test_case["subject"], SUBJECT_TARGET_LENGTHS["DEFAULT"]
            )

            # Calculate deviation
            length_deviation = abs(stem_length - target_length) / target_length

            # Store metrics
            metrics_summary["osym_compliance"].append(osym_score)
            metrics_summary["overall_quality"].append(quality_score)
            metrics_summary["readability"].append(readability)
            metrics_summary["stem_length"].append(stem_length)
            metrics_summary["target_length"].append(target_length)
            metrics_summary["length_deviation"].append(length_deviation)
            if is_valid:
                metrics_summary["validation_passed"] += 1

            # Print question summary
            print(f"\nSTEM ({stem_length} chars, target: {target_length}):")
            print(f"{question['stem'][:150]}...")
            print(f"\nCORRECT ANSWER: {question['correct_answer']}")

            print(f"\nMETRICS:")
            print(
                f"  OSYM Compliance: {osym_score:.2f} {'[OK]' if osym_score >= 0.80 else '[LOW]'}"
            )
            print(f"  Overall Quality: {quality_score:.2f}")
            print(
                f"  Length Deviation: {length_deviation:.1%} {'[OK]' if length_deviation < 0.2 else '[HIGH]'}"
            )
            print(f"  Valid: {'YES' if is_valid else 'NO'}")

            if not is_valid:
                issues = question.get("validation_issues", [])
                print(f"  Issues: {', '.join(issues)}")

            questions.append(question)

            # Brief pause to avoid rate limiting
            await asyncio.sleep(2)

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Calculate summary statistics
    print("\n" + "=" * 80)
    print("OPTION A RESULTS - COMPARISON WITH BASELINE")
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
        avg_deviation = sum(metrics_summary["length_deviation"]) / len(
            metrics_summary["length_deviation"]
        )

        # Show improvement
        baseline_osym = 0.49
        improvement = ((avg_osym - baseline_osym) / baseline_osym) * 100
        target_osym = 0.65
        target_reached = avg_osym >= target_osym

        print(f"Questions Generated: {len(questions)}/10")
        print(f"Validation Passed: {metrics_summary['validation_passed']}/10")
        print(f"\nKEY METRICS:")
        print(f"  OSYM Compliance: {avg_osym:.2f}")
        print(f"    - Baseline:    0.49")
        print(f"    - Improvement: {improvement:+.1f}%")
        print(
            f"    - Target:      0.65 {'[REACHED]' if target_reached else '[NOT REACHED]'}"
        )
        print(f"\n  Overall Quality: {avg_quality:.2f}")
        print(f"  Readability:     {avg_readability:.2f}")
        print(f"  Avg Length:      {avg_length:.0f} chars")
        print(f"  Avg Deviation:   {avg_deviation:.1%}")

        # Distribution analysis
        print(f"\nDISTRIBUTION:")
        perfect_scores = sum(1 for s in metrics_summary["osym_compliance"] if s >= 0.80)
        good_scores = sum(
            1 for s in metrics_summary["osym_compliance"] if 0.60 <= s < 0.80
        )
        low_scores = sum(1 for s in metrics_summary["osym_compliance"] if s < 0.60)

        print(f"  Perfect (>=0.80): {perfect_scores}/10 ({perfect_scores*10}%)")
        print(f"  Good (0.60-0.79): {good_scores}/10 ({good_scores*10}%)")
        print(f"  Low (<0.60):      {low_scores}/10 ({low_scores*10}%)")

        # Individual scores
        print(f"\nINDIVIDUAL OSYM COMPLIANCE SCORES:")
        for i, (score, length, target) in enumerate(
            zip(
                metrics_summary["osym_compliance"],
                metrics_summary["stem_length"],
                metrics_summary["target_length"],
            ),
            1,
        ):
            deviation = abs(length - target) / target
            status = (
                "[PERFECT]" if score >= 0.80 else "[GOOD]" if score >= 0.60 else "[LOW]"
            )
            print(
                f"  Q{i}: {score:.2f} {status} (length: {length}/{target}, deviation: {deviation:.1%})"
            )

        # Success criteria
        print(f"\n" + "=" * 80)
        print("SUCCESS CRITERIA")
        print("=" * 80 + "\n")

        criteria_met = []
        criteria_failed = []

        # Criterion 1: Average OSYM compliance >= 0.65
        if avg_osym >= 0.65:
            criteria_met.append(f"[OK] Average OSYM >= 0.65 ({avg_osym:.2f})")
        else:
            criteria_failed.append(f"[FAIL] Average OSYM >= 0.65 (got {avg_osym:.2f})")

        # Criterion 2: At least 5 questions >= 0.80
        if perfect_scores >= 5:
            criteria_met.append(
                f"[OK] At least 5 questions >= 0.80 (got {perfect_scores})"
            )
        else:
            criteria_failed.append(
                f"[FAIL] At least 5 questions >= 0.80 (got {perfect_scores})"
            )

        # Criterion 3: Average length deviation < 30%
        if avg_deviation < 0.3:
            criteria_met.append(f"[OK] Average deviation < 30% ({avg_deviation:.1%})")
        else:
            criteria_failed.append(
                f"[FAIL] Average deviation < 30% (got {avg_deviation:.1%})"
            )

        # Criterion 4: Improvement over baseline
        if improvement > 0:
            criteria_met.append(f"[OK] Improvement over baseline ({improvement:+.1f}%)")
        else:
            criteria_failed.append(
                f"[FAIL] No improvement over baseline ({improvement:+.1f}%)"
            )

        for criterion in criteria_met:
            print(criterion)
        for criterion in criteria_failed:
            print(criterion)

        # Overall verdict
        print(f"\n" + "=" * 80)
        if len(criteria_failed) == 0:
            print("VERDICT: [SUCCESS] Option A works as expected!")
            print("  Database-average length approach is effective.")
            print("  Ready to move to subject-specific prompts.")
        elif avg_osym > baseline_osym:
            print("VERDICT: [PARTIAL SUCCESS] Option A shows improvement.")
            print(f"  Improvement: {improvement:+.1f}%")
            print("  Recommendation: Continue with subject-specific optimization.")
        else:
            print("VERDICT: [NEEDS WORK] Option A did not improve results.")
            print("  Recommendation: Investigate prompt or examples quality.")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "option_a_database_average",
            "baseline_osym_compliance": baseline_osym,
            "target_osym_compliance": target_osym,
            "summary": {
                "total_generated": len(questions),
                "validation_passed": metrics_summary["validation_passed"],
                "avg_osym_compliance": avg_osym,
                "improvement_over_baseline": improvement,
                "target_reached": target_reached,
                "avg_quality": avg_quality,
                "avg_readability": avg_readability,
                "avg_stem_length": avg_length,
                "avg_length_deviation": avg_deviation,
                "perfect_scores": perfect_scores,
                "good_scores": good_scores,
                "low_scores": low_scores,
            },
            "criteria_met": criteria_met,
            "criteria_failed": criteria_failed,
            "questions": questions,
            "metrics_by_question": metrics_summary,
        }

        output_file = f"test_option_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    asyncio.run(test_option_a())
