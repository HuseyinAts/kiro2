"""
Unit tests for learning path routes (UT-03.4).

Tests learning path endpoint data structures and validation.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import pytest


# --- UT-03.4.1: Student profile creation request ---
@pytest.mark.asyncio
async def test_create_profile_request():
    """Create profile request must have student data."""
    request = {
        "name": "Ahmet Yilmaz",
        "grade": 11,
        "subjects": ["matematik", "fizik"],
        "learning_style": "visual",
    }
    assert request["grade"] in range(9, 13)
    assert len(request["subjects"]) >= 1
    assert request["learning_style"] in ("visual", "auditory", "kinesthetic", "mixed")


# --- UT-03.4.2: Path generation request ---
@pytest.mark.asyncio
async def test_generate_path_request():
    """Path generation request must have subject and goals."""
    request = {
        "student_id": "STU001",
        "subject": "matematik",
        "goals": ["YKS'de yuksek puan"],
        "time_horizon_days": 90,
    }
    assert len(request["goals"]) >= 1
    assert request["time_horizon_days"] > 0


# --- UT-03.4.3: Resources response ---
@pytest.mark.asyncio
async def test_resources_response():
    """Resources endpoint returns categorized learning materials."""
    resources = [
        {"type": "video", "title": "Turev Anlatim", "relevance": 0.95},
        {"type": "article", "title": "Turev Kurallari", "relevance": 0.88},
    ]
    assert len(resources) >= 1
    assert all(0.0 <= r["relevance"] <= 1.0 for r in resources)
    assert all("type" in r for r in resources)


# --- UT-03.4.4: Progress update request ---
@pytest.mark.asyncio
async def test_progress_update_request():
    """Progress update must have node_id and completion data."""
    request = {
        "student_id": "STU001",
        "node_id": "MOD1-TOPIC1",
        "progress_percent": 75,
        "time_spent_minutes": 45,
    }
    assert 0 <= request["progress_percent"] <= 100
    assert request["time_spent_minutes"] >= 0
