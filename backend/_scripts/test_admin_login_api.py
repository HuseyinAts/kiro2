#!/usr/bin/env python3
"""
Admin login API testi
"""
import requests
import json

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"

CREDENTIALS = {
    "email": "admin@turkiyesinav.com",
    "password": "admin123"
}

def test_login():
    """Test login endpoint"""
    print("Testing login endpoint...")
    print(f"URL: {LOGIN_URL}")
    print(f"Credentials: {CREDENTIALS}")
    print()

    try:
        # Send login request
        response = requests.post(
            LOGIN_URL,
            json=CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            data = response.json()
            print("[OK] Login SUCCESSFUL!")
            print()
            print("Response:")
            print(json.dumps(data, indent=2))
        else:
            print("[ERROR] Login FAILED!")
            print()
            print("Response:")
            print(response.text)

    except Exception as e:
        print(f"[ERROR] Request failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()
