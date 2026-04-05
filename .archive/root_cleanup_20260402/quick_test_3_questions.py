"""Hızlı 3 soru testi"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.llm.claude_provider import ClaudeProvider
from services.llm.multi_llm_config import MultiLLMConfig

async def test():
    print("Testing Claude soru uretimi...")
    provider = ClaudeProvider(MultiLLMConfig.CLAUDE_CONFIG)

    for i in range(1, 4):
        print(f"\n[{i}/3] Generating...", end=" ")
        try:
            result = await provider.create_osym_question(
                topic="Matematik",
                subtopic="Sayilar",
                difficulty=0.5,
                bloom_level=2,
                exam_type="TYT"
            )
            print(f"OK")
            print(f"  Stem: {result['stem'][:80]}...")
            print(f"  Options: {len(result['options'])}")
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\nTest complete!")

asyncio.run(test())
