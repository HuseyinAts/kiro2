#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude API Key Test
"""

import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_claude_api():
    print("="*80)
    print("CLAUDE API KEY TEST")
    print("="*80)
    print()

    try:
        import anthropic

        api_key = "[REDACTED_ANTHROPIC_KEY]"

        print("API Key:", api_key[:20] + "..." + api_key[-10:])
        print()
        print("[TEST] Claude API'ye baglaniyor...")

        client = anthropic.Anthropic(api_key=api_key)

        # Basit bir test mesajı
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Merhaba! Sadece 'Test basarili!' diye cevap ver."
                }
            ]
        )

        response = message.content[0].text

        print("[BASARILI] API baglantisi OK!")
        print()
        print("Claude'un Cevabi:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        print()
        print("[OK] API KEY GECERLI! Soru uretmeye hazir!")
        print()
        print("="*80)

        return True

    except Exception as e:
        print(f"[HATA] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_claude_api()
