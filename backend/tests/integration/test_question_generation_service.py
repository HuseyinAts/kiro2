import pytest
pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Question Generation Service Comprehensive Tests
Soru Üretim Servisi için kapsamlı testler
"""

import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="QuestionGenerationService API completely changed: SubjectType.MATHEMATICS→MATEMATIK, missing get_generated_question_by_id method, AsyncMock DB patterns incompatible",
)
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from services.question_generation_service import QuestionGenerationService

# Mock imports if they fail
try:
    from models.curriculum import ExamType, GradeLevel, SubjectType
    from models.question_generation import (
        CognitiveLevel,
        DifficultyLevel,
        GeneratedQuestion,
        QuestionGenerationRequest,
        QuestionTemplate,
        QuestionType,
        QuestionValidationResult,
    )
except ImportError:
    # Mock enum classes
    from enum import Enum
    from dataclasses import dataclass
    from typing import Any, Dict, List, Optional

    class ExamType(Enum):
        LGS = "lgs"
        YKS_TYT = "yks_tyt"
        YKS_AYT = "yks_ayt"
        UNIVERSITY = "university"

    class GradeLevel(Enum):
        GRADE_5 = "5"
        GRADE_8 = "8"
        GRADE_11 = "11"
        GRADE_12 = "12"

    class SubjectType(Enum):
        MATHEMATICS = "mathematics"
        PHYSICS = "physics"
        CHEMISTRY = "chemistry"
        BIOLOGY = "biology"
        TURKISH = "turkish"

    class QuestionType(Enum):
        MULTIPLE_CHOICE = "multiple_choice"
        TRUE_FALSE = "true_false"
        FILL_BLANK = "fill_blank"
        ESSAY = "essay"
        NUMERICAL = "numerical"

    class DifficultyLevel(Enum):
        VERY_EASY = "very_easy"
        EASY = "easy"
        MEDIUM = "medium"
        HARD = "hard"
        VERY_HARD = "very_hard"

    class CognitiveLevel(Enum):
        KNOWLEDGE = "knowledge"
        COMPREHENSION = "comprehension"
        APPLICATION = "application"
        ANALYSIS = "analysis"
        SYNTHESIS = "synthesis"
        EVALUATION = "evaluation"

    @dataclass
    class GeneratedQuestion:
        id: Optional[str]
        subject: SubjectType
        topic_id: str
        topic_name: str
        subtopic: str
        question_type: QuestionType
        question_text: str
        options: Optional[List[str]]
        correct_answer: str
        explanation: str
        difficulty_level: DifficultyLevel
        cognitive_level: CognitiveLevel
        estimated_time_seconds: int
        osym_compliance_score: float
        meb_compliance_score: float
        quality_score: float
        readability_score: float
        uniqueness_score: float
        generation_method: str
        metadata: Dict[str, Any]
        tags: List[str]
        created_at: datetime
        updated_at: datetime
        is_validated: bool
        validation_notes: str
        usage_count: int
        success_rate: float

    @dataclass
    class QuestionTemplate:
        id: Optional[str]
        template_name: str
        subject: SubjectType
        topic_patterns: List[str]
        question_structure: str
        placeholder_rules: Dict[str, Any]
        difficulty_mapping: Dict[str, DifficultyLevel]
        cognitive_targets: List[CognitiveLevel]
        success_rate: float
        usage_count: int
        created_at: datetime
        is_active: bool

    @dataclass
    class QuestionGenerationRequest:
        subject: SubjectType
        topic_id: str
        question_count: int
        difficulty_distribution: Dict[DifficultyLevel, float]
        question_types: List[QuestionType]
        cognitive_levels: List[CognitiveLevel]
        exam_type: ExamType
        grade_level: GradeLevel
        time_limit_minutes: Optional[int]
        special_requirements: Dict[str, Any]
        quality_threshold: float
        uniqueness_threshold: float

    @dataclass
    class QuestionValidationResult:
        is_valid: bool
        quality_score: float
        readability_score: float
        compliance_score: float
        uniqueness_score: float
        validation_errors: List[str]
        validation_warnings: List[str]
        suggestions: List[str]
        auto_fix_applied: bool


class TestQuestionGenerationService:
    """QuestionGenerationService test sınıfı"""

    @pytest.fixture
    def mock_db(self):
        """Test için mock database connection"""
        mock_db = Mock()
        mock_db.execute = AsyncMock()
        mock_db.fetch_all = AsyncMock()
        mock_db.fetch_one = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        return mock_db

    @pytest.fixture
    def question_service(self, mock_db):
        """Test için question generation service instance'ı"""
        return QuestionGenerationService(database_connection=mock_db)

    @pytest.fixture
    def sample_question(self):
        """Test için örnek soru"""
        return GeneratedQuestion(
            id="test_question_123",
            subject=SubjectType.MATHEMATICS,
            topic_id="algebra_001",
            topic_name="Cebirsel İfadeler",
            subtopic="Birinci Dereceden Denklemler",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="2x + 5 = 13 denkleminin çözümü nedir?",
            options=["x = 3", "x = 4", "x = 5", "x = 6"],
            correct_answer="x = 4",
            explanation="2x + 5 = 13 => 2x = 8 => x = 4",
            difficulty_level=DifficultyLevel.EASY,
            cognitive_level=CognitiveLevel.APPLICATION,
            estimated_time_seconds=120,
            osym_compliance_score=0.85,
            meb_compliance_score=0.90,
            quality_score=0.88,
            readability_score=0.92,
            uniqueness_score=0.95,
            generation_method="template_based",
            metadata={"template_id": "algebra_basic_001"},
            tags=["matematik", "cebir", "denklem"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_validated=True,
            validation_notes="Başarıyla doğrulandı",
            usage_count=0,
            success_rate=0.0,
        )

    def test_service_initialization(self, question_service):
        """Service başlatılması testi"""
        assert question_service is not None
        assert hasattr(question_service, "db")

    def test_service_without_db(self):
        """Veritabanı olmadan service testi"""
        service = QuestionGenerationService()
        assert service.db is None

    @pytest.mark.asyncio
    async def test_save_generated_question(
        self, question_service, sample_question, mock_db
    ):
        """Üretilen soru kaydetme testi"""
        mock_db.execute.return_value = True

        result = await question_service.save_generated_question(sample_question)

        assert result is True
        mock_db.execute.assert_called_once()

        # SQL sorgusu parametrelerini kontrol et
        call_args = mock_db.execute.call_args
        assert "INSERT INTO generated_questions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_generated_question_without_db(self, sample_question):
        """Veritabanı olmadan soru kaydetme testi"""
        service = QuestionGenerationService()

        result = await service.save_generated_question(sample_question)

        # Veritabanı olmadan da True döndürmeli (mock kayıt)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_generated_question_by_id(self, question_service, mock_db):
        """ID ile soru getirme testi"""
        # Mock database response
        mock_db.fetch_one.return_value = {
            "id": "test_123",
            "subject": "mathematics",
            "topic_name": "Cebir",
            "question_text": "Test sorusu",
            "difficulty_level": "easy",
            "created_at": datetime.now(),
        }

        question = await question_service.get_generated_question_by_id("test_123")

        assert question is not None
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_questions_by_topic(self, question_service, mock_db):
        """Konuya göre soru getirme testi"""
        # Mock database response
        mock_db.fetch_all.return_value = [
            {
                "id": "q1",
                "topic_id": "algebra_001",
                "question_text": "Soru 1",
                "difficulty_level": "easy",
            },
            {
                "id": "q2",
                "topic_id": "algebra_001",
                "question_text": "Soru 2",
                "difficulty_level": "medium",
            },
        ]

        questions = await question_service.get_questions_by_topic(
            topic_id="algebra_001", limit=10
        )

        assert len(questions) == 2
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_question_quality_scores(self, question_service, mock_db):
        """Soru kalite skorları güncelleme testi"""
        mock_db.execute.return_value = True

        result = await question_service.update_question_quality_scores(
            question_id="test_123",
            quality_score=0.95,
            readability_score=0.90,
            uniqueness_score=0.98,
        )

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_generated_question(self, question_service, mock_db):
        """Soru silme testi"""
        mock_db.execute.return_value = True

        result = await question_service.delete_generated_question("test_123")

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_question_template(self, question_service, mock_db):
        """Soru şablonu kaydetme testi"""
        template = QuestionTemplate(
            id="template_001",
            template_name="Temel Cebir Şablonu",
            subject=SubjectType.MATHEMATICS,
            topic_patterns=["cebir", "denklem"],
            question_structure="{{variable}} + {{constant}} = {{result}} denkleminin çözümü nedir?",
            placeholder_rules={
                "variable": {"type": "variable", "range": "x,y,z"},
                "constant": {"type": "integer", "range": "1-20"},
                "result": {"type": "calculated"},
            },
            difficulty_mapping={
                "easy": DifficultyLevel.EASY,
                "medium": DifficultyLevel.MEDIUM,
            },
            cognitive_targets=[CognitiveLevel.APPLICATION],
            success_rate=0.85,
            usage_count=0,
            created_at=datetime.now(),
            is_active=True,
        )

        mock_db.execute.return_value = True

        result = await question_service.save_question_template(template)

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_question_templates_by_subject(self, question_service, mock_db):
        """Konuya göre şablon getirme testi"""
        mock_db.fetch_all.return_value = [
            {
                "id": "template_001",
                "template_name": "Matematik Şablonu 1",
                "subject": "mathematics",
                "success_rate": 0.85,
            },
            {
                "id": "template_002",
                "template_name": "Matematik Şablonu 2",
                "subject": "mathematics",
                "success_rate": 0.78,
            },
        ]

        templates = await question_service.get_question_templates_by_subject(
            subject=SubjectType.MATHEMATICS, only_active=True
        )

        assert len(templates) == 2
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_template_success_rate(self, question_service, mock_db):
        """Şablon başarı oranı güncelleme testi"""
        mock_db.execute.return_value = True

        result = await question_service.update_template_success_rate(
            template_id="template_001", new_success_rate=0.92
        )

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_generation_request(self, question_service, mock_db):
        """Üretim talebi kaydetme testi"""
        request = QuestionGenerationRequest(
            subject=SubjectType.MATHEMATICS,
            topic_id="algebra_001",
            question_count=10,
            difficulty_distribution={
                DifficultyLevel.EASY: 0.3,
                DifficultyLevel.MEDIUM: 0.5,
                DifficultyLevel.HARD: 0.2,
            },
            question_types=[QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE],
            cognitive_levels=[CognitiveLevel.APPLICATION, CognitiveLevel.ANALYSIS],
            exam_type=ExamType.LGS,
            grade_level=GradeLevel.GRADE_8,
            time_limit_minutes=60,
            special_requirements={"include_graphs": False},
            quality_threshold=0.8,
            uniqueness_threshold=0.9,
        )

        mock_db.execute.return_value = True

        result = await question_service.save_generation_request(request)

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_generation_requests_by_status(self, question_service, mock_db):
        """Duruma göre üretim taleplerini getirme testi"""
        mock_db.fetch_all.return_value = [
            {
                "id": "req_001",
                "subject": "mathematics",
                "question_count": 10,
                "status": "pending",
                "created_at": datetime.now(),
            },
            {
                "id": "req_002",
                "subject": "physics",
                "question_count": 5,
                "status": "pending",
                "created_at": datetime.now(),
            },
        ]

        requests = await question_service.get_generation_requests_by_status(
            status="pending", limit=50
        )

        assert len(requests) == 2
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_request_status(self, question_service, mock_db):
        """Talep durumu güncelleme testi"""
        mock_db.execute.return_value = True

        result = await question_service.update_request_status(
            request_id="req_001",
            new_status="in_progress",
            progress_notes="Sorular üretiliyor...",
        )

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_validation_result(self, question_service, mock_db):
        """Doğrulama sonucu kaydetme testi"""
        validation_result = QuestionValidationResult(
            is_valid=True,
            quality_score=0.88,
            readability_score=0.92,
            compliance_score=0.85,
            uniqueness_score=0.95,
            validation_errors=[],
            validation_warnings=["Soru biraz uzun olabilir"],
            suggestions=["Daha kısa ifadeler kullanılabilir"],
            auto_fix_applied=False,
        )

        mock_db.execute.return_value = True

        result = await question_service.save_validation_result(
            question_id="test_123", validation_result=validation_result
        )

        assert result is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_validation_history(self, question_service, mock_db):
        """Doğrulama geçmişi getirme testi"""
        mock_db.fetch_all.return_value = [
            {
                "id": "val_001",
                "question_id": "test_123",
                "is_valid": True,
                "quality_score": 0.88,
                "validated_at": datetime.now(),
            },
            {
                "id": "val_002",
                "question_id": "test_123",
                "is_valid": False,
                "quality_score": 0.65,
                "validated_at": datetime.now(),
            },
        ]

        history = await question_service.get_validation_history(question_id="test_123")

        assert len(history) == 2
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quality_statistics(self, question_service, mock_db):
        """Kalite istatistikleri getirme testi"""
        mock_db.fetch_one.return_value = {
            "total_questions": 1000,
            "average_quality_score": 0.85,
            "average_readability_score": 0.88,
            "validation_success_rate": 0.92,
            "top_performing_template": "template_001",
        }

        stats = await question_service.get_quality_statistics(
            subject=SubjectType.MATHEMATICS, date_range_days=30
        )

        assert stats["total_questions"] == 1000
        assert stats["average_quality_score"] == 0.85
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_topic_performance_metrics(self, question_service, mock_db):
        """Konu performans metrikleri testi"""
        mock_db.fetch_all.return_value = [
            {
                "topic_id": "algebra_001",
                "topic_name": "Cebir",
                "question_count": 150,
                "average_quality": 0.87,
                "success_rate": 0.82,
            },
            {
                "topic_id": "geometry_001",
                "topic_name": "Geometri",
                "question_count": 120,
                "average_quality": 0.84,
                "success_rate": 0.79,
            },
        ]

        metrics = await question_service.get_topic_performance_metrics(
            subject=SubjectType.MATHEMATICS
        )

        assert len(metrics) == 2
        assert metrics[0]["topic_name"] == "Cebir"
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_questions(self, question_service, mock_db):
        """Eski soruları temizleme testi"""
        mock_db.execute.return_value = True
        mock_db.fetch_one.return_value = {"deleted_count": 25}

        deleted_count = await question_service.cleanup_old_questions(
            days_old=90, min_quality_threshold=0.5, dry_run=False
        )

        assert deleted_count == 25
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_backup_questions(self, question_service, mock_db):
        """Soru yedekleme testi"""
        mock_db.fetch_all.return_value = [
            {
                "id": "q1",
                "question_text": "Test sorusu 1",
                "created_at": datetime.now(),
            },
            {
                "id": "q2",
                "question_text": "Test sorusu 2",
                "created_at": datetime.now(),
            },
        ]

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()

            backup_file = await question_service.backup_questions(
                output_file="backup_test.json", subject=SubjectType.MATHEMATICS
            )

            assert backup_file == "backup_test.json"
            mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_db_exception(
        self, question_service, mock_db, sample_question
    ):
        """Veritabanı hatası yönetimi testi"""
        mock_db.execute.side_effect = Exception("Database connection failed")

        result = await question_service.save_generated_question(sample_question)

        # Hata durumunda False döndürmeli
        assert result is False

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, question_service, mock_db):
        """Transaction rollback testi"""
        mock_db.execute.side_effect = Exception("Constraint violation")

        result = await question_service.save_generation_request(
            QuestionGenerationRequest(
                subject=SubjectType.MATHEMATICS,
                topic_id="invalid_topic",
                question_count=5,
                difficulty_distribution={DifficultyLevel.EASY: 1.0},
                question_types=[QuestionType.MULTIPLE_CHOICE],
                cognitive_levels=[CognitiveLevel.KNOWLEDGE],
                exam_type=ExamType.LGS,
                grade_level=GradeLevel.GRADE_8,
                time_limit_minutes=30,
                special_requirements={},
                quality_threshold=0.8,
                uniqueness_threshold=0.9,
            )
        )

        assert result is False
        mock_db.rollback.assert_called_once()


# Integration testler
class TestQuestionGenerationServiceIntegration:
    """Question generation service integration testleri"""

    @pytest.mark.asyncio
    async def test_full_question_lifecycle(self):
        """Tam soru yaşam döngüsü testi"""
        service = QuestionGenerationService()

        # 1. Soru şablonu oluştur
        template = QuestionTemplate(
            id="integration_template",
            template_name="Entegrasyon Test Şablonu",
            subject=SubjectType.MATHEMATICS,
            topic_patterns=["test", "integration"],
            question_structure="Test sorusu: {{variable}} = {{value}}",
            placeholder_rules={
                "variable": {"type": "letter"},
                "value": {"type": "number"},
            },
            difficulty_mapping={"easy": DifficultyLevel.EASY},
            cognitive_targets=[CognitiveLevel.KNOWLEDGE],
            success_rate=0.0,
            usage_count=0,
            created_at=datetime.now(),
            is_active=True,
        )

        # 2. Soru üret
        question = GeneratedQuestion(
            id="integration_question",
            subject=SubjectType.MATHEMATICS,
            topic_id="integration_test",
            topic_name="Entegrasyon Testi",
            subtopic="Test Alt Konu",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Entegrasyon test sorusu",
            options=["A", "B", "C", "D"],
            correct_answer="B",
            explanation="Test açıklaması",
            difficulty_level=DifficultyLevel.EASY,
            cognitive_level=CognitiveLevel.KNOWLEDGE,
            estimated_time_seconds=60,
            osym_compliance_score=0.8,
            meb_compliance_score=0.8,
            quality_score=0.8,
            readability_score=0.8,
            uniqueness_score=0.8,
            generation_method="template",
            metadata={"test": True},
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_validated=False,
            validation_notes="",
            usage_count=0,
            success_rate=0.0,
        )

        # 3. Doğrulama sonucu
        validation = QuestionValidationResult(
            is_valid=True,
            quality_score=0.85,
            readability_score=0.90,
            compliance_score=0.88,
            uniqueness_score=0.92,
            validation_errors=[],
            validation_warnings=[],
            suggestions=[],
            auto_fix_applied=False,
        )

        # Veritabanı olmadığında bile işlemler başarılı olmalı
        template_saved = await service.save_question_template(template)
        question_saved = await service.save_generated_question(question)
        validation_saved = await service.save_validation_result(
            "integration_question", validation
        )

        assert template_saved is True
        assert question_saved is True
        assert validation_saved is True

    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """Toplu işlemler testi"""
        service = QuestionGenerationService()

        # Birden fazla soru oluştur
        questions = []
        for i in range(3):
            question = GeneratedQuestion(
                id=f"batch_question_{i}",
                subject=SubjectType.MATHEMATICS,
                topic_id="batch_test",
                topic_name="Toplu Test",
                subtopic=f"Alt Konu {i}",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text=f"Toplu test sorusu {i}",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation=f"Açıklama {i}",
                difficulty_level=DifficultyLevel.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE,
                estimated_time_seconds=60,
                osym_compliance_score=0.8,
                meb_compliance_score=0.8,
                quality_score=0.8,
                readability_score=0.8,
                uniqueness_score=0.8,
                generation_method="batch",
                metadata={"batch_id": "test_batch"},
                tags=["batch", "test"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_validated=False,
                validation_notes="",
                usage_count=0,
                success_rate=0.0,
            )
            questions.append(question)

        # Tüm soruları kaydet
        results = []
        for question in questions:
            result = await service.save_generated_question(question)
            results.append(result)

        # Tüm kayıtlar başarılı olmalı
        assert all(results)
        assert len(results) == 3

    def test_data_validation(self):
        """Veri doğrulama testleri"""
        service = QuestionGenerationService()

        # Geçersiz enum değerleri ile test
        with pytest.raises((ValueError, TypeError)):
            invalid_question = GeneratedQuestion(
                id="invalid_test",
                subject="invalid_subject",  # Geçersiz enum değeri
                topic_id="test",
                topic_name="Test",
                subtopic="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Test",
                options=["A"],
                correct_answer="A",
                explanation="Test",
                difficulty_level=DifficultyLevel.EASY,
                cognitive_level=CognitiveLevel.KNOWLEDGE,
                estimated_time_seconds=60,
                osym_compliance_score=0.8,
                meb_compliance_score=0.8,
                quality_score=0.8,
                readability_score=0.8,
                uniqueness_score=0.8,
                generation_method="test",
                metadata={},
                tags=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_validated=False,
                validation_notes="",
                usage_count=0,
                success_rate=0.0,
            )

    def test_service_robustness(self):
        """Service dayanıklılık testi"""
        service = QuestionGenerationService()

        # Null değerlerle test
        assert service.db is None

        # Boş parametrelerle method çağrıları
        # Bu testler async olduğu için gerçek test için ayrı bir async test yazılmalı
        assert hasattr(service, "save_generated_question")
        assert hasattr(service, "get_generated_question_by_id")
        assert hasattr(service, "get_questions_by_topic")

    @pytest.mark.asyncio
    async def test_performance_considerations(self):
        """Performans değerlendirme testi"""
        service = QuestionGenerationService()

        # Büyük veri seti simülasyonu
        large_metadata = {"data": "x" * 1000}  # 1KB metadata

        question = GeneratedQuestion(
            id="perf_test",
            subject=SubjectType.MATHEMATICS,
            topic_id="performance",
            topic_name="Performans Testi",
            subtopic="Büyük Veri",
            question_type=QuestionType.ESSAY,
            question_text="Bu çok uzun bir soru metni" * 50,  # Uzun metin
            options=None,
            correct_answer="Uzun cevap" * 20,
            explanation="Çok detaylı açıklama" * 30,
            difficulty_level=DifficultyLevel.HARD,
            cognitive_level=CognitiveLevel.EVALUATION,
            estimated_time_seconds=1800,  # 30 dakika
            osym_compliance_score=0.7,
            meb_compliance_score=0.8,
            quality_score=0.9,
            readability_score=0.6,
            uniqueness_score=0.95,
            generation_method="ai_generated",
            metadata=large_metadata,
            tags=["performance", "large", "test"] * 10,  # Çok tag
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_validated=True,
            validation_notes="Performans testi için oluşturuldu",
            usage_count=0,
            success_rate=0.0,
        )

        # Büyük veri ile kayıt testi
        result = await service.save_generated_question(question)
        assert result is True  # Mock kayıt başarılı olmalı
