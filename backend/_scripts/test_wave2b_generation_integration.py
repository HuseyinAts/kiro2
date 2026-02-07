"""
Wave 2B + Question Generation Integration Test
Tests the complete pipeline: Generate → Evaluate → Filter
"""

import sys
import asyncio
import httpx
from pathlib import Path
import json
from datetime import datetime

# UTF-8 encoding
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"


async def test_hybrid_generation_with_wave2b():
    """Test hybrid generation with Wave 2B quality evaluation"""
    print("\n" + "=" * 80)
    print("TEST 1: Hybrid Question Generation with Wave 2B")
    print("=" * 80)

    request_data = {
        "subject": "Fizik",
        "topic": "Newton Kanunları",
        "difficulty": "orta",
        "exam_type": "TYT",
        "method": "osym_guided",
        "provider": "claude",
        "validate": True,
        "enable_wave2b": True,  # ✨ Wave 2B enabled
        "wave2b_threshold": 0.80,
    }

    print(f"\n📝 Generating question with Wave 2B:")
    print(f"   Subject: {request_data['subject']}")
    print(f"   Topic: {request_data['topic']}")
    print(f"   Wave 2B: Enabled (threshold: {request_data['wave2b_threshold']})")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # First check if user is authenticated (using test credentials)
            # For testing, we'll call the endpoint directly
            response = await client.post(
                f"{BASE_URL}/api/questions/hybrid/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"},  # Mock auth for testing
            )

            if response.status_code == 401:
                print("\n⚠️  Authentication required. This endpoint requires login.")
                print("   Skipping authenticated test...")
                return False

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Question Generated Successfully!")

                # Basic metrics
                print(f"\n📊 Generation Metrics:")
                print(f"   Success: {data['success']}")
                print(f"   Method: {data['method_used']}")
                print(f"   Generation Time: {data['generation_time_seconds']:.1f}s")

                # Quality metrics
                qm = data["quality_metrics"]
                print(f"\n📈 Quality Metrics:")
                print(f"   ÖSYM Compliance: {qm['osym_compliance']:.3f}")
                print(f"   Overall Quality: {qm['overall_quality']:.3f}")
                print(f"   Is Valid: {qm['is_valid']}")

                # Wave 2B metrics
                if "wave2b" in qm and qm["wave2b"].get("enabled"):
                    w2b = qm["wave2b"]
                    print(f"\n✨ Wave 2B Evaluation:")
                    print(f"   Overall Score: {w2b['overall_score']:.3f}")
                    print(f"   Grade: {w2b['overall_grade']}")
                    print(f"   Decision: {w2b['decision']}")
                    print(f"   Bloom Level: {w2b['bloom_level']}")
                    print(f"   Bloom Confidence: {w2b['bloom_confidence']:.2f}")

                    if w2b.get("bertscore_f1"):
                        print(f"   BERTScore F1: {w2b['bertscore_f1']:.3f}")

                    if w2b.get("strengths"):
                        print(f"\n   Strengths:")
                        for s in w2b["strengths"]:
                            print(f"      ✓ {s}")

                    if w2b.get("weaknesses"):
                        print(f"\n   Weaknesses:")
                        for w in w2b["weaknesses"]:
                            print(f"      ⚠️ {w}")

                # Question preview
                question = data["question"]
                print(f"\n📝 Question Preview:")
                print(f"   Stem: {question['stem'][:150]}...")
                print(f"   Options: {len(question.get('options', []))} choices")
                print(f"   Correct Answer: {question.get('correct_answer', 'N/A')}")

                return True

            else:
                print(f"\n❌ Generation failed: {response.status_code}")
                print(response.text)
                return False

        except httpx.ConnectError:
            print("\n❌ Cannot connect to backend!")
            print("   Start backend: cd backend && py -m uvicorn main:app --reload")
            return False
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_wave2b_without_generation():
    """Test Wave 2B API independently"""
    print("\n" + "=" * 80)
    print("TEST 2: Wave 2B API (Standalone)")
    print("=" * 80)

    # Use a sample question
    test_question = {
        "question_text": "4 kg kütleli bir cisme 12 N kuvvet uygulanıyor. Sürtünme katsayısı 0.2 olduğuna göre, cismin ivmesi kaç m/s²'dir? (g=10 m/s²)",
        "difficulty": "orta",
        "subject": "Fizik",
        "evaluation_stage": "standard",
    }

    print(f"\n📝 Evaluating test question:")
    print(f"   Subject: {test_question['subject']}")
    print(f"   Question: {test_question['question_text'][:80]}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v2/quality/evaluate", json=test_question
            )

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Wave 2B Evaluation Complete!")
                print(f"   Overall Score: {data['overall_score']:.3f}")
                print(f"   Grade: {data['overall_grade']}")
                print(f"   Decision: {data['decision']}")
                print(f"   Bloom Level: {data.get('bloom_level', 'N/A')}")
                print(f"   Execution Time: {data['execution_time_ms']:.0f}ms")

                if data.get("strengths"):
                    print(f"\n   Strengths:")
                    for s in data["strengths"][:3]:
                        print(f"      ✓ {s}")

                return True
            else:
                print(f"\n❌ Evaluation failed: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"\n❌ Test error: {e}")
            return False


async def test_generation_without_wave2b():
    """Test generation WITHOUT Wave 2B for comparison"""
    print("\n" + "=" * 80)
    print("TEST 3: Generation WITHOUT Wave 2B (Baseline)")
    print("=" * 80)

    request_data = {
        "subject": "Matematik",
        "topic": "Türev",
        "difficulty": "kolay",
        "exam_type": "TYT",
        "method": "osym_guided",
        "provider": "claude",
        "validate": True,
        "enable_wave2b": False,  # ❌ Wave 2B disabled
    }

    print(f"\n📝 Generating question WITHOUT Wave 2B:")
    print(f"   Subject: {request_data['subject']}")
    print(f"   Topic: {request_data['topic']}")
    print(f"   Wave 2B: Disabled")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/questions/hybrid/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"},
            )

            if response.status_code == 401:
                print("\n⚠️  Authentication required. Skipping...")
                return False

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Question Generated (without Wave 2B)")
                print(f"   Generation Time: {data['generation_time_seconds']:.1f}s")
                print(
                    f"   Overall Quality: {data['quality_metrics']['overall_quality']:.3f}"
                )
                print(f"   Wave 2B: {data['quality_metrics']['wave2b']}")
                return True
            else:
                print(f"\n❌ Generation failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"\n❌ Test error: {e}")
            return False


async def main():
    """Run all integration tests"""
    print("\n" + "=" * 80)
    print(" " * 20 + "WAVE 2B + GENERATION INTEGRATION TESTS")
    print("=" * 80)
    print("\nTesting complete pipeline: Question Generation → Wave 2B Evaluation")

    results = {
        "test1_hybrid_with_wave2b": False,
        "test2_wave2b_standalone": False,
        "test3_generation_baseline": False,
    }

    try:
        # Test 1: Full integration
        results["test1_hybrid_with_wave2b"] = await test_hybrid_generation_with_wave2b()

        # Test 2: Wave 2B standalone
        results["test2_wave2b_standalone"] = await test_wave2b_without_generation()

        # Test 3: Generation without Wave 2B
        results["test3_generation_baseline"] = await test_generation_without_wave2b()

        # Summary
        print("\n" + "=" * 80)
        print(" " * 32 + "SUMMARY")
        print("=" * 80)

        passed = sum(results.values())
        total = len(results)

        print(f"\n📊 Test Results: {passed}/{total} passed")
        print(
            f"\n   Test 1 - Hybrid + Wave 2B: {'✅ PASS' if results['test1_hybrid_with_wave2b'] else '❌ FAIL'}"
        )
        print(
            f"   Test 2 - Wave 2B Standalone: {'✅ PASS' if results['test2_wave2b_standalone'] else '❌ FAIL'}"
        )
        print(
            f"   Test 3 - Generation Baseline: {'✅ PASS' if results['test3_generation_baseline'] else '❌ FAIL'}"
        )

        if passed == total:
            print(f"\n✅ ALL TESTS PASSED! Wave 2B integration is working perfectly.")
        elif passed > 0:
            print(f"\n⚠️  PARTIAL SUCCESS. {total - passed} test(s) failed.")
        else:
            print(f"\n❌ ALL TESTS FAILED. Check backend and authentication.")

        print("\n📚 Integration Complete!")
        print("   • Wave 2B API: /api/v2/quality/evaluate")
        print("   • Hybrid Generation: /api/questions/hybrid/generate")
        print("   • Enable Wave 2B: Set 'enable_wave2b: true' in request")

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
