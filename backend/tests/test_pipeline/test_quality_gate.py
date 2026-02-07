"""
Quality Gate Agent Tests
Final kalite geçidi testleri

Property Tests (design.md):
- Property 3: Weighted Score Correctness
- Property 4: Decision Threshold Consistency
"""

import pytest
from hypothesis import given, strategies as st, settings

# Note: conftest.py adds backend dir to sys.path

from pipeline.agents.quality_gate_agent import QualityGateAgent
from pipeline.stage_base import StageInput


class TestQualityGateAgent:
    """Quality Gate Agent test sınıfı"""

    @pytest.fixture
    def agent(self):
        """Quality Gate Agent fixture"""
        return QualityGateAgent()

    # ============== Unit Tests ==============

    def test_weighted_score_calculation(self, agent):
        """Ağırlıklı skor hesaplama testi"""
        stage_scores = {
            "content_generator": 0.9,
            "difficulty_calibration": 0.8,
            "distractor_generator": 0.85,
            "osym_compliance": 0.95,
            "language_qa": 0.7
        }

        # Manuel hesaplama
        expected = (
            0.9 * 0.25 +   # content
            0.8 * 0.20 +   # difficulty
            0.85 * 0.20 +  # distractor
            0.95 * 0.20 +  # compliance
            0.7 * 0.15     # language
        )

        # Agent hesaplama
        calculated = agent._calculate_weighted_score(stage_scores)

        assert abs(calculated - expected) < 0.001

    def test_decision_approved(self, agent):
        """Onay kararı testi (>= 85%)"""
        decision, reason = agent._make_decision(0.90)

        assert decision == "approved"
        assert "85%" in reason or "90%" in reason

    def test_decision_review(self, agent):
        """Manuel review kararı testi (70-85%)"""
        decision, reason = agent._make_decision(0.75)

        assert decision == "review"
        assert "70%" in reason or "75%" in reason

    def test_decision_rejected(self, agent):
        """Red kararı testi (< 70%)"""
        decision, reason = agent._make_decision(0.60)

        assert decision == "rejected"
        assert "60%" in reason or "70%" in reason

    def test_improvement_suggestions_rejected(self, agent):
        """Reddedilen soru için öneri testi"""
        stage_scores = {
            "content_generator": 0.5,  # Düşük
            "difficulty_calibration": 0.6,  # Düşük
            "distractor_generator": 0.85,
            "osym_compliance": 0.95,
            "language_qa": 0.7
        }

        suggestions = agent._generate_improvement_suggestions(stage_scores, "rejected")

        assert len(suggestions) > 0
        # En düşük skorlu aşamalar için öneri olmalı
        assert any("content" in s.lower() or "kazanım" in s.lower() or "içerik" in s.lower()
                   for s in suggestions)

    @pytest.mark.asyncio
    async def test_process_with_full_scores(self, agent):
        """Tam skorlarla işlem testi"""
        input_data = StageInput(
            question_data={
                "question_text": "Test sorusu",
                "content_score": 0.9,
                "difficulty_score": 0.85
            },
            metadata={"pipeline_id": "test-123"},
            previous_scores={
                "content_generator": 0.9,
                "difficulty_calibration": 0.85,
                "distractor_generator": 0.88,
                "osym_compliance": 0.92,
                "language_qa": 0.78
            }
        )

        output = await agent.process(input_data)

        assert output.score > 0
        assert output.question_data.get("decision") in ["approved", "review", "rejected"]
        assert "final_score" in output.question_data

    # ============== Property Tests ==============

    @given(
        content=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        difficulty=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        distractor=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        compliance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        language=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_property_weighted_score_correctness(
        self, content, difficulty, distractor, compliance, language
    ):
        """
        Property 3 (design.md): Weighted Score Correctness

        Final score = weighted average of stage scores
        Weights: Content 25%, Difficulty 20%, Distractor 20%, Compliance 20%, Language 15%
        """
        agent = QualityGateAgent()

        stage_scores = {
            "content_generator": content,
            "difficulty_calibration": difficulty,
            "distractor_generator": distractor,
            "osym_compliance": compliance,
            "language_qa": language
        }

        calculated = agent._calculate_weighted_score(stage_scores)

        # Manuel hesaplama
        expected = (
            content * 0.25 +
            difficulty * 0.20 +
            distractor * 0.20 +
            compliance * 0.20 +
            language * 0.15
        )

        # Floating point toleransı ile karşılaştır
        assert abs(calculated - expected) < 0.0001

        # Final skor 0-1 aralığında olmalı
        assert 0.0 <= calculated <= 1.0

    @given(score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=100)
    def test_property_decision_threshold_consistency(self, score):
        """
        Property 4 (design.md): Decision Threshold Consistency

        - score >= 0.85 => "approved"
        - 0.70 <= score < 0.85 => "review"
        - score < 0.70 => "rejected"
        """
        agent = QualityGateAgent()
        decision, _ = agent._make_decision(score)

        if score >= 0.85:
            assert decision == "approved"
        elif score >= 0.70:
            assert decision == "review"
        else:
            assert decision == "rejected"

    @given(
        content=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        difficulty=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        distractor=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        compliance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        language=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=50)
    def test_property_final_score_bounds(
        self, content, difficulty, distractor, compliance, language
    ):
        """
        Property 2 (design.md): Final Score Bounds

        Final quality score must be between 0 and 1
        """
        agent = QualityGateAgent()

        stage_scores = {
            "content_generator": content,
            "difficulty_calibration": difficulty,
            "distractor_generator": distractor,
            "osym_compliance": compliance,
            "language_qa": language
        }

        calculated = agent._calculate_weighted_score(stage_scores)

        assert 0.0 <= calculated <= 1.0
        assert isinstance(calculated, float)


class TestDecisionBoundaries:
    """Karar sınırları testleri"""

    @pytest.fixture
    def agent(self):
        return QualityGateAgent()

    def test_boundary_85_percent(self, agent):
        """0.85 sınırı - approved"""
        decision, _ = agent._make_decision(0.85)
        assert decision == "approved"

    def test_boundary_below_85(self, agent):
        """0.85 altı - review"""
        decision, _ = agent._make_decision(0.849999)
        assert decision == "review"

    def test_boundary_70_percent(self, agent):
        """0.70 sınırı - review"""
        decision, _ = agent._make_decision(0.70)
        assert decision == "review"

    def test_boundary_below_70(self, agent):
        """0.70 altı - rejected"""
        decision, _ = agent._make_decision(0.699999)
        assert decision == "rejected"

    def test_boundary_zero(self, agent):
        """0.0 - rejected"""
        decision, _ = agent._make_decision(0.0)
        assert decision == "rejected"

    def test_boundary_one(self, agent):
        """1.0 - approved"""
        decision, _ = agent._make_decision(1.0)
        assert decision == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
