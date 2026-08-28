import aiohttp
import asyncio
import json

async def test_endpoint():
    url = "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud"

    # Test with Turkish content
    prompt = """### System:
Sen Türkiye'deki öğrenciler için kişiselleştirilmiş öğrenme planları oluşturan bir eğitim asistanısın. Öğrenci dostu, anlaşılır ve motive edici bir dil kullan.

### User:
Merhaba, Python öğrenmek istiyorum

### Assistant:"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "return_full_text": False
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_endpoint())
