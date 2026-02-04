"""
Wave 2B API Test Script
Test Wave 2B quality evaluation endpoints
"""

import sys
import asyncio
import httpx
from pathlib import Path

# UTF-8 encoding
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint"""
    print("\n" + "=" * 80)
    print("TEST 1: Health Check")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v2/quality/health")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Health Check: {data['status']}")
            print(f"   Components:")
            for component, status in data.get("components", {}).items():
                icon = "✅" if status else "❌"
                print(f"   {icon} {component}: {status}")
        else:
            print(f"\n❌ Health check failed: {response.status_code}")


async def test_stats():
    """Test stats endpoint"""
    print("\n" + "=" * 80)
    print("TEST 2: System Stats")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v2/quality/stats")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Version: {data['version']}")
            print(f"   Configuration:")
            for key, value in data.get("configuration", {}).items():
                print(f"      {key}: {value}")
        else:
            print(f"\n❌ Stats failed: {response.status_code}")


async def test_evaluate_single():
    """Test single question evaluation"""
    print("\n" + "=" * 80)
    print("TEST 3: Single Question Evaluation")
    print("=" * 80)

    question = {
        "question_text": "Bir sayının 3 katının 5 fazlası 26 ise, bu sayı kaçtır?",
        "difficulty": "kolay",
        "subject": "Matematik",
        "evaluation_stage": "standard",
    }

    print(f"\n📝 Soru: {question['question_text']}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v2/quality/evaluate", json=question
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Değerlendirme Başarılı!")
            print(f"   Kalite Skoru: {data['overall_score']:.3f}")
            print(f"   Derece: {data['overall_grade']}")
            print(f"   Karar: {data['decision']}")
            print(f"   Bloom Seviyesi: {data.get('bloom_level', 'N/A')}")
            print(f"   Güven: {data.get('bloom_confidence', 0):.2f}")
            print(f"   Süre: {data['execution_time_ms']:.0f}ms")

            if data.get("strengths"):
                print(f"\n   Güçlü Yönler:")
                for s in data["strengths"][:3]:
                    print(f"      ✓ {s}")

            if data.get("weaknesses"):
                print(f"\n   İyileştirme Alanları:")
                for w in data["weaknesses"][:3]:
                    print(f"      ⚠️ {w}")
        else:
            print(f"\n❌ Evaluation failed: {response.status_code}")
            print(response.text)


async def test_bertscore():
    """Test BERTScore endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: BERTScore Similarity")
    print("=" * 80)

    data = {
        "candidate": "Bir sayının 3 katı 15'tir. Bu sayı kaçtır?",
        "reference": "Bir sayının 2 katı 12'dir. Bu sayı kaçtır?",
    }

    print(f"\n📝 Soru 1: {data['candidate']}")
    print(f"📝 Soru 2: {data['reference']}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{BASE_URL}/api/v2/quality/bertscore", json=data)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ BERTScore Hesaplandı!")
            print(f"   F1 Score: {result['f1_score']:.3f}")
            print(f"   Precision: {result['precision']:.3f}")
            print(f"   Recall: {result['recall']:.3f}")
            print(f"   Yorum: {result['interpretation']}")
            print(f"   Benzer mi?: {'Evet' if result['is_similar'] else 'Hayır'}")
        else:
            print(f"\n❌ BERTScore failed: {response.status_code}")
            print(response.text)


async def test_batch():
    """Test batch evaluation"""
    print("\n" + "=" * 80)
    print("TEST 5: Batch Evaluation")
    print("=" * 80)

    questions = [
        {
            "question_text": "Bir sayının 3 katı 15'tir. Bu sayı kaçtır?",
            "difficulty": "kolay",
            "subject": "Matematik",
        },
        {
            "question_text": "4 kg kütleli bir cisme 12 N kuvvet uygulanıyor. Cismin ivmesi kaç m/s²'dir?",
            "difficulty": "orta",
            "subject": "Fizik",
        },
        {
            "question_text": "Fotosentezin ışık tepkimelerinde hangi molekül oksijen üretir?",
            "difficulty": "orta",
            "subject": "Biyoloji",
        },
    ]

    print(f"\n📝 {len(questions)} soru toplu değerlendiriliyor...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v2/quality/evaluate-batch",
            json={"questions": questions, "evaluation_stage": "standard"},
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Toplu Değerlendirme Başarılı!")
            print(f"   Toplam: {data['total']}")
            print(
                f"   ✅ Onaylanan: {data['approved']} ({data['approved']/data['total']*100:.0f}%)"
            )
            print(
                f"   ⚠️  İncelenmeli: {data['review']} ({data['review']/data['total']*100:.0f}%)"
            )
            print(f"   ❌ Reddedilen: {data['rejected']}")
            print(f"   Ortalama Kalite: {data['average_score']:.3f}")
            print(f"   Toplam Süre: {data['execution_time_ms']:.0f}ms")

            print(f"\n   Detay:")
            for i, result in enumerate(data["results"], 1):
                print(
                    f"   {i}. {result['decision']} - Score: {result['overall_score']:.3f} - Bloom: Lv{result.get('bloom_level', '?')}"
                )
        else:
            print(f"\n❌ Batch evaluation failed: {response.status_code}")
            print(response.text)


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 25 + "WAVE 2B API TESTS")
    print("=" * 80)
    print("\nBackend should be running at http://localhost:8000")

    try:
        # Test 1: Health
        await test_health()

        # Test 2: Stats
        await test_stats()

        # Test 3: Single evaluation
        await test_evaluate_single()

        # Test 4: BERTScore
        await test_bertscore()

        # Test 5: Batch
        await test_batch()

        # Summary
        print("\n" + "=" * 80)
        print(" " * 32 + "ÖZET")
        print("=" * 80)
        print("\n✅ Tüm testler tamamlandı!")
        print("\n📚 API Endpoint'leri:")
        print("   POST /api/v2/quality/evaluate        - Tek soru değerlendirme")
        print("   POST /api/v2/quality/evaluate-batch  - Toplu değerlendirme")
        print("   POST /api/v2/quality/bertscore       - Benzerlik ölçümü")
        print("   GET  /api/v2/quality/health          - Health check")
        print("   GET  /api/v2/quality/stats           - Sistem bilgisi")

        print("\n📖 Swagger Docs: http://localhost:8000/docs#tag/Wave-2B-Quality")

    except httpx.ConnectError:
        print("\n❌ Backend'e bağlanılamadı!")
        print("   Backend'i başlat: cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
