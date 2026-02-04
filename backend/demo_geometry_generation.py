"""
Demo: Phase 3 Geometry Question Generation

Generates demo questions with geometric figures to test the system.

Test Cases:
1. Right Triangle - Matematik (Pisagor)
2. Complete Circle - Matematik (Daire)
3. Square - Matematik (Alan Hesaplama)
4. Regular Hexagon - Matematik (Çokgenler)
5. Cube (3D) - Matematik (Hacim)

Usage:
    cd backend && py demo_geometry_generation.py
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


async def demo_geometry_generation():
    """Demo geometry question generation"""

    print("\n" + "=" * 70)
    print("PHASE 3: GEOMETRY QUESTION GENERATION DEMO")
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
            "name": "Right Triangle - Matematik (Pisagor)",
            "subject": "Matematik",
            "topic": "Pisagor Teoremi",
            "geometry_type": "triangle",
            "shape_subtype": "right_triangle",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Complete Circle - Matematik (Daire)",
            "subject": "Matematik",
            "topic": "Daire ve Alan",
            "geometry_type": "circle",
            "shape_subtype": "complete_circle",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Square - Matematik (Alan Hesaplama)",
            "subject": "Matematik",
            "topic": "Dörtgenler ve Alan",
            "geometry_type": "quadrilateral",
            "shape_subtype": "square",
            "exam_type": "TYT",
            "difficulty": "kolay",
        },
        {
            "name": "Regular Hexagon - Matematik (Çokgenler)",
            "subject": "Matematik",
            "topic": "Düzgün Çokgenler",
            "geometry_type": "polygon",
            "shape_subtype": "hexagon",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
        {
            "name": "Cube (3D) - Matematik (Hacim)",
            "subject": "Matematik",
            "topic": "Katı Cisimler Hacmi",
            "geometry_type": "3d_shape",
            "shape_subtype": "cube",
            "exam_type": "TYT",
            "difficulty": "orta",
        },
    ]

    print(f"[2/6] Generating {len(test_cases)} geometry questions...\n")

    questions = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST CASE {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'='*70}\n")

        try:
            # Generate question with geometry
            question = await generator.generate_with_few_shot(
                subject=test_case["subject"],
                topic=test_case["topic"],
                exam_type=test_case["exam_type"],
                difficulty=test_case["difficulty"],
                provider="claude",
                include_geometry=True,
                geometry_type=test_case["geometry_type"],
                shape_subtype=test_case["shape_subtype"],
            )

            # Add metadata
            question["test_case"] = test_case["name"]
            question["generated_at"] = datetime.utcnow().isoformat()

            # Validate
            print(f"\n[VALIDATING] Checking question structure...")

            has_stem = bool(question.get("stem"))
            has_options = len(question.get("options", {})) == 5
            has_answer = bool(question.get("correct_answer"))
            has_geometry = question.get("visual_content") is not None

            print(f"  Stem: {'[OK]' if has_stem else '[FAIL]'}")
            print(f"  Options: {'[OK]' if has_options else '[FAIL]'}")
            print(f"  Answer: {'[OK]' if has_answer else '[FAIL]'}")
            print(f"  Geometry: {'[OK]' if has_geometry else '[FAIL]'}")

            if has_geometry:
                geometry_info = question["visual_content"]
                print(f"\n[GEOMETRY INFO]")
                print(f"  Type: {geometry_info['type']}")
                print(f"  Format: {geometry_info['format']}")
                print(f"  Geometry Type: {geometry_info['metadata']['geometry_type']}")
                print(f"  Shape Subtype: {geometry_info['metadata']['shape_subtype']}")
                print(f"  Dimensions: {geometry_info['metadata']['dimensions']}")
                print(f"  SVG Size: {len(geometry_info['content'])} chars")

            # Preview
            print(f"\n[PREVIEW]")
            print(f"Stem (first 120 chars): {question['stem'][:120]}...")
            print(f"Options: {list(question['options'].values())}")
            print(f"Correct Answer: {question['correct_answer']}")

            if has_stem and has_options and has_answer and has_geometry:
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
    print(f"With Geometry: {success_count}/{len(questions)}")
    print(f"Success Rate: {(success_count/len(test_cases)*100):.1f}%")

    # Geometry type breakdown
    print(f"\nGeometry Type Breakdown:")
    geometry_types = {}
    for q in questions:
        if q.get("visual_content"):
            gtype = q["visual_content"]["metadata"]["geometry_type"]
            shape_subtype = q["visual_content"]["metadata"]["shape_subtype"]
            key = f"{gtype} ({shape_subtype})"
            geometry_types[key] = geometry_types.get(key, 0) + 1

    for gtype, count in geometry_types.items():
        print(f"  {gtype}: {count}")

    # Save questions
    if questions:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"demo_geometry_questions_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] All questions saved to: {output_file}")

        # Save individual geometry SVGs for inspection
        for i, q in enumerate(questions, 1):
            if q.get("visual_content"):
                svg_file = f"demo_geometry_Q{i}_{q['visual_content']['metadata']['shape_subtype']}.svg"
                with open(svg_file, "w", encoding="utf-8") as f:
                    f.write(q["visual_content"]["content"])
                print(f"[SAVED] Geometry {i} SVG saved to: {svg_file}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70 + "\n")

    return questions


if __name__ == "__main__":
    asyncio.run(demo_geometry_generation())
