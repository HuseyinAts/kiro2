"""KIRO2 — FSRS API Schemas"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    question_id: UUID
    is_correct:  bool
    response_ms: Optional[int] = Field(None, ge=0, le=300_000)
    item_b:      Optional[float] = Field(None, description="IRT güçlük (opsiyonel)")


class ReviewResponse(BaseModel):
    question_id:    str
    new_stability:  float
    new_difficulty: float
    interval_days:  int
    due_date:       datetime
    state:          int
    puan:           int   # 1-4


class DueItemResponse(BaseModel):
    question_id:    str
    stability:      float
    difficulty:     float
    due_date:       datetime
    retrievability: float
    urgency_score:  float
    state:          int
    reps:           int
    lapses:         int
    # Soru icerik alanlari (FSRS UI icin)
    stem:           Optional[str] = None
    options:        Optional[dict] = None
    subject_id:     Optional[str] = None


class DueCountResponse(BaseModel):
    count: int


class StatsResponse(BaseModel):
    total_cards:    int   = 0
    new_count:      int   = 0
    learning_count: int   = 0
    review_count:   int   = 0
    due_now:        int   = 0
    avg_stability:  float = 0.0
    total_lapses:   int   = 0
