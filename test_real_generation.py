#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Real Question Generation
GPT-5 ve Claude 4.5 ile gerçek soru üretimi
"""

import sys
import os
import requests
import json
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_api_endpoints():
    """Test various API endpoints"""

    base_url = "http://localhost:8000"

    print("=" * 80)
    print("KIRO PLATFORM - GERCEK SORU URETIMI TESTI")
    print("=" * 80)
    print()

    # Test 1: Health Check
    print("[1] Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"    [OK] Sistem Durumu: {data.get('status')}")
            print(f"    [OK] Mesaj: {data.get('message')}")
        else:
            print(f"    [HATA] Status: {response.status_code}")
    except Exception as e:
        print(f"    [HATA] {str(e)}")

    print()

    # Test 2: List available endpoints
    print("[2] Mevcut Endpoint'ler...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            paths = list(openapi.get('paths', {}).keys())

            # Find question generation endpoints
            question_endpoints = [p for p in paths if 'question' in p.lower() or 'soru' in p.lower()]

            if question_endpoints:
                print(f"    [BULUNDU] {len(question_endpoints)} soru endpoint'i:")
                for ep in question_endpoints[:10]:
                    print(f"      - {ep}")
            else:
                print("    [UYARI] Soru endpoint'i bulunamadi")
                print(f"    [BILGI] Toplam {len(paths)} endpoint mevcut")
                print("    Ilk 10 endpoint:")
                for ep in paths[:10]:
                    print(f"      - {ep}")
    except Exception as e:
        print(f"    [HATA] {str(e)}")

    print()

    # Test 3: Try OSYM endpoint
    print("[3] OSYM Soru Uretme Endpoint'i Test Ediliyor...")
    try:
        payload = {
            "konu": "Matematik - Turev",
            "zorluk": "orta",
            "sinav_tipi": "TYT"
        }

        response = requests.post(
            f"{base_url}/api/osym/generate-question",
            json=payload,
            timeout=30
        )

        print(f"    Status Code: {response.status_code}")
        print(f"    Response:")
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

    except requests.exceptions.Timeout:
        print("    [TIMEOUT] 30 saniye icinde cevap alinmadi")
    except Exception as e:
        print(f"    [HATA] {str(e)}")

    print()

    # Test 4: Try direct service import
    print("[4] Servisleri Dogrudan Test Ediliyor...")
    try:
        from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
        from services.hitl_workflow_service import HITLWorkflowService

        kg_service = KnowledgeGraphService()
        hitl_service = HITLWorkflowService()

        print(f"    [OK] Knowledge Graph: {len(kg_service.graph.nodes())} node")
        print(f"    [OK] HITL Workflow: {len(hitl_service.experts)} expert")

        # Add a test question
        test_question = QuestionNode(
            id="TEST_001",
            konu="Matematik",
            kazanim="Test kazanim",
            bloom_level="apply",
            irt_difficulty=0.0,
            cognitive_skills=["test"]
        )

        kg_service.add_question_node(test_question)
        print(f"    [OK] Test sorusu eklendi: {test_question.id}")
        print(f"    [OK] Yeni node sayisi: {len(kg_service.graph.nodes())}")

    except Exception as e:
        print(f"    [HATA] {str(e)}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("TEST TAMAMLANDI")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_api_endpoints()
    except KeyboardInterrupt:
        print("\n\nKullanici tarafindan durduruldu")
    except Exception as e:
        print(f"\n\nFATAL HATA: {str(e)}")
        import traceback
        traceback.print_exc()
