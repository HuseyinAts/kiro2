"""
ÖSYM Question Database Models
Task 53: ÖSYM Soru Veri Toplama ve Analiz
Requirements: REQ-48.1-48.16
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class OSYMQuestion(Base):
    """
    ÖSYM Soru Modeli

    REQ-48.1: Her soruyu benzersiz ID ile veritabanına kaydetmek
    REQ-48.2-48.8: Soru bileşenlerini kaydetmek
    """

    __tablename__ = "osym_questions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        String(16), unique=True, nullable=False, index=True
    )  # REQ-48.1: Benzersiz ID

    # Soru İçeriği (REQ-48.2-48.4)
    stem = Column(Text, nullable=False)  # REQ-48.2: Soru gövdesi
    key = Column(String(1), nullable=False)  # REQ-48.3: Doğru cevap (A-E)
    distractors = Column(JSON, nullable=False)  # REQ-48.4: Çeldiriciler listesi

    # Metadata (REQ-48.5)
    year = Column(Integer, nullable=False, index=True)
    exam_type = Column(String(10), nullable=False, index=True)  # TYT, AYT, YDT
    subject = Column(String(50), nullable=False, index=True)  # Matematik, Türkçe, vb.
    topic = Column(String(100))  # Alt konu
    subtopic = Column(String(100))  # Daha detaylı konu

    # Görsel ve Formül (REQ-48.6-48.8)
    has_image = Column(Boolean, default=False)  # REQ-48.7: Görsel var mı?
    image_url = Column(String(500))  # Görsel URL'i
    has_formula = Column(Boolean, default=False)  # REQ-48.8: Formül var mı?
    formula_latex = Column(Text)  # LaTeX formatında formül

    # Visual content support (Phase 1: Tables, Phase 2: Graphs, Phase 3: Geometry)
    visual_content = Column(
        JSON
    )  # Structured visual content (tables, graphs, diagrams)

    # Bloom Taxonomy (REQ-48.9-48.12)
    bloom_level = Column(Integer)  # 1-6 arası Bloom seviyesi
    bloom_category = Column(
        String(50)
    )  # bilgi, kavrama, uygulama, analiz, sentez, değerlendirme
    bloom_confidence = Column(Float)  # ML model güven skoru (0-1)

    # IRT Parameters (REQ-48.13-48.16)
    irt_difficulty = Column(Float)  # b parametresi (-3 to +3)
    irt_discrimination = Column(Float)  # a parametresi (0 to 2)
    irt_guessing = Column(Float)  # c parametresi (0 to 1)
    irt_upper_asymptote = Column(Float)  # d parametresi (0 to 1)
    irt_calibrated = Column(Boolean, default=False)  # Kalibrasyon yapıldı mı?
    irt_sample_size = Column(Integer)  # Kalibrasyon için kullanılan öğrenci sayısı

    # Kalite Metrikleri (REQ-48.49-48.56)
    quality_score = Column(Float)  # 0-100 arası kalite skoru
    bleu_score = Column(Float)  # BLEU metriği
    rouge_score = Column(Float)  # ROUGE metriği
    bert_score = Column(Float)  # BERTScore metriği

    # Durum ve Onay
    status = Column(String(20), default="pending")  # pending, approved, rejected
    reviewed_by = Column(String, ForeignKey("users.id"))  # Uzman reviewer
    review_notes = Column(Text)  # İnceleme notları

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime)  # Scraping tarihi

    # Raw Data
    raw_text = Column(Text)  # Orijinal soru metni
    source_url = Column(String(500))  # Kaynak URL

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    student_responses = relationship(
        "StudentQuestionResponse", back_populates="question"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_osym_year_exam", "year", "exam_type"),
        Index("idx_osym_subject_topic", "subject", "topic"),
        Index("idx_osym_bloom", "bloom_level", "bloom_category"),
        Index("idx_osym_irt_difficulty", "irt_difficulty"),
        Index("idx_osym_quality", "quality_score"),
        Index("idx_osym_status", "status"),
    )

    def __repr__(self):
        return f"<OSYMQuestion(id={self.question_id}, year={self.year}, exam={self.exam_type}, subject={self.subject})>"

    def to_dict(self):
        """Soru verisini dictionary'e çevir"""
        return {
            "question_id": self.question_id,
            "stem": self.stem,
            "key": self.key,
            "distractors": self.distractors,
            "year": self.year,
            "exam_type": self.exam_type,
            "subject": self.subject,
            "topic": self.topic,
            "bloom_level": self.bloom_level,
            "bloom_category": self.bloom_category,
            "irt_difficulty": self.irt_difficulty,
            "irt_discrimination": self.irt_discrimination,
            "quality_score": self.quality_score,
            "status": self.status,
            "has_image": self.has_image,
            "has_formula": self.has_formula,
            "visual_content": self.visual_content,
        }


class StudentQuestionResponse(Base):
    """
    Öğrenci Soru Yanıtları
    IRT kalibrasyonu için gerekli
    """

    __tablename__ = "student_question_responses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    question_id = Column(
        String(16), ForeignKey("osym_questions.question_id"), nullable=False
    )

    # Yanıt Bilgileri
    selected_answer = Column(String(1))  # A-E veya NULL (boş)
    is_correct = Column(Boolean)
    response_time_seconds = Column(Integer)  # Yanıt süresi

    # Bağlam
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id"))
    attempt_number = Column(Integer, default=1)  # Kaçıncı deneme

    # Timestamps
    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    question = relationship("OSYMQuestion", back_populates="student_responses")

    # Indexes
    __table_args__ = (
        Index("idx_student_question", "student_id", "question_id"),
        Index("idx_question_responses", "question_id", "is_correct"),
    )

    def __repr__(self):
        return f"<StudentQuestionResponse(student={self.student_id}, question={self.question_id}, correct={self.is_correct})>"


class QuestionGenerationLog(Base):
    """
    Soru Üretim Logları
    LLM ile üretilen soruların takibi için
    """

    __tablename__ = "question_generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(16), ForeignKey("osym_questions.question_id"))

    # Üretim Bilgileri
    generation_method = Column(String(50))  # gpt4, t5, bart, etc.
    prompt_used = Column(Text)
    model_version = Column(String(50))
    temperature = Column(Float)

    # Kalite Metrikleri
    initial_quality_score = Column(Float)
    final_quality_score = Column(Float)
    human_review_score = Column(Float)

    # A/B Test
    ab_test_group = Column(String(10))  # A, B, control
    ab_test_id = Column(String(50))

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QuestionGenerationLog(question={self.question_id}, method={self.generation_method})>"


class QuestionGenerationBatch(Base):
    """
    Batch Question Generation Tracking
    For parallel question generation jobs
    """

    __tablename__ = "question_generation_batches"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)

    # Batch Configuration
    batch_size = Column(Integer, nullable=False)
    exam_type = Column(String(10), nullable=False)
    subject = Column(String(50), nullable=False)
    generation_method = Column(String(50), nullable=False)

    # Status Tracking
    status = Column(
        String(20), default="pending", index=True
    )  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Results
    generated_question_ids = Column(JSON, default=list)
    errors = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Indexes
    __table_args__ = (Index("idx_batch_status", "status", "created_at"),)

    def __repr__(self):
        return f"<QuestionGenerationBatch(task_id={self.task_id}, status={self.status}, progress={self.progress})>"
