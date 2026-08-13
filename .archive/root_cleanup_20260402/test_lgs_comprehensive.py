import requests
import json
import sys

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# Test different LGS queries
test_queries = [
    "LGS matematik konuları",
    "LGS fen bilimleri konuları",
    "LGS nedir",
    "matematik konuları",
    "8. sınıf matematik müfredatı"
]

url = 'http://localhost:8000/api/chat'

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Testing query: '{query}'")
    print('='*60)

    data = {
        'agent': 'learning',
        'message': query,
        'session_id': f'test-{query.replace(" ", "-")}'
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            response_text = result['response']

            # Show first 300 characters of response
            preview = response_text[:300] + '...' if len(response_text) > 300 else response_text
            print(f"Response preview:\n{preview}")
            print(f"\nResponse length: {len(response_text)} characters")

            # Check response quality
            if len(response_text) > 500:
                print("[CHECK] Detailed response provided")
            else:
                print("⚠️ Response might be too short")

        else:
            print(f"[X] Error: Status code {response.status_code}")

    except Exception as e:
        print(f"[X] Error: {e}")

print(f"\n{'='*60}")
print("All tests completed!")
print('='*60)
