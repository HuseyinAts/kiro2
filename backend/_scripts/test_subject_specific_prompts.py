"""
Test Subject-Specific Prompt Templates
Focus on Chemistry (weakest in Option A) and Mathematics

Expected Improvement:
- Chemistry: 0.45-0.63 → 0.75+ (better length adherence to 202 chars)
- Mathematics: 0.76-1.00 → maintain 0.90+ (already good)
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.hybrid_question_generator import HybridQuestionGenerator


async def test_subject_specific():
    """
    Test subject-specific prompt templates

    Baseline (Option A):
    - Chemistry avg: 0.52 ÖSYM compliance (struggled with 202 char target)
    - Mathematics avg: 0.92 ÖSYM compliance (strong with 388 char target)

    Target (Subject-Specific):
    - Chemistry: 0.75+ ÖSYM compliance
    - Mathematics: 0.90+ ÖSYM compliance (maintain)
    """

    print("\n" + "=" * 80)
    print("TEST: SUBJECT-SPECIFIC PROMPT TEMPLATES")
    print("=" * 80 + "\n")
    print("FOCUS: Chemistry (202 chars) and Mathematics (388 chars)")
    print("GOAL: Improve Chemistry length adherence\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test cases - Focus on Chemistry and Mathematics
    test_cases = [
        # Chemistry (most challenging - 202 chars target)
        {
            "subject": "Kimya",
            "topic": "Mol Kavrami",
            "difficulty": "kolay",
            "expected_length": 202,
        },
        {
            "subject": "Kimya",
            "topic": "Asit-Baz Tepkimeleri",
            "difficulty": "orta",
            "expected_length": 202,
        },
        {
            "subject": "Kimya",
            "topic": "Kimyasal Denge",
            "difficulty": "orta",
            "expected_length": 202,
        },
        {
            "subject": "Kimya",
            "topic": "Periyodik Sistem",
            "difficulty": "kolay",
            "expected_length": 202,
        },
        {
            "subject": "Kimya",
            "topic": "Stokiyometri",
            "difficulty": "orta",
            "expected_length": 202,
        },
        # Mathematics (already strong - verify maintained)
        {
            "subject": "Matematik",
            "topic": "Turev Alma Kurallari",
            "difficulty": "orta",
            "expected_length": 388,
        },
        {
            "subject": "Matematik",
            "topic": "Limit",
            "difficulty": "kolay",
            "expected_length": 388,
        },
        {
            "subject": "Matematik",
            "topic": "Fonksiyonlar",
            "difficulty": "zor",
            "expected_length": 388,
        },
    ]

    questions = []
    metrics_by_subject = {
        "Kimya": {"osym_compliance": [], "stem_length": [], "length_deviation": []},
        "Matematik": {"osym_compliance": [], "stem_length": [], "length_deviation": []},
    }

    for i, test_case in enumerate(test_cases, 1):
        subject = test_case["subject"]
        print(f"\n[{i}/{len(test_cases)}] Generating: {subject} - {test_case['topic']}")
        print("-" * 80)

        try:
            question = await generator.generate_osym_quality_question(
                subject=subject,
                topic=test_case["topic"],
                difficulty=test_case["difficulty"],
                exam_type="TYT",
                provider="claude",
                validate=True,
            )

            # Extract metrics
            osym_score = question.get("osym_compliance_score", 0)
            stem_length = len(question.get("stem", ""))
            target_length = test_case["expected_length"]
            length_deviation = abs(stem_length - target_length) / target_length

            # Store by subject
            metrics_by_subject[subject]["osym_compliance"].append(osym_score)
            metrics_by_subject[subject]["stem_length"].append(stem_length)
            metrics_by_subject[subject]["length_deviation"].append(length_deviation)

            # Print summary (avoid unicode errors)
            print(
                f"\nLENGTH: {stem_length} chars (target: {target_length}, deviation: {length_deviation:.1%})"
            )
            print(f"METRICS:")
            print(
                f"  OSYM Compliance: {osym_score:.2f} {'[OK]' if osym_score >= 0.80 else '[LOW]'}"
            )
            print(
                f"  Length Match: {'[EXCELLENT]' if length_deviation < 0.10 else '[GOOD]' if length_deviation < 0.20 else '[NEEDS WORK]'}"
            )

            questions.append({**question, "test_case": test_case})

            # Brief pause
            await asyncio.sleep(2)

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Analyze results by subject
    print("\n" + "=" * 80)
    print("SUBJECT-SPECIFIC RESULTS")
    print("=" * 80 + "\n")

    overall_results = {}

    for subject in ["Kimya", "Matematik"]:
        if not metrics_by_subject[subject]["osym_compliance"]:
            continue

        avg_osym = sum(metrics_by_subject[subject]["osym_compliance"]) / len(
            metrics_by_subject[subject]["osym_compliance"]
        )
        avg_length = sum(metrics_by_subject[subject]["stem_length"]) / len(
            metrics_by_subject[subject]["stem_length"]
        )
        avg_deviation = sum(metrics_by_subject[subject]["length_deviation"]) / len(
            metrics_by_subject[subject]["length_deviation"]
        )

        perfect_count = sum(
            1 for s in metrics_by_subject[subject]["osym_compliance"] if s >= 0.80
        )
        total_count = len(metrics_by_subject[subject]["osym_compliance"])

        overall_results[subject] = {
            "avg_osym_compliance": avg_osym,
            "avg_stem_length": avg_length,
            "avg_length_deviation": avg_deviation,
            "perfect_count": perfect_count,
            "total_count": total_count,
            "perfect_rate": perfect_count / total_count if total_count > 0 else 0,
        }

        # Get baseline (from Option A)
        baseline_osym = {
            "Kimya": 0.52,  # Average from Option A (Q1: 0.63, Q2: 0.45, Q10: 1.00)
            "Matematik": 0.92,  # Average from Option A (Q3: 0.76, Q4: 1.00, Q8: 1.00)
        }

        baseline = baseline_osym.get(subject, 0.50)
        improvement = ((avg_osym - baseline) / baseline) * 100 if baseline > 0 else 0

        print(f"### {subject}")
        print(f"Questions: {total_count}")
        print(f"OSYM Compliance: {avg_osym:.2f}")
        print(f"  - Baseline (Option A): {baseline:.2f}")
        print(f"  - Improvement: {improvement:+.1f}%")
        print(
            f"  - Status: {'[IMPROVED]' if improvement > 0 else '[MAINTAINED]' if improvement > -5 else '[REGRESSED]'}"
        )
        print(f"\nLength Performance:")
        print(f"  - Avg Length: {avg_length:.0f} chars")
        print(f"  - Avg Deviation: {avg_deviation:.1%}")
        print(
            f"  - Perfect Scores (>=0.80): {perfect_count}/{total_count} ({perfect_rate:.0%})"
        )
        print()

    # Overall verdict
    print("=" * 80)
    print("OVERALL VERDICT")
    print("=" * 80 + "\n")

    if "Kimya" in overall_results:
        chem_improved = overall_results["Kimya"]["avg_osym_compliance"] >= 0.75
        chem_status = "[SUCCESS]" if chem_improved else "[NEEDS MORE WORK]"
        print(f"Chemistry: {chem_status}")
        print(f"  - Target: 0.75+")
        print(f"  - Actual: {overall_results['Kimya']['avg_osym_compliance']:.2f}")
        print(
            f"  - Length adherence: {overall_results['Kimya']['avg_length_deviation']:.1%} deviation"
        )
        print()

    if "Matematik" in overall_results:
        math_maintained = overall_results["Matematik"]["avg_osym_compliance"] >= 0.90
        math_status = "[SUCCESS]" if math_maintained else "[NEEDS WORK]"
        print(f"Mathematics: {math_status}")
        print(f"  - Target: 0.90+ (maintain)")
        print(f"  - Actual: {overall_results['Matematik']['avg_osym_compliance']:.2f}")
        print()

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "subject_specific_prompts",
        "summary": overall_results,
        "questions": questions,
    }

    output_file = (
        f"test_subject_specific_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80 + "\n")

    return questions


if __name__ == "__main__":
    asyncio.run(test_subject_specific())
