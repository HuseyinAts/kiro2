"""
Test script for Learning Path API endpoints
"""
import asyncio

import aiohttp

BASE_URL = "http://localhost:8000"


async def test_api_endpoints():
    """Test all Learning Path API endpoints"""

    print("Testing Learning Path API Endpoints...")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # Test 1: Create Student Profile
        print("\n1. Testing Create Student Profile...")
        print("-" * 30)

        profile_data = {
            "name": "Mehmet",
            "grade": 10,
            "subjects": ["Matematik", "Fizik", "Kimya", "Biyoloji"],
            "goals": ["YKS'de yüksek puan almak", "Tıp fakültesi kazanmak"],
            "learning_style": "visual",
            "available_time": 180,
        }

        async with session.post(
            f"{BASE_URL}/api/learning-path/create-profile", json=profile_data
        ) as response:
            result = await response.json()
            print(f"Status: {response.status}")
            if result.get("success"):
                print(f"Profile created successfully!")
                print(f"Student ID: {result['profile']['student_id']}")
                print(f"Learning Style: {result['profile']['learning_style']}")
                print(f"Knowledge Level: {result['profile']['knowledge_level']}")
                student_id = result["profile"]["student_id"]
            else:
                print(f"Error: {result.get('error')}")
                student_id = None

        # Test 2: Assess Knowledge
        print("\n2. Testing Knowledge Assessment...")
        print("-" * 30)

        if student_id:
            assessment_data = {
                "student_id": student_id,
                "subject": "Matematik",
                "questions": [
                    "Türev nedir?",
                    "İntegral nasıl alınır?",
                    "Limit kavramını açıklayın",
                ],
            }

            async with session.post(
                f"{BASE_URL}/api/learning-path/assess-knowledge", json=assessment_data
            ) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                if result.get("success"):
                    print(f"Knowledge Level: {result['assessment']}")
                else:
                    print(f"Error: {result.get('error')}")

        # Test 3: Create Learning Path
        print("\n3. Testing Create Learning Path...")
        print("-" * 30)

        if student_id:
            path_data = {
                "student_profile": {
                    "student_id": student_id,
                    "name": "Mehmet",
                    "grade": 10,
                    "subjects": ["Matematik"],
                    "goal": "YKS matematik konularını öğrenmek",
                },
                "topic": "Türev ve İntegral",
                "duration_weeks": 6,
            }

            async with session.post(
                f"{BASE_URL}/api/learning-path/create-path", json=path_data
            ) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                if result.get("success"):
                    print(f"Learning Path created!")
                    print(f"Path ID: {result['learning_path']['path_id']}")
                    print(
                        f"Total Time: {result['learning_path']['total_time']} minutes"
                    )
                    print(f"Resources: {len(result['learning_path']['resources'])}")
                    path_id = result["learning_path"]["path_id"]
                else:
                    print(f"Error: {result.get('error')}")
                    path_id = None

        # Test 4: Search Resources
        print("\n4. Testing Resource Search...")
        print("-" * 30)

        search_data = {
            "topic": "Python programlama",
            "learning_style": "visual",
            "level": "beginner",
            "language": "tr",
            "limit": 5,
        }

        async with session.post(
            f"{BASE_URL}/api/learning-path/search-resources", json=search_data
        ) as response:
            result = await response.json()
            print(f"Status: {response.status}")
            if result.get("success"):
                print(f"Found {len(result['resources'])} resources:")
                for i, resource in enumerate(result["resources"][:3], 1):
                    print(f"  {i}. {resource['title']}")
                    print(f"     Type: {resource['type']}")
                    print(f"     Time: {resource['estimated_time']} min")
            else:
                print(f"Error: {result.get('error')}")

        # Test 5: Adapt Learning Path
        print("\n5. Testing Adapt Learning Path...")
        print("-" * 30)

        if path_id:
            adapt_data = {
                "path_id": path_id,
                "progress_data": {
                    "completed_resources": 3,
                    "total_resources": 5,
                    "correct_rate": 0.85,
                    "topics_completed": ["Türev tanımı", "Türev alma kuralları"],
                    "struggle_areas": ["Zincir kuralı"],
                    "average_study_time": 60,
                    "engagement_level": "high",
                },
            }

            async with session.post(
                f"{BASE_URL}/api/learning-path/adapt-path", json=adapt_data
            ) as response:
                result = await response.json()
                print(f"Status: {response.status}")
                if result.get("success"):
                    print(f"Path adapted successfully!")
                    print(
                        f"New Total Time: {result['adapted_path']['total_time']} minutes"
                    )
                    print(f"Resources: {len(result['adapted_path']['resources'])}")
                else:
                    print(f"Error: {result.get('error')}")

        # Test 6: Check API Status
        print("\n6. Testing API Status...")
        print("-" * 30)

        async with session.get(f"{BASE_URL}/") as response:
            result = await response.json()
            print(f"Status: {response.status}")
            print(f"API Status: {result['status']}")
            print(f"Version: {result['version']}")
            print(f"Available Agents: {result['agents']}")
            print(f"Total Endpoints: {len(result['endpoints'])}")

    print("\n" + "=" * 50)
    print("All API tests completed!")


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the backend server is running on http://localhost:8000")
    print()
    asyncio.run(test_api_endpoints())
