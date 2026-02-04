"""
Demo: Phase 2 Graph Question Generation

Generates demo questions with graphs to test the system.

Test Cases:
1. Line graph - Fizik (Hareket)
2. Bar chart - Matematik (Istatistik)
3. Pie chart - Cografya (Nufus Dagilimi)
4. Scatter plot - Matematik (Korelasyon)
5. Histogram - Biyoloji (Frekans Dagilimi)

Usage:
    cd backend && py demo_graph_generation.py
"""

import sys
import io
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.osym_inspired_generator import OSYMInspiredGenerator


async def demo_graph_generation():
    """Demo graph question generation"""

    print("\n" + "=" * 70)
    print("PHASE 2: GRAPH QUESTION GENERATION DEMO")
    print("=" * 70 + "\n")

    # Initialize generator
    print("[1/6] Initializing OSYM generator...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not found in .env")
        return

    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)
    print("      [OK] Generator ready\n")

    # Test cases
    test_cases = [
        {
            "name": "Line Graph - Fizik (Hareket)",
            "subject": "Fizik",
            "topic": "Hareket",
            "graph_type": "line",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Bar Chart - Matematik (Istatistik)",
            "subject": "Matematik",
            "topic": "Istatistik",
            "graph_type": "bar",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Pie Chart - Matematik (Kategori Dagilimi)",
            "subject": "Matematik",
            "topic": "Veri Analizi",
            "graph_type": "pie",
            "exam_type": "TYT",
            "difficulty": "kolay",
        },
        {
            "name": "Scatter Plot - Matematik (Korelasyon)",
            "subject": "Matematik",
            "topic": "Korelasyon",
            "graph_type": "scatter",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Histogram - Biyoloji (Dagilim)",
            "subject": "Biyoloji",
            "topic": "Frekans Dagilimi",
            "graph_type": "histogram",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
    ]

    print(f"[2/6] Generating {len(test_cases)} graph questions...\n")

    questions = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST CASE {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'='*70}\n")

        try:
            # Generate question with graph
            question = await generator.generate_with_few_shot(
                subject=test_case["subject"],
                topic=test_case["topic"],
                exam_type=test_case["exam_type"],
                difficulty=test_case["difficulty"],
                provider="claude",
                include_graph=True,
                graph_type=test_case["graph_type"],
            )

            # Add metadata
            question["test_case"] = test_case["name"]
            question["generated_at"] = datetime.utcnow().isoformat()

            # Validate
            print(f"\n[VALIDATING] Checking question structure...")

            has_stem = bool(question.get("stem"))
            has_options = len(question.get("options", {})) == 5
            has_answer = bool(question.get("correct_answer"))
            has_graph = question.get("visual_content") is not None

            print(f"  Stem: {'[OK]' if has_stem else '[FAIL]'}")
            print(f"  Options: {'[OK]' if has_options else '[FAIL]'}")
            print(f"  Answer: {'[OK]' if has_answer else '[FAIL]'}")
            print(f"  Graph: {'[OK]' if has_graph else '[FAIL]'}")

            if has_graph:
                graph_info = question["visual_content"]
                print(f"\n[GRAPH INFO]")
                print(f"  Type: {graph_info['type']}")
                print(f"  Format: {graph_info['format']}")
                print(f"  Graph Type: {graph_info['metadata']['graph_type']}")
                print(f"  Title: {graph_info['metadata']['title']}")
                print(f"  SVG Size: {len(graph_info['content'])} chars")

            # Preview
            print(f"\n[PREVIEW]")
            print(f"Stem (first 120 chars): {question['stem'][:120]}...")
            print(f"Options: {list(question['options'].values())}")
            print(f"Correct Answer: {question['correct_answer']}")

            if has_stem and has_options and has_answer and has_graph:
                print(f"\n[SUCCESS] Question {i} generated successfully!")
                questions.append(question)
            else:
                print(f"\n[WARNING] Question {i} has missing components")
                questions.append(question)  # Still save for inspection

        except Exception as e:
            print(f"\n[ERROR] Failed to generate question {i}: {str(e)}")
            import traceback

            traceback.print_exc()

    # Summary
    print("\n\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70 + "\n")

    success_count = sum(1 for q in questions if q.get("visual_content") is not None)
    print(f"Total Questions Generated: {len(questions)}/{len(test_cases)}")
    print(f"With Graphs: {success_count}/{len(questions)}")
    print(f"Success Rate: {(success_count/len(test_cases)*100):.1f}%")

    # Graph type breakdown
    print(f"\nGraph Type Breakdown:")
    graph_types = {}
    for q in questions:
        if q.get("visual_content"):
            gtype = q["visual_content"]["metadata"]["graph_type"]
            graph_types[gtype] = graph_types.get(gtype, 0) + 1

    for gtype, count in graph_types.items():
        print(f"  {gtype}: {count}")

    # Save questions
    if questions:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"demo_graph_questions_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] All questions saved to: {output_file}")

        # Save individual graph SVGs for inspection
        for i, q in enumerate(questions, 1):
            if q.get("visual_content"):
                svg_file = f"demo_graph_Q{i}_{q['visual_content']['metadata']['graph_type']}.svg"
                with open(svg_file, "w", encoding="utf-8") as f:
                    f.write(q["visual_content"]["content"])
                print(f"[SAVED] Graph {i} SVG saved to: {svg_file}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70 + "\n")

    return questions


if __name__ == "__main__":
    asyncio.run(demo_graph_generation())
