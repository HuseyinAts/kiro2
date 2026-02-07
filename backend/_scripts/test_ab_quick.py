"""
Quick A/B Test - Generate 3 Math + 3 Turkish questions for rapid validation
This is a quick version of the full A/B test for immediate feedback
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator
from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator
from database.connection import async_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def quick_test():
    """Quick A/B test with 3+3 questions"""

    print("\n" + "=" * 70)
    print("QUICK A/B TEST - Enhanced Templates Validation (3 Math + 3 Turkish)")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[REJECT] ERROR: ANTHROPIC_API_KEY not found in .env")
        return

    print(f"\n[OK] API Key loaded: {api_key[:10]}...")

    # Initialize generator
    print("\n[1/6] Initializing OSYMInspiredGenerator...")
    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)
    print("[OK] Generator ready")

    # Load ÖSYM references for Wave 2B
    print("\n[2/6] Loading ÖSYM reference questions...")
    async with AsyncSession(async_engine) as db:
        query = text(
            """
            SELECT metin, dogru_cevap, zorluk, konu
            FROM sorular
            WHERE dogru_cevap IS NOT NULL
            AND metin IS NOT NULL
            LIMIT 20
        """
        )
        result = await db.execute(query)
        rows = result.fetchall()
        osym_questions = [
            {
                "question_text": row[0],
                "correct_answer": row[1],
                "difficulty": row[2],
                "topic": row[3],
            }
            for row in rows
        ]
    print(f"[OK] Loaded {len(osym_questions)} ÖSYM references")

    # Initialize evaluator
    print("\n[3/6] Initializing Wave 2B evaluator...")
    evaluator = ComprehensiveQualityEvaluator(osym_reference_questions=osym_questions)
    print("[OK] Wave 2B evaluator ready")

    # Baseline scores (from database analysis)
    baseline = {
        "Matematik": {"score": 0.750, "approval": 0.20, "length": 180},
        "Türkçe": {"score": 0.727, "approval": 0.00, "length": 160},
    }

    results = {"Matematik": [], "Türkçe": []}

    # Generate and evaluate Math questions
    print("\n[4/6] Testing MATEMATIK questions (enhanced templates)...")
    print("-" * 70)

    for i, topic in enumerate(["Türev", "İntegral", "Limit"], 1):
        try:
            print(f"\n  [{i}/3] Generating {topic}...")

            question = await generator.generate_with_few_shot(
                subject="Matematik", topic=topic, difficulty="orta", exam_type="TYT"
            )

            length = len(question.get("stem", ""))
            print(f"  [OK] Generated: {length} chars")

            # Evaluate with Wave 2B
            evaluation = evaluator.evaluate(
                question={"question_text": question["stem"], "subject": "Matematik"},
                stage="standard",
            )

            print(
                f"  [OK] Wave 2B Score: {evaluation.overall_score:.3f} | Decision: {evaluation.decision} | Bloom: L{evaluation.bloom_level}"
            )

            results["Matematik"].append(
                {
                    "topic": topic,
                    "length": length,
                    "score": evaluation.overall_score,
                    "decision": evaluation.decision,
                    "bloom_level": evaluation.bloom_level,
                    "question_preview": question["stem"][:100] + "...",
                }
            )

        except Exception as e:
            print(f"  [ERROR] Error: {str(e)}")

    # Generate and evaluate Turkish questions
    print("\n[5/6] Testing TÜRKÇE questions (enhanced templates)...")
    print("-" * 70)

    for i, topic in enumerate(["Fiilimsiler", "Paragraf", "Sözcük Bilgisi"], 1):
        try:
            print(f"\n  [{i}/3] Generating {topic}...")

            question = await generator.generate_with_few_shot(
                subject="Türkçe", topic=topic, difficulty="orta", exam_type="TYT"
            )

            length = len(question.get("stem", ""))
            print(f"  [OK] Generated: {length} chars")

            # Evaluate with Wave 2B
            evaluation = evaluator.evaluate(
                question={"question_text": question["stem"], "subject": "Türkçe"},
                stage="standard",
            )

            print(
                f"  [OK] Wave 2B Score: {evaluation.overall_score:.3f} | Decision: {evaluation.decision} | Bloom: L{evaluation.bloom_level}"
            )

            results["Türkçe"].append(
                {
                    "topic": topic,
                    "length": length,
                    "score": evaluation.overall_score,
                    "decision": evaluation.decision,
                    "bloom_level": evaluation.bloom_level,
                    "question_preview": question["stem"][:100] + "...",
                }
            )

        except Exception as e:
            print(f"  [ERROR] Error: {str(e)}")

    # Summary
    print("\n[6/6] SUMMARY - Quick A/B Test Results")
    print("=" * 70)

    for subject in ["Matematik", "Türkçe"]:
        if not results[subject]:
            continue

        scores = [r["score"] for r in results[subject]]
        lengths = [r["length"] for r in results[subject]]
        approvals = sum(1 for r in results[subject] if r["decision"] == "APPROVE")

        avg_score = sum(scores) / len(scores)
        avg_length = sum(lengths) / len(lengths)
        approval_rate = approvals / len(results[subject])

        base = baseline[subject]

        print(f"\n{subject}:")
        print(
            f"  Baseline  -> Quality: {base['score']:.3f} | Approval: {base['approval']*100:.0f}% | Length: ~{base['length']} chars"
        )
        print(
            f"  Enhanced  -> Quality: {avg_score:.3f} | Approval: {approval_rate*100:.0f}% | Length: {avg_length:.0f} chars"
        )
        print(
            f"  Change    -> Quality: {avg_score - base['score']:+.3f} ({(avg_score - base['score'])/base['score']*100:+.1f}%)"
        )
        print(f"              Approval: {approval_rate - base['approval']:+.2f}")
        print(
            f"              Length: {avg_length - base['length']:+.0f} chars ({(avg_length - base['length'])/base['length']*100:+.1f}%)"
        )

        print(f"\n  Individual Results:")
        for r in results[subject]:
            status = (
                "[APPROVE]"
                if r["decision"] == "APPROVE"
                else "[REVIEW]"
                if r["decision"] == "REVIEW"
                else "[REJECT]"
            )
            print(
                f"    {status} {r['topic']:20} | Score: {r['score']:.3f} | Bloom: L{r['bloom_level']} | {r['length']:3d} chars"
            )

    print("\n" + "=" * 70)
    print("[APPROVE] QUICK TEST COMPLETE")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Review the results above")
    print("  2. If successful, run full test: py test_ab_enhanced_questions.py")
    print("  3. Full test will generate 10+10 questions for comprehensive analysis")
    print("\n")


if __name__ == "__main__":
    asyncio.run(quick_test())
