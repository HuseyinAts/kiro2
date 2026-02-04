import requests
import json

url = "http://localhost:8000/api/chat"

# Test chat API
payload = {
    "agent": "learning",
    "message": "Öğrenme planı oluştur",
    "session_id": "test-session-123"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")