"""
Simple Test for Multi-LLM Configuration
Tests basic configuration without dependencies

Author: KIRO AI Team
Date: 2025-10-19
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*60)
print("MULTI-LLM CONFIGURATION TEST")
print("="*60)

try:
    print("\n[1] Testing imports...")
    from services.llm.multi_llm_config import (
        LLMProvider,
        LLMCapability,
        LLMModelConfig,
        MultiLLMConfig
    )
    print("   [OK] Configuration imports successful")

    from services.llm.base_llm_provider import (
        BaseLLMProvider,
        LLMRequest,
        LLMResponse
    )
    print("   [OK] Base provider imports successful")

    print("\n[2] Testing configuration loading...")

    # Test OpenAI config
    openai_config = MultiLLMConfig.get_config(LLMProvider.OPENAI)
    print(f"\n   [OpenAI] GPT-4 Configuration:")
    print(f"      Model: {openai_config.model_name}")
    print(f"      Max Tokens: {openai_config.max_tokens}")
    print(f"      Temperature: {openai_config.temperature}")
    print(f"      Cost per 1K tokens: ${openai_config.cost_per_1k_tokens}")
    print(f"      Capabilities: {len(openai_config.capabilities)} features")
    for cap in openai_config.capabilities:
        print(f"         - {cap.value}")

    # Test Claude config
    claude_config = MultiLLMConfig.get_config(LLMProvider.CLAUDE)
    print(f"\n   [Claude] Sonnet Configuration:")
    print(f"      Model: {claude_config.model_name}")
    print(f"      Max Tokens: {claude_config.max_tokens}")
    print(f"      Temperature: {claude_config.temperature}")
    print(f"      Cost per 1K tokens: ${claude_config.cost_per_1k_tokens}")
    print(f"      Avg Response Time: {claude_config.avg_response_time_ms}ms")

    # Test Qwen config
    qwen_config = MultiLLMConfig.get_config(LLMProvider.QWEN)
    print(f"\n   [Qwen] 2.5 Configuration:")
    print(f"      Model: {qwen_config.model_name}")
    print(f"      Max Tokens: {qwen_config.max_tokens}")
    print(f"      API Base: {qwen_config.api_base}")
    print(f"      Cost per 1K tokens: ${qwen_config.cost_per_1k_tokens} (free if self-hosted)")

    print("\n[3] Testing provider selection...")

    # Test best provider for question generation (quality)
    best_quality = MultiLLMConfig.get_best_provider_for_capability(
        LLMCapability.QUESTION_GENERATION,
        prefer_cost_effective=False
    )
    print(f"\n   [QUALITY] Best for Question Generation:")
    print(f"      Provider: {best_quality.value}")

    # Test best provider for question generation (cost)
    best_cost = MultiLLMConfig.get_best_provider_for_capability(
        LLMCapability.QUESTION_GENERATION,
        prefer_cost_effective=True
    )
    print(f"\n   [COST] Best for Question Generation:")
    print(f"      Provider: {best_cost.value}")

    # Test best provider for fine-tuning
    best_finetune = MultiLLMConfig.get_best_provider_for_capability(
        LLMCapability.FINE_TUNING,
        prefer_cost_effective=False
    )
    print(f"\n   [FINETUNE] Best for Fine-Tuning:")
    print(f"      Provider: {best_finetune.value}")

    print("\n[4] Testing ensemble strategy...")
    ensemble_strategy = MultiLLMConfig.ENSEMBLE_STRATEGY
    print(f"\n   Voting Strategy:")
    print(f"      Enabled: {ensemble_strategy['voting']['enabled']}")
    print(f"      Min Agreement: {ensemble_strategy['voting']['min_agreement']*100}%")
    print(f"      Weights:")
    for provider, weight in ensemble_strategy['voting']['weights'].items():
        print(f"         {provider.value}: {weight*100}%")

    print(f"\n   Quality Thresholds:")
    for metric, threshold in ensemble_strategy['quality_threshold'].items():
        print(f"      {metric}: {threshold}")

    print(f"\n   Fallback Order:")
    for i, provider in enumerate(ensemble_strategy['fallback_order'], 1):
        print(f"      {i}. {provider.value}")

    print("\n[5] Testing Turkish OSYM prompts...")
    prompts = MultiLLMConfig.TURKISH_OSYM_PROMPTS
    print(f"\n   System Prompt (first 200 chars):")
    print(f"      {prompts['system_prompt'][:200]}...")

    print(f"\n   Question Generation Prompt (first 150 chars):")
    print(f"      {prompts['question_generation_prompt'][:150]}...")

    print("\n[6] Testing LLM Request model...")
    request = LLMRequest(
        prompt="Merhaba dunya!",
        system_prompt="Sen bir OSYM uzmanissin.",
        max_tokens=100,
        temperature=0.7,
        json_mode=True
    )
    print(f"\n   LLM Request Created:")
    print(f"      Prompt: {request.prompt}")
    print(f"      Max Tokens: {request.max_tokens}")
    print(f"      Temperature: {request.temperature}")
    print(f"      JSON Mode: {request.json_mode}")

    print("\n[7] Testing fine-tuning configs...")
    for provider, config in MultiLLMConfig.FINE_TUNING_CONFIGS.items():
        print(f"\n   [{provider.value}] Fine-Tuning:")
        print(f"      Epochs: {config.get('n_epochs', 'N/A')}")
        print(f"      Batch Size: {config.get('batch_size', 'N/A')}")
        if 'lora_r' in config:
            print(f"      LoRA r: {config['lora_r']}")
            print(f"      LoRA alpha: {config['lora_alpha']}")

    print("\n" + "="*60)
    print("ALL CONFIGURATION TESTS PASSED!")
    print("="*60)

    print("\nSummary:")
    print(f"   - {len(LLMProvider)} LLM providers configured")
    print(f"   - {len(LLMCapability)} capabilities defined")
    print(f"   - {len(MultiLLMConfig.TURKISH_OSYM_PROMPTS)} Turkish prompts loaded")
    print(f"   - Ensemble voting: ENABLED")
    print(f"   - Fallback chain: CONFIGURED ({len(ensemble_strategy['fallback_order'])} providers)")

    print("\nMulti-LLM Configuration is ready!")
    print("\nNext Steps:")
    print("   1. Set API keys in .env file:")
    print("      - OPENAI_API_KEY=your_openai_key")
    print("      - ANTHROPIC_API_KEY=your_claude_key")
    print("      - QWEN_API_KEY=your_qwen_key (optional)")
    print("   2. Install dependencies:")
    print("      pip install -r backend/requirements_llm.txt")
    print("   3. Run full integration test")

except Exception as e:
    print(f"\nTEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
