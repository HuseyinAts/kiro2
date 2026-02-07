#!/usr/bin/env python3
"""Simple login test - writes response to file"""
import requests
import json

# Test login with English "password" field (frontend format)
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "test@kiro2.com", "password": "Test123!"},
    headers={"Content-Type": "application/json"}
)

# Write response to file
with open("login_response.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, indent=2, ensure_ascii=False)

print("Status Code:", response.status_code)
print("Response written to login_response.json")

# Print response keys
data = response.json()
print("\nResponse keys:", list(data.keys()))

# Check for frontend fields
if "success" in data:
    print("  - success: YES")
if "token" in data:
    print("  - token: YES")
if "refreshToken" in data:
    print("  - refreshToken: YES")
if "user" in data:
    print("  - user: YES")
    print("    - user.rol:", data["user"].get("rol"))
