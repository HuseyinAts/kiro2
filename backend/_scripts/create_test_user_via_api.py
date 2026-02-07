#!/usr/bin/env python3
"""
Create test user via API call
"""
import requests
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_test_user():
    """Create test user via API"""
    print("🔧 Creating test user via API...")

    # API endpoint
    url = "http://localhost:8000/api/auth/register"

    # Test user data
    user_data = {
        "email": "test@kiro2.com",
        "password": "Test123!",
        "ad": "Test",
        "soyad": "User",
        "rol": "ogrenci"
    }

    try:
        # First, get CSRF token from the server
        session = requests.Session()

        # Try to get CSRF token
        csrf_url = "http://localhost:8000/api/auth/csrf"
        try:
            csrf_response = session.get(csrf_url)
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                csrf_token = csrf_data.get('csrf_token')
                print(f"✅ Got CSRF token: {csrf_token[:20]}...")
                headers = {
                    'X-CSRF-Token': csrf_token,
                    'Content-Type': 'application/json'
                }
            else:
                print("⚠️  No CSRF endpoint found, trying without token...")
                headers = {'Content-Type': 'application/json'}
        except:
            print("⚠️  CSRF fetch failed, trying without token...")
            headers = {'Content-Type': 'application/json'}

        # Make the registration request
        print(f"\n📤 Sending registration request to {url}")
        print(f"   Data: {json.dumps(user_data, indent=2)}")

        response = session.post(url, json=user_data, headers=headers)

        print(f"\n📥 Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        print(f"   Response body: {response.text}")

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"\n{'='*50}")
            print("🎉 Test user created successfully!")
            print(f"{'='*50}")
            print(f"\n📝 Login credentials:")
            print(f"   Email: test@kiro2.com")
            print(f"   Password: Test123!")
            print(f"\n🌐 Test at: http://localhost:3001")
            print(f"{'='*50}\n")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            if 'already exists' in response.text.lower() or 'duplicate' in response.text.lower():
                print(f"\n⚠️  User already exists!")
                print(f"\n📝 Login credentials:")
                print(f"   Email: test@kiro2.com")
                print(f"   Password: Test123!")
                print(f"\n🌐 Test at: http://localhost:3001\n")
                return True
            else:
                print(f"\n❌ Registration failed: {response.text}")
                return False
        else:
            print(f"\n❌ Registration failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend server!")
        print("   Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = create_test_user()
    sys.exit(0 if success else 1)
