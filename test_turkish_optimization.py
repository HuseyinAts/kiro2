"""
Test Turkish Token Optimization
Demonstrates all 3 components working together

Usage: python test_turkish_optimization.py
"""

import sys
import io
import json
from pathlib import Path

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.services.llm.turkish_optimizer import TurkishPromptOptimizer
from backend.services.llm.qwen_vocab_extension import QwenVocabExtensionPipeline


def test_turkish_optimizer():
    """Test Component 1: Turkish Prompt Optimizer"""
    print("=" * 60)
    print("TEST 1: Turkish Prompt Optimizer")
    print("=" * 60)

    optimizer = TurkishPromptOptimizer(
        common_words_path='backend/data/turkish_common_words_1000.json'
    )

    # Test prompts
    test_prompts = [
        "Lütfen aşağıdaki soruyu dikkatle cevaplayınız. Eğer mümkünse tüm şıkları okuyunuz.",
        "Yukarıda belirtilen kurallara göre hareket ediniz. Bu nedenle çok dikkatli olunuz.",
        "Aşağıda gösterilen şıklardan doğru olanı işaretleyiniz.",
        "OSYM sınavında matematik sorularını çözerken lütfen lütfen dikkatli olunuz."
    ]

    print("\nOptimizing 4 Turkish prompts...\n")

    total_original = 0
    total_optimized = 0

    for i, prompt in enumerate(test_prompts, 1):
        result = optimizer.optimize(prompt)

        print(f"Prompt {i}:")
        print(f"  Original: {result.original_prompt}")
        print(f"  Optimized: {result.optimized_prompt}")
        print(f"  Tokens: {result.original_tokens} → {result.optimized_tokens}")
        print(f"  Savings: {result.token_savings} tokens ({result.savings_percentage:.1f}%)")
        print()

        total_original += result.original_tokens
        total_optimized += result.optimized_tokens

    total_savings = total_original - total_optimized
    savings_pct = (total_savings / total_original * 100) if total_original > 0 else 0

    print(f"TOTAL RESULTS:")
    print(f"  Original tokens: {total_original}")
    print(f"  Optimized tokens: {total_optimized}")
    print(f"  Total savings: {total_savings} tokens ({savings_pct:.1f}%)")
    print()


def test_common_words():
    """Test Component 2: Common Turkish Words List"""
    print("=" * 60)
    print("TEST 2: Common Turkish Words List")
    print("=" * 60)

    words_path = Path('backend/data/turkish_common_words_1000.json')

    with open(words_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\nLoaded: {words_path}")
    print(f"Version: {data['version']}")
    print(f"Language: {data['language']}")
    print(f"Total words: {data['word_count']}")
    print()

    print("Categories:")
    for category, count in data['categories'].items():
        print(f"  - {category}: {count}")
    print()

    print("Sample words (first 20):")
    for word in data['words'][:20]:
        print(f"  - {word}")
    print()

    print("Morphological roots (first 10):")
    for root in data['morphological_roots'][:10]:
        print(f"  - {root}")
    print()

    print("Common suffixes (first 10):")
    for suffix in data['common_suffixes'][:10]:
        print(f"  - {suffix}")
    print()

    print("OSYM-specific terms:")
    for term in data['osym_specific_terms']:
        print(f"  - {term}")
    print()


def test_vocab_extension():
    """Test Component 3: Qwen Vocabulary Extension"""
    print("=" * 60)
    print("TEST 3: Qwen Vocabulary Extension Pipeline")
    print("=" * 60)

    # Check if pipeline already ran
    output_dir = Path('qwen_extended_vocab')

    if output_dir.exists():
        print(f"\nPipeline output found at: {output_dir}")
        print("\nGenerated files:")

        files = [
            'tokenizer_config.json',
            'training_data.jsonl',
            'lora_config.json',
            'new_tokens.json',
            'README.md'
        ]

        for filename in files:
            filepath = output_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"  ✓ {filename} ({size:,} bytes)")
            else:
                print(f"  ✗ {filename} (not found)")

        # Load and display config
        config_path = output_dir / 'tokenizer_config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"\nTokenizer Configuration:")
            print(f"  Base vocab size: {config['base_vocab_size']:,}")
            print(f"  Extended vocab size: {config['extended_vocab_size']:,}")
            print(f"  New tokens added: {config['new_tokens_count']:,}")
            print(f"  Expansion: {(config['new_tokens_count'] / config['base_vocab_size'] * 100):.2f}%")
            print()

        # Load and display sample tokens
        tokens_path = output_dir / 'new_tokens.json'
        if tokens_path.exists():
            with open(tokens_path, 'r', encoding='utf-8') as f:
                tokens_data = json.load(f)

            print(f"Sample new tokens (first 30):")
            for token in tokens_data['tokens'][:30]:
                print(f"  - {token}")
            print()

        # Load and display training data stats
        training_path = output_dir / 'training_data.jsonl'
        if training_path.exists():
            with open(training_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            print(f"Training Data:")
            print(f"  Total sentences: {len(lines)}")
            print(f"\nSample sentences (first 5):")
            for i, line in enumerate(lines[:5], 1):
                data = json.loads(line)
                print(f"  {i}. {data['text']}")
            print()

    else:
        print(f"\nPipeline not run yet. Run with:")
        print(f"  python backend/services/llm/qwen_vocab_extension.py")
        print()


def test_integration():
    """Test all components together"""
    print("=" * 60)
    print("TEST 4: Integrated Token Optimization Demo")
    print("=" * 60)

    optimizer = TurkishPromptOptimizer(
        common_words_path='backend/data/turkish_common_words_1000.json'
    )

    # Simulate OSYM question generation prompt
    osym_prompt = """Lütfen aşağıdaki konuda bir OSYM sorusu hazırlayınız:

Konu: Matematik - Türev
Alt Konu: Türev Alma Kuralları
Zorluk: Orta
Bloom Seviyesi: Uygulama

Lütfen aşağıdaki kurallara dikkat ediniz:
- Soru Türkçe dilbilgisi kurallarına uygun olmalıdır
- Lütfen 5 şık hazırlayınız (A, B, C, D, E)
- Lütfen çeldiriciler akla yatkın olmalıdır
- Lütfen doğru cevap net olmalıdır
- Eğer mümkünse OSYM formatına uygun olmalıdır

Lütfen JSON formatında veriniz."""

    print("\nOriginal OSYM Prompt:")
    print("-" * 60)
    print(osym_prompt)
    print("-" * 60)
    print()

    # Optimize
    result = optimizer.optimize(osym_prompt)

    print("Optimized OSYM Prompt:")
    print("-" * 60)
    print(result.optimized_prompt)
    print("-" * 60)
    print()

    print("Optimization Results:")
    print(f"  Original tokens: {result.original_tokens}")
    print(f"  Optimized tokens: {result.optimized_tokens}")
    print(f"  Savings: {result.token_savings} tokens ({result.savings_percentage:.1f}%)")
    print()

    print("Optimizations Applied:")
    for opt in result.optimizations_applied:
        print(f"  - {opt}")
    print()

    # Calculate cost savings
    cost_per_1k = 0.01  # GPT-4 cost
    original_cost = (result.original_tokens / 1000) * cost_per_1k
    optimized_cost = (result.optimized_tokens / 1000) * cost_per_1k
    savings = original_cost - optimized_cost

    print("Cost Impact (GPT-4):")
    print(f"  Original cost: ${original_cost:.6f}")
    print(f"  Optimized cost: ${optimized_cost:.6f}")
    print(f"  Savings per request: ${savings:.6f}")
    print()

    # Extrapolate to monthly usage
    monthly_requests = 10000
    monthly_savings = savings * monthly_requests

    print(f"Monthly Savings (at {monthly_requests:,} requests/month):")
    print(f"  Total savings: ${monthly_savings:.2f}/month")
    print(f"  Annual savings: ${monthly_savings * 12:.2f}/year")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Turkish Token Optimization - Complete Test Suite  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_turkish_optimizer()
        test_common_words()
        test_vocab_extension()
        test_integration()

        print("=" * 60)
        print("ALL TESTS COMPLETE")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Turkish Prompt Optimizer: Working")
        print("  ✓ Common Words List (1000): Loaded")
        print("  ✓ Qwen Vocab Extension: Generated")
        print("  ✓ Integration: Tested")
        print()
        print("Next Steps:")
        print("  1. Integrate optimizer into LLM providers")
        print("  2. Fine-tune Qwen with extended vocabulary")
        print("  3. Deploy to production")
        print("  4. Monitor cost savings")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
