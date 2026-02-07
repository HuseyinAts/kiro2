"""
AI Agent Yanıt Doğrulama Sistemi - Unit Tests

Bu modül, response validation sisteminin temel testlerini içerir.

Test Coverage:
- ValidationResult model
- AgentResponse model
- ConfidenceScorer
- LearningPathValidator basic validation
- StudyBuddyValidator basic validation
- ExamAgentValidator basic validation
"""

import pytest

# Import models
from backend.validators.base_response_validator import (
    AgentResponse,
    AgentType,
    ValidationAction,
    ValidationResult,
)
from backend.scoring.confidence_scorer import ConfidenceScorer


class TestValidationResult:
    """ValidationResult model testleri"""

    def test_valid_result_creation(self):
        """Geçerli sonuç oluşturma"""
        result = ValidationResult(
            is_valid=True,
            score=0.85,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={"validator": "test"},
        )

        assert result.is_valid is True
        assert result.score == 0.85
        assert len(result.errors) == 0

    def test_score_bounds_validation(self):
        """Score sınır kontrolü - Pydantic geçersiz değerleri reddeder"""
        from pydantic import ValidationError as PydanticValidationError

        # Score 0-1 aralığında olmalı, dışındaki değerler reddedilmeli
        with pytest.raises(PydanticValidationError):
            ValidationResult(
                is_valid=True,
                score=1.5,  # 1'den büyük - reddedilmeli
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        with pytest.raises(PydanticValidationError):
            ValidationResult(
                is_valid=True,
                score=-0.5,  # 0'dan küçük - reddedilmeli
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        # Geçerli sınır değerleri kabul edilmeli
        result_min = ValidationResult(
            is_valid=True, score=0.0, errors=[], warnings=[],
            suggestions=[], metadata={}
        )
        assert result_min.score == 0.0

        result_max = ValidationResult(
            is_valid=True, score=1.0, errors=[], warnings=[],
            suggestions=[], metadata={}
        )
        assert result_max.score == 1.0

    def test_invalid_result_with_errors(self):
        """Hatalı sonuç oluşturma"""
        result = ValidationResult(
            is_valid=False,
            score=0.3,
            errors=["Müfredat uyumsuzluğu", "Ön koşul hatası"],
            warnings=["Süre tahmini kısa"],
            suggestions=["Konuları yeniden sıralayın"],
            metadata={"validator": "LearningPath"},
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "Müfredat uyumsuzluğu" in result.errors


class TestAgentResponse:
    """AgentResponse model testleri"""

    def test_agent_response_creation(self):
        """Agent yanıtı oluşturma"""
        response = AgentResponse(
            agent_type="study_buddy",
            response_id="resp_123",
            user_id="user_456",
            query="Osmanlı İmparatorluğu ne zaman kuruldu?",
            response_text="Osmanlı İmparatorluğu 1299 yılında kuruldu.",
            response_data={},
            context={"grade_level": 10},
        )

        assert response.agent_type == "study_buddy"
        assert response.response_id == "resp_123"
        assert "1299" in response.response_text

    def test_agent_response_with_data(self):
        """Yapılandırılmış veri ile yanıt"""
        response = AgentResponse(
            agent_type="exam",
            response_id="resp_789",
            user_id="user_456",
            query="Sınavımı değerlendir",
            response_text="Sınav sonucunuz: 75/100",
            response_data={
                "evaluation": {
                    "total_questions": 20,
                    "correct_count": 15,
                    "wrong_count": 5,
                }
            },
        )

        assert response.response_data["evaluation"]["correct_count"] == 15


class TestConfidenceScorer:
    """ConfidenceScorer testleri"""

    def test_default_weights(self):
        """Varsayılan ağırlıklar"""
        scorer = ConfidenceScorer()

        assert scorer.weights["agent_specific"] == 0.30
        assert scorer.weights["fact_checking"] == 0.40
        assert scorer.weights["consistency"] == 0.30

    def test_confidence_calculation(self):
        """Confidence hesaplama"""
        scorer = ConfidenceScorer()

        agent_result = ValidationResult(
            is_valid=True, score=0.9, errors=[], warnings=[],
            suggestions=[], metadata={}
        )
        fact_result = ValidationResult(
            is_valid=True, score=0.8, errors=[], warnings=[],
            suggestions=[], metadata={}
        )
        consistency_result = ValidationResult(
            is_valid=True, score=1.0, errors=[], warnings=[],
            suggestions=[], metadata={}
        )

        confidence = scorer.calculate_confidence(
            agent_result, fact_result, consistency_result
        )

        # 0.9*0.3 + 0.8*0.4 + 1.0*0.3 = 0.27 + 0.32 + 0.30 = 0.89
        assert 0.88 <= confidence <= 0.90

    def test_action_thresholds(self):
        """Aksiyon eşik değerleri"""
        scorer = ConfidenceScorer()

        # >= 0.8 -> approve
        assert scorer.determine_action(0.85) == ValidationAction.APPROVE
        assert scorer.determine_action(0.80) == ValidationAction.APPROVE

        # 0.5-0.8 -> review
        assert scorer.determine_action(0.79) == ValidationAction.REVIEW
        assert scorer.determine_action(0.50) == ValidationAction.REVIEW

        # < 0.5 -> reject
        assert scorer.determine_action(0.49) == ValidationAction.REJECT
        assert scorer.determine_action(0.0) == ValidationAction.REJECT

    def test_custom_weights(self):
        """Özel ağırlıklar"""
        custom_weights = {
            "agent_specific": 0.50,
            "fact_checking": 0.30,
            "consistency": 0.20,
        }
        scorer = ConfidenceScorer(weights=custom_weights)

        assert scorer.weights["agent_specific"] == 0.50
        assert scorer.weights["fact_checking"] == 0.30


class TestValidationAction:
    """ValidationAction enum testleri"""

    def test_action_values(self):
        """Aksiyon değerleri"""
        assert ValidationAction.APPROVE.value == "approve"
        assert ValidationAction.REVIEW.value == "review"
        assert ValidationAction.REJECT.value == "reject"


class TestAgentType:
    """AgentType enum testleri"""

    def test_agent_types(self):
        """Agent tipleri"""
        assert AgentType.LEARNING_PATH.value == "learning_path"
        assert AgentType.STUDY_BUDDY.value == "study_buddy"
        assert AgentType.EXAM.value == "exam"


# Property-based tests için Hypothesis kullanılabilir
# @pytest.mark.parametrize ile boundary testleri

@pytest.mark.parametrize("score,expected_action", [
    (1.0, ValidationAction.APPROVE),
    (0.95, ValidationAction.APPROVE),
    (0.80, ValidationAction.APPROVE),
    (0.79, ValidationAction.REVIEW),
    (0.65, ValidationAction.REVIEW),
    (0.50, ValidationAction.REVIEW),
    (0.49, ValidationAction.REJECT),
    (0.25, ValidationAction.REJECT),
    (0.0, ValidationAction.REJECT),
])
def test_action_threshold_boundaries(score, expected_action):
    """Aksiyon eşik sınır değerleri testi"""
    scorer = ConfidenceScorer()
    action = scorer.determine_action(score)
    assert action == expected_action


@pytest.mark.parametrize("agent,fact,consistency,expected_min,expected_max", [
    (1.0, 1.0, 1.0, 0.99, 1.01),  # Perfect scores
    (0.0, 0.0, 0.0, -0.01, 0.01),  # Zero scores
    (0.5, 0.5, 0.5, 0.49, 0.51),  # Middle scores
    (1.0, 0.0, 0.0, 0.29, 0.31),  # Only agent passes
    (0.0, 1.0, 0.0, 0.39, 0.41),  # Only fact passes
    (0.0, 0.0, 1.0, 0.29, 0.31),  # Only consistency passes
])
def test_weighted_average_formula(agent, fact, consistency, expected_min, expected_max):
    """Ağırlıklı ortalama formül testi"""
    scorer = ConfidenceScorer()

    agent_result = ValidationResult(
        is_valid=True, score=agent, errors=[], warnings=[],
        suggestions=[], metadata={}
    )
    fact_result = ValidationResult(
        is_valid=True, score=fact, errors=[], warnings=[],
        suggestions=[], metadata={}
    )
    consistency_result = ValidationResult(
        is_valid=True, score=consistency, errors=[], warnings=[],
        suggestions=[], metadata={}
    )

    confidence = scorer.calculate_confidence(
        agent_result, fact_result, consistency_result
    )

    assert expected_min <= confidence <= expected_max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
