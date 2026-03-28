# -*- coding: utf-8 -*-
"""
Exam Models Alias Module
Backward compatibility module that re-exports exam models
Tests expect to import from models.exam_models
"""

# Re-export all exam models from their actual locations
from .exam import (
    SinavSorusu,
    SinavOturumu,
    SinavCevabi,
    KonuPerformansi,
    SinavSonucu,
    PerformansRaporu,
)

from .database import (
    Question,
    ExamSession,
    ExamQuestion,
    StudentAnswer,
    StudentProfile,
)

from .enums import (
    SinavDurumu,
    SinavTipi,
    ZorlukSeviyesi,
)

# Backward compatibility aliases
Student = StudentProfile

__all__ = [
    # Exam models (Turkish)
    "SinavSorusu",
    "SinavOturumu",
    "SinavCevabi",
    "KonuPerformansi",
    "SinavSonucu",
    "PerformansRaporu",
    # Exam models (English)
    "Question",
    "ExamSession",
    "ExamQuestion",
    "StudentAnswer",
    # User models
    "StudentProfile",
    "Student",
    # Enums
    "SinavDurumu",
    "SinavTipi",
    "ZorlukSeviyesi",
]
