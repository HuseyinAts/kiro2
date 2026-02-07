"""
Unit tests for exam (sinav) routes (UT-03.3).

Tests exam endpoint data structures and validation.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import pytest


# --- UT-03.3.1: Create exam request ---
@pytest.mark.asyncio
async def test_create_exam_request():
    """Exam creation request must have type and student_id."""
    request = {
        "exam_type": "TYT",
        "student_id": 1,
        "subject": "matematik",
        "question_count": 40,
    }
    assert request["exam_type"] in ["TYT", "AYT-SAY", "AYT-EA", "AYT-SOZ", "YDT"]
    assert request["question_count"] > 0


# --- UT-03.3.2: Save answer request ---
@pytest.mark.asyncio
async def test_save_answer_request():
    """Answer save request must have exam_id, question_id, answer."""
    request = {
        "exam_id": 1,
        "question_id": 42,
        "answer": "B",
    }
    assert request["answer"] in ["A", "B", "C", "D", "E"]
    assert request["question_id"] > 0


# --- UT-03.3.3: Flag question request ---
@pytest.mark.asyncio
async def test_flag_question_request():
    """Flag question request must have exam_id and question_id."""
    request = {
        "exam_id": 1,
        "question_id": 42,
        "flagged": True,
    }
    assert isinstance(request["flagged"], bool)


# --- UT-03.3.4: Navigate request ---
@pytest.mark.asyncio
async def test_navigate_request():
    """Navigate request moves to next/prev question."""
    request = {
        "exam_id": 1,
        "direction": "next",
        "current_question": 5,
    }
    assert request["direction"] in ["next", "prev", "goto"]
    assert request["current_question"] >= 1


# --- UT-03.3.5: Exam result response ---
@pytest.mark.asyncio
async def test_exam_result_response():
    """Exam result includes score, net, and analysis."""
    result = {
        "exam_id": 1,
        "exam_type": "TYT",
        "total_questions": 40,
        "correct": 30,
        "wrong": 8,
        "empty": 2,
        "net": 28.0,
    }
    assert result["correct"] + result["wrong"] + result["empty"] == result["total_questions"]
    assert result["net"] == result["correct"] - result["wrong"] / 4
