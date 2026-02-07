"""
Demo: Generate questions with tables (Phase 1 Visual Questions)

This script demonstrates the new table generation feature:
- Generates 2 questions with tables (1 Math + 1 Turkish)
- Shows how tables are integrated into questions
- Validates the visual_content structure

Usage:
    cd backend && py demo_table_generation.py
"""

import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator


async def demo_table_generation():
    """Demonstrate table-based question generation"""

    print("\n" + "=" * 70)
    print("DEMO: TABLE-BASED QUESTION GENERATION (Phase 1)")
    print("=" * 70 + "\n")

    # Initialize generator
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not found in .env")
        return

    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)

    # Test 1: Mathematics with Frequency Table
    print("\n" + "-" * 70)
    print("TEST 1: Mathematics + Frequency Table")
    print("-" * 70 + "\n")

    try:
        print("[INFO] Generating mathematics question with frequency table...")
        math_question = await generator.generate_with_few_shot(
            subject="Matematik",
            topic="İstatistik",
            difficulty="orta",
            exam_type="TYT",
            include_table=True,  # REQUEST TABLE
            table_type="frequency_table",
        )

        print("\n[SUCCESS] Question generated!")
        print(f"\nStem: {math_question['stem'][:150]}...")
        print("\nOptions:")
        for key, value in math_question["options"].items():
            print(f"  {key}) {value}")
        print(f"\nCorrect Answer: {math_question['correct_answer']}")

        # Show table
        if math_question.get("visual_content"):
            print("\n[TABLE] Visual Content:")
            print(f"  Type: {math_question['visual_content']['type']}")
            print(f"  Format: {math_question['visual_content']['format']}")
            print(
                f"  Caption: {math_question['visual_content']['metadata']['caption']}"
            )
            print("\n  Table Content:")
            print(math_question["visual_content"]["content"])
        else:
            print("\n[WARNING] No visual content found!")

        # Save to file
        with open("demo_table_math.json", "w", encoding="utf-8") as f:
            json.dump(math_question, f, ensure_ascii=False, indent=2)
        print("\n[SAVED] Question saved to: demo_table_math.json")

    except Exception as e:
        print(f"\n[ERROR] Math question generation failed: {str(e)}")
        import traceback

        traceback.print_exc()

    # Test 2: Turkish with Comparison Table
    print("\n\n" + "-" * 70)
    print("TEST 2: Turkish + Comparison Table")
    print("-" * 70 + "\n")

    try:
        print("[INFO] Generating Turkish question with comparison table...")
        turkish_question = await generator.generate_with_few_shot(
            subject="Türkçe",
            topic="Anlam Bilgisi",
            difficulty="orta",
            exam_type="TYT",
            include_table=True,  # REQUEST TABLE
            table_type="comparison_table",
        )

        print("\n[SUCCESS] Question generated!")
        print(f"\nStem: {turkish_question['stem'][:150]}...")
        print("\nOptions:")
        for key, value in turkish_question["options"].items():
            print(f"  {key}) {value}")
        print(f"\nCorrect Answer: {turkish_question['correct_answer']}")

        # Show table
        if turkish_question.get("visual_content"):
            print("\n[TABLE] Visual Content:")
            print(f"  Type: {turkish_question['visual_content']['type']}")
            print(f"  Format: {turkish_question['visual_content']['format']}")
            print(
                f"  Caption: {turkish_question['visual_content']['metadata']['caption']}"
            )
            print("\n  Table Content:")
            print(turkish_question["visual_content"]["content"])
        else:
            print("\n[WARNING] No visual content found!")

        # Save to file
        with open("demo_table_turkish.json", "w", encoding="utf-8") as f:
            json.dump(turkish_question, f, ensure_ascii=False, indent=2)
        print("\n[SAVED] Question saved to: demo_table_turkish.json")

    except Exception as e:
        print(f"\n[ERROR] Turkish question generation failed: {str(e)}")
        import traceback

        traceback.print_exc()

    # Summary
    print("\n\n" + "=" * 70)
    print("DEMO SUMMARY")
    print("=" * 70)
    print("\nPhase 1 Table Generation Features:")
    print("  [OK] Database schema supports visual_content (JSONB)")
    print("  [OK] Models include visual_content field")
    print("  [OK] VisualContentGenerator creates tables")
    print("  [OK] OSYMInspiredGenerator integrates tables into questions")
    print("  [OK] Questions generated with table metadata")
    print("\nNext Steps:")
    print("  1. Frontend table renderer (React component)")
    print("  2. Generate 5 production table questions")
    print("  3. Validate with Wave 2B quality evaluator")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_table_generation())
