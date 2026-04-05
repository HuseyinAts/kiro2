"""
Test ONLY the Multi-LLM Configuration (no provider dependencies)

Author: KIRO AI Team
Date: 2025-10-19
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*60)
print("MULTI-LLM CONFIGURATION TEST (Config Only)")
print("="*60)

try:
    print("\n[1] Testing configuration imports...")
    from services.llm.multi_llm_config import (
        LLMProvider,
        LLMCapability,
        LLMModelConfig,
        MultiLLMConfig
    )
    print("   [OK] Configuration module imported")

    print("\n[2] Testing base provider models...")
    from services.llm.base_llm_provider import (
        LLMRequest,
        LLMResponse
    )
    print("   [OK] Base models imported")

    print("\n[3] Testing LLM Providers enum...")
    print(f"   Available providers: {len(LLMProvider)} providers")
    for provider in LLMProvider:
        print(f"      - {provider.value}")

    print("\n[4] Testing LLM Capabilities enum...")
    print(f"   Available capabilities: {len(LLMCapability)} capabilities")
    for capability in LLMCapability:
        print(f"      - {capability.value}")

    print("\n[5] Testing OpenAI configuration...")
    openai_config = MultiLLMConfig.get_config(LLMProvider.OPENAI)
    print(f"   Model: {openai_config.model_name}")
    print(f"   Max Tokens: {openai_config.max_tokens}")
    print(f"   Temperature: {openai_config.temperature}")
    print(f"   Top P: {openai_config.top_p}")
    print(f"   Cost per 1K tokens: ${openai_config.cost_per_1k_tokens}")
    print(f"   Avg Response Time: {openai_config.avg_response_time_ms}ms")
    print(f"   Capabilities: {len(openai_config.capabilities)}")
    for cap in openai_config.capabilities:
        cap_val = cap.value if hasattr(cap, 'value') else cap
        print(f"      - {cap_val}")

    print("\n[6] Testing Claude configuration...")
    claude_config = MultiLLMConfig.get_config(LLMProvider.CLAUDE)
    print(f"   Model: {claude_config.model_name}")
    print(f"   Max Tokens: {claude_config.max_tokens}")
    print(f"   Cost per 1K tokens: ${claude_config.cost_per_1k_tokens}")
    print(f"   Avg Response Time: {claude_config.avg_response_time_ms}ms")
    print(f"   Capabilities: {len(claude_config.capabilities)}")

    print("\n[7] Testing Qwen configuration...")
    qwen_config = MultiLLMConfig.get_config(LLMProvider.QWEN)
    print(f"   Model: {qwen_config.model_name}")
    print(f"   Max Tokens: {qwen_config.max_tokens}")
    print(f"   API Base: {qwen_config.api_base}")
    print(f"   Cost per 1K tokens: ${qwen_config.cost_per_1k_tokens}")
    print(f"   Capabilities: {len(qwen_config.capabilities)}")

    print("\n[8] Testing provider selection (Quality priority)...")
    for capability in LLMCapability:
        try:
            best = MultiLLMConfig.get_best_provider_for_capability(
                capability,
                prefer_cost_effective=False
            )
            print(f"   {capability.value:.<35} {best.value}")
        except ValueError:
            print(f"   {capability.value:.<35} Not supported")

    print("\n[9] Testing provider selection (Cost priority)...")
    for capability in LLMCapability:
        try:
            best = MultiLLMConfig.get_best_provider_for_capability(
                capability,
                prefer_cost_effective=True
            )
            print(f"   {capability.value:.<35} {best.value}")
        except ValueError:
            print(f"   {capability.value:.<35} Not supported")

    print("\n[10] Testing ensemble strategy configuration...")
    ensemble = MultiLLMConfig.ENSEMBLE_STRATEGY

    print(f"   Voting enabled: {ensemble['voting']['enabled']}")
    print(f"   Min agreement: {ensemble['voting']['min_agreement']*100}%")
    print(f"   Provider weights:")
    for provider, weight in ensemble['voting']['weights'].items():
        print(f"      {provider.value}: {weight*100:.0f}%")

    print(f"\n   Quality thresholds:")
    for metric, value in ensemble['quality_threshold'].items():
        print(f"      {metric}: {value}")

    print(f"\n   Fallback order:")
    for i, provider in enumerate(ensemble['fallback_order'], 1):
        print(f"      {i}. {provider.value}")

    print("\n[11] Testing fine-tuning configurations...")
    for provider, config in MultiLLMConfig.FINE_TUNING_CONFIGS.items():
        print(f"\n   {provider.value}:")
        for key, value in config.items():
            print(f"      {key}: {value}")

    print("\n[12] Testing Turkish OSYM prompts...")
    prompts = MultiLLMConfig.TURKISH_OSYM_PROMPTS
    print(f"   Prompt templates: {len(prompts)}")
    for key in prompts.keys():
        print(f"      - {key}")

    print(f"\n   System prompt preview:")
    print(f"      {prompts['system_prompt'][:150]}...")

    print("\n[13] Testing LLMRequest model...")
    request = LLMRequest(
        prompt="Test prompt",
        system_prompt="Test system",
        max_tokens=100,
        temperature=0.7,
        top_p=0.9,
        json_mode=True
    )
    print(f"   Prompt: {request.prompt}")
    print(f"   System: {request.system_prompt}")
    print(f"   Max Tokens: {request.max_tokens}")
    print(f"   Temperature: {request.temperature}")
    print(f"   Top P: {request.top_p}")
    print(f"   JSON Mode: {request.json_mode}")

    print("\n[14] Testing LLMResponse model...")
    from datetime import datetime
    response = LLMResponse(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4-turbo",
        content="Test response",
        latency_ms=150.5,
        tokens_used=50,
        cost_usd=0.005,
        timestamp=datetime.now()
    )
    print(f"   Provider: {response.provider}")
    print(f"   Model: {response.model_name}")
    print(f"   Content: {response.content}")
    print(f"   Latency: {response.latency_ms}ms")
    print(f"   Tokens: {response.tokens_used}")
    print(f"   Cost: ${response.cost_usd}")

    print("\n" + "="*60)
    print("ALL CONFIGURATION TESTS PASSED!")
    print("="*60)

    print("\nSummary:")
    print(f"   [OK] {len(LLMProvider)} LLM providers configured")
    print(f"   [OK] {len(LLMCapability)} capabilities defined")
    print(f"   [OK] Ensemble voting strategy configured")
    print(f"   [OK] {len(MultiLLMConfig.FINE_TUNING_CONFIGS)} fine-tuning configs")
    print(f"   [OK] {len(MultiLLMConfig.TURKISH_OSYM_PROMPTS)} Turkish prompts")
    print(f"   [OK] Request/Response models working")

    print("\nConfiguration layer is READY!")
    print("\nNext: Install provider dependencies to test full integration:")
    print("   pip install openai anthropic httpx transformers torch")

except Exception as e:
    print(f"\nTEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
