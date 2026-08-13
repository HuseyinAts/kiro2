#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test API Question Endpoints"""

import requests
import json
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_api():
    """Test the question API endpoints"""
    base_url = "http://localhost:8000"

    print("="*60)
    print("TESTING KIRO2 API ENDPOINTS")
    print("="*60)

    # Test 1: Health check
    print("\n1. Testing API health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️ Health check returned: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Please start the backend server:")
        print("   cd backend && py main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

    # Test 2: Get questions endpoint
    print("\n2. Testing questions endpoint...")
    endpoints = [
        "/api/v1/questions",
        "/api/v1/questions/list",
        "/api/questions",
        "/questions"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint {endpoint} works!")
                if isinstance(data, list):
                    print(f"   Found {len(data)} questions")
                elif isinstance(data, dict) and 'items' in data:
                    print(f"   Found {len(data['items'])} questions")
                elif isinstance(data, dict) and 'questions' in data:
                    print(f"   Found {len(data['questions'])} questions")
                break
            elif response.status_code == 404:
                continue
            else:
                print(f"   {endpoint}: Status {response.status_code}")
        except Exception as e:
            continue

    # Test 3: Search questions
    print("\n3. Testing question search...")
    search_endpoints = [
        "/api/v1/questions/search",
        "/api/questions/search",
        "/questions/search"
    ]

    for endpoint in search_endpoints:
        try:
            params = {
                "exam_type": "TYT",
                "limit": 5
            }
            response = requests.get(f"{base_url}{endpoint}", params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Search endpoint {endpoint} works!")
                break
        except:
            continue

    print("\n" + "="*60)
    print("API test complete!")
    print("="*60)
    return True

if __name__ == "__main__":
    # First, let's check if the backend is configured to use SQLite
    import sqlite3

    print("\n📊 Current database status:")
    conn = sqlite3.connect('turkiye_sinav.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions')
    total = cursor.fetchone()[0]
    print(f"   SQLite database has {total} questions")
    conn.close()

    # Test the API
    test_api()
