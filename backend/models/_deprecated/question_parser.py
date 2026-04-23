from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ParsedQuestion(Base):
    """Ayrıştırılmış soru modeli"""
    __tablename__ = 'parsed_questions'

    id = Column(Integer, primary_key=True, index=True)

    # Tespit bilgileri
    detection_confidence = Column(Float)
    ocr_confidence = Column(Float)

    # Soru metaveri
    question_number = Column(Integer)
    subject = Column(String(50))
    topic = Column(String(100))
    test_identifier = Column(String(50))
    page_number = Column(Integer)
    source_file = Column(String(255))

    # İçerik
    question_text = Column(Text)
    options = Column(JSON)  # {"A": "...", "B": "...", ...}
    correct_answer = Column(String(1), nullable=True)  # Manuel eklenecek

    # Görsel/Matematik flag'leri
    has_image = Column(Boolean, default=False)
    has_equation = Column(Boolean, default=False)

    # Kalite kontrol
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)

    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tezdeki 44 kötü keyword kontrolü
    has_problematic_keywords = Column(Boolean, default=False)
    problematic_keywords = Column(JSON, nullable=True)

class QuestionBatch(Base):
    """Toplu işlem takibi"""
    __tablename__ = 'question_batches'

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(100), unique=True)
    source_files = Column(JSON)
    total_pages = Column(Integer)
    processed_pages = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    status = Column(String(20))  # processing, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    error_log = Column(Text, nullable=True)
