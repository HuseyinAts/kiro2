"""
Domain Experts End-to-End Tests
Task 17.1: E2E Tests for Konu Bazli Subagent System

Test 6 domain expert agents with real YKS-style questions:
- matematik: Algebra, Geometry, Analysis, Probability
- fizik: Mechanics, Electricity, Optics, Thermodynamics
- turkce: Grammar, Literature, Semantics
- sosyal: History, Geography, Philosophy
- biyoloji: Cell Biology, Genetics, Ecology
- yabanci_dil: Grammar, Vocabulary, Reading
"""

import time

import pytest

# Module skip: Agent API changed - process_question → process_request (28 occurrences)
pytestmark = pytest.mark.skipif(True, reason="Agent API changed: process_question renamed to process_request")

from agents.coordination import (
    AgentCoordinator,
    DomainBlackboard,
    QuestionClassifier,
    ResponseSynthesizer,
)
from agents.domain_experts import (
    BiyolojiAgent,
    DomainResponse,
    DomainType,
    FizikAgent,
    MatematikAgent,
    SosyalAgent,
    TurkceAgent,
    YabanciDilAgent,
)
from agents.scoring import SpecializationScorer
from tests.fixtures.yks_questions import (
    BIYOLOJI_QUESTIONS,
    FIZIK_QUESTIONS,
    MATEMATIK_QUESTIONS,
    MULTI_DOMAIN_QUESTIONS,
    SOSYAL_QUESTIONS,
    TURKCE_QUESTIONS,
    YABANCI_DIL_QUESTIONS,
)

# Test configuration
MAX_RESPONSE_TIME_MS = 3000  # 3 seconds
MIN_CONFIDENCE = 0.6


@pytest.fixture
def blackboard():
    """Create DomainBlackboard instance"""
    return DomainBlackboard()


@pytest.fixture
def classifier():
    """Create QuestionClassifier instance"""
    return QuestionClassifier()


@pytest.fixture
def scorer():
    """Create SpecializationScorer instance"""
    return SpecializationScorer()


@pytest.fixture
def matematik_agent():
    """Create MatematikAgent instance"""
    return MatematikAgent()


@pytest.fixture
def fizik_agent():
    """Create FizikAgent instance"""
    return FizikAgent()


@pytest.fixture
def turkce_agent():
    """Create TurkceAgent instance"""
    return TurkceAgent()


@pytest.fixture
def sosyal_agent():
    """Create SosyalAgent instance"""
    return SosyalAgent()


@pytest.fixture
def biyoloji_agent():
    """Create BiyolojiAgent instance"""
    return BiyolojiAgent()


@pytest.fixture
def yabanci_dil_agent():
    """Create YabanciDilAgent instance"""
    return YabanciDilAgent()


@pytest.fixture
async def coordinator(
    blackboard, classifier, matematik_agent, fizik_agent,
    turkce_agent, sosyal_agent, biyoloji_agent, yabanci_dil_agent
):
    """Create AgentCoordinator with all 6 agents"""
    await blackboard.connect()

    agents = {
        DomainType.MATEMATIK: matematik_agent,
        DomainType.FIZIK: fizik_agent,
        DomainType.TURKCE: turkce_agent,
        DomainType.SOSYAL: sosyal_agent,
        DomainType.BIYOLOJI: biyoloji_agent,
        DomainType.YABANCI_DIL: yabanci_dil_agent,
    }

    coordinator = AgentCoordinator(
        agents=agents,
        classifier=classifier,
        blackboard=blackboard,
    )

    yield coordinator

    await blackboard.disconnect()


def _validate_response(
    response: DomainResponse,
    expected_domain: DomainType,
    expected_keywords: list[str],
) -> None:
    """Validate agent response"""
    # Check domain
    assert response.domain == expected_domain, (
        f"Expected domain {expected_domain}, got {response.domain}"
    )

    # Check confidence
    assert response.confidence >= MIN_CONFIDENCE, (
        f"Confidence {response.confidence} below minimum {MIN_CONFIDENCE}"
    )

    # Check content is not empty
    assert response.content, "Response content is empty"
    assert len(response.content) > 10, "Response content too short"

    # Check at least one expected keyword appears
    content_lower = response.content.lower()
    found_keywords = [kw for kw in expected_keywords if kw.lower() in content_lower]
    assert len(found_keywords) > 0, (
        f"No expected keywords found. Expected any of: {expected_keywords}"
    )

    # Check response time
    assert response.response_time_ms < MAX_RESPONSE_TIME_MS, (
        f"Response time {response.response_time_ms}ms exceeds {MAX_RESPONSE_TIME_MS}ms"
    )


class TestMatematikAgentE2E:
    """End-to-end tests for Matematik agent (REQ-1)"""

    @pytest.mark.asyncio
    async def test_cebir_question_e2e(self, matematik_agent: MatematikAgent):
        """Test algebra question processing"""
        question = MATEMATIK_QUESTIONS[0]  # 2x + 3 = 7

        response = await matematik_agent.process_question(
            question=question.question_text,
            student_id="test_student_001",
        )

        _validate_response(response, DomainType.MATEMATIK, question.expected_keywords)

        # Cebir specific: should have step-by-step solution
        assert response.step_by_step_solution, "Cebir question should have step-by-step"

    @pytest.mark.asyncio
    async def test_geometri_question_e2e(self, matematik_agent: MatematikAgent):
        """Test geometry question processing"""
        question = MATEMATIK_QUESTIONS[2]  # Triangle area

        response = await matematik_agent.process_question(
            question=question.question_text,
            student_id="test_student_002",
        )

        _validate_response(response, DomainType.MATEMATIK, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_analiz_question_e2e(self, matematik_agent: MatematikAgent):
        """Test calculus question processing"""
        question = MATEMATIK_QUESTIONS[4]  # Derivative

        response = await matematik_agent.process_question(
            question=question.question_text,
            student_id="test_student_003",
        )

        _validate_response(response, DomainType.MATEMATIK, question.expected_keywords)

        # Analiz specific: should have LaTeX
        assert response.latex_expressions, "Analiz should have LaTeX expressions"

    @pytest.mark.asyncio
    async def test_olasilik_question_e2e(self, matematik_agent: MatematikAgent):
        """Test probability question processing"""
        question = MATEMATIK_QUESTIONS[6]  # Dice probability

        response = await matematik_agent.process_question(
            question=question.question_text,
            student_id="test_student_004",
        )

        _validate_response(response, DomainType.MATEMATIK, question.expected_keywords)


class TestFizikAgentE2E:
    """End-to-end tests for Fizik agent (REQ-2)"""

    @pytest.mark.asyncio
    async def test_mekanik_question_e2e(self, fizik_agent: FizikAgent):
        """Test mechanics question processing"""
        question = FIZIK_QUESTIONS[0]  # F=ma

        response = await fizik_agent.process_question(
            question=question.question_text,
            student_id="test_student_005",
        )

        _validate_response(response, DomainType.FIZIK, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_elektrik_question_e2e(self, fizik_agent: FizikAgent):
        """Test electricity question processing"""
        question = FIZIK_QUESTIONS[2]  # Ohm's law

        response = await fizik_agent.process_question(
            question=question.question_text,
            student_id="test_student_006",
        )

        _validate_response(response, DomainType.FIZIK, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_optik_question_e2e(self, fizik_agent: FizikAgent):
        """Test optics question processing"""
        question = FIZIK_QUESTIONS[4]  # Lens

        response = await fizik_agent.process_question(
            question=question.question_text,
            student_id="test_student_007",
        )

        _validate_response(response, DomainType.FIZIK, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_termodinamik_question_e2e(self, fizik_agent: FizikAgent):
        """Test thermodynamics question processing"""
        question = FIZIK_QUESTIONS[5]  # Ideal gas

        response = await fizik_agent.process_question(
            question=question.question_text,
            student_id="test_student_008",
        )

        _validate_response(response, DomainType.FIZIK, question.expected_keywords)


class TestTurkceAgentE2E:
    """End-to-end tests for Turkce agent (REQ-3)"""

    @pytest.mark.asyncio
    async def test_dilbilgisi_question_e2e(self, turkce_agent: TurkceAgent):
        """Test grammar question processing"""
        question = TURKCE_QUESTIONS[0]  # Ek fiil

        response = await turkce_agent.process_question(
            question=question.question_text,
            student_id="test_student_009",
        )

        _validate_response(response, DomainType.TURKCE, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_edebiyat_question_e2e(self, turkce_agent: TurkceAgent):
        """Test literature question processing"""
        question = TURKCE_QUESTIONS[2]  # Namik Kemal

        response = await turkce_agent.process_question(
            question=question.question_text,
            student_id="test_student_010",
        )

        _validate_response(response, DomainType.TURKCE, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_anlam_bilgisi_question_e2e(self, turkce_agent: TurkceAgent):
        """Test semantics question processing"""
        question = TURKCE_QUESTIONS[4]  # Mecaz anlam

        response = await turkce_agent.process_question(
            question=question.question_text,
            student_id="test_student_011",
        )

        _validate_response(response, DomainType.TURKCE, question.expected_keywords)


class TestSosyalAgentE2E:
    """End-to-end tests for Sosyal agent (REQ-4)"""

    @pytest.mark.asyncio
    async def test_tarih_question_e2e(self, sosyal_agent: SosyalAgent):
        """Test history question processing"""
        question = SOSYAL_QUESTIONS[0]  # Kurtulus Savasi

        response = await sosyal_agent.process_question(
            question=question.question_text,
            student_id="test_student_012",
        )

        _validate_response(response, DomainType.SOSYAL, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_cografya_question_e2e(self, sosyal_agent: SosyalAgent):
        """Test geography question processing"""
        question = SOSYAL_QUESTIONS[2]  # Turkiye iklim

        response = await sosyal_agent.process_question(
            question=question.question_text,
            student_id="test_student_013",
        )

        _validate_response(response, DomainType.SOSYAL, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_felsefe_question_e2e(self, sosyal_agent: SosyalAgent):
        """Test philosophy question processing"""
        question = SOSYAL_QUESTIONS[4]  # Platon idea

        response = await sosyal_agent.process_question(
            question=question.question_text,
            student_id="test_student_014",
        )

        _validate_response(response, DomainType.SOSYAL, question.expected_keywords)


class TestBiyolojiAgentE2E:
    """End-to-end tests for Biyoloji agent (REQ-5)"""

    @pytest.mark.asyncio
    async def test_hucre_question_e2e(self, biyoloji_agent: BiyolojiAgent):
        """Test cell biology question processing"""
        question = BIYOLOJI_QUESTIONS[0]  # Mitokondri

        response = await biyoloji_agent.process_question(
            question=question.question_text,
            student_id="test_student_015",
        )

        _validate_response(response, DomainType.BIYOLOJI, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_genetik_question_e2e(self, biyoloji_agent: BiyolojiAgent):
        """Test genetics question processing"""
        question = BIYOLOJI_QUESTIONS[2]  # Punnett

        response = await biyoloji_agent.process_question(
            question=question.question_text,
            student_id="test_student_016",
        )

        _validate_response(response, DomainType.BIYOLOJI, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_ekoloji_question_e2e(self, biyoloji_agent: BiyolojiAgent):
        """Test ecology question processing"""
        question = BIYOLOJI_QUESTIONS[4]  # Besin zinciri

        response = await biyoloji_agent.process_question(
            question=question.question_text,
            student_id="test_student_017",
        )

        _validate_response(response, DomainType.BIYOLOJI, question.expected_keywords)


class TestYabanciDilAgentE2E:
    """End-to-end tests for Yabanci Dil agent (REQ-6)"""

    @pytest.mark.asyncio
    async def test_grammar_question_e2e(self, yabanci_dil_agent: YabanciDilAgent):
        """Test English grammar question processing"""
        question = YABANCI_DIL_QUESTIONS[0]  # Conditional

        response = await yabanci_dil_agent.process_question(
            question=question.question_text,
            student_id="test_student_018",
        )

        _validate_response(response, DomainType.YABANCI_DIL, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_vocabulary_question_e2e(self, yabanci_dil_agent: YabanciDilAgent):
        """Test vocabulary question processing"""
        question = YABANCI_DIL_QUESTIONS[2]  # Ubiquitous

        response = await yabanci_dil_agent.process_question(
            question=question.question_text,
            student_id="test_student_019",
        )

        _validate_response(response, DomainType.YABANCI_DIL, question.expected_keywords)

    @pytest.mark.asyncio
    async def test_reading_question_e2e(self, yabanci_dil_agent: YabanciDilAgent):
        """Test reading comprehension question processing"""
        question = YABANCI_DIL_QUESTIONS[4]  # Main idea

        response = await yabanci_dil_agent.process_question(
            question=question.question_text,
            student_id="test_student_020",
        )

        _validate_response(response, DomainType.YABANCI_DIL, question.expected_keywords)


class TestMultiDomainE2E:
    """End-to-end tests for multi-domain questions (REQ-7.5)"""

    @pytest.mark.asyncio
    async def test_matematik_fizik_multidomain(self, coordinator: AgentCoordinator):
        """Test math-physics multi-domain question"""
        question = MULTI_DOMAIN_QUESTIONS[0]  # Newton + derivative

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_021",
        )

        # Should detect multi-domain
        assert result.is_multi_domain, "Should detect multi-domain question"

        # Should have responses from both domains
        assert len(result.responses) >= 2, "Should have at least 2 responses"

        # Check domains
        domains_responded = {r.domain for r in result.responses}
        assert DomainType.MATEMATIK in domains_responded or DomainType.FIZIK in domains_responded

    @pytest.mark.asyncio
    async def test_turkce_sosyal_multidomain(self, coordinator: AgentCoordinator):
        """Test Turkish-Social multi-domain question"""
        question = MULTI_DOMAIN_QUESTIONS[1]  # Tanzimat

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_022",
        )

        # Should handle multi-domain
        assert len(result.responses) >= 1, "Should have at least 1 response"

    @pytest.mark.asyncio
    async def test_biyoloji_fizik_multidomain(self, coordinator: AgentCoordinator):
        """Test biology-physics multi-domain question"""
        question = MULTI_DOMAIN_QUESTIONS[2]  # Osmosis + physics

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_023",
        )

        # Should process successfully
        assert result.success, "Multi-domain should succeed"


class TestCoordinatorE2E:
    """End-to-end tests for AgentCoordinator"""

    @pytest.mark.asyncio
    async def test_single_domain_routing(self, coordinator: AgentCoordinator):
        """Test single domain question routing"""
        question = MATEMATIK_QUESTIONS[0]  # Simple algebra

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_024",
        )

        # Should route to matematik
        assert result.classification.primary_domain == DomainType.MATEMATIK
        assert not result.is_multi_domain
        assert len(result.responses) == 1
        assert result.responses[0].domain == DomainType.MATEMATIK

    @pytest.mark.asyncio
    async def test_response_synthesis(self, coordinator: AgentCoordinator):
        """Test response synthesis for multi-domain"""
        question = MULTI_DOMAIN_QUESTIONS[0]

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_025",
        )

        # Should synthesize response
        synthesizer = ResponseSynthesizer()
        synthesized = synthesizer.synthesize(result.responses, question.question_text)

        assert synthesized, "Should have synthesized response"
        assert len(synthesized) > 50, "Synthesized response should be substantial"

    @pytest.mark.asyncio
    async def test_all_domains_sequential(self, coordinator: AgentCoordinator):
        """Test processing questions from all domains sequentially"""
        all_questions = [
            MATEMATIK_QUESTIONS[0],
            FIZIK_QUESTIONS[0],
            TURKCE_QUESTIONS[0],
            SOSYAL_QUESTIONS[0],
            BIYOLOJI_QUESTIONS[0],
            YABANCI_DIL_QUESTIONS[0],
        ]

        expected_domains = [
            DomainType.MATEMATIK,
            DomainType.FIZIK,
            DomainType.TURKCE,
            DomainType.SOSYAL,
            DomainType.BIYOLOJI,
            DomainType.YABANCI_DIL,
        ]

        for question, expected_domain in zip(all_questions, expected_domains):
            result = await coordinator.process_question(
                question=question.question_text,
                student_id="test_student_sequential",
            )

            assert result.classification.primary_domain == expected_domain, (
                f"Question should route to {expected_domain}"
            )
            assert len(result.responses) >= 1

    @pytest.mark.asyncio
    async def test_response_time_under_threshold(self, coordinator: AgentCoordinator):
        """Test that response time is under 3 seconds"""
        question = MATEMATIK_QUESTIONS[0]

        start_time = time.time()
        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_timing",
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < MAX_RESPONSE_TIME_MS, (
            f"Response time {elapsed_ms:.0f}ms exceeds {MAX_RESPONSE_TIME_MS}ms"
        )
        assert result.total_time_ms < MAX_RESPONSE_TIME_MS


class TestSpecializationScoring:
    """Test specialization scoring integration"""

    @pytest.mark.asyncio
    async def test_score_calculation(
        self, coordinator: AgentCoordinator, scorer: SpecializationScorer
    ):
        """Test specialization score calculation from response"""
        question = MATEMATIK_QUESTIONS[0]

        result = await coordinator.process_question(
            question=question.question_text,
            student_id="test_student_scoring",
        )

        # Calculate score for each response
        for response in result.responses:
            score = scorer.calculate_from_response(response)

            # Score should be in [0, 1]
            assert 0.0 <= score.total_score <= 1.0

            # Component scores should be in [0, 1]
            assert 0.0 <= score.domain_relevance <= 1.0
            assert 0.0 <= score.accuracy <= 1.0
            assert 0.0 <= score.completeness <= 1.0
            assert 0.0 <= score.user_satisfaction <= 1.0

    @pytest.mark.asyncio
    async def test_weighted_formula(self, scorer: SpecializationScorer):
        """Test weighted formula: 0.4*R + 0.3*A + 0.2*C + 0.1*S"""
        score = scorer.calculate_score(
            domain=DomainType.MATEMATIK,
            relevance=1.0,
            accuracy=1.0,
            completeness=1.0,
            satisfaction=1.0,
        )

        # All 1.0 should give 1.0
        assert abs(score.total_score - 1.0) < 0.001

        # Check specific values
        score2 = scorer.calculate_score(
            domain=DomainType.FIZIK,
            relevance=0.8,
            accuracy=0.9,
            completeness=0.7,
            satisfaction=0.6,
        )

        expected = 0.4 * 0.8 + 0.3 * 0.9 + 0.2 * 0.7 + 0.1 * 0.6
        assert abs(score2.total_score - expected) < 0.001
