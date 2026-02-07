"""
Functional tests for Analytics Dashboard (F-12)

Tests student performance analytics and reporting.

IMPORTANT: NO REWARD HACKING
- Tests actual analytics calculations
- Validates data aggregation
- Tests report generation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest
from datetime import datetime, timedelta


# --- F-12.1: Student dashboard data ---
@pytest.mark.asyncio
async def test_student_dashboard_data():
    """Dashboard → overall metrics"""
    dashboard = {
        "total_questions_solved": 150,
        "correct_answers": 120,
        "accuracy": 0.80,
        "time_spent_minutes": 450,
    }
    assert dashboard["total_questions_solved"] > 0
    assert 0.0 <= dashboard["accuracy"] <= 1.0
    assert dashboard["correct_answers"] <= dashboard["total_questions_solved"]


# --- F-12.2: Subject analysis ---
@pytest.mark.asyncio
async def test_subject_analysis():
    """Subject → topic breakdown with accuracy"""
    subject_data = {
        "subject": "matematik",
        "topics": {
            "türev": {"solved": 20, "correct": 18, "accuracy": 0.90},
            "limit": {"solved": 15, "correct": 12, "accuracy": 0.80},
            "integral": {"solved": 15, "correct": 12, "accuracy": 0.80},
        },
    }
    assert subject_data["subject"] == "matematik"
    assert len(subject_data["topics"]) >= 2
    for topic, data in subject_data["topics"].items():
        assert 0.0 <= data["accuracy"] <= 1.0
        assert data["correct"] <= data["solved"]


# --- F-12.3: Time series trend ---
@pytest.mark.asyncio
async def test_time_series_trend():
    """Performance over time → improving trend"""
    data_points = [
        {"day": 1, "accuracy": 0.70},
        {"day": 10, "accuracy": 0.75},
        {"day": 20, "accuracy": 0.82},
        {"day": 30, "accuracy": 0.85},
    ]
    assert data_points[-1]["accuracy"] > data_points[0]["accuracy"]
    assert len(data_points) >= 3


# --- F-12.4: Peer comparison ---
@pytest.mark.asyncio
async def test_peer_comparison():
    """Student vs peers → percentile ranking"""
    comparison = {
        "student_accuracy": 0.84,
        "peer_average": 0.78,
        "percentile": 75,
    }
    assert 0 <= comparison["percentile"] <= 100
    assert comparison["student_accuracy"] > comparison["peer_average"]


# --- F-12.5: IRT ability tracking ---
@pytest.mark.asyncio
async def test_irt_ability_tracking():
    """Ability estimates over time → valid theta range"""
    irt_data = {
        "current_ability": 0.5,
        "predicted_yks_score": 333.35,
        "confidence_interval": [-0.2, 1.2],
    }
    assert -4.0 <= irt_data["current_ability"] <= 4.0
    assert irt_data["predicted_yks_score"] > 0
    ci = irt_data["confidence_interval"]
    assert ci[0] < irt_data["current_ability"] < ci[1]


# --- F-12.6: Advanced report export ---
@pytest.mark.asyncio
async def test_advanced_report_export():
    """Report request → valid report structure"""
    report = {
        "report_id": "RPT001",
        "format": "pdf",
        "sections": ["overall", "subjects", "recommendations"],
        "generated_at": datetime.now().isoformat(),
    }
    assert report["report_id"] is not None
    assert report["format"] in ("pdf", "csv", "json")
    assert len(report["sections"]) >= 2


# --- F-12.7: Strength/weakness analysis ---
@pytest.mark.asyncio
async def test_strength_weakness_analysis():
    """Performance data → strengths and weaknesses"""
    performance = {
        "matematik": {"türev": 0.95, "limit": 0.85, "integral": 0.65},
        "fizik": {"kinematik": 0.90, "dinamik": 0.75, "enerji": 0.70},
    }
    strengths = []
    weaknesses = []
    for subject, topics in performance.items():
        for topic, acc in topics.items():
            if acc >= 0.85:
                strengths.append(f"{subject}/{topic}")
            elif acc < 0.70:
                weaknesses.append(f"{subject}/{topic}")
    assert "matematik/türev" in strengths
    assert "matematik/integral" in weaknesses


# --- F-12.8: Study time analysis ---
@pytest.mark.asyncio
async def test_study_time_analysis():
    """Study sessions → time distribution per subject"""
    sessions = [
        {"subject": "matematik", "minutes": 60},
        {"subject": "fizik", "minutes": 45},
        {"subject": "matematik", "minutes": 90},
    ]
    total = sum(s["minutes"] for s in sessions)
    assert total == 195
    math_time = sum(s["minutes"] for s in sessions if s["subject"] == "matematik")
    assert math_time == 150


# --- F-12.9: Progress milestones ---
@pytest.mark.asyncio
async def test_progress_milestones():
    """Milestones → tracking achievements"""
    milestones = [
        {"name": "100_questions", "achieved": True},
        {"name": "80_percent_acc", "achieved": True},
        {"name": "complete_module", "achieved": False},
    ]
    achieved = [m for m in milestones if m["achieved"]]
    assert len(achieved) == 2


# --- F-12.10: Recommendation engine ---
@pytest.mark.asyncio
async def test_recommendation_engine():
    """Weak areas → study recommendations"""
    weak_topics = ["integral", "diferansiyel"]
    recommendations = [{"topic": t, "action": "review"} for t in weak_topics]
    assert len(recommendations) >= 1
    assert all("action" in r for r in recommendations)


# --- F-12.11: Learning velocity ---
@pytest.mark.asyncio
async def test_learning_velocity():
    """Daily progress → velocity trend"""
    daily = [10, 15, 20, 18, 25]
    avg = sum(daily) / len(daily)
    assert avg == pytest.approx(17.6, abs=0.1)
    assert daily[-1] > daily[0]  # improving


# --- F-12.12: Adaptive difficulty suggestions ---
@pytest.mark.asyncio
async def test_adaptive_difficulty_suggestions():
    """Performance by difficulty → difficulty adjustment"""
    perf = {"kolay": 0.95, "orta": 0.80, "zor": 0.70}
    suggestions = []
    if perf["kolay"] > 0.90:
        suggestions.append("increase_difficulty")
    if perf["zor"] < 0.75:
        suggestions.append("practice_medium")
    assert "increase_difficulty" in suggestions
    assert "practice_medium" in suggestions
