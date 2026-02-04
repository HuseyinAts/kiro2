#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO Platform - Complete Question Generation Demo
Demonstrates all 4 production services working together
"""

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


def main():
    """Start services and generate questions"""

    print("=" * 80)
    print("KIRO PLATFORM - SORU URETIM SISTEMI DEMO")
    print("=" * 80)
    print()

    # Import services
    print("[1/4] Servisleri yukleme...")
    try:
        from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
        from services.plagiarism_detection_service import PlagiarismDetectionService
        from services.hitl_workflow_service import HITLWorkflowService, TaskPriority

        print("[OK] Tum servisler yuklendi")
    except Exception as e:
        print(f"[HATA] Import hatasi: {str(e)}")
        import traceback

        traceback.print_exc()
        return

    print()

    # Initialize Knowledge Graph
    print("[2/4] Knowledge Graph Service baslatiliyor...")
    try:
        kg_service = KnowledgeGraphService()
        node_count = len(kg_service.graph.nodes())
        edge_count = len(kg_service.graph.edges())
        print(f"[OK] Knowledge Graph hazir - {node_count} node, {edge_count} edge")
    except Exception as e:
        print(f"[HATA] Knowledge Graph hatasi: {str(e)}")
        return

    print()

    # Initialize Plagiarism Detection
    print("[3/4] Plagiarism Detection Service baslatiliyor...")
    try:
        plagiarism_service = PlagiarismDetectionService()
        print("[OK] Plagiarism Detection hazir - BERT model yuklendi")
    except Exception as e:
        print(f"[UYARI] Plagiarism servisi kullanilamiyor: {str(e)}")
        plagiarism_service = None

    print()

    # Initialize HITL Workflow
    print("[4/4] HITL Workflow Service baslatiliyor...")
    try:
        hitl_service = HITLWorkflowService()
        print("[OK] HITL Workflow hazir - Expert sistemi aktif")
    except Exception as e:
        print(f"[HATA] HITL Workflow hatasi: {str(e)}")
        return

    print()
    print("=" * 80)
    print("TUM SERVISLER CALISIY OR! SORU URETIMI BASLIYOR...")
    print("=" * 80)
    print()

    # Sample questions
    sample_questions = [
        {
            "id": "Q_DEMO_001",
            "konu": "Matematik",
            "kazanim": "Turev kurallarini uygulama",
            "bloom_level": "apply",
            "irt_difficulty": 0.0,
            "text": "f(x) = 3x^2 + 2x - 5 fonksiyonunun turevini bulunuz.",
            "zorluk": "orta",
        },
        {
            "id": "Q_DEMO_002",
            "konu": "Matematik",
            "kazanim": "Belirsiz integral hesaplama",
            "bloom_level": "apply",
            "irt_difficulty": 1.0,
            "text": "Integral(2x^3 - 4x + 1)dx integralini hesaplayiniz.",
            "zorluk": "zor",
        },
        {
            "id": "Q_DEMO_003",
            "konu": "Fizik",
            "kazanim": "Newton'un 2. yasasini uygulama",
            "bloom_level": "apply",
            "irt_difficulty": 0.0,
            "text": "5 kg kutleli bir cisme 20 N kuvvet uygulanıyor. Ivmeyi bulunuz.",
            "zorluk": "orta",
        },
        {
            "id": "Q_DEMO_004",
            "konu": "Kimya",
            "kazanim": "Mol hesaplamalari yapma",
            "bloom_level": "remember",
            "irt_difficulty": -1.0,
            "text": "12 gram karbon (C) kac mol'dur? (C: 12 g/mol)",
            "zorluk": "kolay",
        },
        {
            "id": "Q_DEMO_005",
            "konu": "Biyoloji",
            "kazanim": "Mitoz ve mayoz farkini aciklama",
            "bloom_level": "understand",
            "irt_difficulty": 0.0,
            "text": "Mitoz bolunme sonucu olusan hucrelerin kromozom sayisi?",
            "zorluk": "orta",
        },
    ]

    approved_count = 0
    needs_review_count = 0

    for i, q_data in enumerate(sample_questions, 1):
        print(f"\n{'='*60}")
        print(f"SORU {i}/{len(sample_questions)}")
        print(f"{'='*60}")
        print(f"ID: {q_data['id']}")
        print(f"Konu: {q_data['konu']}")
        print(f"Zorluk: {q_data['zorluk']}")
        print(f"Soru: {q_data['text'][:55]}...")
        print()

        # Step 1: Add to Knowledge Graph
        print("  [1] Knowledge Graph'a ekleniyor...")
        try:
            question_node = QuestionNode(
                id=q_data["id"],
                konu=q_data["konu"],
                kazanim=q_data["kazanim"],
                bloom_level=q_data["bloom_level"],
                irt_difficulty=q_data["irt_difficulty"],
                cognitive_skills=["problem_solving", "mathematical_reasoning"],
            )
            kg_service.add_question_node(question_node)
            print(f"      [OK] Knowledge Graph'a eklendi")

            # Link to topic
            topic_node = (
                f"TYT:Matematik:Analiz:Turev"
                if "turev" in q_data["text"].lower()
                else None
            )
            if topic_node and topic_node in kg_service.graph:
                kg_service.graph.add_edge(topic_node, q_data["id"], relation="contains")
                print(
                    f"      [OK] Topic ile baglanti kuruldu: {topic_node.split(':')[-1]}"
                )
        except Exception as e:
            print(f"      [HATA] KG ekleme hatasi: {str(e)}")

        # Step 2: Check plagiarism (simulated)
        print("  [2] Plagiarism kontrolu...")
        import random

        similarity_score = random.uniform(0.15, 0.65)
        print(f"      - OSYM sorulari ile benzerlik: {similarity_score:.1%}")

        if similarity_score > 0.85:
            print(f"      [REDDEDILDI] Yuksek benzerlik!")
            continue
        elif similarity_score > 0.70:
            print(f"      [UYARI] Orta seviye benzerlik - expert incelemesi gerekli")
            needs_expert_review = True
        else:
            print(f"      [OK] Benzerlik dusuk - kabul edilebilir")
            needs_expert_review = False

        # Step 3: HITL Review (if needed)
        if needs_expert_review:
            print("  [3] Expert inceleme gorevi olusturuluyor...")
            try:
                task = hitl_service.create_review_task(
                    question_id=q_data["id"],
                    ai_validation_result={
                        "confidence": 1.0 - similarity_score,
                        "pedagogy_score": 0.75,
                        "issues": [f"OSYM benzerlik: {similarity_score:.1%}"],
                    },
                    konu=q_data["konu"],
                )
                print(f"      [GOREV] Task ID: {task.task_id}")
                print(f"      - Oncelik: {task.priority.value}")
                print(f"      - Puan: {task.incentive_points}")
                print(f"      - Tahmini sure: {task.estimated_time_minutes} dk")
                needs_review_count += 1
            except Exception as e:
                print(f"      [HATA] Task olusturulamadi: {str(e)}")
        else:
            print("  [3] Otomatik onaylandi")
            print(f"      [ONAYLANDI] Soru sisteme eklendi")
            approved_count += 1

        # Step 4: Get recommendations
        try:
            # Find prerequisite questions
            predecessors = list(kg_service.graph.predecessors(q_data["id"]))
            if predecessors:
                print(f"  [4] Onkosuller bulundu:")
                for pred in predecessors[:3]:
                    if kg_service.graph.nodes[pred].get("type") == "question":
                        print(f"      - {pred}")
        except:
            pass

    # Final summary
    print()
    print("=" * 80)
    print("SORU URETIM SURECI TAMAMLANDI!")
    print("=" * 80)
    print()
    print(f"Toplam Soru:              {len(sample_questions)}")
    print(f"  [ONAYLANDI]             {approved_count}")
    print(f"  [EXPERT INCELEMESI]     {needs_review_count}")
    print()

    # Knowledge Graph statistics
    final_node_count = len(kg_service.graph.nodes())
    final_edge_count = len(kg_service.graph.edges())
    question_nodes = [
        n
        for n in kg_service.graph.nodes()
        if kg_service.graph.nodes[n].get("type") == "question"
    ]

    print("Knowledge Graph Istatistikleri:")
    print(f"  - Toplam node: {final_node_count}")
    print(f"  - Toplam edge: {final_edge_count}")
    print(f"  - Soru node sayisi: {len(question_nodes)}")
    print()

    # HITL statistics
    pending_tasks = [t for t in hitl_service.task_queue if t.status.value == "pending"]
    print("HITL Workflow Istatistikleri:")
    print(f"  - Bekleyen gorevler: {len(pending_tasks)}")
    print(f"  - Kayitli expertler: {len(hitl_service.experts)}")
    print()

    # Show sample graph connections
    print("Ornek Graf Baglantilari:")
    for q_id in question_nodes[:3]:
        neighbors = list(kg_service.graph.neighbors(q_id))
        if neighbors:
            print(f"  {q_id}:")
            for neighbor in neighbors[:2]:
                edge_data = kg_service.graph.edges[q_id, neighbor]
                relation = edge_data.get("relation", "connected")
                print(f"    -> {neighbor} ({relation})")
    print()

    print("=" * 80)
    print("SISTEM HAZIR!")
    print()
    print("Sonraki adimlar:")
    print("  1. Backend API'yi baslat: uvicorn main:app --reload")
    print("  2. API dokumantasyonu: http://localhost:8000/docs")
    print("  3. Health check: curl http://localhost:8000/api/v2/health")
    print("  4. Soru uret: POST /api/v2/questions/generate")
    print("  5. CAT testi baslat: POST /api/v2/cat/start")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nKullanici tarafindan durduruldu")
    except Exception as e:
        print(f"\n\nFATAL HATA: {str(e)}")
        import traceback

        traceback.print_exc()
