"""
Test Hybrid Question Bank System
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
    print("   ✅ Generator initialized")
    print(f"   📊 GPT-5 client: {type(generator.gpt_client).__name__}")
    print(
        f"   📊 Claude 4.5 client: {type(generator.claude_client).__name__ if generator.claude_client else 'Not configured'}"
    )

    # Test model selection
    model = generator.select_model("Matematik")
    print(f"   🤖 Matematik → {model}")

    model = generator.select_model("Türkçe")
    print(f"   🤖 Türkçe → {model}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Knowledge Graph Service
print("\n2️⃣ Testing Knowledge Graph Service...")
try:
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode

    kg = KnowledgeGraphService()
    print("   ✅ Knowledge Graph initialized")

    # Add test question
    test_question = QuestionNode(
        id="test-q-001",
        konu="Türev",
        kazanim="M.11.3.1.1",
        bloom_level="apply",
        irt_difficulty=0.6,
        cognitive_skills=["problem_solving"],
    )
    kg.add_question_node(test_question)
    print("   ✅ Question added to graph")

    # Get stats
    stats = kg.export_graph_stats()
    print(f"   📊 Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
    print(f"   📊 Topics: {stats['topic_count']}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Plagiarism Detection
print("\n3️⃣ Testing Plagiarism Detection Service...")
try:
    from services.plagiarism_detection_service import PlagiarismDetectionService

    detector = PlagiarismDetectionService()
    print("   ✅ Plagiarism detector initialized")

    async def test_plagiarism():
        test_text = "Bir fonksiyonun türevi nasıl alınır?"
        result = await detector.comprehensive_plagiarism_check(test_text)
        return result

    result = asyncio.run(test_plagiarism())
    print(f"   📊 Is safe: {result['is_safe']}")
    print(f"   📊 ÖSYM similarity: {result['osym_check']['similarity']:.3f}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Adaptive Testing (CAT)
print("\n4️⃣ Testing Adaptive Testing Service...")
try:
    from services.adaptive_testing_service import (
        ComputerAdaptiveTestingService,
        IRTParameters,
    )

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
    print("   ✅ CAT service initialized")

    # Start session
    session = cat.start_new_session("test-student", "test-session")
    print(f"   📊 Session started, initial θ: {session.current_ability.theta:.2f}")

    # Select first question
    q1 = cat.select_next_question(session.session_id)
    print(f"   📊 First question: {q1['id']} (difficulty: {q1['irt_params']['b']:.2f})")

    # Submit response
    result = cat.submit_response(
        session.session_id, q1["id"], is_correct=True, response_time_seconds=45
    )
    print(
        f"   📊 After response: θ = {result['current_ability']:.2f}, SEM = {result['current_sem']:.2f}"
    )

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: HITL Workflow
print("\n5️⃣ Testing HITL Workflow Service...")
try:
    from services.hitl_workflow_service import (
        HITLWorkflowService,
        ExpertProfile,
        ExpertiseLevel,
    )

    hitl = HITLWorkflowService()
    print("   ✅ HITL service initialized")

    # Register expert
    expert = ExpertProfile(
        id="exp-001",
        name="Test Expert",
        expertise_level=ExpertiseLevel.SENIOR,
        specializations=["Matematik", "Fizik"],
        quality_score=85.0,
    )
    hitl.register_expert(expert)
    print(f"   📊 Expert registered: {expert.name}")

    # Evaluate question
    question_data = {"id": "q-test", "konu": "Matematik"}
    ai_result = {"confidence": 0.65, "weaknesses": ["Test weakness"]}

    eval_result = hitl.evaluate_question_for_review("q-test", question_data, ai_result)
    print(f"   📊 Needs review: {eval_result['needs_review']}")
    print(f"   📊 Decision: {eval_result['decision']}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Generate Real Question (with actual API)
print("\n6️⃣ Testing REAL Question Generation...")
print("   ⚠️  This will use actual API credits (~ $0.04)")
choice = input("   Continue? (y/n): ")

if choice.lower() == "y":
    try:

        async def generate_real_question():
            generator = HybridQuestionGenerator()

            print("   🔄 Generating with GPT-5...")
            question = await generator.generate_question(
                konu="Matematik",
                alt_konu="Türev",
                kazanim="Türev kurallarını kullanarak fonksiyonların türevini alabilme",
                zorluk="medium",
                bloom_level="apply",
            )
            return question

        result = asyncio.run(generate_real_question())

        if "error" not in result:
            print("   ✅ Question generated successfully!")
            print(f"   📝 Model used: {result.get('ai_model', 'unknown')}")
            print(f"   📝 Question preview: {result.get('metin', '')[:100]}...")
            print(f"   📝 Options: {len(result.get('secenekler', {}))} choices")
        else:
            print(f"   ❌ Generation failed: {result['error']}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
else:
    print("   ⏭️  Skipped real API test")

# Summary
print("\n" + "=" * 60)
print("✅ SYSTEM TEST COMPLETE!")
print("\n📊 COMPONENTS TESTED:")
print("   1. AI Question Generator (GPT-5 + Claude 4.5)")
print("   2. Knowledge Graph Service")
print("   3. Plagiarism Detection Service")
print("   4. Adaptive Testing (CAT + AutoIRT)")
print("   5. HITL Workflow Service")
print("   6. Real API Integration")

print("\n🚀 NEXT STEPS:")
print("   1. Review IMPLEMENTATION_ROADMAP.md for detailed plan")
print("   2. Start with Week 1: Database upgrade")
print("   3. Build API endpoints (question_bank_v2_routes.py)")
print("   4. Frontend integration (CAT UI, Expert Dashboard)")
print(
    "\n💡 TIP: See ADVANCED_QUESTION_BANK_SYSTEM_ARCHITECTURE.md for architecture details"
)
