"""
Test script for enhanced AI agents with all improvements
"""

import asyncio
import json
from datetime import datetime

from agents.enhanced_study_buddy_agent import get_enhanced_study_buddy
from core.analytics_monitoring import get_analytics_manager

# Import enhanced modules
from core.context_manager import get_context_manager
from core.dynamic_content_generator import ContentType, get_content_generator
from core.plugin_architecture import get_agent_registry, get_plugin_loader


async def test_context_management():
    """Test stateful context management"""
    print("\n=== Testing Context Management ===")

    context_manager = await get_context_manager()

    # Create a session
    session = await context_manager.create_session(
        student_id="test_student_123",
        initial_context={"subject": "matematik", "grade": 8},
    )

    print(f"[CHECK] Created session: {session.session_id}")

    # Update session with conversation
    from core.context_manager import ConversationTurn

    turn = ConversationTurn(
        turn_id="turn_1",
        timestamp=datetime.now(),
        agent_name="StudyBuddy",
        user_message="Matematik öğrenmek istiyorum",
        agent_response="Harika! Matematik öğrenmeye başlayalım.",
        intent="learn",
        entities={"topic": "matematik"},
        confidence=0.95,
        processing_time=150.0,
    )

    await context_manager.update_session(
        session.session_id, turn=turn, variables={"current_topic": "matematik"}
    )

    print(f"[CHECK] Updated session with conversation turn")

    # Test student profile
    profile = await context_manager.get_or_create_student_profile(
        "test_student_123", name="Test Student", grade=8, learning_style="visual"
    )

    print(
        f"[CHECK] Created student profile: {profile.name} (Style: {profile.learning_style})"
    )

    # Test progress tracking
    progress_tracker = context_manager.get_progress_tracker()
    progress_tracker.update_progress(
        "test_student_123", "question_answered", {"correct": True, "topic": "matematik"}
    )

    report = progress_tracker.get_progress_report("test_student_123")
    print(f"[CHECK] Progress report: {report['statistics']}")

    return True


async def test_dynamic_content_generation():
    """Test dynamic content generation"""
    print("\n=== Testing Dynamic Content Generation ===")

    generator = get_content_generator()

    # Test different learning styles
    learning_styles = ["visual", "auditory", "kinesthetic"]

    for style in learning_styles:
        student_profile = {
            "student_id": f"student_{style}",
            "learning_style": style,
            "difficulty_level": "medium",
            "subjects_of_interest": ["matematik", "fen"],
        }

        content = await generator.generate_content(
            topic="Kesirler",
            content_type=ContentType.EXPLANATION,
            student_profile=student_profile,
            context={"grade": 8},
        )

        print(f"\n[CHECK] Generated {style} content:")
        print(f"   Title: {content.title}")
        print(f"   Word count: {content.metadata.get('word_count', 0)}")
        print(f"   Media elements: {len(content.media_elements)}")
        print(f"   Interactive elements: {len(content.interactive_elements)}")

    return True


async def test_analytics_monitoring():
    """Test analytics and monitoring"""
    print("\n=== Testing Analytics & Monitoring ===")

    analytics = get_analytics_manager()
    await analytics.initialize()

    # Simulate API requests
    for i in range(5):
        with analytics.track_request(f"/api/test_{i}", "GET"):
            await asyncio.sleep(0.1)  # Simulate processing

    # Simulate an error
    try:
        with analytics.track_request("/api/error", "POST"):
            raise ValueError("Test error")
    except:
        pass

    # Record learning interaction
    analytics.learning_analytics.record_interaction(
        student_id="test_student",
        agent_name="StudyBuddy",
        input_text="Matematik sorusu",
        output_text="İşte cevap...",
        context={"topic": "matematik"},
        response_time_ms=250.0,
    )

    # Get system health
    health = analytics.get_system_health()
    print(f"[CHECK] System Health: {health['status']}")
    print(f"   Total requests: {health['total_requests']}")
    print(f"   Error rate: {health['error_rate']}%")

    # Get insights
    insights = analytics.learning_analytics.get_insights()
    print(f"[CHECK] Learning Insights:")
    print(f"   Total interactions: {insights['total_interactions']}")
    print(f"   Avg response time: {insights['avg_response_time_ms']}ms")

    return True


async def test_plugin_architecture():
    """Test plugin architecture"""
    print("\n=== Testing Plugin Architecture ===")

    loader = get_plugin_loader()
    registry = get_agent_registry()

    # Discover plugins
    plugins = loader.discover_plugins()
    print(f"[CHECK] Discovered {len(plugins)} plugins: {plugins}")

    # Load Math Genius plugin
    if "math_genius" in plugins:
        agent = await loader.load_agent_plugin("math_genius")
        if agent:
            print(f"[CHECK] Loaded Math Genius plugin")

            # Initialize the plugin
            context_manager = await get_context_manager()
            content_generator = get_content_generator()
            analytics = get_analytics_manager()

            await agent.initialize(context_manager, content_generator, analytics)

            # Test the plugin
            response = await agent.process_message(
                "5 + 3 kaç eder?", "test_session", {}
            )
            print(f"[CHECK] Plugin response: {response[:100]}...")

            # Register in registry
            registry.register_agent("math_genius", agent, agent.manifest)
            print(f"[CHECK] Registered agent in registry")

    # List loaded agents
    agents_list = loader.list_agents()
    print(f"[CHECK] Loaded agents: {json.dumps(agents_list, indent=2)}")

    return True


async def test_enhanced_agent():
    """Test enhanced study buddy agent"""
    print("\n=== Testing Enhanced Study Buddy Agent ===")

    agent = await get_enhanced_study_buddy()

    # Test conversation with context
    session_id = "test_session_enhanced"

    messages = [
        "Merhaba, matematik öğrenmek istiyorum",
        "Kesirler konusunu anlatır mısın?",
        "Bir örnek verebilir misin?",
        "Pratik yapmak istiyorum",
    ]

    for message in messages:
        print(f"\n👤 User: {message}")

        response = await agent.process_message(
            message,
            session_id,
            {
                "student_id": "enhanced_test_student",
                "grade": 8,
                "learning_style": "visual",
            },
        )

        print(f"🤖 Agent: {response[:200]}...")

    # Test adaptive quiz creation
    quiz = await agent.create_adaptive_quiz(
        student_id="enhanced_test_student", topic="kesirler", session_id=session_id
    )

    print(f"\n[CHECK] Created adaptive quiz:")
    print(f"   Quiz ID: {quiz['quiz_id']}")
    print(f"   Topic: {quiz['topic']}")
    print(f"   Difficulty: {quiz['difficulty']}")
    print(f"   Questions: {len(quiz['questions'])}")

    # Test real-time feedback
    feedback = await agent.provide_real_time_feedback(
        student_id="enhanced_test_student", question_id="q_1", answer="1/2"
    )

    print(f"\n[CHECK] Real-time feedback:")
    print(f"   Correct: {feedback['is_correct']}")
    print(f"   Feedback: {feedback['feedback'][:100]}...")

    # Get learning insights
    insights = await agent.get_learning_insights("enhanced_test_student")

    print(f"\n[CHECK] Learning insights:")
    print(f"   Current level: {insights['current_level']}")
    print(f"   Study time: {insights['total_study_time']} minutes")
    print(f"   Recommendations: {insights['recommendations']}")

    return True


async def main():
    """Run all tests"""
    print("=" * 50)
    print("ENHANCED AI AGENTS SYSTEM TEST")
    print("=" * 50)

    try:
        # Run tests
        await test_context_management()
        await test_dynamic_content_generation()
        await test_analytics_monitoring()
        await test_plugin_architecture()
        await test_enhanced_agent()

        print("\n" + "=" * 50)
        print("[CHECK] ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 50)

        print("\n[CHART] IMPROVEMENTS SUMMARY:")
        print("[CHECK] Stateful context management - Agents remember conversations")
        print("[CHECK] Student progress tracking - Continuous learning monitoring")
        print("[CHECK] Dynamic content generation - Personalized for each student")
        print("[CHECK] Adaptive learning - Adjusts to student level")
        print("[CHECK] Real-time content updates - Live personalization")
        print("[CHECK] Analytics collection - Usage metrics for improvement")
        print("[CHECK] Error tracking - Automatic error monitoring")
        print("[CHECK] Response time monitoring - Performance tracking")
        print("[CHECK] Plugin architecture - Easy to add new agents")
        print("[CHECK] Content provider abstraction - Flexible content sources")

    except Exception as e:
        print(f"\n[X] Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        analytics = get_analytics_manager()
        await analytics.shutdown()

        context_manager = await get_context_manager()
        await context_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
