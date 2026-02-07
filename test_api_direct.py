"""Direct API test"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from openai import OpenAI
import asyncio

# Test OpenAI API directly
async def test_openai():
    try:
        # Load from .env
        from dotenv import load_dotenv
        load_dotenv('backend/.env')

        api_key = os.getenv('OPENAI_API_KEY')
        print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )

        print(f"SUCCESS: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_openai())
