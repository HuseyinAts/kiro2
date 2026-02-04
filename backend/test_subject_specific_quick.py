"""
Quick Test: Subject-Specific Prompts (3 questions)
Verify the system works before running full test
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from services.hybrid_question_generator import HybridQuestionGenerator
from services.subject_specific_prompts import get_subject_config


async def quick_test():
    print("\n" + "=" * 80)
    print("QUICK TEST: Subject-Specific Prompt System")
    print("=" * 80 + "\n")

    # Verify configurations loaded
    print("1. Checking subject configurations...")
    for subject in ["Kimya", "Matematik", "Fizik"]:
        config = get_subject_config(subject)
        if config:
            print(
                f"   [{subject}] Loaded: {config.min_length}-{config.max_length} chars, {len(config.common_misconceptions)} misconceptions"
            )
        else:
            print(f"   [{subject}] NOT FOUND")

    print("\n2. Testing question generation...")

    generator = HybridQuestionGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Test 1: Chemistry (should use 172-232 char range)
    print("\n   [Test 1/3] Chemistry - Mol Kavrami")
    try:
        q1 = await generator.generate_osym_quality_question(
            subject="Kimya",
            topic="Mol Kavrami",
            difficulty="kolay",
            exam_type="TYT",
            provider="claude",
            validate=False,
        )
        print(
            f"   Result: {len(q1['stem'])} chars, OSYM: {q1['osym_compliance_score']:.2f}"
        )
    except Exception as e:
        print(f"   ERROR: {e}")

    await asyncio.sleep(2)

    # Test 2: Mathematics (should use 330-446 char range)
    print("\n   [Test 2/3] Mathematics - Turev")
    try:
        q2 = await generator.generate_osym_quality_question(
            subject="Matematik",
            topic="Turev",
            difficulty="orta",
            exam_type="TYT",
            provider="claude",
            validate=False,
        )
        print(
            f"   Result: {len(q2['stem'])} chars, OSYM: {q2['osym_compliance_score']:.2f}"
        )
    except Exception as e:
        print(f"   ERROR: {e}")

    await asyncio.sleep(2)

    # Test 3: Fizik (should use 385-521 char range)
    print("\n   [Test 3/3] Fizik - Newton Kanunlari")
    try:
        q3 = await generator.generate_osym_quality_question(
            subject="Fizik",
            topic="Newton Kanunlari",
            difficulty="orta",
            exam_type="TYT",
            provider="claude",
            validate=False,
        )
        print(
            f"   Result: {len(q3['stem'])} chars, OSYM: {q3['osym_compliance_score']:.2f}"
        )
    except Exception as e:
        print(f"   ERROR: {e}")

    print("\n" + "=" * 80)
    print("QUICK TEST COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(quick_test())
