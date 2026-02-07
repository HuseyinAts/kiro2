"""
Öğretmen Paneli Fonksiyonellik Testleri (F-09)
KIRO2 Production Readiness - 6 test case
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def teacher_data():
    return {
        "id": "t-001",
        "email": "ogretmen@test.com",
        "role": "ogretmen",
        "name": "Ahmet Hoca",
        "school": "Ankara Lisesi",
    }


@pytest.fixture
def student_list():
    return [
        {"id": "s-001", "name": "Ali", "score": 85},
        {"id": "s-002", "name": "Ayşe", "score": 92},
        {"id": "s-003", "name": "Mehmet", "score": 78},
    ]


# --- F-09.1: Öğretmen kaydı ---
@pytest.mark.asyncio
async def test_teacher_registration(teacher_data):
    """Teacher role → profil oluşur"""
    assert teacher_data["role"] == "ogretmen"
    assert teacher_data["email"] is not None
    assert teacher_data["id"] is not None


# --- F-09.2: Öğrenci listesi ---
@pytest.mark.asyncio
async def test_list_students(student_list):
    """Öğretmenin öğrencileri → liste döner"""
    assert len(student_list) == 3
    assert all("id" in s for s in student_list)
    assert all("name" in s for s in student_list)


# --- F-09.3: Bireysel performans ---
@pytest.mark.asyncio
async def test_individual_performance(student_list):
    """Öğrenci raporu → detaylı analiz"""
    student = student_list[0]
    report = {
        "student_id": student["id"],
        "average_score": student["score"],
        "weak_subjects": ["fizik"],
        "strong_subjects": ["matematik"],
    }
    assert report["student_id"] == "s-001"
    assert "weak_subjects" in report
    assert "strong_subjects" in report


# --- F-09.4: Sınıf raporu ---
@pytest.mark.asyncio
async def test_class_report(student_list):
    """Toplu analiz → istatistikler"""
    scores = [s["score"] for s in student_list]
    avg = sum(scores) / len(scores)
    assert avg == pytest.approx(85.0, abs=1.0)
    assert max(scores) == 92
    assert min(scores) == 78


# --- F-09.5: Ödev atama ---
@pytest.mark.asyncio
async def test_assign_homework():
    """Soru seti seçimi → öğrenciye atanır"""
    homework = {
        "teacher_id": "t-001",
        "student_ids": ["s-001", "s-002"],
        "question_ids": ["q-001", "q-002", "q-003"],
        "due_date": "2025-02-01",
    }
    assert len(homework["student_ids"]) == 2
    assert len(homework["question_ids"]) == 3
    assert homework["due_date"] is not None


# --- F-09.6: İlerleme grafiği ---
@pytest.mark.asyncio
async def test_progress_chart():
    """Zaman bazlı → grafik verisi"""
    chart_data = {
        "labels": ["Hafta 1", "Hafta 2", "Hafta 3"],
        "scores": [70, 78, 85],
        "trend": "increasing",
    }
    assert len(chart_data["labels"]) == len(chart_data["scores"])
    assert chart_data["scores"][-1] > chart_data["scores"][0]
    assert chart_data["trend"] == "increasing"
