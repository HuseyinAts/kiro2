"""
Wave 2B Quality Evaluation for Phase 1 Table Questions

Evaluates the 5 generated table questions with Wave 2B quality system.
Target: 0.85+ quality score

Usage:
    cd backend && py evaluate_table_questions_wave2b.py
"""

import sys
import json
import asyncio
from pathlib import Path
import io
from datetime import datetime

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator


async def load_table_questions():
    """Load the 5 generated table questions"""
    json_file = "production_5_table_questions_20251107_115039.json"

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            questions = json.load(f)

        print(f"[OK] Loaded {len(questions)} table questions from {json_file}")
        return questions
    except FileNotFoundError:
        print(f"[ERROR] File not found: {json_file}")
        print("[INFO] Looking for individual question files...")

        # Try loading individual files
        questions = []
        for i in range(1, 6):
            files = [
                f"production_table_Q{i}_Math_Frequency.json",
                f"production_table_Q{i}_Math_Statistics.json",
                f"production_table_Q{i}_Turkish_Comparison.json",
                f"production_table_Q{i}_Physics_Experiment.json",
                f"production_table_Q{i}_Chemistry_Elements.json",
            ]

            for filename in files:
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        q = json.load(f)
                        questions.append(q)
                        print(f"  [OK] Loaded {filename}")
                except FileNotFoundError:
                    continue

        if questions:
            print(f"[OK] Loaded {len(questions)} questions from individual files")
            return questions
        else:
            print("[ERROR] No question files found")
            return []
    except Exception as e:
        print(f"[ERROR] Failed to load questions: {str(e)}")
        return []


async def evaluate_questions():
    """Evaluate table questions with Wave 2B"""

    print("\n" + "=" * 70)
    print("WAVE 2B QUALITY EVALUATION - PHASE 1 TABLE QUESTIONS")
    print("=" * 70 + "\n")

    # Load questions
    questions = await load_table_questions()

    if not questions:
        print("[ERROR] No questions to evaluate")
        return

    # Initialize evaluator
    print("[1/4] Initializing Wave 2B evaluator...")
    evaluator = ComprehensiveQualityEvaluator()
    print("      [OK] Evaluator ready\n")

    # Evaluate each question
    print("[2/4] Evaluating questions...")
    results = []

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"QUESTION {i}/{len(questions)}")
        print(f"{'='*70}")

        # Extract question data
        stem = question.get("stem", "")
        options = question.get("options", {})
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")
        visual_content = question.get("visual_content")
        metadata = question.get("metadata", {})

        # Display question info
        print(f"\nSubject: {metadata.get('spec_name', 'Unknown')}")
        print(f"Table Type: {metadata.get('table_type', 'Unknown')}")
        print(f"Stem Length: {len(stem)} chars")
        print(f"Has Table: {'Yes' if visual_content else 'No'}")

        if visual_content:
            table_info = visual_content.get("metadata", {})
            print(
                f"Table Size: {table_info.get('rows', '?')} rows x {table_info.get('columns', '?')} cols"
            )

        print(f"\nStem Preview: {stem[:120]}...")

        # Format for Wave 2B
        question_for_eval = {
            "question_text": stem,
            "correct_answer": correct_answer,
            "difficulty": "orta",  # Default medium difficulty
            "subject": metadata.get("spec_name", "").split("_")[1]
            if metadata.get("spec_name")
            else "Unknown",
        }

        # Evaluate
        print("\n[EVALUATING] Running Wave 2B quality checks...")

        try:
            eval_result = evaluator.evaluate(question_for_eval, stage="standard")
            score = eval_result.overall_score

            print(f"\n[RESULT] Quality Score: {score:.3f}")
            print(f"  Grade: {eval_result.overall_grade}")
            print(f"  Decision: {eval_result.decision}")

            # Status
            if score >= 0.85:
                status = "[EXCELLENT] Target exceeded!"
                status_emoji = "✅"
            elif score >= 0.75:
                status = "[GOOD] Close to target"
                status_emoji = "⚠️"
            else:
                status = "[NEEDS WORK] Below target"
                status_emoji = "❌"

            print(f"{status_emoji} {status}")

            results.append(
                {
                    "question_id": i,
                    "spec_name": metadata.get("spec_name"),
                    "table_type": metadata.get("table_type"),
                    "stem_length": len(stem),
                    "has_table": visual_content is not None,
                    "quality_score": score,
                    "grade": eval_result.overall_grade,
                    "decision": eval_result.decision,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            print(f"\n[ERROR] Evaluation failed: {str(e)}")
            import traceback

            traceback.print_exc()

            results.append(
                {
                    "question_id": i,
                    "spec_name": metadata.get("spec_name"),
                    "table_type": metadata.get("table_type"),
                    "quality_score": None,
                    "error": str(e),
                }
            )

    # Summary
    print("\n\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70 + "\n")

    valid_scores = [
        r["quality_score"] for r in results if r.get("quality_score") is not None
    ]

    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        min_score = min(valid_scores)
        max_score = max(valid_scores)

        print(f"Total Questions Evaluated: {len(valid_scores)}/{len(results)}")
        print(f"Average Quality Score: {avg_score:.3f}")
        print(f"Minimum Score: {min_score:.3f}")
        print(f"Maximum Score: {max_score:.3f}")
        print(f"\nTarget Score: 0.850")

        if avg_score >= 0.85:
            print(
                f"\n✅ [SUCCESS] Average score EXCEEDS target! ({avg_score:.3f} >= 0.85)"
            )
        elif avg_score >= 0.80:
            print(f"\n⚠️  [CLOSE] Average score close to target ({avg_score:.3f})")
            print(f"    Need improvement: {0.85 - avg_score:.3f} points")
        else:
            print(f"\n❌ [NEEDS WORK] Average score below target ({avg_score:.3f})")
            print(f"    Gap: {0.85 - avg_score:.3f} points")

        # Individual results
        print(f"\nIndividual Results:")
        print(f"{'='*70}")

        for r in results:
            if r.get("quality_score") is not None:
                score = r["quality_score"]
                emoji = "✅" if score >= 0.85 else "⚠️" if score >= 0.75 else "❌"
                print(
                    f"{emoji} Q{r['question_id']}: {r['spec_name']:<35} Score: {score:.3f}"
                )
            else:
                print(f"❌ Q{r['question_id']}: {r['spec_name']:<35} ERROR")

        # Breakdown by table type
        print(f"\nBreakdown by Table Type:")
        print(f"{'='*70}")

        table_type_scores = {}
        for r in results:
            if r.get("quality_score") is not None:
                tt = r.get("table_type", "Unknown")
                if tt not in table_type_scores:
                    table_type_scores[tt] = []
                table_type_scores[tt].append(r["quality_score"])

        for tt, scores in table_type_scores.items():
            avg = sum(scores) / len(scores)
            print(f"  {tt:<30} Avg: {avg:.3f} ({len(scores)} question(s))")

    else:
        print("❌ [ERROR] No valid scores obtained")

    # Save results
    output_file = f"wave2b_table_questions_evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    evaluation_report = {
        "evaluation_date": datetime.utcnow().isoformat(),
        "phase": "Phase 1 - Tables",
        "total_questions": len(results),
        "valid_evaluations": len(valid_scores),
        "average_score": avg_score if valid_scores else None,
        "min_score": min_score if valid_scores else None,
        "max_score": max_score if valid_scores else None,
        "target_score": 0.85,
        "target_met": avg_score >= 0.85 if valid_scores else False,
        "results": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] Full report saved to: {output_file}")

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70 + "\n")

    return evaluation_report


if __name__ == "__main__":
    asyncio.run(evaluate_questions())
