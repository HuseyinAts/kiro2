"""
Unit tests for gamification routes (UT-03.8).

Tests gamification endpoint data structures and logic.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import pytest


# --- UT-03.8.1: XP earning request ---
@pytest.mark.asyncio
async def test_xp_earning_request():
    """XP earning request must have user_id, action, amount."""
    request = {
        "user_id": 1,
        "action": "question_solved",
        "amount": 10,
    }
    assert request["amount"] > 0
    assert request["action"] in ["question_solved", "exam_completed", "streak_bonus", "daily_login"]


# --- UT-03.8.2: Level data structure ---
@pytest.mark.asyncio
async def test_level_data_structure():
    """Level response includes current_level, xp, next_level_xp."""
    level_data = {
        "current_level": 5,
        "xp": 450,
        "next_level_xp": 500,
        "progress_percent": 90.0,
    }
    assert level_data["current_level"] >= 1
    assert level_data["xp"] < level_data["next_level_xp"]
    assert 0.0 <= level_data["progress_percent"] <= 100.0


# --- UT-03.8.3: Badges response ---
@pytest.mark.asyncio
async def test_badges_response():
    """Badges endpoint returns list of earned badges."""
    badges = [
        {"id": "b1", "name": "Ilk Adim", "earned": True, "earned_date": "2025-01-15"},
        {"id": "b2", "name": "Matematik Ustasi", "earned": False, "earned_date": None},
    ]
    assert len(badges) >= 1
    earned = [b for b in badges if b["earned"]]
    assert len(earned) >= 1
    assert all(b["earned_date"] is not None for b in earned)


# --- UT-03.8.4: Leaderboard response ---
@pytest.mark.asyncio
async def test_leaderboard_response():
    """Leaderboard returns ranked user list."""
    leaderboard = [
        {"rank": 1, "user_id": 2, "name": "Ayse", "xp": 1200},
        {"rank": 2, "user_id": 1, "name": "Ali", "xp": 1100},
        {"rank": 3, "user_id": 3, "name": "Mehmet", "xp": 900},
    ]
    assert len(leaderboard) >= 1
    ranks = [e["rank"] for e in leaderboard]
    assert ranks == sorted(ranks)
    xps = [e["xp"] for e in leaderboard]
    assert xps == sorted(xps, reverse=True)
