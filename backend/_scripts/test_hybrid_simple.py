"""
Simple Hybrid Question Generation Test
Tek bir soru uret ve sonucu goster
"""

import asyncio
import os
import sys

# Load environment variables from .env
from dotenv import load_dotenv

load_dotenv()

# Print API key status
print("\n" + "=" * 80)
print("API KEY STATUS")
print("=" * 80)

anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
openai_key = os.getenv("OPENAI_API_KEY", "")

if anthropic_key and anthropic_key.startswith("sk-ant"):
    print("[OK] ANTHROPIC_API_KEY: Found")
else:
    print("[ERROR] ANTHROPIC_API_KEY: Not found or invalid")
    print("   Please add to .env file: ANTHROPIC_API_KEY=sk-ant-...")

if openai_key and openai_key.startswith("sk-"):
    print("[OK] OPENAI_API_KEY: Found")
else:
    print("[ERROR] OPENAI_API_KEY: Not found or invalid")
    print("   Please add to .env file: OPENAI_API_KEY=sk-...")

if not anthropic_key or not openai_key:
    print("\n[WARNING] API keys are required for question generation!")
    print("   Add them to backend/.env file")
    sys.exit(1)

print("\n" + "=" * 80)
print("HYBRID QUESTION GENERATION - SIMPLE TEST")
print("=" * 80 + "\n")

from services.hybrid_question_generator import HybridQuestionGenerator


async def generate_one_question():
    """Generate a single question with detailed output"""

    print("[INFO] GENERATING QUESTION...")
    print("   Subject: Matematik")
    print("   Topic: Turev Alma Kurallari")
    print("   Difficulty: orta")
    print("   Method: osym_guided (3 OSYM examples)")
    print("   Provider: claude\n")

    # Initialize generator
    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    try:
        # Generate question
        question = await generator.generate_osym_quality_question(
            subject="Matematik",
            topic="Turev Alma Kurallari",
            difficulty="orta",
            exam_type="TYT",
            provider="claude",
            validate=True,
        )

        # Display results
        print("=" * 80)
        print("[SUCCESS] QUESTION GENERATED SUCCESSFULLY!")
        print("=" * 80 + "\n")

        print("QUESTION (STEM):")
        print("-" * 80)
        print(question["stem"])
        print("-" * 80 + "\n")

        print("OPTIONS:")
        for key, value in question["options"].items():
            marker = "[OK]" if key == question["correct_answer"] else "    "
            print(f"  {marker} {key}) {value}")

        print(f"\nCORRECT ANSWER: {question['correct_answer']}")

        print(f"\nEXPLANATION:")
        print(f"{question['explanation']}\n")

        print("=" * 80)
        print("QUALITY METRICS")
        print("=" * 80)
        print(f"  Overall Quality:        {question['quality_score']:.2f}/1.00")
        print(f"  OSYM Compliance:        {question['osym_compliance_score']:.2f}/1.00")
        print(
            f"  Grammar Score:          {question.get('grammar_score', 0.85):.2f}/1.00"
        )
        print(
            f"  IRT Difficulty:         {question['irt_difficulty']:.2f} (range: -3 to +3)"
        )
        print(
            f"  IRT Discrimination:     {question['irt_discrimination']:.2f} (range: 0.5 to 2.5)"
        )
        print(f"  Morphology Complexity:  {question['morphology_complexity']:.2f}/1.00")
        print(f"  Readability Score:      {question['readability_score']:.2f}/1.00")

        print(
            f"\n  Validation Status:      {'[OK] PASSED' if question['is_valid'] else '[ERROR] FAILED'}"
        )

        if question.get("validation_issues"):
            print(
                f"  Issues:                 {', '.join(question['validation_issues'])}"
            )

        print("\n" + "=" * 80)
        print("GENERATION INFO")
        print("=" * 80)
        print(f"  Method:                 {question['generation_method']}")
        print(f"  Provider:               {question['provider']}")
        print(f"  OSYM Examples Used:     {question['osym_examples_used']}")
        print(f"  Created:                {question['created_at']}")

        print("\n" + "=" * 80)
        print("[SUCCESS] TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80 + "\n")

        print("NEXT STEPS:")
        print("   1. Review the quality metrics above")
        print(
            "   2. Test via HTTP API: http://localhost:8000/api/questions/hybrid/generate"
        )
        print("   3. Generate more questions with different topics")
        print("   4. Generate bulk questions (10+) for production\n")

        return question

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()

        print("\nTROUBLESHOOTING:")
        print("   1. Check if database is running (PostgreSQL)")
        print("   2. Verify OSYM questions exist in database:")
        print("      SELECT COUNT(*) FROM questions WHERE source = 'OSYM';")
        print("   3. Check API keys in .env file")
        print("   4. See HYBRID_API_QUICK_START.md for more help\n")

        return None


if __name__ == "__main__":
    asyncio.run(generate_one_question())
