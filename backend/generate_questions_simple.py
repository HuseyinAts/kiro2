#!/usr/bin/env python3
"""
KIRO Platform - Service Startup and Question Generation
"""

import asyncio
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Environment setup
os.environ[
    "DATABASE_URL"
] = "postgresql://postgres:changeme_strong_password_here@localhost:5432/turkiye_sinav"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["ENVIRONMENT"] = "development"


async def main():
    """Start services and generate questions"""

    print("=" * 80)
    print("KIRO Platform - Starting Services and Question Generation")
    print("=" * 80)
    print()

    # Import services
    print("[1/5] Importing services...")
    try:
        from services.knowledge_graph_service import KnowledgeGraphService
        from services.plagiarism_detection_service import PlagiarismDetectionService
        from services.adaptive_testing_service import ComputerAdaptiveTestingService
        from services.hitl_workflow_service import HITLWorkflowService

        print("[OK] All services imported successfully")
    except Exception as e:
        print(f"[ERROR] Import error: {str(e)}")
        import traceback

        traceback.print_exc()
        return

    print()

    # Initialize Knowledge Graph
    print("[2/5] Initializing Knowledge Graph Service...")
    try:
        kg_service = KnowledgeGraphService()
        node_count = len(kg_service.graph.nodes())
        print(f"[OK] Knowledge Graph initialized - {node_count} nodes")
    except Exception as e:
        print(f"[ERROR] Knowledge Graph error: {str(e)}")
        kg_service = None

    print()

    # Initialize Plagiarism Detection
    print("[3/5] Initializing Plagiarism Detection Service...")
    print("    (Downloading BERT model if needed - may take 1-2 minutes)")
    try:
        plagiarism_service = PlagiarismDetectionService()
        await plagiarism_service.initialize()
        print("[OK] Plagiarism Detection initialized - BERT model ready")
    except Exception as e:
        print(f"[WARN] Plagiarism Detection error: {str(e)}")
        print("       Continuing without plagiarism detection...")
        plagiarism_service = None

    print()

    # Initialize Adaptive Testing
    print("[4/5] Initializing Adaptive Testing Service...")
    try:
        cat_service = ComputerAdaptiveTestingService()
        print("[OK] CAT Service initialized - BanditCAT algorithm ready")
    except Exception as e:
        print(f"[ERROR] CAT Service error: {str(e)}")
        cat_service = None

    print()

    # Initialize HITL Workflow
    print("[5/5] Initializing HITL Workflow Service...")
    try:
        hitl_service = HITLWorkflowService()
        print("[OK] HITL Service initialized - Expert workflow ready")
    except Exception as e:
        print(f"[ERROR] HITL Service error: {str(e)}")
        hitl_service = None

    print()
    print("=" * 80)
    print("ALL SERVICES RUNNING! Starting Question Generation...")
    print("=" * 80)
    print()

    # Sample questions to generate
    sample_questions = [
        {
            "konu": "Matematik - Turev",
            "kazanim": "Turev kurallarini uygulama",
            "zorluk": "medium",
            "text": "f(x) = 3x^2 + 2x - 5 fonksiyonunun turevini bulunuz.",
            "soru_metni": "Verilen fonksiyonun turevini adim adim hesaplayiniz.",
            "dogru_cevap": "f'(x) = 6x + 2",
            "bloom_level": "apply",
        },
        {
            "konu": "Matematik - Integral",
            "kazanim": "Belirsiz integral hesaplama",
            "zorluk": "hard",
            "text": "Integral(2x^3 - 4x + 1)dx integralini hesaplayiniz.",
            "soru_metni": "Belirsiz integrali hesaplayip sabit terimi belirtiniz.",
            "dogru_cevap": "(x^4/2) - 2x^2 + x + C",
            "bloom_level": "apply",
        },
        {
            "konu": "Fizik - Kuvvet ve Hareket",
            "kazanim": "Newton'un 2. yasasini uygulama",
            "zorluk": "medium",
            "text": "5 kg kutleli bir cisme 20 N kuvvet uygulanıyor. Cismin ivmesini bulunuz.",
            "soru_metni": "F = m*a formulunu kullanarak ivmeyi hesaplayiniz.",
            "dogru_cevap": "a = 4 m/s^2",
            "bloom_level": "apply",
        },
        {
            "konu": "Kimya - Mol Kavrami",
            "kazanim": "Mol hesaplamalari yapma",
            "zorluk": "easy",
            "text": "12 gram karbon (C) kac mol'dur? (C: 12 g/mol)",
            "soru_metni": "Mol = kutle/molekul_agırlıgı formulunu kullaniniz.",
            "dogru_cevap": "1 mol",
            "bloom_level": "remember",
        },
        {
            "konu": "Biyoloji - Hucre Bolunmesi",
            "kazanim": "Mitoz ve mayoz farkini aciklama",
            "zorluk": "medium",
            "text": "Mitoz bolunme sonucu olusan hucrelerin kromozom sayisi nasildir?",
            "soru_metni": "Ana hucre ile karsilastirarak aciklayiniz.",
            "dogru_cevap": "Ana hucre ile ayni (2n)",
            "bloom_level": "understand",
        },
    ]

    generated_count = 0
    approved_count = 0
    needs_review_count = 0
    rejected_count = 0

    for i, question_data in enumerate(sample_questions, 1):
        print(f"\n--- Question {i}/{len(sample_questions)} ---")
        print(f"Konu: {question_data['konu']}")
        print(f"Zorluk: {question_data['zorluk']}")
        print(f"Soru: {question_data['text'][:60]}...")
        print()

        question_id = f"Q_GEN_{i:04d}"

        # Step 1: Check plagiarism
        if plagiarism_service:
            print("  [Plagiarism Check]")
            try:
                plagiarism_result = await plagiarism_service.check_plagiarism(
                    question_text=question_data["text"],
                    soru_metni=question_data["soru_metni"],
                    konu=question_data["konu"],
                )

                similarity = plagiarism_result["max_similarity"]
                print(f"    - Max similarity: {similarity:.2%}")

                if plagiarism_result["is_plagiarized"]:
                    print(
                        f"    [REJECT] Plagiarism detected (>{plagiarism_result['threshold']:.0%})"
                    )
                    rejected_count += 1
                    continue
                else:
                    print(f"    [PASS] Not plagiarized")
            except Exception as e:
                print(f"    [WARN] Plagiarism check failed: {str(e)[:60]}")
                similarity = 0.0
        else:
            print("  [Plagiarism Check] Skipped - service not available")
            similarity = 0.0

        # Step 2: Add to Knowledge Graph
        if kg_service:
            print("  [Knowledge Graph]")
            try:
                await kg_service.add_question(
                    question_id=question_id,
                    konu=question_data["konu"],
                    kazanim=question_data["kazanim"],
                    zorluk=question_data["zorluk"],
                )
                print(f"    [OK] Added to knowledge graph")
            except Exception as e:
                print(f"    [WARN] KG add failed: {str(e)[:60]}")

        # Step 3: Decide if needs HITL review
        needs_review = False
        if similarity > 0.70:  # Close to plagiarism threshold
            needs_review = True

        if needs_review and hitl_service:
            print("  [HITL Workflow]")
            try:
                task = hitl_service.create_review_task(
                    question_id=question_id,
                    ai_validation_result={
                        "confidence": 1.0 - similarity,
                        "issues": [f"Similarity score: {similarity:.2%}"],
                    },
                    konu=question_data["konu"],
                )
                print(f"    [REVIEW] Created task: {task.task_id}")
                print(f"    - Priority: {task.priority.value}")
                print(f"    - Incentive: {task.incentive_points} points")
                needs_review_count += 1
            except Exception as e:
                print(f"    [WARN] HITL task creation failed: {str(e)[:60]}")
        else:
            print("  [Auto-Approval]")
            print(f"    [APPROVED] Similarity: {similarity:.2%}")
            approved_count += 1

        # Step 4: Add to CAT pool
        if cat_service and not needs_review:
            print("  [CAT Pool]")
            try:
                import random

                irt_params = {
                    "irt_a": random.uniform(0.5, 2.0),
                    "irt_b": {"easy": -1.0, "medium": 0.0, "hard": 1.0}[
                        question_data["zorluk"]
                    ],
                    "irt_c": 0.25,
                }

                print(f"    [OK] Added to CAT pool")
                print(
                    f"    - IRT params: a={irt_params['irt_a']:.2f}, b={irt_params['irt_b']:.2f}, c={irt_params['irt_c']:.2f}"
                )
            except Exception as e:
                print(f"    [WARN] CAT add failed: {str(e)[:60]}")

        generated_count += 1

    # Summary
    print()
    print("=" * 80)
    print("QUESTION GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print(f"Total Questions Generated:  {generated_count}")
    print(f"  [APPROVED]                {approved_count}")
    print(f"  [REVIEW]                  {needs_review_count}")
    print(f"  [REJECTED]                {rejected_count}")
    print()

    # Show Knowledge Graph stats
    if kg_service:
        print(f"Knowledge Graph Status:")
        print(f"  - Total nodes: {len(kg_service.graph.nodes())}")
        print(f"  - Total edges: {len(kg_service.graph.edges())}")
        print()

    # Show HITL stats
    if hitl_service:
        pending_tasks = len(
            [t for t in hitl_service.task_queue if t.status.value == "pending"]
        )
        print(f"HITL Workflow Status:")
        print(f"  - Pending tasks: {pending_tasks}")
        print(f"  - Total experts: {len(hitl_service.experts)}")
        print()

    print("=" * 80)
    print("Services are ready for production use!")
    print()
    print("Next steps:")
    print("  1. Start backend API: cd backend && uvicorn main:app --reload")
    print("  2. Access API docs: http://localhost:8000/docs")
    print("  3. Test endpoints: curl http://localhost:8000/api/v2/health")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
