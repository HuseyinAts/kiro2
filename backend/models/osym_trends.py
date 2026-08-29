"""
OSYM Linguistic Trends Model
Phase 14: Post-Exam Golden Dataset Evolution
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from .base import Base


class OSYMLinguisticTrend(Base):
    """
    Stores linguistic statistics (word lengths, readability) of OSYM exams
    to calibrate LLM question generation for future years.
    """

    __tablename__ = "osym_linguistic_trends"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True, nullable=False)
    exam_type = Column(String(50), index=True, nullable=False)  # TYT, AYT, YDT
    subject = Column(
        String(50), index=True, nullable=False
    )  # Türkçe, Matematik, Tarih vb.

    # NLP Metrics
    avg_word_length = Column(Float, nullable=False)
    avg_words_per_sentence = Column(Float, nullable=False)
    atesman_readability_index = Column(Float, nullable=False)
    question_length_chars = Column(
        Integer, nullable=False
    )  # Average char length per question
    cognitive_load_score = Column(
        Float, nullable=True
    )  # Gemini Ultra Cognitive Alignment Vector/Score

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OSYMLinguisticTrend {self.year} {self.exam_type} {self.subject}>"
