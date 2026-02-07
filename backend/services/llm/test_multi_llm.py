"""
Test Script for Multi-LLM Integration
Tests OpenAI, Claude, Qwen, and Ensemble Manager

Author: KIRO AI Team
Date: 2025-10-19
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from services.llm import (
    LLMProvider,
    LLMRequest,
    LLMCapability,
    MultiLLMConfig,
    MultiLLMEnsembleManager,
)


async def test_configuration():
    """Test 1: Configuration Loading"""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)

    try:
        # Test OpenAI config
        openai_config = MultiLLMConfig.get_config(LLMProvider.OPENAI)
        print("✅ OpenAI Config:")
        print(f"   Model: {openai_config.model_name}")
        print(f"   Max Tokens: {openai_config.max_tokens}")
        print(f"   Cost per 1K: ${openai_config.cost_per_1k_tokens}")
        print(f"   Capabilities: {len(openai_config.capabilities)}")

        # Test Claude config
        claude_config = MultiLLMConfig.get_config(LLMProvider.CLAUDE)
        print("\n✅ Claude Config:")
        print(f"   Model: {claude_config.model_name}")
        print(f"   Max Tokens: {claude_config.max_tokens}")
        print(f"   Cost per 1K: ${claude_config.cost_per_1k_tokens}")

        # Test Qwen config
        qwen_config = MultiLLMConfig.get_config(LLMProvider.QWEN)
        print("\n✅ Qwen Config:")
        print(f"   Model: {qwen_config.model_name}")
        print(f"   Max Tokens: {qwen_config.max_tokens}")
        print(f"   Cost per 1K: ${qwen_config.cost_per_1k_tokens}")

        # Test best provider selection
        best_for_generation = MultiLLMConfig.get_best_provider_for_capability(
            LLMCapability.QUESTION_GENERATION, prefer_cost_effective=False
        )
        print(
            f"\n✅ Best provider for question generation (quality): {best_for_generation.value}"
        )

        best_for_generation_cost = MultiLLMConfig.get_best_provider_for_capability(
            LLMCapability.QUESTION_GENERATION, prefer_cost_effective=True
        )
        print(
            f"✅ Best provider for question generation (cost): {best_for_generation_cost.value}"
        )

        print("\n✅ Configuration test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Configuration test FAILED: {e}")
        return False


async def test_ensemble_initialization():
    """Test 2: Ensemble Manager Initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: Ensemble Manager Initialization")
    print("=" * 60)

    try:
        # Check environment variables
        print("\n🔍 Checking API keys...")
        openai_key = os.getenv("OPENAI_API_KEY")
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        qwen_key = os.getenv("QWEN_API_KEY")

        print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
        print(f"   Claude API Key: {'✅ Set' if claude_key else '❌ Not set'}")
        print(
            f"   Qwen API Key: {'✅ Set (optional)' if qwen_key else '⚠️  Not set (will use local)'}"
        )

        # Initialize ensemble manager
        print("\n🚀 Initializing Ensemble Manager...")

        # Only enable providers with valid API keys
        manager = MultiLLMEnsembleManager(
            enable_openai=bool(openai_key),
            enable_claude=bool(claude_key),
            enable_qwen=False,  # Disable Qwen for now (requires large model download)
            qwen_use_local=False,
        )

        print(
            f"\n✅ Ensemble Manager initialized with {len(manager.providers)} provider(s)"
        )
        print(f"   Active providers: {[p.value for p in manager.providers.keys()]}")

        # Test health check
        print("\n🏥 Running health checks...")
        health_status = await manager.check_health_all()

        for provider, is_healthy in health_status.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"   {provider.value}: {status}")

        return manager

    except Exception as e:
        print(f"\n❌ Ensemble initialization FAILED: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_simple_generation(manager: MultiLLMEnsembleManager):
    """Test 3: Simple Text Generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Simple Text Generation")
    print("=" * 60)

    try:
        # Create simple test request
        request = LLMRequest(
            prompt="Merhaba! 'Türkiye' kelimesini kullanarak kısa bir cümle yaz.",
            max_tokens=50,
            temperature=0.7,
        )

        print("\n📝 Prompt:", request.prompt)
        print("\n🤖 Generating with fallback strategy...")

        # Test with fallback
        response = await manager.generate_with_fallback(request)

        print("\n✅ Response received:")
        print(f"   Provider: {response.provider.value}")
        print(f"   Model: {response.model_name}")
        print(f"   Latency: {response.latency_ms:.2f}ms")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_usd:.4f}")
        print(f"\n   Content: {response.content}")

        return True

    except Exception as e:
        print(f"\n❌ Simple generation FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_osym_question_generation(manager: MultiLLMEnsembleManager):
    """Test 4: ÖSYM Question Generation"""
    print("\n" + "=" * 60)
    print("TEST 4: ÖSYM Question Generation")
    print("=" * 60)

    try:
        print("\n📚 Generating ÖSYM question...")
        print("   Topic: Matematik")
        print("   Subtopic: Türev")
        print("   Difficulty: 0.5 (Medium)")
        print("   Bloom Level: 3 (Application)")
        print("   Exam Type: TYT")

        # Generate question
        question = await manager.generate_osym_question_ensemble(
            topic="Matematik",
            subtopic="Türev Alma Kuralları",
            difficulty=0.5,
            bloom_level=3,
            exam_type="TYT",
            use_voting=False,
        )

        print("\n✅ Question generated successfully:")
        print(f"\n📋 Stem: {question.get('stem', 'N/A')[:200]}...")
        print("\n🔤 Options:")
        for i, option in enumerate(question.get("options", [])[:5]):
            marker = "✓" if i == question.get("correct_answer", -1) else " "
            print(f"   [{marker}] {chr(65+i)}) {option[:100]}...")

        print(f"\n💡 Explanation: {question.get('explanation', 'N/A')[:150]}...")
        print(f"\n🏷️  Keywords: {', '.join(question.get('keywords', [])[:5])}")
        print(f"⏱️  Estimated Time: {question.get('estimated_time_seconds', 90)}s")

        return True

    except Exception as e:
        print(f"\n❌ ÖSYM question generation FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_ensemble_voting(manager: MultiLLMEnsembleManager):
    """Test 5: Ensemble Voting"""
    print("\n" + "=" * 60)
    print("TEST 5: Ensemble Voting Strategy")
    print("=" * 60)

    if len(manager.providers) < 2:
        print("\n⚠️  Skipping: Need at least 2 providers for ensemble voting")
        return True

    try:
        request = LLMRequest(
            prompt="'Yapay zeka' terimini tek bir cümleyle açıkla.",
            max_tokens=50,
            temperature=0.7,
        )

        print("\n📝 Prompt:", request.prompt)
        print("\n🤖 Generating with ensemble voting...")

        response = await manager.generate_with_ensemble(
            request, strategy="majority_voting"
        )

        print("\n✅ Ensemble voting completed:")
        print(f"   Selected Provider: {response.provider.value}")
        print(f"   Latency: {response.latency_ms:.2f}ms")
        print(f"   Cost: ${response.cost_usd:.4f}")
        print(f"\n   Content: {response.content}")

        # Show all provider metrics
        print("\n📊 Provider Metrics:")
        all_metrics = manager.get_metrics_all()
        for provider, metrics in all_metrics.items():
            print(f"\n   {provider.value}:")
            print(f"      Total Requests: {metrics['total_requests']}")
            print(f"      Total Tokens: {metrics['total_tokens']}")
            print(f"      Total Cost: ${metrics['total_cost_usd']:.4f}")
            print(f"      Avg Latency: {metrics['avg_latency_ms']:.2f}ms")

        return True

    except Exception as e:
        print(f"\n❌ Ensemble voting FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 MULTI-LLM INTEGRATION TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Configuration
    result1 = await test_configuration()
    results.append(("Configuration", result1))

    # Test 2: Ensemble Initialization
    manager = await test_ensemble_initialization()
    results.append(("Ensemble Init", manager is not None))

    if manager is None:
        print("\n❌ Cannot proceed without Ensemble Manager")
        return

    # Test 3: Simple Generation
    result3 = await test_simple_generation(manager)
    results.append(("Simple Generation", result3))

    # Test 4: ÖSYM Question Generation
    result4 = await test_osym_question_generation(manager)
    results.append(("ÖSYM Question Gen", result4))

    # Test 5: Ensemble Voting
    result5 = await test_ensemble_voting(manager)
    results.append(("Ensemble Voting", result5))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name:.<40} {status}")

    print(f"\n   Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")


if __name__ == "__main__":
    asyncio.run(main())
