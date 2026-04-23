"""
Exam Models Alias Module
Backward compatibility module that re-exports exam models
Tests expect to import from models.exam_models
"""

# Re-export all exam models from their actual locations
from .database import (
    ExamQuestion,
    ExamSession,
    Question,
    StudentAnswer,
    StudentProfile,
)
from .enums import (
    SinavDurumu,
    SinavTipi,
    ZorlukSeviyesi,
)
from .exam import (
    KonuPerformansi,
    PerformansRaporu,
    SinavCevabi,
    SinavOturumu,
    SinavSonucu,
    SinavSorusu,
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
