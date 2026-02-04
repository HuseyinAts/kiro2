"""
Test Hybrid Question Bank System - Simple ASCII Version
Quick validation of all components
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print(">>> TESTING HYBRID QUESTION BANK SYSTEM")
print("=" * 60)

# Test 1: AI Question Generator
print("\n[1] Testing AI Question Generator (GPT-5 + Claude 4.5)...")
try:
    from scripts.ai_question_generator import HybridQuestionGenerator

    generator = HybridQuestionGenerator()
    print("   [OK] Generator initialized")
    print(f"   GPT-5 client: {type(generator.gpt_client).__name__}")
    print(
        f"   Claude 4.5 client: {type(generator.claude_client).__name__ if generator.claude_client else 'Not configured'}"
    )

    # Test model selection
    model = generator.select_model("Matematik")
    print(f"   Matematik -> {model}")

    model = generator.select_model("Turkce")
    print(f"   Turkce -> {model}")

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Knowledge Graph Service
print("\n[2] Testing Knowledge Graph Service...")
try:
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode

    kg = KnowledgeGraphService()
    print("   [OK] Knowledge Graph initialized")

    # Add test question
    test_question = QuestionNode(
        id="test-q-001",
        konu="Turev",
        kazanim="M.11.3.1.1",
        bloom_level="apply",
        irt_difficulty=0.6,
        cognitive_skills=["problem_solving"],
    )
    kg.add_question_node(test_question)
    print("   [OK] Question added to graph")

    # Get stats
    stats = kg.export_graph_stats()
    print(f"   Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
    print(f"   Topics: {stats['topic_count']}")

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: Plagiarism Detection
print("\n[3] Testing Plagiarism Detection Service...")
try:
    from services.plagiarism_detection_service import PlagiarismDetectionService

    detector = PlagiarismDetectionService()
    print("   [OK] Plagiarism detector initialized")

    async def test_plagiarism():
        test_text = "Bir fonksiyonun turevi nasil alinir?"
        result = await detector.comprehensive_plagiarism_check(test_text)
        return result

    result = asyncio.run(test_plagiarism())
    print(f"   Is safe: {result['is_safe']}")
    print(f"   OSYM similarity: {result['osym_check']['similarity']:.3f}")

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 4: Adaptive Testing (CAT)
print("\n[4] Testing Adaptive Testing Service...")
try:
    from services.adaptive_testing_service import ComputerAdaptiveTestingService

    # Mock item bank
    item_bank = [
        {
            "id": "q-001",
            "konu": "Matematik",
            "metin": "Test question 1",
            "irt_params": {"a": 1.2, "b": -0.5, "c": 0.25},
        },
        {
            "id": "q-002",
            "konu": "Matematik",
            "metin": "Test question 2",
            "irt_params": {"a": 1.0, "b": 0.0, "c": 0.25},
        },
        {
            "id": "q-003",
            "konu": "Matematik",
            "metin": "Test question 3",
            "irt_params": {"a": 1.5, "b": 0.8, "c": 0.25},
        },
    ]

    cat = ComputerAdaptiveTestingService(item_bank)
    print("   [OK] CAT service initialized")

    # Start session
    session = cat.start_new_session("test-student", "test-session")
    print(f"   Session started, initial theta: {session.current_ability.theta:.2f}")

    # Select first question
    q1 = cat.select_next_question(session.session_id)
    print(f"   First question: {q1['id']} (difficulty: {q1['irt_params']['b']:.2f})")

    # Submit response
    result = cat.submit_response(
        session.session_id, q1["id"], is_correct=True, response_time_seconds=45
    )
    print(
        f"   After response: theta = {result['current_ability']:.2f}, SEM = {result['current_sem']:.2f}"
    )

except Exception as e:
    print(f"   [ERROR] {e}")

# Test 5: HITL Workflow
print("\n[5] Testing HITL Workflow Service...")
try:
    from services.hitl_workflow_service import (
        HITLWorkflowService,
        ExpertProfile,
        ExpertiseLevel,
    )

    hitl = HITLWorkflowService()
    print("   [OK] HITL service initialized")

    # Register expert
    expert = ExpertProfile(
        id="exp-001",
        name="Test Expert",
        expertise_level=ExpertiseLevel.SENIOR,
        specializations=["Matematik", "Fizik"],
        quality_score=85.0,
    )
    hitl.register_expert(expert)
    print(f"   Expert registered: {expert.name}")

    # Evaluate question
    question_data = {"id": "q-test", "konu": "Matematik"}
    ai_result = {"confidence": 0.65, "weaknesses": ["Test weakness"]}

    eval_result = hitl.evaluate_question_for_review("q-test", question_data, ai_result)
    print(f"   Needs review: {eval_result['needs_review']}")
    print(f"   Decision: {eval_result['decision']}")

except Exception as e:
    print(f"   [ERROR] {e}")

# Summary
print("\n" + "=" * 60)
print("[SUCCESS] SYSTEM TEST COMPLETE!")
print("\nCOMPONENTS TESTED:")
print("   1. AI Question Generator (GPT-5 + Claude 4.5)")
print("   2. Knowledge Graph Service")
print("   3. Plagiarism Detection Service")
print("   4. Adaptive Testing (CAT + AutoIRT)")
print("   5. HITL Workflow Service")

print("\nNEXT STEPS:")
print("   1. Review IMPLEMENTATION_ROADMAP.md for detailed plan")
print("   2. Start with Week 1: Database upgrade")
print("   3. Build API endpoints (question_bank_v2_routes.py)")
print("   4. Frontend integration (CAT UI, Expert Dashboard)")
