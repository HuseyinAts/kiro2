"""
Test ÖSYM-Inspired Question Generation
Quick demo of using real ÖSYM questions for AI generation
"""
import asyncio
import os


async def demo_few_shot_generation():
    """
    DEMO 1: Few-Shot Learning
    Use 3 real ÖSYM questions to generate a new one
    """
    print("\n" + "=" * 80)
    print("DEMO 1: FEW-SHOT LEARNING WITH REAL ÖSYM QUESTIONS")
    print("=" * 80 + "\n")

    from services.osym_inspired_generator import OSYMInspiredGenerator

    # Initialize (put your API keys in .env)
    generator = OSYMInspiredGenerator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    try:
        # Generate a new question inspired by ÖSYM
        print("🔄 Generating question inspired by real ÖSYM examples...")

        new_question = await generator.generate_with_few_shot(
            subject="Matematik",
            topic="Türev Alma Kuralları",
            exam_type="TYT",
            difficulty="orta",
            provider="claude",  # or "openai"
        )

        print("\n✅ GENERATED QUESTION:")
        print("-" * 80)
        print(f"STEM: {new_question['stem']}\n")

        print("OPTIONS:")
        for key, value in new_question["options"].items():
            marker = "✓" if key == new_question["correct_answer"] else " "
            print(f"{marker} {key}) {value}")

        print(f"\n✅ Correct Answer: {new_question['correct_answer']}")
        print(f"📝 Explanation: {new_question['explanation']}")
        print(f"🎯 Method: {new_question['method']}")
        print(f"📚 ÖSYM Examples Used: {new_question['osym_examples_used']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Backend is running")
        print("2. Database has ÖSYM questions")
        print("3. API keys are in .env file")


async def demo_style_analysis():
    """
    DEMO 2: Style Analysis
    Analyze ÖSYM question patterns
    """
    print("\n" + "=" * 80)
    print("DEMO 2: ÖSYM STYLE ANALYSIS")
    print("=" * 80 + "\n")

    from services.osym_inspired_generator import OSYMInspiredGenerator

    generator = OSYMInspiredGenerator()

    try:
        print("🔍 Analyzing ÖSYM Matematik questions...")

        style_guide = await generator.analyze_osym_style(
            subject="Matematik", exam_type="TYT"
        )

        print(f"\n📊 ANALYSIS RESULTS:")
        print("-" * 80)
        print(f"Questions Analyzed: {style_guide['total_analyzed']}")
        print(f"Average Length: {style_guide['avg_stem_length']} characters")
        print(f"Average Words: {style_guide['avg_word_count']}")

        print(f"\n📝 STYLE NOTES:")
        for note in style_guide["style_notes"]:
            print(f"  • {note}")

        print(f"\n🎯 COMMON PATTERNS:")
        for starter, count in style_guide["common_starters"]:
            print(f'  • "{starter}..." ({count} times)')

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_get_examples():
    """
    DEMO 3: Get Real ÖSYM Examples
    Retrieve authentic ÖSYM questions
    """
    print("\n" + "=" * 80)
    print("DEMO 3: GET REAL ÖSYM EXAMPLES")
    print("=" * 80 + "\n")

    from services.osym_inspired_generator import OSYMInspiredGenerator

    generator = OSYMInspiredGenerator()

    try:
        print("📚 Fetching 3 real ÖSYM Matematik questions...")

        examples = await generator.get_similar_osym_questions(
            subject="Matematik", exam_type="TYT", count=3
        )

        for i, q in enumerate(examples, 1):
            print(f"\n📖 EXAMPLE {i} (ÖSYM {q['year']}):")
            print("-" * 80)
            print(f"Subject: {q['subject']}")
            print(f"Stem (first 150 chars): {q['stem'][:150]}...")
            print(f"Options: {list(q['options'].keys())}")
            if q["correct_answer"]:
                print(f"✅ Correct Answer: {q['correct_answer']}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_statistics():
    """
    DEMO 4: Training Statistics
    Show available ÖSYM data for training
    """
    print("\n" + "=" * 80)
    print("DEMO 4: ÖSYM TRAINING DATA STATISTICS")
    print("=" * 80 + "\n")

    from services.osym_inspired_generator import OSYMInspiredGenerator

    generator = OSYMInspiredGenerator()

    try:
        stats = await generator.get_osym_statistics()

        print(f"📊 ÖSYM QUESTION BANK:")
        print("-" * 80)
        print(f"Total Questions: {stats['total_osym_questions']}")
        print(f"Training Ready: {stats['usable_for_training']} (with answers)")
        print(f"Ready to Train: {'✅ YES' if stats['training_ready'] else '❌ NO'}")

        print(f"\n📚 BY SUBJECT:")
        for subject, count in sorted(
            stats["by_subject"].items(), key=lambda x: x[1], reverse=True
        ):
            bar = "█" * (count // 10)
            print(f"  {subject:20} {count:4} {bar}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """
    Run all demos
    """
    print("\n" + "=" * 80)
    print("🎯 ÖSYM-INSPIRED QUESTION GENERATION - DEMO SUITE")
    print("=" * 80)
    print("\nUsing 1988 real ÖSYM questions for AI-powered question generation!")
    print("\nPress Ctrl+C to skip any demo\n")

    try:
        # Demo 1: Few-Shot Generation (requires API key)
        await demo_few_shot_generation()

        # Demo 2: Style Analysis
        await demo_style_analysis()

        # Demo 3: Get Examples
        await demo_get_examples()

        # Demo 4: Statistics
        await demo_statistics()

        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETED!")
        print("=" * 80)

        print("\n📚 NEXT STEPS:")
        print("  1. Add API keys to .env (ANTHROPIC_API_KEY, OPENAI_API_KEY)")
        print("  2. Use /api/v1/osym-inspired/generate endpoint")
        print("  3. Integrate with your question generation system")
        print("  4. See: OSYM_SORU_URETIM_REHBERI.md for full guide")

    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
