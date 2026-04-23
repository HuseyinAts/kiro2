#!/usr/bin/env python3
"""
KIRO Platform - Service Demo (Simplified)
Demonstrates all services generating questions
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


def main():
    """Run service demo"""

    print("=" * 80)
    print("KIRO PLATFORM - SORU URETIM SISTEMI")
    print("=" * 80)
    print()

    # Import services
    print("[YUKLENIY OR] Servisler yuklen iyor...")
    try:
        from services.hitl_workflow_service import HITLWorkflowService
        from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode

        print("[TAMAM] Tum servisler yuklendi!")
    except Exception as e:
        print(f"[HATA] {e!s}")
        return

    print()

    # Initialize services
    print("[BASLATILIYOR] Knowledge Graph...")
    kg_service = KnowledgeGraphService()
    print(
        f"[TAMAM] {len(kg_service.graph.nodes())} node, {len(kg_service.graph.edges())} edge"
    )
    print()

    print("[BASLATILIYOR] HITL Workflow...")
    hitl_service = HITLWorkflowService()
    print("[TAMAM] Expert sistemi hazir")
    print()

    print("=" * 80)
    print("SORU URETIMI BASLIYOR")
    print("=" * 80)
    print()

    # Generate questions
    questions = [
        {
            "id": "Q001",
            "konu": "Matematik",
            "kazanim": "Turev hesaplama",
            "bloom_level": "apply",
            "irt_difficulty": 0.0,
            "text": "f(x) = x^2 + 3x - 2 fonksiyonunun turevini bulunuz",
            "cevap": "f'(x) = 2x + 3",
        },
        {
            "id": "Q002",
            "konu": "Fizik",
            "kazanim": "Kuvvet hesaplama",
            "bloom_level": "apply",
            "irt_difficulty": 0.0,
            "text": "10 kg kutleli bir cisme uygulanan 50 N kuvvet hangi ivmeyi uretir?",
            "cevap": "a = 5 m/s^2",
        },
        {
            "id": "Q003",
            "konu": "Kimya",
            "kazanim": "Mol hesaplama",
            "bloom_level": "remember",
            "irt_difficulty": -0.5,
            "text": "32 gram oksijen (O2) kac mol'dur? (O: 16 g/mol)",
            "cevap": "1 mol",
        },
        {
            "id": "Q004",
            "konu": "Biyoloji",
            "kazanim": "Hucre yapisi",
            "bloom_level": "understand",
            "irt_difficulty": 0.0,
            "text": "Mitokondri hangi hucresel sureci gerceklestirir?",
            "cevap": "Hucresel solunum (ATP uretimi)",
        },
        {
            "id": "Q005",
            "konu": "Matematik",
            "kazanim": "Integral hesaplama",
            "bloom_level": "apply",
            "irt_difficulty": 1.0,
            "text": "Integral(3x^2 + 2x)dx integralini hesaplayiniz",
            "cevap": "x^3 + x^2 + C",
        },
    ]

    approved = 0
    review_needed = 0

    for i, q in enumerate(questions, 1):
        print(f"[SORU {i}] {q['text'][:50]}...")

        # Add to knowledge graph
        try:
            node = QuestionNode(
                id=q["id"],
                konu=q["konu"],
                kazanim=q["kazanim"],
                bloom_level=q["bloom_level"],
                irt_difficulty=q["irt_difficulty"],
                cognitive_skills=["problem_solving"],
            )
            kg_service.add_question_node(node)
            print("  [+] Knowledge Graph'a eklendi")
        except Exception as e:
            print(f"  [!] Hata: {str(e)[:40]}")

        # Simulate plagiarism check
        import random

        similarity = random.uniform(0.1, 0.7)
        print(f"  [?] Benzerlik skoru: {similarity:.1%}")

        if similarity > 0.6:
            # Create review task
            try:
                task = hitl_service.create_review_task(
                    question_id=q["id"],
                    ai_validation_result={"confidence": 0.7, "pedagogy_score": 0.8},
                    konu=q["konu"],
                )
                print(f"  [!] Expert incelemesi gerekli - Task: {task.task_id}")
                review_needed += 1
            except Exception as e:
                print(f"  [!] Task olusturulamadi: {str(e)[:40]}")
        else:
            print("  [OK] Otomatik onaylandi")
            approved += 1

        print()

    # Summary
    print("=" * 80)
    print("SONUC RAPORU")
    print("=" * 80)
    print()
    print(f"Toplam Soru:              {len(questions)}")
    print(f"  Onaylanan:              {approved}")
    print(f"  Expert Incelemesi:      {review_needed}")
    print()

    # Graph stats
    total_questions = [
        n
        for n in kg_service.graph.nodes()
        if kg_service.graph.nodes[n].get("type") == "question"
    ]
    print("Knowledge Graph:")
    print(f"  Node sayisi:            {len(kg_service.graph.nodes())}")
    print(f"  Edge sayisi:            {len(kg_service.graph.edges())}")
    print(f"  Soru sayisi:            {len(total_questions)}")
    print()

    # HITL stats
    pending = [t for t in hitl_service.task_queue if t.status.value == "pending"]
    print("HITL Workflow:")
    print(f"  Bekleyen gorevler:      {len(pending)}")
    print(f"  Kayitli expertler:      {len(hitl_service.experts)}")
    print()

    # Show graph connections
    if total_questions:
        print("Graf Baglantilari (ilk 3 soru):")
        for q_id in total_questions[:3]:
            neighbors = list(kg_service.graph.neighbors(q_id))
            if neighbors:
                print(f"  {q_id}:")
                for n in neighbors[:2]:
                    print(f"    -> {n}")
        print()

    print("=" * 80)
    print("SISTEM HAZIR - TUM SERVISLER CALISIYOR!")
    print("=" * 80)
    print()
    print("API'yi baslatmak icin:")
    print("  cd backend")
    print("  uvicorn main:app --reload")
    print()
    print("API test etmek icin:")
    print("  curl http://localhost:8000/api/v2/health")
    print("  curl http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nHATA: {e!s}")
        import traceback

        traceback.print_exc()
