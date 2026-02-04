"""
Production Monitoring Demo - Enhanced Templates with Wave 2B Tracking

This script demonstrates how to use the production quality monitoring system
with enhanced question generation templates.

Usage:
    cd backend && py demo_production_monitoring.py

What it does:
1. Generates 5 Math + 5 Turkish questions using enhanced templates
2. Automatically logs each with Wave 2B evaluation
3. Shows real-time quality metrics
4. Generates a production report

Expected output:
- 10 questions generated
- Wave 2B scores displayed
- Approval decisions shown
- Summary report generated
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator
from services.production_quality_monitor import get_monitor


async def demo_production_workflow():
    """
    Demonstrate production question generation with monitoring
    """

    print("\n" + "=" * 70)
    print("PRODUCTION MONITORING DEMO - Enhanced Templates with Wave 2B")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[ERROR] ANTHROPIC_API_KEY not found in .env")
        return

    print(f"\n[OK] API Key loaded: {api_key[:10]}...")

    # Initialize components
    print("\n[1/5] Initializing components...")
    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)
    monitor = get_monitor()
    print("[OK] Generator and monitor ready")

    # Test configuration
    test_config = {
        "Matematik": ["Türev", "İntegral", "Limit", "Fonksiyonlar", "Geometri"],
        "Türkçe": [
            "Fiilimsiler",
            "Cümle Bilgisi",
            "Paragraf",
            "Sözcük Bilgisi",
            "Anlam Bilgisi",
        ],
    }

    # Generate and monitor Math questions
    print("\n[2/5] Generating Mathematics questions with monitoring...")
    print("-" * 70)

    for i, topic in enumerate(test_config["Matematik"], 1):
        try:
            print(f"\n  [{i}/5] Generating {topic}...")

            # Generate question
            question = await generator.generate_with_few_shot(
                subject="Matematik", topic=topic, difficulty="orta", exam_type="TYT"
            )

            print(f"  [OK] Generated: {len(question.get('stem', ''))} chars")

            # Log with automatic Wave 2B evaluation
            evaluation = await monitor.log_question(
                question=question,
                subject="Matematik",
                topic=topic,
                question_id=f"demo-math-{i}",
                enhanced=True,
            )

            if evaluation:
                print(
                    f"  [OK] Wave 2B: {evaluation.overall_score:.3f} | {evaluation.decision} | Bloom L{evaluation.bloom_level}"
                )
            else:
                print(f"  [WARNING] Evaluation failed")

        except Exception as e:
            print(f"  [ERROR] Error: {str(e)}")

    # Generate and monitor Turkish questions
    print("\n[3/5] Generating Turkish questions with monitoring...")
    print("-" * 70)

    for i, topic in enumerate(test_config["Türkçe"], 1):
        try:
            print(f"\n  [{i}/5] Generating {topic}...")

            # Generate question
            question = await generator.generate_with_few_shot(
                subject="Türkçe", topic=topic, difficulty="orta", exam_type="TYT"
            )

            print(f"  [OK] Generated: {len(question.get('stem', ''))} chars")

            # Log with automatic Wave 2B evaluation
            evaluation = await monitor.log_question(
                question=question,
                subject="Türkçe",
                topic=topic,
                question_id=f"demo-turkish-{i}",
                enhanced=True,
            )

            if evaluation:
                print(
                    f"  [OK] Wave 2B: {evaluation.overall_score:.3f} | {evaluation.decision} | Bloom L{evaluation.bloom_level}"
                )
            else:
                print(f"  [WARNING] Evaluation failed")

        except Exception as e:
            print(f"  [ERROR] Error: {str(e)}")

    # Show statistics
    print("\n[4/5] Production Statistics")
    print("=" * 70)

    stats = monitor.get_stats_summary()

    if stats.get("total_questions", 0) > 0:
        print(f"\nTotal Questions Generated: {stats['total_questions']}")
        print(f"Average Wave 2B Score: {stats['average_score']:.3f}")
        print(f"Approval Rate: {stats['approval_rate']:.1f}%")
        print(f"Subjects: {', '.join(stats['subjects'])}")
        print(f"Last Question: {stats['last_question']}")

        # Show recent questions
        print("\nRecent Questions:")
        for log in monitor.logs[-10:]:
            status_emoji = (
                "[APPROVE]"
                if log.decision == "APPROVE"
                else "[REVIEW]"
                if log.decision == "REVIEW"
                else "[REJECT]"
            )
            print(
                f"  {status_emoji} {log.subject:10} | {log.topic:20} | Score: {log.wave2b_score:.3f} | Bloom: L{log.bloom_level}"
            )

    else:
        print("\n[WARNING] No questions logged")

    # Generate report
    print("\n[5/5] Generating Production Report...")
    print("-" * 70)

    report = await monitor.generate_report()

    # Save report
    report_file = "demo_production_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[OK] Report saved: {report_file}")

    # Print summary from report
    print("\n" + "=" * 70)
    print("DEMO COMPLETE - Production Monitoring Active!")
    print("=" * 70)

    if stats.get("total_questions", 0) > 0:
        print(f"\nKey Metrics:")
        print(f"  - Generated: {stats['total_questions']} questions")
        print(f"  - Quality: {stats['average_score']:.3f} average")
        print(f"  - Approval: {stats['approval_rate']:.1f}%")
        print(f"  - Report: {report_file}")

    print("\nNext Steps:")
    print("  1. Review the report: cat demo_production_report.md")
    print(
        "  2. Check monitoring API: curl http://localhost:8000/api/v1/monitoring/stats"
    )
    print(
        "  3. View recent questions: curl http://localhost:8000/api/v1/monitoring/recent"
    )
    print("\n")


async def quick_monitoring_check():
    """
    Quick check of current monitoring status
    """
    print("\n" + "=" * 70)
    print("QUICK MONITORING CHECK")
    print("=" * 70)

    monitor = get_monitor()
    stats = monitor.get_stats_summary()

    if stats.get("total_questions", 0) == 0:
        print("\n[INFO] No questions logged yet")
        print("Run: py demo_production_monitoring.py")
        return

    print(f"\nProduction Status:")
    print(f"  Total Questions: {stats['total_questions']}")
    print(f"  Average Quality: {stats['average_score']:.3f}")
    print(f"  Approval Rate: {stats['approval_rate']:.1f}%")
    print(f"  Last Update: {stats['last_question']}")

    # Quality assessment
    if stats["average_score"] >= 0.85:
        print("\n[OK] Quality: EXCELLENT (>= 0.85)")
    elif stats["average_score"] >= 0.80:
        print("\n[OK] Quality: GOOD (>= 0.80)")
    elif stats["average_score"] >= 0.75:
        print("\n[WARNING] Quality: ACCEPTABLE (>= 0.75)")
    else:
        print("\n[ERROR] Quality: NEEDS IMPROVEMENT (< 0.75)")

    # Approval assessment
    if stats["approval_rate"] >= 85:
        print("[OK] Approval: EXCELLENT (>= 85%)")
    elif stats["approval_rate"] >= 70:
        print("[OK] Approval: GOOD (>= 70%)")
    elif stats["approval_rate"] >= 50:
        print("[WARNING] Approval: ACCEPTABLE (>= 50%)")
    else:
        print("[ERROR] Approval: NEEDS IMPROVEMENT (< 50%)")

    print("\nFor detailed report, run:")
    print("  curl http://localhost:8000/api/v1/monitoring/report")
    print("\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Quick check mode
        asyncio.run(quick_monitoring_check())
    else:
        # Full demo
        asyncio.run(demo_production_workflow())
