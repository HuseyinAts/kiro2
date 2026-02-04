"""
Test 20 Questions with Retry Logic
Goal: Improve from 0.83 → 0.90 ÖSYM compliance

Focus: Chemistry retry logic + balanced subject distribution
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.hybrid_question_generator import HybridQuestionGenerator


async def test_20_questions_with_retry():
    """
    Test 20 questions with retry logic enabled

    Baseline (Option A without retry): 0.83 ÖSYM compliance
    Target (Option A + retry): 0.90 ÖSYM compliance (+8% improvement)
    """

    print("\n" + "=" * 80)
    print("TEST: 20 QUESTIONS WITH RETRY LOGIC")
    print("=" * 80 + "\n")
    print("BASELINE: 0.83 ÖSYM compliance (Option A)")
    print("TARGET:   0.90 ÖSYM compliance (Option A + Retry)")
    print("FOCUS:    Chemistry retry logic\n")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test cases - 20 questions, balanced across subjects
    # Chemistry: 6 questions (30%) - needs most attention
    # Mathematics: 5 questions (25%)
    # Physics: 4 questions (20%)
    # Biology: 3 questions (15%)
    # Turkish: 2 questions (10%)
    test_cases = [
        # Chemistry (6 questions - priority due to length issues)
        {"subject": "Kimya", "topic": "Mol Kavramı", "difficulty": "kolay"},
        {"subject": "Kimya", "topic": "Asit-Baz Tepkimeleri", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Kimyasal Denge", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Periyodik Sistem", "difficulty": "kolay"},
        {"subject": "Kimya", "topic": "Stokiyometri", "difficulty": "orta"},
        {"subject": "Kimya", "topic": "Elektrokimya", "difficulty": "zor"},
        # Mathematics (5 questions - already strong)
        {"subject": "Matematik", "topic": "Türev Alma Kuralları", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Limit", "difficulty": "kolay"},
        {"subject": "Matematik", "topic": "Fonksiyonlar", "difficulty": "zor"},
        {"subject": "Matematik", "topic": "İntegral", "difficulty": "orta"},
        {"subject": "Matematik", "topic": "Olasılık", "difficulty": "kolay"},
        # Physics (4 questions)
        {"subject": "Fizik", "topic": "Newton Kanunları", "difficulty": "orta"},
        {"subject": "Fizik", "topic": "Hareket", "difficulty": "kolay"},
        {"subject": "Fizik", "topic": "Kuvvet ve Hareket", "difficulty": "zor"},
        {"subject": "Fizik", "topic": "Elektrik", "difficulty": "orta"},
        # Biology (3 questions)
        {"subject": "Biyoloji", "topic": "Fotosentez", "difficulty": "orta"},
        {"subject": "Biyoloji", "topic": "Genetik", "difficulty": "zor"},
        {"subject": "Biyoloji", "topic": "Hücre Bölünmesi", "difficulty": "kolay"},
        # Turkish (2 questions - longest questions)
        {"subject": "Türkçe", "topic": "Okuduğunu Anlama", "difficulty": "orta"},
        {"subject": "Türkçe", "topic": "Dil Bilgisi", "difficulty": "kolay"},
    ]

    questions = []
    metrics_by_subject = {}
    retry_stats = {
        "total_retries": 0,
        "chemistry_retries": 0,
        "successful_after_retry": 0,
    }

    for i, test_case in enumerate(test_cases, 1):
        subject = test_case["subject"]
        print(
            f"\n[{i}/20] Generating: {subject} - {test_case['topic']} ({test_case['difficulty']})"
        )
        print("-" * 80)

        # Initialize subject metrics if needed
        if subject not in metrics_by_subject:
            metrics_by_subject[subject] = {
                "osym_compliance": [],
                "stem_length": [],
                "length_deviation": [],
                "perfect_count": 0,
                "total_count": 0,
            }

        try:
            # Generate with retry enabled
            question = await generator.generate_osym_quality_question(
                subject=subject,
                topic=test_case["topic"],
                difficulty=test_case["difficulty"],
                exam_type="TYT",
                provider="claude",
                validate=True,
                enable_retry=True,  # RETRY ENABLED!
            )

            # Extract metrics
            osym_score = question.get("osym_compliance_score", 0)
            stem_length = len(question.get("stem", ""))

            # Get target length
            from services.subject_specific_prompts import SUBJECT_TARGET_LENGTHS

            target_length = SUBJECT_TARGET_LENGTHS.get(subject, 400)
            length_deviation = abs(stem_length - target_length) / target_length

            # Store metrics
            metrics_by_subject[subject]["osym_compliance"].append(osym_score)
            metrics_by_subject[subject]["stem_length"].append(stem_length)
            metrics_by_subject[subject]["length_deviation"].append(length_deviation)
            metrics_by_subject[subject]["total_count"] += 1

            if osym_score >= 0.80:
                metrics_by_subject[subject]["perfect_count"] += 1

            # Print summary
            status = "[OK]" if osym_score >= 0.80 else "[LOW]"
            print(f"\nRESULT: {status}")
            print(f"  Length: {stem_length} chars (target: {target_length})")
            print(f"  Deviation: {length_deviation:.1%}")
            print(f"  OSYM Compliance: {osym_score:.2f}")

            questions.append(
                {**question, "test_case": test_case, "target_length": target_length}
            )

            # Brief pause
            await asyncio.sleep(2)

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Calculate overall statistics
    print("\n" + "=" * 80)
    print("RESULTS: 20-QUESTION TEST WITH RETRY LOGIC")
    print("=" * 80 + "\n")

    if questions:
        # Overall metrics
        all_osym = []
        all_lengths = []
        all_deviations = []

        for subject_metrics in metrics_by_subject.values():
            all_osym.extend(subject_metrics["osym_compliance"])
            all_lengths.extend(subject_metrics["stem_length"])
            all_deviations.extend(subject_metrics["length_deviation"])

        avg_osym = sum(all_osym) / len(all_osym) if all_osym else 0
        avg_length = sum(all_lengths) / len(all_lengths) if all_lengths else 0
        avg_deviation = (
            sum(all_deviations) / len(all_deviations) if all_deviations else 0
        )

        perfect_count = sum(1 for s in all_osym if s >= 0.80)
        good_count = sum(1 for s in all_osym if 0.60 <= s < 0.80)
        low_count = sum(1 for s in all_osym if s < 0.60)

        # Show improvement
        baseline_osym = 0.83
        target_osym = 0.90
        improvement = ((avg_osym - baseline_osym) / baseline_osym) * 100
        target_reached = avg_osym >= target_osym

        print(f"Questions Generated: {len(questions)}/20")
        print(f"\nOVERALL METRICS:")
        print(f"  OSYM Compliance: {avg_osym:.2f}")
        print(f"    - Baseline:    0.83 (Option A)")
        print(f"    - Improvement: {improvement:+.1f}%")
        print(
            f"    - Target:      0.90 {'[REACHED!]' if target_reached else '[NOT REACHED]'}"
        )
        print(f"\n  Perfect (>=0.80): {perfect_count}/20 ({perfect_count*5}%)")
        print(f"  Good (0.60-0.79): {good_count}/20 ({good_count*5}%)")
        print(f"  Low (<0.60):      {low_count}/20 ({low_count*5}%)")
        print(f"\n  Avg Length:      {avg_length:.0f} chars")
        print(f"  Avg Deviation:   {avg_deviation:.1%}")

        # Subject-by-subject analysis
        print(f"\n" + "=" * 80)
        print("SUBJECT-BY-SUBJECT ANALYSIS")
        print("=" * 80 + "\n")

        for subject, metrics in sorted(metrics_by_subject.items()):
            if not metrics["osym_compliance"]:
                continue

            subj_avg_osym = sum(metrics["osym_compliance"]) / len(
                metrics["osym_compliance"]
            )
            subj_avg_length = sum(metrics["stem_length"]) / len(metrics["stem_length"])
            subj_avg_deviation = sum(metrics["length_deviation"]) / len(
                metrics["length_deviation"]
            )

            from services.subject_specific_prompts import SUBJECT_TARGET_LENGTHS

            target = SUBJECT_TARGET_LENGTHS.get(subject, 400)

            print(f"### {subject}")
            print(f"Questions: {metrics['total_count']}")
            print(f"OSYM Compliance: {subj_avg_osym:.2f}")
            print(
                f"Perfect Scores: {metrics['perfect_count']}/{metrics['total_count']}"
            )
            print(f"Avg Length: {subj_avg_length:.0f} chars (target: {target})")
            print(f"Avg Deviation: {subj_avg_deviation:.1%}")
            print()

        # Success criteria
        print("=" * 80)
        print("SUCCESS CRITERIA")
        print("=" * 80 + "\n")

        criteria = []

        # Criterion 1: Average OSYM >= 0.90
        if avg_osym >= 0.90:
            criteria.append(f"[OK] Average OSYM >= 0.90 ({avg_osym:.2f})")
        else:
            criteria.append(f"[FAIL] Average OSYM >= 0.90 (got {avg_osym:.2f})")

        # Criterion 2: At least 15/20 questions >= 0.80
        if perfect_count >= 15:
            criteria.append(
                f"[OK] At least 15/20 questions >= 0.80 (got {perfect_count})"
            )
        else:
            criteria.append(
                f"[PARTIAL] At least 15/20 questions >= 0.80 (got {perfect_count})"
            )

        # Criterion 3: Chemistry improvement
        if "Kimya" in metrics_by_subject:
            chem_avg = sum(metrics_by_subject["Kimya"]["osym_compliance"]) / len(
                metrics_by_subject["Kimya"]["osym_compliance"]
            )
            baseline_chem = 0.69  # From Option A test
            if chem_avg >= 0.80:
                criteria.append(
                    f"[OK] Chemistry >= 0.80 ({chem_avg:.2f}, was {baseline_chem:.2f})"
                )
            elif chem_avg > baseline_chem:
                criteria.append(
                    f"[IMPROVED] Chemistry improved from {baseline_chem:.2f} to {chem_avg:.2f}"
                )
            else:
                criteria.append(f"[FAIL] Chemistry not improved ({chem_avg:.2f})")

        # Criterion 4: Improvement over baseline
        if improvement > 0:
            criteria.append(f"[OK] Improvement over baseline ({improvement:+.1f}%)")
        else:
            criteria.append(
                f"[FAIL] No improvement over baseline ({improvement:+.1f}%)"
            )

        for criterion in criteria:
            print(criterion)

        # Overall verdict
        print(f"\n" + "=" * 80)
        success_count = sum(1 for c in criteria if c.startswith("[OK]"))
        if avg_osym >= 0.90:
            print("VERDICT: [SUCCESS] Target reached! Retry logic works!")
            print(f"  OSYM compliance: {avg_osym:.2f} >= 0.90")
            print("  System is ready for 100-question production run.")
        elif avg_osym >= 0.85:
            print("VERDICT: [NEAR SUCCESS] Very close to target.")
            print(f"  OSYM compliance: {avg_osym:.2f} (target: 0.90)")
            print("  Recommendation: Minor tweaks, then production ready.")
        elif improvement > 0:
            print("VERDICT: [IMPROVED] Retry logic shows positive impact.")
            print(f"  Improvement: {improvement:+.1f}%")
            print(f"  Current: {avg_osym:.2f} (target: 0.90)")
            print("  Recommendation: Additional optimization needed.")
        else:
            print("VERDICT: [NEEDS WORK] No improvement observed.")
            print("  Recommendation: Review retry logic and Chemistry prompts.")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "20_questions_with_retry",
            "baseline_osym_compliance": baseline_osym,
            "target_osym_compliance": target_osym,
            "summary": {
                "total_generated": len(questions),
                "avg_osym_compliance": avg_osym,
                "improvement_over_baseline": improvement,
                "target_reached": target_reached,
                "perfect_count": perfect_count,
                "good_count": good_count,
                "low_count": low_count,
                "avg_length": avg_length,
                "avg_deviation": avg_deviation,
            },
            "by_subject": {
                subject: {
                    "total_questions": metrics["total_count"],
                    "avg_osym_compliance": sum(metrics["osym_compliance"])
                    / len(metrics["osym_compliance"]),
                    "perfect_count": metrics["perfect_count"],
                    "avg_length": sum(metrics["stem_length"])
                    / len(metrics["stem_length"]),
                    "avg_deviation": sum(metrics["length_deviation"])
                    / len(metrics["length_deviation"]),
                }
                for subject, metrics in metrics_by_subject.items()
                if metrics["osym_compliance"]
            },
            "success_criteria": criteria,
            "questions": questions,
        }

        output_file = (
            f"test_20_questions_retry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    asyncio.run(test_20_questions_with_retry())
