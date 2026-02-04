"""
Automated Question Generator Comprehensive Tests
Otomatik Soru Üretim Sistemi için kapsamlı testler
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from core.automated_question_generator import AutomatedQuestionGenerator

# Mock imports if they fail
try:
    from models.curriculum import (
        ExamType,
        MEBCurriculumStandard,
        OSYMStandard,
        SubjectType,
    )
    from models.question_generation import (
        CognitiveLevel,
        DifficultyLevel,
        GeneratedQuestion,
        OSYMQuestionFormat,
        QuestionBankStatus,
        QuestionGenerationRequest,
        QuestionTemplate,
        QuestionType,
        QuestionValidationResult,
    )
except ImportError:
    # Mock missing models
    from enum import Enum
    from dataclasses import dataclass
    from typing import Any, Dict, List, Optional

    class ExamType(Enum):
        LGS = "lgs"
        YKS_TYT = "yks_tyt"
        YKS_AYT = "yks_ayt"

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

    class DifficultyLevel(Enum):
        EASY = "easy"
        MEDIUM = "medium"
        HARD = "hard"

    class CognitiveLevel(Enum):
        KNOWLEDGE = "knowledge"
        COMPREHENSION = "comprehension"
        APPLICATION = "application"
        ANALYSIS = "analysis"

    class QuestionBankStatus(Enum):
        PENDING = "pending"
        GENERATING = "generating"
        COMPLETED = "completed"
        FAILED = "failed"

    @dataclass
    class OSYMQuestionFormat:
        question_number: int
        question_text: str
        options: List[str]
        correct_answer: str
        explanation: str

    @dataclass
    class GeneratedQuestion:
        id: str
        subject: SubjectType
        topic_id: str
        topic_name: str
        subtopic: str
        question_type: QuestionType
        question_text: str
        options: List[str]
        correct_answer: str
        explanation: str
        difficulty_level: DifficultyLevel
        cognitive_level: CognitiveLevel
        estimated_time_seconds: int
        osym_format: OSYMQuestionFormat
        osym_compliance_score: float
        meb_compliance_score: float
        quality_score: float
        readability_score: float
        uniqueness_score: float
        generation_method: str
        generation_parameters: Dict[str, Any]
        source_materials: List[str]
        is_validated: bool
        validation_errors: List[str]
        is_approved: bool
        approved_by: Optional[str]
        created_at: datetime
        updated_at: datetime
        last_used_at: Optional[datetime]
        meb_standard_id: Optional[str]
        learning_outcome_ids: List[str]

    @dataclass
    class QuestionTemplate:
        id: str
        name: str
        description: str
        subject: SubjectType
        topic_pattern: str
        question_template: str
        options_template: List[str]
        explanation_template: str
        template_variables: Dict[str, Any]
        difficulty_level: DifficultyLevel
        cognitive_level: CognitiveLevel
        usage_count: int
        success_rate: float
        created_by: str
        is_active: bool
        created_at: datetime
        updated_at: datetime

    @dataclass
    class QuestionGenerationRequest:
        id: str
        subject: SubjectType
        topic_id: str
        exam_type: ExamType
        grade_level: Optional[str]
        question_count: int
        question_types: List[QuestionType]
        difficulty_distribution: Dict[DifficultyLevel, float]
        cognitive_distribution: Dict[CognitiveLevel, float]
        min_quality_score: float
        min_osym_compliance: float
        min_meb_compliance: float
        generation_method: str
        use_existing_templates: bool
        allow_duplicates: bool
        requested_by: str
        priority: str
        deadline: Optional[datetime]
        status: str
        created_at: datetime

    @dataclass
    class QuestionValidationResult:
        is_valid: bool
        quality_score: float
        readability_score: float
        osym_compliance_score: float
        meb_compliance_score: float
        uniqueness_score: float
        errors: List[str]
        warnings: List[str]
        suggestions: List[str]

    @dataclass
    class MEBCurriculumStandard:
        id: str
        subject: SubjectType
        grade_level: str
        topic: str
        learning_outcome: str
        description: str

    @dataclass
    class OSYMStandard:
        id: str
        exam_type: ExamType
        subject: SubjectType
        topic: str
        specification: str
        weight: float


class TestAutomatedQuestionGenerator:
    """AutomatedQuestionGenerator test sınıfı"""

    @pytest.fixture
    def mock_services(self):
        """Test için mock servisler"""
        return {
            "curriculum_service": Mock(),
            "llm_service": Mock(),
            "database_service": Mock(),
            "cache_service": Mock(),
        }

    @pytest.fixture
    def generator(self, mock_services):
        """Test için AutomatedQuestionGenerator instance'ı"""
        return AutomatedQuestionGenerator(**mock_services)

    @pytest.fixture
    def sample_question_template(self):
        """Test için örnek soru şablonu"""
        return QuestionTemplate(
            id="template_001",
            name="Matematik Temel Şablon",
            description="Temel matematik soruları için şablon",
            subject=SubjectType.MATHEMATICS,
            topic_pattern="cebir_*",
            question_template="{{variable}} + {{number}} = {{result}} ise {{variable}} kaçtır?",
            options_template=["{{correct}}", "{{wrong1}}", "{{wrong2}}", "{{wrong3}}"],
            explanation_template="{{variable}} = {{result}} - {{number}} = {{answer}}",
            template_variables={
                "variable": "x",
                "number": "5",
                "result": "13",
                "correct": "8",
                "wrong1": "7",
                "wrong2": "9",
                "wrong3": "10",
                "answer": "8",
            },
            difficulty_level=DifficultyLevel.EASY,
            cognitive_level=CognitiveLevel.APPLICATION,
            usage_count=10,
            success_rate=0.85,
            created_by="system",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def sample_generation_request(self):
        """Test için örnek üretim talebi"""
        return QuestionGenerationRequest(
            id="req_001",
            subject=SubjectType.MATHEMATICS,
            topic_id="cebir_001",
            exam_type=ExamType.LGS,
            grade_level="8",
            question_count=10,
            question_types=[QuestionType.MULTIPLE_CHOICE],
            difficulty_distribution={
                DifficultyLevel.EASY: 0.4,
                DifficultyLevel.MEDIUM: 0.4,
                DifficultyLevel.HARD: 0.2,
            },
            cognitive_distribution={
                CognitiveLevel.KNOWLEDGE: 0.2,
                CognitiveLevel.COMPREHENSION: 0.3,
                CognitiveLevel.APPLICATION: 0.3,
                CognitiveLevel.ANALYSIS: 0.2,
            },
            min_quality_score=0.7,
            min_osym_compliance=0.8,
            min_meb_compliance=0.8,
            generation_method="template_based",
            use_existing_templates=True,
            allow_duplicates=False,
            requested_by="teacher_001",
            priority="normal",
            deadline=None,
            status="pending",
            created_at=datetime.now(),
        )

    def test_generator_initialization(self, generator):
        """Generator başlatma testi"""
        assert generator is not None
        assert generator.target_questions_per_topic == 1000
        assert generator.min_osym_compliance_score == 0.8
        assert generator.min_meb_compliance_score == 0.8
        assert generator.min_quality_score == 0.7
        assert hasattr(generator, "question_templates")
        assert hasattr(generator, "generation_stats")
        assert hasattr(generator, "osym_format_rules")

    @pytest.mark.asyncio
    async def test_initialize_success(self, generator):
        """Başarılı sistem başlatma testi"""
        with patch.object(
            generator, "_load_question_templates", new_callable=AsyncMock
        ) as mock_load:
            with patch.object(
                generator, "_analyze_current_question_bank", new_callable=AsyncMock
            ) as mock_analyze:
                mock_load.return_value = True
                mock_analyze.return_value = True

                result = await generator.initialize()

                assert result is True
                mock_load.assert_called_once()
                mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, generator):
        """Sistem başlatma hatası testi"""
        with patch.object(
            generator, "_load_question_templates", new_callable=AsyncMock
        ) as mock_load:
            mock_load.side_effect = Exception("Template loading failed")

            result = await generator.initialize()

            assert result is False

    @pytest.mark.asyncio
    async def test_generate_questions_for_topic_success(self, generator):
        """Başarılı konu soru üretimi testi"""
        topic_id = "cebir_001"
        subject = SubjectType.MATHEMATICS
        exam_type = ExamType.LGS

        # Mock dependencies
        with patch.object(
            generator, "_get_current_question_count", new_callable=AsyncMock
        ) as mock_count:
            with patch.object(
                generator, "_get_meb_standards_for_topic", new_callable=AsyncMock
            ) as mock_meb:
                with patch.object(
                    generator, "_get_osym_standards_for_topic", new_callable=AsyncMock
                ) as mock_osym:
                    with patch.object(
                        generator, "_create_generation_plan", new_callable=AsyncMock
                    ) as mock_plan:
                        with patch.object(
                            generator,
                            "_generate_questions_batch",
                            new_callable=AsyncMock,
                        ) as mock_batch:
                            with patch.object(
                                generator, "validate_question", new_callable=AsyncMock
                            ) as mock_validate:
                                with patch.object(
                                    generator,
                                    "_save_generated_question",
                                    new_callable=AsyncMock,
                                ) as mock_save:
                                    mock_count.return_value = 0  # Hiç soru yok
                                    mock_meb.return_value = []
                                    mock_osym.return_value = []
                                    mock_plan.return_value = [{"id": "plan_1"}]

                                    # Mock generated question
                                    sample_question = GeneratedQuestion(
                                        id="q_001",
                                        subject=subject,
                                        topic_id=topic_id,
                                        topic_name="Cebir",
                                        subtopic="Denklemler",
                                        question_type=QuestionType.MULTIPLE_CHOICE,
                                        question_text="x + 5 = 13 ise x kaçtır?",
                                        options=["8", "7", "9", "10"],
                                        correct_answer="8",
                                        explanation="x = 13 - 5 = 8",
                                        difficulty_level=DifficultyLevel.EASY,
                                        cognitive_level=CognitiveLevel.APPLICATION,
                                        estimated_time_seconds=120,
                                        osym_format=OSYMQuestionFormat(
                                            1, "Test", ["A", "B"], "A", "Test"
                                        ),
                                        osym_compliance_score=0.9,
                                        meb_compliance_score=0.85,
                                        quality_score=0.8,
                                        readability_score=0.9,
                                        uniqueness_score=0.95,
                                        generation_method="template",
                                        generation_parameters={},
                                        source_materials=[],
                                        is_validated=False,
                                        validation_errors=[],
                                        is_approved=False,
                                        approved_by=None,
                                        created_at=datetime.now(),
                                        updated_at=datetime.now(),
                                        last_used_at=None,
                                        meb_standard_id=None,
                                        learning_outcome_ids=[],
                                    )

                                    mock_batch.return_value = [sample_question]
                                    mock_validate.return_value = (
                                        QuestionValidationResult(
                                            is_valid=True,
                                            quality_score=0.8,
                                            readability_score=0.9,
                                            osym_compliance_score=0.9,
                                            meb_compliance_score=0.85,
                                            uniqueness_score=0.95,
                                            errors=[],
                                            warnings=[],
                                            suggestions=[],
                                        )
                                    )
                                    mock_save.return_value = True

                                    questions = (
                                        await generator.generate_questions_for_topic(
                                            topic_id, subject, exam_type, target_count=5
                                        )
                                    )

                                    assert len(questions) == 1
                                    assert questions[0].is_validated is True
                                    mock_save.assert_called()

    @pytest.mark.asyncio
    async def test_generate_questions_for_topic_no_questions_needed(self, generator):
        """Yeterli soru mevcut olduğunda test"""
        topic_id = "cebir_001"

        with patch.object(
            generator, "_get_current_question_count", new_callable=AsyncMock
        ) as mock_count:
            mock_count.return_value = 1000  # Yeterli soru var

            questions = await generator.generate_questions_for_topic(
                topic_id, SubjectType.MATHEMATICS, ExamType.LGS
            )

            assert len(questions) == 0  # Yeni soru üretilmemeli

    @pytest.mark.asyncio
    async def test_process_generation_request_success(
        self, generator, sample_generation_request
    ):
        """Başarılı üretim talebi işleme testi"""
        with patch.object(
            generator, "_save_generation_request", new_callable=AsyncMock
        ) as mock_save_req:
            with patch.object(
                generator, "generate_questions_for_topic", new_callable=AsyncMock
            ) as mock_generate:
                with patch.object(
                    generator, "_update_generation_request", new_callable=AsyncMock
                ) as mock_update:
                    # Mock soru üretimi
                    mock_questions = [Mock() for _ in range(5)]
                    for i, q in enumerate(mock_questions):
                        q.id = f"q_{i}"
                    mock_generate.return_value = mock_questions

                    result = await generator.process_generation_request(
                        sample_generation_request
                    )

                    assert result["request_id"] == sample_generation_request.id
                    assert result["requested_count"] == 10
                    assert result["generated_count"] == 5
                    assert result["success_rate"] == 0.5
                    assert result["status"] == "completed"
                    assert len(result["questions"]) == 5

                    mock_save_req.assert_called_once()
                    mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_generation_request_failure(
        self, generator, sample_generation_request
    ):
        """Üretim talebi işleme hatası testi"""
        with patch.object(
            generator, "_save_generation_request", new_callable=AsyncMock
        ) as mock_save:
            mock_save.side_effect = Exception("Database error")

            result = await generator.process_generation_request(
                sample_generation_request
            )

            assert result["status"] == "error"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_validate_question_osym_format(self, generator):
        """ÖSYM format doğrulama testi"""
        # Geçerli ÖSYM formatında soru
        valid_question = GeneratedQuestion(
            id="valid_q",
            subject=SubjectType.MATHEMATICS,
            topic_id="test",
            topic_name="Test",
            subtopic="Test",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Bu geçerli bir soru metnidir?",
            options=["A) Evet", "B) Hayır", "C) Belki", "D) Bilmiyorum"],
            correct_answer="A",
            explanation="Geçerli açıklama",
            difficulty_level=DifficultyLevel.MEDIUM,
            cognitive_level=CognitiveLevel.COMPREHENSION,
            estimated_time_seconds=120,
            osym_format=OSYMQuestionFormat(
                1, "Test", ["A", "B", "C", "D"], "A", "Test"
            ),
            osym_compliance_score=0.9,
            meb_compliance_score=0.85,
            quality_score=0.8,
            readability_score=0.9,
            uniqueness_score=0.95,
            generation_method="test",
            generation_parameters={},
            source_materials=[],
            is_validated=False,
            validation_errors=[],
            is_approved=False,
            approved_by=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_used_at=None,
            meb_standard_id=None,
            learning_outcome_ids=[],
        )

        result = await generator.validate_question(valid_question)

        assert result.is_valid is True
        assert result.osym_compliance_score >= generator.min_osym_compliance_score

    @pytest.mark.asyncio
    async def test_validate_question_invalid_format(self, generator):
        """Geçersiz ÖSYM format doğrulama testi"""
        # Geçersiz ÖSYM formatında soru (çok az seçenek)
        invalid_question = GeneratedQuestion(
            id="invalid_q",
            subject=SubjectType.MATHEMATICS,
            topic_id="test",
            topic_name="Test",
            subtopic="Test",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Bu geçersiz bir soru metnidir?",
            options=["A) Evet", "B) Hayır"],  # Sadece 2 seçenek (min 4 gerekli)
            correct_answer="A",
            explanation="Açıklama",
            difficulty_level=DifficultyLevel.MEDIUM,
            cognitive_level=CognitiveLevel.COMPREHENSION,
            estimated_time_seconds=120,
            osym_format=OSYMQuestionFormat(1, "Test", ["A", "B"], "A", "Test"),
            osym_compliance_score=0.9,
            meb_compliance_score=0.85,
            quality_score=0.8,
            readability_score=0.9,
            uniqueness_score=0.95,
            generation_method="test",
            generation_parameters={},
            source_materials=[],
            is_validated=False,
            validation_errors=[],
            is_approved=False,
            approved_by=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_used_at=None,
            meb_standard_id=None,
            learning_outcome_ids=[],
        )

        result = await generator.validate_question(invalid_question)

        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_create_from_template_success(
        self, generator, sample_question_template
    ):
        """Şablondan soru oluşturma başarı testi"""
        topic_variables = {
            "topic_name": "Birinci Dereceden Denklemler",
            "difficulty": "easy",
        }

        with patch.object(
            generator, "_generate_template_variables", new_callable=AsyncMock
        ) as mock_vars:
            mock_vars.return_value = sample_question_template.template_variables

            question = await generator.create_from_template(
                sample_question_template, "test_topic", topic_variables
            )

            assert question is not None
            assert question.subject == sample_question_template.subject
            assert (
                question.difficulty_level == sample_question_template.difficulty_level
            )
            assert question.cognitive_level == sample_question_template.cognitive_level
            assert len(question.options) >= 4  # ÖSYM minimum

    @pytest.mark.asyncio
    async def test_create_from_template_failure(
        self, generator, sample_question_template
    ):
        """Şablondan soru oluşturma hata testi"""
        with patch.object(
            generator, "_generate_template_variables", new_callable=AsyncMock
        ) as mock_vars:
            mock_vars.side_effect = Exception("Template variable generation failed")

            question = await generator.create_from_template(
                sample_question_template, "test_topic", {}
            )

            assert question is None

    @pytest.mark.asyncio
    async def test_get_question_bank_status(self, generator):
        """Soru bankası durumu getirme testi"""
        with patch.object(
            generator, "_analyze_current_question_bank", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = {
                "total_questions": 5000,
                "by_subject": {"mathematics": 2000, "physics": 1500, "chemistry": 1500},
                "by_difficulty": {"easy": 2000, "medium": 2000, "hard": 1000},
            }

            status = await generator.get_question_bank_status()

            assert status is not None
            assert "total_questions" in status
            assert "by_subject" in status
            assert "by_difficulty" in status

    @pytest.mark.asyncio
    async def test_get_generation_statistics(self, generator):
        """Üretim istatistikleri getirme testi"""
        # Mock istatistikleri ayarla
        generator.generation_stats = {
            "total_generated": 1000,
            "total_validated": 850,
            "total_approved": 800,
            "success_rate": 0.85,
        }

        stats = await generator.get_generation_statistics()

        assert stats["total_generated"] == 1000
        assert stats["total_validated"] == 850
        assert stats["success_rate"] == 0.85

    @pytest.mark.asyncio
    async def test_priority_based_generation(self, generator):
        """Öncelik bazlı üretim testi"""
        high_priority_request = QuestionGenerationRequest(
            id="high_req",
            subject=SubjectType.MATHEMATICS,
            topic_id="urgent_topic",
            exam_type=ExamType.LGS,
            grade_level="8",
            question_count=20,
            question_types=[QuestionType.MULTIPLE_CHOICE],
            difficulty_distribution={DifficultyLevel.MEDIUM: 1.0},
            cognitive_distribution={CognitiveLevel.APPLICATION: 1.0},
            min_quality_score=0.8,
            min_osym_compliance=0.85,
            min_meb_compliance=0.85,
            generation_method="ai_assisted",
            use_existing_templates=True,
            allow_duplicates=False,
            requested_by="admin",
            priority="high",
            deadline=datetime.now(),
            status="pending",
            created_at=datetime.now(),
        )

        with patch.object(
            generator, "_save_generation_request", new_callable=AsyncMock
        ) as mock_save:
            with patch.object(
                generator, "generate_questions_for_topic", new_callable=AsyncMock
            ) as mock_generate:
                with patch.object(
                    generator, "_update_generation_request", new_callable=AsyncMock
                ) as mock_update:
                    mock_generate.return_value = [
                        Mock() for _ in range(15)
                    ]  # 15 soru üretildi

                    result = await generator.process_generation_request(
                        high_priority_request
                    )

                    assert result["status"] == "completed"
                    assert result["generated_count"] == 15

    def test_osym_format_validation_rules(self, generator):
        """ÖSYM format doğrulama kuralları testi"""
        rules = generator.osym_format_rules

        assert rules["max_question_length"] == 500
        assert rules["min_options"] == 4
        assert rules["max_options"] == 5
        assert rules["option_length_range"] == (10, 100)
        assert "question_text" in rules["required_elements"]
        assert "options" in rules["required_elements"]
        assert "correct_answer" in rules["required_elements"]

    @pytest.mark.asyncio
    async def test_batch_question_generation(self, generator):
        """Toplu soru üretimi testi"""
        batch_plan = {
            "batch_id": "batch_001",
            "template_id": "template_001",
            "count": 5,
            "topic_id": "test_topic",
            "variables": {"subject": "matematik"},
        }

        with patch.object(
            generator, "_get_question_template", new_callable=AsyncMock
        ) as mock_template:
            with patch.object(
                generator, "create_from_template", new_callable=AsyncMock
            ) as mock_create:
                mock_template.return_value = Mock()  # Mock template
                mock_create.return_value = Mock()  # Mock question

                questions = await generator._generate_questions_batch(batch_plan)

                # Veritabanı bağlantısı olmadığında bile boş liste dönmeli
                assert isinstance(questions, list)

    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, generator):
        """Veritabanı hatası yönetimi testi"""
        generator.db = Mock()
        generator.db.execute = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Soru kaydetme hatası
        question = Mock()
        question.id = "test_q"

        result = await generator._save_generated_question(question)

        # Hata durumunda False dönmeli
        assert result is False

    @pytest.mark.asyncio
    async def test_template_caching(self, generator):
        """Şablon cache sistemi testi"""
        subject_key = SubjectType.MATHEMATICS.value

        # Cache boş
        assert subject_key not in generator.question_templates

        # Mock templates
        mock_templates = [Mock() for _ in range(3)]

        with patch.object(
            generator, "_load_templates_for_subject", new_callable=AsyncMock
        ) as mock_load:
            mock_load.return_value = mock_templates

            # İlk yükleme - cache'e kaydedilmeli
            templates1 = await generator._get_templates_for_subject(
                SubjectType.MATHEMATICS
            )

            # Cache'den ikinci erişim
            templates2 = await generator._get_templates_for_subject(
                SubjectType.MATHEMATICS
            )

            # Cache çalışıyorsa aynı sonuç dönmeli
            assert templates1 == templates2
            mock_load.assert_called_once()  # Sadece bir kez yüklenmeli

    @pytest.mark.asyncio
    async def test_question_uniqueness_check(self, generator):
        """Soru benzersizlik kontrolü testi"""
        question_text = "x + 5 = 13 ise x kaçtır?"

        with patch.object(
            generator, "_check_question_exists", new_callable=AsyncMock
        ) as mock_check:
            # İlk soru - benzersiz
            mock_check.return_value = False
            unique = await generator._check_question_uniqueness(
                question_text, "topic_001"
            )
            assert unique is True

            # İkinci soru - aynı metin
            mock_check.return_value = True
            duplicate = await generator._check_question_uniqueness(
                question_text, "topic_001"
            )
            assert duplicate is False

    @pytest.mark.asyncio
    async def test_concurrent_generation_handling(self, generator):
        """Eşzamanlı üretim yönetimi testi"""
        import asyncio

        # Birden fazla üretim talebini eşzamanlı başlat
        requests = [
            QuestionGenerationRequest(
                id=f"concurrent_req_{i}",
                subject=SubjectType.MATHEMATICS,
                topic_id=f"topic_{i}",
                exam_type=ExamType.LGS,
                grade_level="8",
                question_count=5,
                question_types=[QuestionType.MULTIPLE_CHOICE],
                difficulty_distribution={DifficultyLevel.EASY: 1.0},
                cognitive_distribution={CognitiveLevel.KNOWLEDGE: 1.0},
                min_quality_score=0.7,
                min_osym_compliance=0.8,
                min_meb_compliance=0.8,
                generation_method="template",
                use_existing_templates=True,
                allow_duplicates=False,
                requested_by="test",
                priority="normal",
                deadline=None,
                status="pending",
                created_at=datetime.now(),
            )
            for i in range(3)
        ]

        with patch.object(
            generator, "_save_generation_request", new_callable=AsyncMock
        ):
            with patch.object(
                generator, "generate_questions_for_topic", new_callable=AsyncMock
            ) as mock_generate:
                with patch.object(
                    generator, "_update_generation_request", new_callable=AsyncMock
                ):
                    mock_generate.return_value = []  # Boş liste döndür

                    # Eşzamanlı çalıştır
                    tasks = [
                        generator.process_generation_request(req) for req in requests
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Hiçbiri exception olmamalı
                    for result in results:
                        assert not isinstance(result, Exception)
                        assert "request_id" in result


# Integration Tests
class TestAutomatedQuestionGeneratorIntegration:
    """AutomatedQuestionGenerator integration testleri"""

    @pytest.mark.asyncio
    async def test_full_question_generation_workflow(self):
        """Tam soru üretim iş akışı testi"""
        generator = AutomatedQuestionGenerator()

        # 1. Sistem başlatma
        with patch.object(
            generator, "_load_question_templates", new_callable=AsyncMock
        ):
            with patch.object(
                generator, "_analyze_current_question_bank", new_callable=AsyncMock
            ):
                init_result = await generator.initialize()
                assert init_result is True

        # 2. Soru üretimi
        with patch.object(
            generator, "_get_current_question_count", new_callable=AsyncMock
        ) as mock_count:
            with patch.object(
                generator, "_get_meb_standards_for_topic", new_callable=AsyncMock
            ):
                with patch.object(
                    generator, "_get_osym_standards_for_topic", new_callable=AsyncMock
                ):
                    with patch.object(
                        generator, "_create_generation_plan", new_callable=AsyncMock
                    ) as mock_plan:
                        with patch.object(
                            generator,
                            "_generate_questions_batch",
                            new_callable=AsyncMock,
                        ) as mock_batch:
                            with patch.object(
                                generator,
                                "_save_generated_question",
                                new_callable=AsyncMock,
                            ):
                                mock_count.return_value = 0
                                mock_plan.return_value = [{"test": True}]

                                # Mock bir soru üret
                                mock_question = Mock()
                                mock_question.id = "integration_test_q"
                                mock_question.is_validated = False
                                mock_batch.return_value = [mock_question]

                                # Mock validation
                                with patch.object(
                                    generator,
                                    "validate_question",
                                    new_callable=AsyncMock,
                                ) as mock_validate:
                                    mock_validate.return_value = (
                                        QuestionValidationResult(
                                            is_valid=True,
                                            quality_score=0.8,
                                            readability_score=0.9,
                                            osym_compliance_score=0.85,
                                            meb_compliance_score=0.8,
                                            uniqueness_score=0.95,
                                            errors=[],
                                            warnings=[],
                                            suggestions=[],
                                        )
                                    )

                                    questions = (
                                        await generator.generate_questions_for_topic(
                                            "integration_topic",
                                            SubjectType.MATHEMATICS,
                                            ExamType.LGS,
                                            target_count=1,
                                        )
                                    )

                                    assert len(questions) == 1
                                    assert questions[0].is_validated is True


if __name__ == "__main__":
    pytest.main([__file__])
