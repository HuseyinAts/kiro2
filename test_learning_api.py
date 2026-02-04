import requests
import json

# Test learning path API
url = "http://localhost:8000/api/learning-path/create-profile"

payload = {
    "name": "Test Öğrenci",
    "grade": 8,
    "subjects": ["Matematik", "Fen Bilgisi"],
    "goals": ["LGS'ye hazırlanmak", "Matematik notumu yükseltmek"],
    "learning_style": "visual",
    "available_time": 120
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

# Test learning path creation
if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        student_id = result["profile"]["student_id"]
        
        # Create learning path
        path_url = "http://localhost:8000/api/learning-path/create-path"
        path_payload = {
            "student_profile": {
                "student_id": student_id
            },
            "topic": "LGS Matematik Hazırlık",
            "duration_weeks": 4
        }
        
        try:
            path_response = requests.post(path_url, json=path_payload, headers=headers)
            print(f"\nLearning Path Status: {path_response.status_code}")
            print(f"Learning Path: {json.dumps(path_response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Learning Path Error: {e}")