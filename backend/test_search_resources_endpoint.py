"""
Test script for /api/learning-path/search-resources endpoint
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient

# Import main app
try:
    from main import app
except ImportError:
    from backend.main import app

client = TestClient(app)


def test_search_resources_basic():
    """Test basic search-resources endpoint"""
    print("\n=== Test 1: Basic Search ===")

    response = client.post(
        "/api/learning-path/search-resources",
        json={
            "subject": "matematik",
            "topic": "türev",
            "difficulty": "orta",
            "max_results": 5,
        },
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total Resources: {data.get('total')}")
        print(f"Engine: {data.get('metadata', {}).get('engine')}")

        if data.get("resources"):
            print(f"\nFirst Resource:")
            first_resource = data["resources"][0]
            print(f"  Title: {first_resource.get('title')}")
            print(f"  Channel: {first_resource.get('channel_name')}")
            print(
                f"  Turkish Score: {first_resource.get('scores', {}).get('turkish_score')}"
            )
            print(
                f"  Relevance Score: {first_resource.get('scores', {}).get('relevance_score')}"
            )
            print(
                f"  Final Score: {first_resource.get('scores', {}).get('final_score')}"
            )
    else:
        print(f"Error: {response.text}")


def test_search_resources_without_topic():
    """Test search without specific topic"""
    print("\n=== Test 2: Search Without Topic ===")

    response = client.post(
        "/api/learning-path/search-resources",
        json={"subject": "fizik", "difficulty": "kolay", "max_results": 3},
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total Resources: {data.get('total')}")
    else:
        print(f"Error: {response.text}")


def test_search_resources_validation():
    """Test validation - missing subject"""
    print("\n=== Test 3: Validation (Missing Subject) ===")

    response = client.post(
        "/api/learning-path/search-resources",
        json={"topic": "atom", "difficulty": "orta"},
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_search_resources_with_profile():
    """Test search with student profile"""
    print("\n=== Test 4: Search With Student Profile ===")

    response = client.post(
        "/api/learning-path/search-resources",
        json={
            "subject": "kimya",
            "topic": "atom",
            "difficulty": "zor",
            "max_results": 5,
            "student_profile": {"grade": 11, "learning_style": "visual"},
        },
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total Resources: {data.get('total')}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing /api/learning-path/search-resources Endpoint")
    print("=" * 60)

    try:
        test_search_resources_basic()
        test_search_resources_without_topic()
        test_search_resources_validation()
        test_search_resources_with_profile()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
