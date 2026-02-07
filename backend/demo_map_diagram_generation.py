"""
Demo: Phase 4 Map/Diagram Question Generation

Generates 5 ÖSYM-style questions with maps and diagrams:
1. Turkey Regions Map - Coğrafya
2. Flowchart - Fen Bilimleri (Water Cycle)
3. Venn Diagram - Matematik (Set Theory)
4. Horizontal Timeline - Tarih (Turkish Republic)
5. Tree Diagram - Biyoloji (Animal Classification)

Usage:
    cd backend && py demo_map_diagram_generation.py

Output:
    - demo_map_diagram_questions_TIMESTAMP.json (5 questions)
    - Individual SVG files for each diagram
"""

import sys
import io
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator
import os


# Test cases for Phase 4
TEST_CASES = [
    {
        "name": "Turkey Regions Map",
        "subject": "Coğrafya",
        "topic": "Türkiye Bölgeleri",
        "diagram_type": "geographic_map",
        "diagram_subtype": "turkey_regions",
        "exam_type": "TYT",
    },
    {
        "name": "Flowchart (Water Cycle)",
        "subject": "Fen Bilimleri",
        "topic": "Su Döngüsü",
        "diagram_type": "process_diagram",
        "diagram_subtype": "flowchart",
        "exam_type": "TYT",
    },
    {
        "name": "Venn Diagram",
        "subject": "Matematik",
        "topic": "Kümeler",
        "diagram_type": "classification_diagram",
        "diagram_subtype": "venn_diagram",
        "exam_type": "TYT",
    },
    {
        "name": "Horizontal Timeline",
        "subject": "Tarih",
        "topic": "Türkiye Cumhuriyeti",
        "diagram_type": "timeline",
        "diagram_subtype": "horizontal_timeline",
        "exam_type": "AYT",
    },
    {
        "name": "Tree Diagram",
        "subject": "Biyoloji",
        "topic": "Canlı Sınıflandırması",
        "diagram_type": "classification_diagram",
        "diagram_subtype": "tree_diagram",
        "exam_type": "AYT",
    },
]


async def generate_demo_questions():
    """Generate 5 demo map/diagram questions"""

    print("=" * 70)
    print("PHASE 4: MAP/DIAGRAM QUESTION GENERATION DEMO")
    print("=" * 70)
    print()

    # Initialize generator
    print("[1/3] Initializing generator...")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("      [WARNING] No ANTHROPIC_API_KEY found, trying without...")
    generator = OSYMInspiredGenerator(anthropic_api_key=anthropic_key)
    print("      [OK] Generator ready\n")

    # Generate questions
    print("[2/3] Generating 5 questions with maps/diagrams...")
    print()

    questions = []
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"{'='*70}")
        print(f"QUESTION {i}/5: {test_case['name']}")
        print(f"{'='*70}")
        print(f"Subject:       {test_case['subject']}")
        print(f"Topic:         {test_case['topic']}")
        print(f"Diagram Type:  {test_case['diagram_type']}")
        print(f"Diagram Subtype: {test_case['diagram_subtype']}")
        print()

        try:
            # Generate question with map/diagram
            question = await generator.generate_with_few_shot(
                subject=test_case["subject"],
                topic=test_case["topic"],
                exam_type=test_case["exam_type"],
                difficulty="orta",
                provider="claude",
                include_map_diagram=True,
                diagram_type=test_case["diagram_type"],
                diagram_subtype=test_case["diagram_subtype"],
            )

            # Validate question
            if not question.get("stem"):
                raise Exception("No stem generated")
            if not question.get("options"):
                raise Exception("No options generated")
            if not question.get("correct_answer"):
                raise Exception("No correct answer generated")
            if not question.get("visual_content"):
                raise Exception("No visual content generated")

            # Add test case info
            question["test_case"] = test_case["name"]
            question["metadata"] = {
                "spec_name": f"phase4_{test_case['diagram_subtype']}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            questions.append(question)

            # Display info
            print("[OK] Question generated successfully!")
            print(f"     Stem:      {question['stem'][:100]}...")
            print(f"     Options:   {len(question['options'])} choices")
            print(f"     Answer:    {question['correct_answer']}")
            print(
                f"     Diagram:   {question['visual_content']['metadata']['diagram_subtype']}"
            )
            print(f"     SVG Size:  {len(question['visual_content']['content'])} chars")
            print()

            # Save individual SVG
            svg_filename = f"demo_map_diagram_Q{i}_{test_case['diagram_subtype']}.svg"
            with open(svg_filename, "w", encoding="utf-8") as f:
                f.write(question["visual_content"]["content"])
            print(f"[SAVED] SVG saved to: {svg_filename}\n")

        except Exception as e:
            print(f"[ERROR] Failed to generate question: {str(e)}\n")
            import traceback

            traceback.print_exc()

    # Save all questions
    print("[3/3] Saving questions...")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = f"demo_map_diagram_questions_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"      [OK] Saved {len(questions)} questions to: {output_file}\n")

    # Summary
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print(f"Generated:        {len(questions)}/5 questions")
    print(f"Success Rate:     {len(questions)/5*100:.0f}%")
    print(
        f"Diagram Types:    {len(set(q['visual_content']['metadata']['diagram_type'] for q in questions))}/4"
    )
    print()

    if questions:
        print("Questions Preview:")
        print("-" * 70)
        for i, q in enumerate(questions, 1):
            print(f"Q{i}: {q['test_case']}")
            print(f"    Diagram: {q['visual_content']['metadata']['diagram_subtype']}")
            print(f"    Stem: {q['stem'][:80]}...")
            print(f"    Answer: {q['correct_answer']}")
            print()

    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(generate_demo_questions())
