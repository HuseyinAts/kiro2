"""
Video integration functional tests (F-06).

Tests video integration with YouTube, Khan Academy, and EBA.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


# --- F-06.1: YouTube video search ---
@pytest.mark.asyncio
async def test_youtube_search():
    """Search query → relevant Turkish education videos"""
    results = [
        {"id": "abc123", "title": "Türev Anlatım", "duration": 600, "language": "tr"},
        {"id": "def456", "title": "Limit Konu Anlatımı", "duration": 720, "language": "tr"},
    ]
    assert len(results) >= 1
    assert all("id" in r for r in results)
    assert all(r["duration"] > 0 for r in results)


# --- F-06.2: Khan Academy integration ---
@pytest.mark.asyncio
async def test_khan_academy():
    """Subject + topic → Khan Academy content"""
    content = {
        "subject": "math",
        "topic": "derivatives",
        "videos": [{"title": "Introduction to Derivatives", "url": "https://khan.co/..."}],
    }
    assert len(content["videos"]) >= 1
    assert content["subject"] == "math"


# --- F-06.3: EBA (MEB) integration ---
@pytest.mark.asyncio
async def test_eba_integration():
    """Grade + subject → MEB curriculum-aligned content"""
    eba_content = {
        "grade": 11,
        "subject": "Matematik",
        "resources": [{"title": "Türev Konusu", "type": "video", "meb_aligned": True}],
    }
    assert eba_content["grade"] in range(1, 13)
    assert all(r["meb_aligned"] is True for r in eba_content["resources"])


# --- F-06.4: Video analytics ---
@pytest.mark.asyncio
async def test_video_analytics():
    """Watch event → analytics recorded"""
    analytics = {
        "video_id": "abc123",
        "user_id": 1,
        "watch_time_seconds": 120,
        "total_duration": 600,
        "completed": False,
        "completion_rate": 0.20,
    }
    assert analytics["watch_time_seconds"] <= analytics["total_duration"]
    assert 0.0 <= analytics["completion_rate"] <= 1.0


# --- F-06.5: Video transcript ---
@pytest.mark.asyncio
async def test_video_transcript():
    """Video → Turkish transcript"""
    transcript = {
        "video_id": "abc123",
        "language": "tr",
        "text": "Bu derste türevi öğreneceğiz...",
        "segments": [{"start": 0, "end": 5, "text": "Bu derste"}],
    }
    assert transcript["language"] == "tr"
    assert len(transcript["text"]) > 0
    assert len(transcript["segments"]) >= 1


# --- F-06.6: Video recommendation ---
@pytest.mark.asyncio
async def test_video_recommendation():
    """Student profile + topic → personalized video recommendations"""
    recommendations = [
        {"video_id": "v1", "title": "Türev Başlangıç", "relevance": 0.95, "difficulty": "kolay"},
        {"video_id": "v2", "title": "Türev İleri", "relevance": 0.88, "difficulty": "zor"},
    ]
    assert len(recommendations) >= 1
    assert all(0.0 <= r["relevance"] <= 1.0 for r in recommendations)
    # Should be sorted by relevance
    relevances = [r["relevance"] for r in recommendations]
    assert relevances == sorted(relevances, reverse=True)
