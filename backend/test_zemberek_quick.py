#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zemberek-NLP Quick Test Script
Fast verification of Zemberek functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_zemberek():
    """Quick Zemberek functionality test"""
    print("=" * 60)
    print("Zemberek-NLP Quick Test")
    print("=" * 60)
    print()

    # Test 1: Import
    print("[1/5] Testing import...")
    try:
        from core.zemberek_service import get_zemberek_service, MorphemeType, POSTag

        print("      OK - Import successful")
    except ImportError as e:
        print(f"      FAIL - Import error: {e}")
        return False

    # Test 2: Initialize service
    print("[2/5] Initializing service...")
    try:
        zemberek = await get_zemberek_service()
        print("      OK - Service initialized")
    except Exception as e:
        print(f"      FAIL - Initialization error: {e}")
        return False

    # Test 3: Check status
    print("[3/5] Checking service status...")
    try:
        stats = await zemberek.get_service_stats()
        print(f"      OK - Initialized: {stats['initialized']}")
        print(f"      OK - Fallback mode: {stats['use_fallback']}")
        if stats["use_fallback"]:
            print(f"      WARNING - Reason: {stats['fallback_reason']}")
    except Exception as e:
        print(f"      FAIL - Status check error: {e}")
        return False

    # Test 4: Morphology analysis
    print("[4/5] Testing morphology analysis...")
    try:
        test_words = ["kitap", "kitaplar", "kitaplarımızdan"]
        for word in test_words:
            analysis = await zemberek.analyze_morphology(word)
            print(f"      OK - {word}")
            print(f"           Stem: {analysis.stem}")
            print(f"           Suffixes: {analysis.suffixes}")
            print(f"           Complexity: {analysis.complexity_score:.2f}")
    except Exception as e:
        print(f"      FAIL - Analysis error: {e}")
        return False

    # Test 5: Tokenization
    print("[5/5] Testing tokenization...")
    try:
        text = "Merhaba dunya! Nasilsiniz?"
        tokens = await zemberek.tokenize(text)
        print(f"      OK - Tokenized: {len(tokens)} tokens")
        for token in tokens[:3]:  # Show first 3
            print(f"           {token.text} (word: {token.is_word})")
    except Exception as e:
        print(f"      FAIL - Tokenization error: {e}")
        return False

    print()
    print("=" * 60)
    print("All tests passed! Zemberek is functional.")
    print("=" * 60)
    return True


async def main():
    """Main test runner"""
    try:
        success = await test_zemberek()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows
    import os

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # Run async test
    asyncio.run(main())
