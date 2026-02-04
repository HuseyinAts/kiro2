"""
Test OSYM Questions API Endpoints
Quick test script to verify API functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_osym_statistics():
    """Test /api/v1/osym/statistics endpoint"""
    print("\n" + "=" * 80)
    print("TEST 1: OSYM Statistics")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/osym/statistics"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("[OK] Statistics endpoint working!")
    else:
        print(f"[ERROR] Failed: {response.text}")


def test_osym_subjects():
    """Test /api/v1/osym/subjects endpoint"""
    print("\n" + "=" * 80)
    print("TEST 2: Available Subjects")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/osym/subjects"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("[OK] Subjects endpoint working!")
    else:
        print(f"[ERROR] Failed: {response.text}")


def test_random_questions():
    """Test /api/v1/osym/random-questions endpoint"""
    print("\n" + "=" * 80)
    print("TEST 3: Random Questions")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/osym/random-questions"
    params = {"exam_type": "TYT", "count": 5, "with_answers": True}

    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Count: {data['count']}")
        print(f"Message: {data['message']}")

        if data["data"]:
            print(f"\nSample Question:")
            q = data["data"][0]
            print(f"  Subject: {q['subject']}")
            print(f"  Difficulty: {q['difficulty']}")
            print(f"  Stem (first 100 chars): {q['stem'][:100]}...")
            print(f"  Options: {list(q['options'].keys())}")
            print(f"  Correct Answer: {q.get('correct_answer', 'N/A')}")

        print("[OK] Random questions endpoint working!")
    else:
        print(f"[ERROR] Failed: {response.text}")


def test_practice_exam():
    """Test /api/v1/osym/practice-exam endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: Practice Exam Generator")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/osym/practice-exam"
    params = {"exam_type": "TYT"}

    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Total Questions: {data['total_questions']}")
        print(f"Message: {data['message']}")

        if "data" in data and "sections" in data["data"]:
            print(f"\nSections:")
            for section in data["data"]["sections"]:
                print(
                    f"  {section['subject']}: {section['actual_count']}/{section['requested_count']} questions"
                )

        print("[OK] Practice exam generator working!")
    else:
        print(f"[ERROR] Failed: {response.text}")


def test_filtered_questions():
    """Test /api/v1/osym/questions with filters"""
    print("\n" + "=" * 80)
    print("TEST 5: Filtered Questions")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/osym/questions"
    params = {"subject": "Matematik", "exam_type": "TYT", "limit": 5}

    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Count: {data['count']}")
        print(f"Message: {data['message']}")

        print("[OK] Filtered questions endpoint working!")
    else:
        print(f"[ERROR] Failed: {response.text}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("OSYM API ENDPOINTS TEST SUITE")
    print("=" * 80)
    print("\nMake sure backend is running on http://localhost:8000")
    print("Press Ctrl+C to cancel\n")

    try:
        # Run all tests
        test_osym_statistics()
        test_osym_subjects()
        test_random_questions()
        test_practice_exam()
        test_filtered_questions()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED!")
        print("=" * 80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to backend at http://localhost:8000")
        print("Please start the backend first: cd backend && uvicorn main:app")
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
