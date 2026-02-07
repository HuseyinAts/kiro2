"""
Test script for Learning Path Agent
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.learning_path_agent import KnowledgeLevel, LearningPathAgent, LearningStyle


async def test_learning_path_agent():
    """Test Learning Path Agent functionality"""

    print("Testing Learning Path Agent...")
    print("=" * 50)

    # Initialize agent
    agent = LearningPathAgent()

    # Test 1: Analyze Student
    print("\n1. Testing Student Analysis...")
    print("-" * 30)

    student_profile = await agent.analyze_student(
        student_id="student_123",
        initial_data={
            "name": "Ahmet",
            "grade": 9,
            "subjects": ["Matematik", "Fizik", "Kimya"],
            "goal": "YKS'de başarılı olmak ve mühendislik okumak",
            "exam_target": "YKS",
            "available_time": 120,
            "learning_style_preference": "visual",
        },
    )

    print(f"Student Profile Created:")
    print(f"  Name: {student_profile.name}")
    print(f"  Grade: {student_profile.grade}")
    print(f"  Learning Style: {student_profile.learning_style.value}")
    print(f"  Knowledge Level: {student_profile.knowledge_level.value}")
    print(f"  Goal: {student_profile.learning_goal}")

    # Test 2: Create Learning Path
    print("\n2. Testing Learning Path Creation...")
    print("-" * 30)

    # Create learning path using student_id
    learning_path = await agent.create_learning_path(
        student_id="student_123",
        goal="Trigonometri konusunu öğrenmek",
        duration_weeks=4,
    )

    print(f"Learning Path Created:")
    print(f"  Path ID: {learning_path.path_id}")
    print(f"  Student: {learning_path.student_profile.name}")
    print(f"  Total Time: {learning_path.total_time} minutes")
    print(f"  Number of Resources: {len(learning_path.resources)}")
    print(f"  Number of Phases: {len(learning_path.phases)}")
    print(f"  Reasoning: {learning_path.reasoning[:100]}...")

    # Test 3: Search Resources
    print("\n3. Testing Resource Search...")
    print("-" * 30)

    resources = await agent.search_resources(
        topic="Python programlama",
        learning_style=LearningStyle.VISUAL,
        level=KnowledgeLevel.BEGINNER,
        language="tr",
        limit=5,
    )

    print(f"Found {len(resources)} resources:")
    for i, resource in enumerate(resources, 1):
        print(f"{i}. {resource.title}")
        print(f"   Type: {resource.resource_type}")
        print(f"   Duration: {resource.estimated_time} minutes")
        print(f"   Difficulty: {resource.difficulty_level.value}")

    # Test 4: Knowledge Assessment
    print("\n4. Testing Knowledge Assessment...")
    print("-" * 30)

    assessment = await agent.assess_knowledge_level(
        student_id="student_123",
        subject="Matematik",
        test_results={
            "questions": [
                "Trigonometrik fonksiyonları tanımlayabilir misin?",
                "Sin(30°) değeri nedir?",
                "Pisagor teoremi nedir?",
            ],
            "answers": ["Sinüs, kosinüs ve tanjant fonksiyonları", "0.5", "a²+b²=c²"],
            "scores": [90, 100, 100],
        },
    )

    print(f"Knowledge Assessment Result: {assessment.value}")

    # Test 5: Adapt Learning Path
    print("\n5. Testing Learning Path Adaptation...")
    print("-" * 30)

    adapted_path = await agent.adapt_learning_path(
        path_id=learning_path.path_id,  # Use the path_id from the created learning path
        progress_data={
            "correct_rate": 0.7,
            "topics_completed": ["Temel trigonometri"],
            "struggle_areas": ["Trigonometrik denklemler"],
            "average_study_time": 45,
            "engagement_level": "high",
            "completed_resources": 2,
            "total_resources": 5,
        },
    )

    print(f"Adapted Learning Path:")
    print(f"  Path ID: {adapted_path.path_id}")
    print(f"  Total Time: {adapted_path.total_time} minutes")
    print(f"  Number of Resources: {len(adapted_path.resources)}")
    print(f"  Number of Phases: {len(adapted_path.phases)}")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_learning_path_agent())
