"""
Generate 5 Production Table Questions (Phase 1 Visual Questions)

This script generates 5 table-based questions across different subjects:
1. Matematik - İstatistik (frequency_table)
2. Matematik - Veri Analizi (statistics_summary)
3. Türkçe - Anlam Bilgisi (comparison_table)
4. Fizik - Deney Sonuçları (comparison_table)
5. Kimya - Element Özellikleri (comparison_table)

Usage:
    cd backend && py generate_5_table_questions.py
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.osym_inspired_generator import OSYMInspiredGenerator


async def generate_5_production_questions():
    """Generate 5 production-quality table questions"""

    print("\n" + "=" * 70)
    print("PRODUCTION: 5 TABLE-BASED QUESTIONS (Phase 1)")
    print("=" * 70 + "\n")

    # Initialize generator
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not found in .env")
        return

    generator = OSYMInspiredGenerator(anthropic_api_key=api_key)

    # Define 5 diverse table questions
    question_specs = [
        {
            "subject": "Matematik",
            "topic": "İstatistik",
            "difficulty": "orta",
            "exam_type": "TYT",
            "table_type": "frequency_table",
            "name": "Q1_Math_Frequency",
        },
        {
            "subject": "Matematik",
            "topic": "Veri Analizi",
            "difficulty": "orta",
            "exam_type": "TYT",
            "table_type": "statistics_summary",
            "name": "Q2_Math_Statistics",
        },
        {
            "subject": "Türkçe",
            "topic": "Anlam Bilgisi",
            "difficulty": "orta",
            "exam_type": "TYT",
            "table_type": "comparison_table",
            "name": "Q3_Turkish_Comparison",
        },
        {
            "subject": "Fizik",
            "topic": "Deney ve Ölçme",
            "difficulty": "orta",
            "exam_type": "TYT",
            "table_type": "comparison_table",
            "name": "Q4_Physics_Experiment",
        },
        {
            "subject": "Kimya",
            "topic": "Periyodik Tablo",
            "difficulty": "orta",
            "exam_type": "TYT",
            "table_type": "comparison_table",
            "name": "Q5_Chemistry_Elements",
        },
    ]

    results = []

    for i, spec in enumerate(question_specs, 1):
        print(f"\n{'='*70}")
        print(f"GENERATING QUESTION {i}/5: {spec['name']}")
        print(
            f"Subject: {spec['subject']} | Topic: {spec['topic']} | Table: {spec['table_type']}"
        )
        print(f"{'='*70}\n")

        try:
            question = await generator.generate_with_few_shot(
                subject=spec["subject"],
                topic=spec["topic"],
                difficulty=spec["difficulty"],
                exam_type=spec["exam_type"],
                include_table=True,
                table_type=spec["table_type"],
            )

            # Add metadata
            question["metadata"] = {
                "phase": "Phase 1 - Tables",
                "generated_at": datetime.utcnow().isoformat(),
                "spec_name": spec["name"],
                "table_type": spec["table_type"],
            }

            results.append(question)

            # Save individual question
            filename = f"production_table_{spec['name']}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(question, f, ensure_ascii=False, indent=2)

            print(f"\n[SUCCESS] Question {i}/5 generated!")
            print(f"  Stem: {question['stem'][:100]}...")
            print(f"  Correct Answer: {question['correct_answer']}")
            if question.get("visual_content"):
                print(f"  Table: {question['visual_content']['metadata']['caption']}")
                print(
                    f"  Table Size: {question['visual_content']['metadata']['rows']} rows x {question['visual_content']['metadata']['columns']} cols"
                )
            print(f"  [SAVED] {filename}")

        except Exception as e:
            print(f"\n[ERROR] Question {i}/5 generation failed: {str(e)}")
            import traceback

            traceback.print_exc()

    # Save all questions together
    output_file = f"production_5_table_questions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)
    print(f"\nTotal Questions Generated: {len(results)}/5")
    print(f"All questions saved to: {output_file}")
    print("\nBreakdown by Subject:")

    subject_counts = {}
    for q in results:
        subject_counts[q.get("metadata", {}).get("spec_name", "Unknown")] = 1

    for spec_name in subject_counts:
        print(f"  - {spec_name}: [OK]")

    print("\nBreakdown by Table Type:")
    table_type_counts = {}
    for q in results:
        table_type = (
            q.get("visual_content", {}).get("metadata", {}).get("caption", "Unknown")
        )
        table_type_counts[table_type] = table_type_counts.get(table_type, 0) + 1

    for table_type, count in table_type_counts.items():
        print(f"  - {table_type}: {count} question(s)")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Validate questions with Wave 2B quality evaluator")
    print("2. Implement frontend table renderer (React component)")
    print("3. Create visual regression tests")
    print("4. Deploy to production")
    print("\n" + "=" * 70 + "\n")

    return results


if __name__ == "__main__":
    asyncio.run(generate_5_production_questions())
