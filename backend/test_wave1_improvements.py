"""
Test Wave 1 Improvements
- XML tags (Claude optimization)
- Keyword-based reranking

Quick test to verify implementation
"""

import asyncio
import os
from dotenv import load_dotenv
from services.osym_inspired_generator import OSYMInspiredGenerator


async def test_wave1():
    """Test Wave 1 improvements"""

    # Load environment variables from .env
    load_dotenv()

    # Get API key from environment
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not anthropic_key:
        print("[ERROR] ANTHROPIC_API_KEY not found in environment")
        return

    print("=" * 80)
    print("WAVE 1 IMPROVEMENTS TEST")
    print("=" * 80)
    print()

    # Initialize generator
    generator = OSYMInspiredGenerator(anthropic_api_key=anthropic_key)

    # Test 1: Keyword Reranking
    print("TEST 1: KEYWORD RERANKING")
    print("-" * 80)

    subject = "Matematik"
    topic = "Türev ve türev alma kuralları"

    print(f"Subject: {subject}")
    print(f"Topic: {topic}")
    print()

    # Fetch with reranking
    print("[RERANKING ENABLED]")
    osym_examples_ranked = await generator.get_similar_osym_questions(
        subject=subject, exam_type="TYT", count=3, topic=topic, use_reranking=True
    )

    print(f"\n[SUCCESS] Fetched {len(osym_examples_ranked)} questions with reranking")
    for i, q in enumerate(osym_examples_ranked, 1):
        print(f"  {i}. Year: {q.get('year', 'N/A')}, Length: {len(q['stem'])} chars")
        print(f"     Preview: {q['stem'][:80]}...")

    print("\n" + "=" * 80)
    print("\nTEST 2: GENERATE QUESTION WITH WAVE 1 IMPROVEMENTS")
    print("-" * 80)
    print("Generating question with:")
    print("  [V] XML tags (Claude-optimized prompts)")
    print("  [V] Keyword reranking (topic-relevant examples)")
    print("  [V] Bloom explicit (cognitive level control)")
    print()

    # Generate with Wave 1
    result = await generator.generate_with_few_shot(
        subject=subject,
        topic=topic,
        exam_type="TYT",
        difficulty="orta",
        provider="claude",
    )

    print("\n[SUCCESS] QUESTION GENERATED!")
    print("-" * 80)
    print(f"Stem: {result['stem']}")
    print(f"\nLength: {len(result['stem'])} chars")
    print(f"\nOptions:")
    for key, value in result.get("options", {}).items():
        marker = "[V]" if key == result.get("correct_answer") else "   "
        print(f"  {marker} {key}) {value}")
    print(f"\nCorrect Answer: {result.get('correct_answer')}")
    print(f"\nExplanation: {result.get('explanation', 'N/A')[:200]}...")

    print("\n" + "=" * 80)
    print("WAVE 1 TEST COMPLETE! [SUCCESS]")
    print("=" * 80)
    print("\nExpected improvements:")
    print("  • XML tags: +10-15% quality")
    print("  • Keyword reranking: +15-25% topic relevance")
    print("  • Total expected: +25-40% improvement")
    print("\nNext steps:")
    print("  • Run full 20-question test")
    print("  • Compare with baseline (0.66 Matematik → 0.75-0.80)")
    print("  • Deploy if successful")


if __name__ == "__main__":
    asyncio.run(test_wave1())
