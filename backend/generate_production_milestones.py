"""
Production Milestone Generator - Generate questions to reach all milestones

This script generates questions in batches to reach milestones:
- 25 questions (Week 1 target)
- 50 questions (Mid-term checkpoint)
- 75 questions (Extended monitoring)
- 100 questions (Month 1 complete)

Usage:
    cd backend && py generate_production_milestones.py --target 100

What it does:
1. Checks current question count
2. Generates questions to reach target milestone
3. Logs all with Wave 2B evaluation
4. Triggers automatic milestone reports
5. Creates summary analysis
"""

import asyncio
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator
from services.production_quality_monitor import get_monitor


async def generate_to_milestone(target: int = 100):
    """
    Generate questions to reach target milestone

    Args:
        target: Target number of questions (25, 50, 75, or 100)
    """

    print("\n" + "=" * 70)
    print(f"PRODUCTION MILESTONE GENERATOR - Target: {target} questions")
    print("=" * 70)

    # Initialize
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[ERROR] ANTHROPIC_API_KEY not found in .env")
        return

    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)
    monitor = get_monitor()

    # Check current count
    current_count = len(monitor.logs)
    print(f"\n[INFO] Current questions: {current_count}")
    print(f"[INFO] Target: {target}")
    print(f"[INFO] Need to generate: {target - current_count}")

    if current_count >= target:
        print(f"\n[OK] Already at or past target ({current_count} >= {target})")
        print(f"[INFO] Generating final report...")
        report = await monitor.generate_report()
        report_file = f"production_report_{current_count}_questions.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Report saved: {report_file}")
        return

    # Topic rotation for variety
    math_topics = [
        "Türev",
        "İntegral",
        "Limit",
        "Fonksiyonlar",
        "Geometri",
        "Trigonometri",
        "Logaritma",
        "Üslü Sayılar",
        "Diziler",
        "Olasılık",
    ]
    turkish_topics = [
        "Fiilimsiler",
        "Cümle Bilgisi",
        "Anlam Bilgisi",
        "Paragraf",
        "Sözcük Bilgisi",
        "Ses Bilgisi",
        "Anlatım Bozuklukları",
        "Yazım Kuralları",
        "Noktalama",
        "Cümle Türleri",
    ]

    questions_needed = target - current_count
    batch_size = 5
    batches = (questions_needed + batch_size - 1) // batch_size

    print(f"\n[STRATEGY] Will generate in {batches} batches of ~{batch_size} questions")
    print(f"[INFO] Subject split: ~50% Math, ~50% Turkish\n")

    # Generate in batches
    for batch_num in range(batches):
        current = len(monitor.logs)
        remaining = target - current

        if remaining <= 0:
            break

        batch_actual_size = min(batch_size, remaining)
        math_count = batch_actual_size // 2 + (batch_actual_size % 2)
        turkish_count = batch_actual_size - math_count

        print(f"{'='*70}")
        print(
            f"Batch {batch_num + 1}/{batches} - Generating {batch_actual_size} questions"
        )
        print(f"  Math: {math_count} | Turkish: {turkish_count}")
        print(f"  Progress: {current}/{target} ({current/target*100:.1f}%)")
        print(f"{'='*70}\n")

        # Generate Math questions
        for i in range(math_count):
            try:
                topic = math_topics[i % len(math_topics)]
                print(f"  [Math {i+1}/{math_count}] Generating {topic}...")

                question = await generator.generate_with_few_shot(
                    subject="Matematik", topic=topic, difficulty="orta", exam_type="TYT"
                )

                evaluation = await monitor.log_question(
                    question=question,
                    subject="Matematik",
                    topic=topic,
                    question_id=f"prod-math-{len(monitor.logs)+1}",
                    enhanced=True,
                )

                if evaluation:
                    print(
                        f"    -> Score: {evaluation.overall_score:.3f} | {evaluation.decision} | Length: {len(question.get('stem',''))} chars"
                    )
                else:
                    print(f"    -> [WARNING] Evaluation failed")

            except Exception as e:
                print(f"    -> [ERROR] {str(e)[:100]}")

        # Generate Turkish questions
        for i in range(turkish_count):
            try:
                topic = turkish_topics[i % len(turkish_topics)]
                print(f"  [Turkish {i+1}/{turkish_count}] Generating {topic}...")

                question = await generator.generate_with_few_shot(
                    subject="Türkçe", topic=topic, difficulty="orta", exam_type="TYT"
                )

                evaluation = await monitor.log_question(
                    question=question,
                    subject="Türkçe",
                    topic=topic,
                    question_id=f"prod-turkish-{len(monitor.logs)+1}",
                    enhanced=True,
                )

                if evaluation:
                    print(
                        f"    -> Score: {evaluation.overall_score:.3f} | {evaluation.decision} | Length: {len(question.get('stem',''))} chars"
                    )
                else:
                    print(f"    -> [WARNING] Evaluation failed")

            except Exception as e:
                print(f"    -> [ERROR] {str(e)[:100]}")

        # Check for milestone
        current = len(monitor.logs)
        if current in [25, 50, 75, 100]:
            print(f"\n{'='*70}")
            print(f"[MILESTONE] {current} QUESTIONS REACHED!")
            print(f"{'='*70}\n")

        print(f"\n[Progress] {current}/{target} questions generated\n")

    # Final summary
    final_count = len(monitor.logs)
    print(f"\n{'='*70}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"\nFinal Count: {final_count} questions")
    print(f"Target: {target}")
    print(f"Status: {'TARGET REACHED' if final_count >= target else 'INCOMPLETE'}")

    # Generate final report
    print(f"\nGenerating final report...")
    stats = monitor.get_stats_summary()

    print(f"\n{'='*70}")
    print(f"FINAL STATISTICS")
    print(f"{'='*70}")
    print(f"Total Questions: {stats['total_questions']}")
    print(f"Average Score: {stats['average_score']:.3f}")
    print(f"Approval Rate: {stats['approval_rate']:.1f}%")
    print(f"Subjects: {', '.join(stats['subjects'])}")

    report = await monitor.generate_report()
    report_file = f"production_report_{final_count}_questions_final.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[OK] Final report saved: {report_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate production questions to milestone"
    )
    parser.add_argument(
        "--target", type=int, default=100, help="Target milestone (25, 50, 75, or 100)"
    )
    args = parser.parse_args()

    asyncio.run(generate_to_milestone(args.target))
