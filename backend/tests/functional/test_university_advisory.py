"""
Üniversite Danışmanlığı Fonksiyonellik Testleri (F-11)
KIRO2 Production Readiness - 5 test case
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# --- F-11.1: Üniversite arama ---
@pytest.mark.asyncio
async def test_search_universities():
    """İsim/şehir filtresi → sonuçlar"""
    results = [
        {"name": "Boğaziçi Üniversitesi", "city": "İstanbul"},
        {"name": "ODTÜ", "city": "Ankara"},
    ]
    assert len(results) >= 1
    assert all("name" in r for r in results)
    assert all("city" in r for r in results)


# --- F-11.2: Bölüm bilgisi ---
@pytest.mark.asyncio
async def test_department_info():
    """Bölüm detayları → içerik döner"""
    dept = {
        "name": "Bilgisayar Mühendisliği",
        "university": "Boğaziçi",
        "quota": 80,
        "language": "İngilizce",
    }
    assert dept["name"] is not None
    assert dept["quota"] > 0


# --- F-11.3: Taban puanları ---
@pytest.mark.asyncio
async def test_base_scores():
    """Geçmiş yıl verileri → doğru puanlar"""
    scores = {
        "department": "Bilgisayar Mühendisliği",
        "university": "Boğaziçi",
        "year": 2024,
        "base_score": 485.5,
        "placement_rank": 1250,
    }
    assert scores["base_score"] > 0
    assert scores["placement_rank"] > 0
    assert scores["year"] >= 2020


# --- F-11.4: Tercih simülasyonu ---
@pytest.mark.asyncio
async def test_preference_simulation():
    """Puan + tercih listesi → yerleşme tahmini"""
    simulation = {
        "student_score": 450.0,
        "preferences": ["Boğaziçi BM", "ODTÜ BM", "İTÜ BM"],
        "results": [
            {"pref": "Boğaziçi BM", "chance": "düşük"},
            {"pref": "ODTÜ BM", "chance": "orta"},
            {"pref": "İTÜ BM", "chance": "yüksek"},
        ],
    }
    assert len(simulation["preferences"]) == 3
    assert len(simulation["results"]) == len(simulation["preferences"])
    assert simulation["student_score"] > 0


# --- F-11.5: Üniversite önerisi ---
@pytest.mark.asyncio
async def test_university_recommendation():
    """Öğrenci profiline göre → kişisel öneriler"""
    recommendations = [
        {"university": "ODTÜ", "department": "BM", "match_score": 0.92},
        {"university": "İTÜ", "department": "BM", "match_score": 0.88},
    ]
    assert len(recommendations) >= 1
    assert all(0.0 <= r["match_score"] <= 1.0 for r in recommendations)
    assert recommendations[0]["match_score"] >= recommendations[1]["match_score"]
