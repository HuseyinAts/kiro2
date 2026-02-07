"""
KIRO2 LLM Cache - Usage Examples
Demonstrates how to use the enhanced LLM cache system
"""

import asyncio
from core.llm_cache import LLMCache, LLMCacheConfig, cached_llm, get_llm_cache


# ============================================================================
# EXAMPLE 1: Basic Cache Usage
# ============================================================================


async def example_basic_usage():
    """Basic cache get/set operations"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Cache Usage")
    print("=" * 80)

    # Create cache instance
    cache = LLMCache()
    await cache.initialize()

    # Simulate LLM call
    prompt = "Matematik dersi için örnek soru üret"
    model = "gpt-4"

    # Try to get from cache
    cached_response = await cache.get(prompt, model)

    if cached_response:
        print(f"✓ Cache HIT: {cached_response}")
    else:
        print("✗ Cache MISS - Generating new response...")

        # Simulate LLM API call
        response = "1. İki sayının toplamı 10, farkı 2 ise bu sayılar kaçtır?"

        # Cache the response
        await cache.set(
            prompt=prompt, response=response, model=model, token_count=150, cost=0.003
        )
        print(f"✓ Response cached: {response}")

    # Second call should hit cache
    cached_response = await cache.get(prompt, model)
    print(f"✓ Second call (from cache): {cached_response}")

    # Get statistics
    stats = await cache.get_stats()
    print("\nCache Stats:")
    print(f"  Hit Ratio: {stats['hit_ratio']:.2%}")
    print(f"  Tokens Saved: {stats['total_tokens_saved']}")
    print(f"  Cost Saved: ${stats['total_cost_saved']:.4f}")

    await cache.close()


# ============================================================================
# EXAMPLE 2: Using Decorator
# ============================================================================


async def example_decorator():
    """Using @cached_llm decorator"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Using @cached_llm Decorator")
    print("=" * 80)

    # Create cache instance
    cache = await get_llm_cache()

    # Simulate LLM service
    class MockLLMService:
        call_count = 0

        @cached_llm(ttl=3600, model="gpt-4", cache_instance=cache)
        async def generate_question(self, prompt: str) -> str:
            """Generate educational question (with caching)"""
            self.call_count += 1
            print(f"  → LLM API called (call #{self.call_count})")

            # Simulate API call
            await asyncio.sleep(0.1)
            return f"Generated question based on: {prompt}"

    llm = MockLLMService()

    # First call - will execute function
    print("\nFirst call:")
    result1 = await llm.generate_question("Türev konusu")
    print(f"  Result: {result1}")

    # Second call - will use cache
    print("\nSecond call (same prompt):")
    result2 = await llm.generate_question("Türev konusu")
    print(f"  Result: {result2}")

    # Different prompt - will execute function again
    print("\nThird call (different prompt):")
    result3 = await llm.generate_question("İntegral konusu")
    print(f"  Result: {result3}")

    print(f"\nTotal LLM API calls: {llm.call_count} (saved 1 call)")


# ============================================================================
# EXAMPLE 3: Turkish Language Optimization
# ============================================================================


async def example_turkish_optimization():
    """Turkish character handling"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Turkish Language Optimization")
    print("=" * 80)

    cache = LLMCache()
    await cache.initialize()

    # Turkish prompts with variations
    prompts = [
        "İstanbul'da kaç üniversite var?",
        "istanbul'da kaç üniversite var?",  # Different case
        "  İstanbul'da kaç üniversite var?  ",  # Extra whitespace
    ]

    response = "İstanbul'da 50'den fazla üniversite bulunmaktadır."

    # Cache first version
    await cache.set(prompts[0], response, "gpt-4")

    # All variations should hit the same cache entry
    for i, prompt in enumerate(prompts, 1):
        result = await cache.get(prompt, "gpt-4")
        status = "✓ HIT" if result else "✗ MISS"
        print(f"{i}. {status}: '{prompt[:30]}...'")

    await cache.close()


# ============================================================================
# EXAMPLE 4: Cost and Token Tracking
# ============================================================================


async def example_cost_tracking():
    """Track LLM costs and tokens"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Cost and Token Tracking")
    print("=" * 80)

    cache = LLMCache()
    await cache.initialize()

    # Simulate multiple LLM calls
    questions = [
        ("Matematik sorusu üret", 200, 0.004),
        ("Fizik sorusu üret", 180, 0.0036),
        ("Kimya sorusu üret", 190, 0.0038),
    ]

    print("Simulating LLM calls...\n")

    for prompt, tokens, cost in questions:
        # Check cache
        cached = await cache.get(prompt, "gpt-4")

        if not cached:
            # Simulate new call
            response = f"Örnek soru: {prompt}"
            await cache.set(
                prompt=prompt,
                response=response,
                model="gpt-4",
                token_count=tokens,
                cost=cost,
            )
            print(f"✗ Generated: {prompt[:30]:30} | {tokens:3d} tokens | ${cost:.4f}")
        else:
            print(f"✓ Cached:    {prompt[:30]:30} | Saved!")

    # Second round - all should be cached
    print("\nSecond round (all cached):\n")

    for prompt, tokens, cost in questions:
        cached = await cache.get(prompt, "gpt-4")
        if cached:
            print(
                f"✓ Cached:    {prompt[:30]:30} | Saved {tokens:3d} tokens | ${cost:.4f}"
            )

    # Show savings
    stats = await cache.get_stats()
    print(f"\n{'─' * 80}")
    print("TOTAL SAVINGS:")
    print(f"  Tokens saved: {stats['total_tokens_saved']:,}")
    print(f"  Cost saved:   ${stats['total_cost_saved']:.4f}")
    print(f"  Hit ratio:    {stats['hit_ratio']:.2%}")

    await cache.close()


# ============================================================================
# EXAMPLE 5: Advanced Configuration
# ============================================================================


async def example_advanced_config():
    """Advanced configuration options"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Advanced Configuration")
    print("=" * 80)

    # Custom configuration
    config = LLMCacheConfig(
        redis_url="redis://localhost:6379/0",
        default_ttl=7200,  # 2 hours
        long_ttl=172800,  # 2 days
        max_prompt_length=8000,
        enable_compression=True,
        turkish_normalization=True,
        key_prefix="kiro2:production:llm",
    )

    cache = LLMCache(config=config)
    await cache.initialize()

    print("Configuration:")
    print(f"  Redis URL:      {config.redis_url}")
    print(f"  Default TTL:    {config.default_ttl}s")
    print(f"  Long TTL:       {config.long_ttl}s")
    print(f"  Max Prompt:     {config.max_prompt_length} chars")
    print(f"  Compression:    {config.enable_compression}")
    print(f"  Turkish Norm:   {config.turkish_normalization}")

    # Cache with custom TTL
    await cache.set(
        prompt="Stable content that rarely changes",
        response="This will be cached for 2 days",
        model="gpt-4",
        ttl=config.long_ttl,  # Use long TTL
    )

    print(f"\n✓ Cached with {config.long_ttl}s TTL")

    await cache.close()


# ============================================================================
# EXAMPLE 6: Real-World Integration
# ============================================================================


class QuestionGeneratorService:
    """Example service using LLM cache"""

    def __init__(self):
        self.cache: Optional[LLMCache] = None

    async def initialize(self):
        """Initialize service"""
        self.cache = await get_llm_cache()

    @cached_llm(ttl=7200, model="gpt-4")
    async def generate_question(
        self, topic: str, difficulty: str, question_type: str
    ) -> dict:
        """
        Generate educational question with caching

        Args:
            topic: Subject topic (e.g., "Matematik")
            difficulty: Difficulty level (easy, medium, hard)
            question_type: Type (multiple_choice, open_ended)

        Returns:
            Generated question data
        """
        # Build prompt
        prompt = f"""
        Konu: {topic}
        Zorluk: {difficulty}
        Tip: {question_type}

        Bu özelliklere sahip bir soru üret.
        """

        # This will be automatically cached by decorator
        # In real implementation, call actual LLM API here
        await asyncio.sleep(0.1)  # Simulate API call

        return {
            "question": f"{topic} konusunda {difficulty} seviye soru",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Çözüm açıklaması",
            "metadata": {
                "topic": topic,
                "difficulty": difficulty,
                "type": question_type,
            },
        }


async def example_real_world():
    """Real-world service integration"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Real-World Service Integration")
    print("=" * 80)

    service = QuestionGeneratorService()
    await service.initialize()

    # Generate questions
    topics = [
        ("Matematik", "orta", "multiple_choice"),
        ("Fizik", "zor", "open_ended"),
        ("Matematik", "orta", "multiple_choice"),  # Duplicate - should cache
    ]

    print("Generating questions...\n")

    for i, (topic, difficulty, q_type) in enumerate(topics, 1):
        question = await service.generate_question(topic, difficulty, q_type)
        print(f"{i}. {topic} - {difficulty} - {q_type}")
        print(f"   Question: {question['question']}")
        print()

    # Check stats
    cache = await get_llm_cache()
    stats = await cache.get_stats()
    print("Cache Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Cache Hits:     {stats['cache_hits']}")
    print(f"  Hit Ratio:      {stats['hit_ratio']:.2%}")


# ============================================================================
# Main Runner
# ============================================================================


async def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "KIRO2 LLM CACHE - USAGE EXAMPLES" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        await example_basic_usage()
        await example_decorator()
        await example_turkish_optimization()
        await example_cost_tracking()
        await example_advanced_config()
        await example_real_world()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
