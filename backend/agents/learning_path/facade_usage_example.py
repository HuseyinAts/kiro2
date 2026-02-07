"""
LearningPathFacade Usage Examples
Teknofest 2025 - Eğitim Eylemci Projesi

This file demonstrates how to use the LearningPathFacade
for various learning path operations.
"""

import asyncio
from agents.learning_path import (
    LearningPathFacade,
    get_learning_path_facade,
    KnowledgeLevel,
)
from agents.learning_path.services.path_adaptation import PerformanceMetrics


async def example_create_learning_path():
    """Example: Create a learning path for a student."""
    facade = get_learning_path_facade()

    # Create path for matematik
    result = await facade.create_path_for_student(
        student_id="student-123",
        subject="matematik",
        topics=["türev", "integral", "limit"],
        target_level=KnowledgeLevel.INTERMEDIATE,
        max_duration_hours=20,
    )

    if result.success:
        print(f"✓ Path created: {result.path.path_id}")
        print(f"  Total duration: {result.total_duration_minutes} minutes")
        print(f"  Number of nodes: {len(result.nodes)}")
    else:
        print(f"✗ Error: {result.error}")


async def example_search_resources():
    """Example: Search for learning resources."""
    facade = get_learning_path_facade()

    # Search for türev resources
    resources = await facade.search_resources(
        query="türev",
        subject="matematik",
        difficulty_range=(-2.0, 2.0),
        limit=5,
        platforms=["YouTube", "Khan Academy"],
    )

    print(f"Found {len(resources)} resources:")
    for resource in resources:
        print(f"  - {resource.title} ({resource.source})")
        print(f"    Duration: {resource.estimated_time} min")
        print(f"    Difficulty: {resource.difficulty_level.value}")


async def example_adapt_path():
    """Example: Adapt a learning path based on performance."""
    facade = get_learning_path_facade()

    # Student performance data
    performance = [
        PerformanceMetrics(
            topic="türev",
            quiz_score=85.0,
            completion_time_minutes=45,
            attempts=1,
            resources_viewed=3,
        ),
        PerformanceMetrics(
            topic="integral",
            quiz_score=55.0,  # Struggling
            completion_time_minutes=90,
            attempts=3,
            resources_viewed=5,
        ),
    ]

    # Adapt the path
    result = await facade.adapt_student_path(
        student_id="student-123",
        performance=performance,
    )

    if result.success:
        print(f"✓ Path adapted")
        print(f"  Actions taken: {len(result.actions_taken)}")
        for action in result.actions_taken:
            print(f"    - {action.type.value}: {action.description}")
    else:
        print(f"✗ Error: {result.message}")


async def example_chat_interaction():
    """Example: Process chat messages."""
    facade = get_learning_path_facade()

    # Student asks about progress
    response = await facade.process_chat(
        student_id="student-123",
        message="İlerleme durumum nedir?",
        session_id="session-456",
    )

    print(f"Intent: {response.intent.value}")
    print(f"Response: {response.text}")

    if response.suggestions:
        print("Suggestions:")
        for suggestion in response.suggestions:
            print(f"  - {suggestion}")


async def example_form_submission():
    """Example: Submit student profile form."""
    facade = get_learning_path_facade()

    # Get the form definition
    form = facade.get_profile_form()
    print(f"Form: {form.title}")
    print(f"Fields: {len(form.fields)}")

    # Submit form data
    form_data = {
        "name": "Ahmet Yılmaz",
        "grade": "12",
        "exam_target": "YKS-TYT",
        "learning_goal": "Matematik temeli güçlendirmek",
        "available_time": "240",  # 4 hours in minutes
        "learning_style": "visual",
        "interests": ["matematik", "fizik"],
    }

    result = await facade.submit_profile_form(
        student_id="student-123",
        form_data=form_data,
    )

    if result.success:
        print(f"✓ Profile created for {result.profile.name}")
    else:
        print(f"✗ Validation errors: {result.errors}")


async def example_progress_tracking():
    """Example: Track student progress."""
    facade = get_learning_path_facade()

    # Get progress summary
    progress = await facade.get_progress("student-123")

    if progress["has_path"]:
        print(f"Path: {progress['path_id']}")
        print(f"Goal: {progress['goal']}")
        print(f"Total resources: {progress['total_resources']}")
        print(f"Phases: {progress['phases_count']}")
    else:
        print("No active path found")

    # Mark a resource as complete
    success = await facade.mark_resource_complete(
        student_id="student-123",
        resource_id="resource-456",
    )

    if success:
        print("✓ Resource marked complete")


async def example_facade_statistics():
    """Example: Get facade statistics."""
    facade = get_learning_path_facade()

    stats = facade.get_stats()

    print("Facade Statistics:")
    print(f"  Cached paths: {stats['cached_paths']}")
    print(f"  Cached profiles: {stats['cached_profiles']}")
    print("  Services initialized:")
    for service, initialized in stats['services_initialized'].items():
        status = "✓" if initialized else "✗"
        print(f"    {status} {service}")


async def example_cache_management():
    """Example: Manage facade cache."""
    facade = get_learning_path_facade()

    # Check initial state
    stats = facade.get_stats()
    print(f"Cached paths: {stats['cached_paths']}")

    # Clear cache
    facade.clear_cache()
    print("Cache cleared")

    # Verify
    stats = facade.get_stats()
    print(f"Cached paths after clear: {stats['cached_paths']}")


async def example_dependency_injection():
    """Example: Use dependency injection for testing."""
    # Mock services for testing
    from unittest.mock import Mock

    mock_path_service = Mock()
    mock_resource_service = Mock()

    # Inject mock services
    facade = LearningPathFacade(
        path_generation=mock_path_service,
        resource_discovery=mock_resource_service,
    )

    # Now the facade will use the mock services
    print("Facade created with mock services for testing")


async def run_all_examples():
    """Run all examples sequentially."""
    print("=" * 60)
    print("LearningPathFacade Usage Examples")
    print("=" * 60)

    examples = [
        ("Create Learning Path", example_create_learning_path),
        ("Search Resources", example_search_resources),
        ("Adapt Path", example_adapt_path),
        ("Chat Interaction", example_chat_interaction),
        ("Form Submission", example_form_submission),
        ("Progress Tracking", example_progress_tracking),
        ("Facade Statistics", example_facade_statistics),
        ("Cache Management", example_cache_management),
        ("Dependency Injection", example_dependency_injection),
    ]

    for title, example_func in examples:
        print(f"\n{'=' * 60}")
        print(f"Example: {title}")
        print(f"{'=' * 60}")
        try:
            await example_func()
        except Exception as e:
            print(f"Error: {e}")

    print(f"\n{'=' * 60}")
    print("All examples completed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
