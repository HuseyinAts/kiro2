import requests
import json
import sys

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# Test the learning agent with LGS matematik query
url = 'http://localhost:8000/api/chat'
data = {
    'agent': 'learning',
    'message': 'LGS matematik konuları',
    'session_id': 'test-session'
}

try:
    response = requests.post(url, json=data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        print('SUCCESS! Response received:')
        print('=' * 50)
        # Print first 1000 chars to check if we get detailed response
        response_text = result['response']
        print(response_text[:1000] + '...' if len(response_text) > 1000 else response_text)
        print('=' * 50)
        print(f'Response length: {len(response_text)} characters')
        
        # Check if response contains LGS specific content
        if 'LGS' in response_text and 'matematik' in response_text.lower():
            print('\n[CHECK] VERIFIED: Response contains LGS-specific matematik content!')
        else:
            print('\n⚠️ WARNING: Response may not contain LGS-specific content')
    else:
        print(f'Error: Status code {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')