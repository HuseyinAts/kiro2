"""
Wave 2B Quality Evaluation for Phase 2 Graph Questions

Evaluates the 5 generated graph questions with Wave 2B quality system.
Target: 0.85+ quality score (same as Phase 1)

Usage:
    cd backend && py evaluate_graph_questions_wave2b.py
"""

import asyncio
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator


async def load_graph_questions():
    """Load the 5 generated graph questions"""
    json_file = "demo_graph_questions_20251107_193531.json"

    try:
        with open(json_file, encoding="utf-8") as f:
            questions = json.load(f)

        print(f"[OK] Loaded {len(questions)} graph questions from {json_file}")
        return questions
    except FileNotFoundError:
        print(f"[ERROR] File not found: {json_file}")
        print("[INFO] Please run demo_graph_generation.py first to generate questions")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to load questions: {e!s}")
        return []


async def evaluate_questions():
    """Evaluate graph questions with Wave 2B"""

    print("\n" + "=" * 70)
    print("WAVE 2B QUALITY EVALUATION - PHASE 2 GRAPH QUESTIONS")
    print("=" * 70 + "\n")

    # Load questions
    questions = await load_graph_questions()

    if not questions:
        print("[ERROR] No questions to evaluate")
        return None

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
        test_case = question.get("test_case", "Unknown")

        # Display question info
        print(f"\nTest Case: {test_case}")
        print(f"Stem Length: {len(stem)} chars")
        print(f"Has Graph: {'Yes' if visual_content else 'No'}")

        if visual_content:
            graph_info = visual_content.get("metadata", {})
            print(f"Graph Type: {graph_info.get('graph_type', 'Unknown')}")
            print(f"Graph Title: {graph_info.get('title', 'Unknown')}")
            print(f"SVG Size: {len(visual_content.get('content', ''))} chars")

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
                status_emoji = "[OK]"
            elif score >= 0.75:
                status = "[GOOD] Close to target"
                status_emoji = "[WARN]"
            else:
                status = "[NEEDS WORK] Below target"
                status_emoji = "[FAIL]"

            print(f"{status_emoji} {status}")

            results.append(
                {
                    "question_id": i,
                    "test_case": test_case,
                    "graph_type": graph_info.get("graph_type")
                    if visual_content
                    else None,
                    "stem_length": len(stem),
                    "has_graph": visual_content is not None,
                    "svg_size": len(visual_content.get("content", ""))
                    if visual_content
                    else 0,
                    "quality_score": score,
                    "grade": eval_result.overall_grade,
                    "decision": eval_result.decision,
                    "status": status,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except Exception as e:
            print(f"\n[ERROR] Evaluation failed: {e!s}")
            import traceback

            traceback.print_exc()

            results.append(
                {
                    "question_id": i,
                    "test_case": test_case,
                    "graph_type": graph_info.get("graph_type")
                    if visual_content
                    else None,
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
        print("\nTarget Score: 0.850")

        if avg_score >= 0.85:
            print(
                f"\n[SUCCESS] Average score EXCEEDS target! ({avg_score:.3f} >= 0.85)"
            )
        elif avg_score >= 0.80:
            print(f"\n[CLOSE] Average score close to target ({avg_score:.3f})")
            print(f"    Need improvement: {0.85 - avg_score:.3f} points")
        else:
            print(f"\n[NEEDS WORK] Average score below target ({avg_score:.3f})")
            print(f"    Gap: {0.85 - avg_score:.3f} points")

        # Individual results
        print("\nIndividual Results:")
        print(f"{'='*70}")

        for r in results:
            if r.get("quality_score") is not None:
                score = r["quality_score"]
                emoji = (
                    "[OK]" if score >= 0.85 else "[WARN]" if score >= 0.75 else "[FAIL]"
                )
                print(
                    f"{emoji} Q{r['question_id']}: {r['test_case']:<40} Score: {score:.3f}"
                )
            else:
                print(f"[FAIL] Q{r['question_id']}: {r['test_case']:<40} ERROR")

        # Breakdown by graph type
        print("\nBreakdown by Graph Type:")
        print(f"{'='*70}")

        graph_type_scores = {}
        for r in results:
            if r.get("quality_score") is not None:
                gt = r.get("graph_type", "Unknown")
                if gt not in graph_type_scores:
                    graph_type_scores[gt] = []
                graph_type_scores[gt].append(r["quality_score"])

        for gt, scores in graph_type_scores.items():
            avg = sum(scores) / len(scores)
            print(f"  {gt:<20} Avg: {avg:.3f} ({len(scores)} question(s))")

        # Comparison with Phase 1
        print("\nComparison with Phase 1:")
        print(f"{'='*70}")
        phase1_avg = 0.897  # From Phase 1 evaluation
        print(f"  Phase 1 (Tables):  Avg: {phase1_avg:.3f}")
        print(f"  Phase 2 (Graphs):  Avg: {avg_score:.3f}")
        diff = avg_score - phase1_avg
        if diff >= 0:
            print(f"  Difference: +{diff:.3f} (Phase 2 is {abs(diff):.1%} better)")
        else:
            print(f"  Difference: {diff:.3f} (Phase 2 is {abs(diff):.1%} lower)")

    else:
        print("[ERROR] No valid scores obtained")

    # Save results
    output_file = f"wave2b_graph_questions_evaluation_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"

    evaluation_report = {
        "evaluation_date": datetime.now(UTC).isoformat(),
        "phase": "Phase 2 - Graphs",
        "total_questions": len(results),
        "valid_evaluations": len(valid_scores),
        "average_score": avg_score if valid_scores else None,
        "min_score": min_score if valid_scores else None,
        "max_score": max_score if valid_scores else None,
        "target_score": 0.85,
        "target_met": avg_score >= 0.85 if valid_scores else False,
        "comparison_with_phase1": {
            "phase1_avg": 0.897,
            "phase2_avg": avg_score if valid_scores else None,
            "difference": (avg_score - 0.897) if valid_scores else None,
        },
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
