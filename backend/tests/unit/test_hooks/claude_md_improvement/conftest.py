"""
Test fixtures for CLAUDE.md Self-Improvement hooks.

Bu conftest.py modül yollarını ayarlar ve ortak fixtures sağlar.
"""

import os
import sys

# Backend dizinini Python path'e ekle
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def sample_question():
    """Örnek KIRO2 sorusu."""
    return {
        "content": "2x + 3 = 7 denkleminin çözümü nedir?",
        "options": ["x = 2", "x = 3", "x = 4", "x = 5"],
        "correct_answer": 0,
        "difficulty": 0.5,
        "discrimination": 1.0,
        "guessing": 0.2,
        "subject": "matematik",
        "grade_level": 9,
    }


@pytest.fixture
def sample_feedback():
    """Örnek feedback verisi."""
    return {
        "task_id": "task-123",
        "rule_id": "rule-001",
        "success": True,
        "context": "Test context",
        "outcome": "Task completed successfully",
    }
