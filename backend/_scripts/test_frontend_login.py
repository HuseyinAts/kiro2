#!/usr/bin/env python3
"""
Test login endpoint with frontend-compatible request format
Tests with ENGLISH field name 'password' (not Turkish 'sifre')
"""
import requests
import json

def test_login_with_password_field():
    """Test login using English 'password' field (frontend format)"""
    print("="*60)
    print("FRONTEND-COMPATIBLE LOGIN TEST")
    print("="*60)

    # Frontend sends { email: string, password: string }
    payload = {
        "email": "test@kiro2.com",
        "password": "Test123!"  # English field name
    }

    print(f"\n[REQUEST]")
    print(f"URL: http://localhost:8000/api/v1/auth/login")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"\n[RESPONSE]")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            data = response.json()
            print(f"\n{'='*60}")
            print(f"✅ LOGIN SUCCESSFUL")
            print(f"{'='*60}")
            print(f"Success: {data.get('success')}")
            print(f"Token: {data.get('token', '')[:20]}...")
            print(f"Refresh Token: {data.get('refreshToken', '')[:20]}...")
            if 'user' in data:
                user = data['user']
                print(f"User ID: {user.get('id')}")
                print(f"Email: {user.get('email')}")
                print(f"Role: {user.get('rol')}")
            return True
        else:
            print(f"\n{'='*60}")
            print(f"❌ LOGIN FAILED")
            print(f"{'='*60}")
            return False

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}")
        return False


def test_login_with_sifre_field():
    """Test login using Turkish 'sifre' field (backend format)"""
    print("\n" + "="*60)
    print("BACKEND-COMPATIBLE LOGIN TEST (Turkish field)")
    print("="*60)

    # Backend also accepts { email: string, sifre: string }
    payload = {
        "email": "test@kiro2.com",
        "sifre": "Test123!"  # Turkish field name
    }

    print(f"\n[REQUEST]")
    print(f"URL: http://localhost:8000/api/v1/auth/login")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"\n[RESPONSE]")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            print(f"\n✅ LOGIN SUCCESSFUL (Turkish field)")
            return True
        else:
            print(f"\n❌ LOGIN FAILED (Turkish field)")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Test both formats
    result1 = test_login_with_password_field()
    result2 = test_login_with_sifre_field()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"English 'password' field: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Turkish 'sifre' field: {'✅ PASS' if result2 else '❌ FAIL'}")
    print("="*60)
