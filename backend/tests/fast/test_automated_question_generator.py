"""
Fast unit tests for automated question generator
Tests: Class initialization, basic configuration
Coverage target: +10-15% for core.automated_question_generator
"""
import pytest


class TestAutomatedQuestionGenerator:
    """Test AutomatedQuestionGenerator class"""

    def test_generator_initialization(self):
        """Test generator can be initialized"""
        from core.automated_question_generator import AutomatedQuestionGenerator

        generator = AutomatedQuestionGenerator()

        assert generator is not None
        assert generator.target_questions_per_topic == 1000
        assert generator.min_osym_compliance_score == 0.8
        assert generator.min_meb_compliance_score == 0.8
        assert generator.min_quality_score == 0.7

    def test_generator_with_services(self):
        """Test generator initialization with services"""
        from core.automated_question_generator import AutomatedQuestionGenerator

        generator = AutomatedQuestionGenerator(
            curriculum_service="mock_curriculum",
            llm_service="mock_llm",
            database_service="mock_db",
            cache_service="mock_cache",
        )

        assert generator.curriculum_service == "mock_curriculum"
        assert generator.llm_service == "mock_llm"
        assert generator.db == "mock_db"
        assert generator.cache == "mock_cache"

    def test_generator_has_question_templates_dict(self):
        """Test generator has question_templates dictionary"""
        from core.automated_question_generator import AutomatedQuestionGenerator

        generator = AutomatedQuestionGenerator()

        assert hasattr(generator, "question_templates")
        assert isinstance(generator.question_templates, dict)
        assert len(generator.question_templates) == 0


class TestQuestionGenerationEnums:
    """Test question generation model imports"""

    def test_difficulty_level_enum(self):
        """Test DifficultyLevel enum"""
        from models.question_generation import DifficultyLevel

        assert DifficultyLevel is not None

    def test_cognitive_level_enum(self):
        """Test CognitiveLevel enum"""
        from models.question_generation import CognitiveLevel

        assert CognitiveLevel is not None

    def test_question_type_enum(self):
        """Test QuestionType enum"""
        from models.question_generation import QuestionType

        assert QuestionType is not None

    def test_osym_question_format_enum(self):
        """Test OSYMQuestionFormat enum"""
        from models.question_generation import OSYMQuestionFormat

        assert OSYMQuestionFormat is not None

    def test_question_bank_status_enum(self):
        """Test QuestionBankStatus enum"""
        from models.question_generation import QuestionBankStatus

        assert QuestionBankStatus is not None
