"""
LLM Ensemble Debug - OpenAI ve Claude İş Bölümü Analizi
"""
import sys
import os
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv('backend/.env')

# Force load API keys
backend_env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
with open(backend_env_path, 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            key = line.strip().split('=', 1)[1]
            os.environ['OPENAI_API_KEY'] = key
            print(f"[INFO] OpenAI Key: {key[:20]}...")
        elif line.startswith('ANTHROPIC_API_KEY='):
            key = line.strip().split('=', 1)[1]
            os.environ['ANTHROPIC_API_KEY'] = key
            print(f"[INFO] Claude Key: {key[:20]}...")

from services.llm.ensemble_manager import MultiLLMEnsembleManager
from services.llm.openai_provider import OpenAIProvider
from services.llm.claude_provider import ClaudeProvider
from services.llm.multi_llm_config import LLMProvider


async def test_openai_direct():
    """OpenAI provider'ı direkt test et"""
    print("\n" + "="*80)
    print("TEST 1: OpenAI Direct Test")
    print("="*80)

    try:
        from services.llm.multi_llm_config import MultiLLMConfig
        provider = OpenAIProvider(MultiLLMConfig.OPENAI_CONFIG)

        result = await provider.create_osym_question(
            topic="Matematik",
            subtopic="Sayılar",
            difficulty=0.5,
            bloom_level=2,
            exam_type="TYT"
        )

        print(f"[OK] OpenAI SUCCESS")
        print(f"     Stem length: {len(result.get('stem', ''))} chars")
        print(f"     Options: {len(result.get('options', []))}")
        print(f"     First 100 chars: {result.get('stem', '')[:100]}...")
        return True, result

    except Exception as e:
        print(f"[ERROR] OpenAI FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_claude_direct():
    """Claude provider'ı direkt test et"""
    print("\n" + "="*80)
    print("TEST 2: Claude Direct Test")
    print("="*80)

    try:
        from services.llm.multi_llm_config import MultiLLMConfig
        provider = ClaudeProvider(MultiLLMConfig.CLAUDE_CONFIG)

        result = await provider.create_osym_question(
            topic="Matematik",
            subtopic="Sayılar",
            difficulty=0.5,
            bloom_level=2,
            exam_type="TYT"
        )

        print(f"[OK] Claude SUCCESS")
        print(f"     Stem length: {len(result.get('stem', ''))} chars")
        print(f"     Options: {len(result.get('options', []))}")
        print(f"     First 100 chars: {result.get('stem', '')[:100]}...")
        return True, result

    except Exception as e:
        print(f"[ERROR] Claude FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_ensemble():
    """Ensemble manager test et"""
    print("\n" + "="*80)
    print("TEST 3: Ensemble Manager Test")
    print("="*80)

    try:
        ensemble = MultiLLMEnsembleManager()

        result = await ensemble.generate_osym_question_ensemble(
            topic="Matematik",
            subtopic="Sayılar",
            difficulty=0.5,
            bloom_level=2,
            exam_type="TYT",
            use_voting=True
        )

        print(f"[OK] Ensemble SUCCESS")
        print(f"     Result: {result.get('stem', '')[:100]}...")
        return True, result

    except Exception as e:
        print(f"[ERROR] Ensemble FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def analyze_ensemble_workflow():
    """OpenAI ve Claude iş bölümünü analiz et"""
    print("\n" + "="*80)
    print("ANALYSIS: OpenAI ve Claude İş Bölümü")
    print("="*80)

    from services.llm.multi_llm_config import MultiLLMConfig

    print("\n[1] VOTING WEIGHTS:")
    weights = MultiLLMConfig.ENSEMBLE_STRATEGY["voting"]["weights"]
    for provider, weight in weights.items():
        print(f"     {provider.value:15s}: {weight:.2f}")

    print("\n[2] FALLBACK ORDER:")
    fallback = MultiLLMConfig.ENSEMBLE_STRATEGY["fallback_order"]
    for i, provider in enumerate(fallback, 1):
        print(f"     {i}. {provider.value}")

    print("\n[3] PROVIDER CAPABILITIES:")
    print("     OpenAI GPT-4:")
    openai_config = MultiLLMConfig.OPENAI_CONFIG
    print(f"       Model: {openai_config.model}")
    print(f"       Cost/1K: Input ${openai_config.pricing_per_1k_input}, Output ${openai_config.pricing_per_1k_output}")
    print(f"       Max tokens: {openai_config.max_tokens}")

    print("\n     Claude Sonnet:")
    claude_config = MultiLLMConfig.CLAUDE_CONFIG
    print(f"       Model: {claude_config.model}")
    print(f"       Cost/1K: Input ${claude_config.pricing_per_1k_input}, Output ${claude_config.pricing_per_1k_output}")
    print(f"       Max tokens: {claude_config.max_tokens}")

    print("\n[4] ENSEMBLE WORKFLOW:")
    print("     1. Tüm provider'lar (OpenAI, Claude) paralel çalışır")
    print("     2. Her provider async olarak soru üretir")
    print("     3. Başarılı sonuçlar toplanır")
    print("     4. Voting strategy ile en iyi sonuç seçilir:")
    print("        - majority_voting: Ağırlıklı skorlama")
    print("        - cost_optimized: Kalite korunarak en ucuz")
    print("        - latency_optimized: Kalite korunarak en hızlı")

    print("\n[5] SORUN TESPİTİ:")
    print("     Şu an generate_osym_question_ensemble() fonksiyonunda:")
    print("     - Line 376-377: 'All providers failed' hatası alınıyor")
    print("     - Bu, TÜM provider'ların exception döndüğü anlamına geliyor")
    print("     - Her provider'ın create_osym_question() methodu çağrılıyor")
    print("     - Başarılı sonuç (dict with 'stem') bulunamıyor")


async def test_provider_methods():
    """Provider method'larını detaylı test et"""
    print("\n" + "="*80)
    print("TEST 4: Provider Method Inspection")
    print("="*80)

    from services.llm.multi_llm_config import MultiLLMConfig

    # OpenAI
    print("\n[OpenAI Provider Methods]")
    try:
        provider = OpenAIProvider(MultiLLMConfig.OPENAI_CONFIG)
        methods = [m for m in dir(provider) if not m.startswith('_')]
        print(f"     Methods: {', '.join(methods)}")

        if hasattr(provider, 'create_osym_question'):
            print(f"     [OK] create_osym_question EXISTS")
        else:
            print(f"     [ERROR] create_osym_question MISSING!")

    except Exception as e:
        print(f"     [ERROR] Cannot initialize: {e}")

    # Claude
    print("\n[Claude Provider Methods]")
    try:
        provider = ClaudeProvider(MultiLLMConfig.CLAUDE_CONFIG)
        methods = [m for m in dir(provider) if not m.startswith('_')]
        print(f"     Methods: {', '.join(methods)}")

        if hasattr(provider, 'create_osym_question'):
            print(f"     [OK] create_osym_question EXISTS")
        else:
            print(f"     [ERROR] create_osym_question MISSING!")

    except Exception as e:
        print(f"     [ERROR] Cannot initialize: {e}")


async def main():
    print("=" * 80)
    print("   LLM ENSEMBLE DEBUG & ANALYSIS")
    print("=" * 80)

    results = {}

    # Test individual providers
    results['openai'] = await test_openai_direct()
    results['claude'] = await test_claude_direct()

    # Test ensemble
    results['ensemble'] = await test_ensemble()

    # Analyze workflow
    await analyze_ensemble_workflow()

    # Inspect methods
    await test_provider_methods()

    # Summary
    print("\n" + "=" * 80)
    print("   SUMMARY")
    print("=" * 80)
    print(f"\nOpenAI Direct:  {'[OK]' if results['openai'][0] else '[FAIL]'}")
    print(f"Claude Direct:  {'[OK]' if results['claude'][0] else '[FAIL]'}")
    print(f"Ensemble:       {'[OK]' if results['ensemble'][0] else '[FAIL]'}")

    if results['openai'][0] and results['claude'][0]:
        print("\n[DIAGNOSIS] Her iki provider da çalışıyor ama ensemble başarısız.")
        print("            generate_osym_question_ensemble() içinde bir sorun var.")
        print("            Lines 360-377 incelenmeli.")
    elif not results['openai'][0] and not results['claude'][0]:
        print("\n[DIAGNOSIS] HİÇBİR provider çalışmıyor.")
        print("            API key veya network sorunu olabilir.")
    else:
        working = 'OpenAI' if results['openai'][0] else 'Claude'
        print(f"\n[DIAGNOSIS] Sadece {working} çalışıyor.")
        print(f"            Diğer provider debug edilmeli.")

    # Save detailed report
    report_file = f"llm_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'openai': {
                'success': results['openai'][0],
                'result': str(results['openai'][1])[:200] if results['openai'][0] else results['openai'][1]
            },
            'claude': {
                'success': results['claude'][0],
                'result': str(results['claude'][1])[:200] if results['claude'][0] else results['claude'][1]
            },
            'ensemble': {
                'success': results['ensemble'][0],
                'result': str(results['ensemble'][1])[:200] if results['ensemble'][0] else results['ensemble'][1]
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVE] Detailed report: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
