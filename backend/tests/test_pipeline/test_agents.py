"""
Pipeline Agents Tests
Tüm pipeline agent'ları için testler
"""

import pytest

from pipeline.agents import (
    ComplianceAgent,
    ContentGeneratorAgent,
    DifficultyAgent,
    DistractorAgent,
    LanguageQAAgent,
)

# Note: conftest.py adds backend dir to sys.path
from pipeline.stage_base import StageInput, StageOutput


class TestContentGeneratorAgent:
    """Content Generator Agent testleri"""

    @pytest.fixture
    def agent(self):
        return ContentGeneratorAgent()

    def test_stage_name(self, agent):
        """Stage adı kontrolü"""
        assert agent.STAGE_NAME == "content_generator"

    def test_stage_weight(self, agent):
        """Stage ağırlığı kontrolü"""
        assert agent.get_stage_weight() == 0.25

    def test_bloom_levels_defined(self, agent):
        """Bloom seviyeleri tanımlı mı"""
        assert len(agent.BLOOM_LEVELS) == 6
        assert "hatırlama" in agent.BLOOM_LEVELS
        assert "değerlendirme" in agent.BLOOM_LEVELS

    @pytest.mark.asyncio
    async def test_analyze_bloom_level(self, agent):
        """Bloom seviyesi analizi"""
        level = await agent._analyze_bloom_level("Öğrenci denklemi çözer")
        assert level in agent.BLOOM_LEVELS

    @pytest.mark.asyncio
    async def test_process_with_kazanim(self, agent):
        """Kazanım ile işlem"""
        input_data = StageInput(
            question_data={
                "kazanim": "İkinci dereceden denklemleri çözer",
                "subject": "matematik",
                "topic": "Denklemler",
                "target_difficulty": "orta"
            },
            metadata={},
            previous_scores={}
        )

        output = await agent.process(input_data)

        assert isinstance(output, StageOutput)
        assert output.score > 0
        assert "question_text" in output.question_data or output.errors


class TestDifficultyAgent:
    """Difficulty Agent testleri"""

    @pytest.fixture
    def agent(self):
        return DifficultyAgent()

    def test_stage_name(self, agent):
        """Stage adı kontrolü"""
        assert agent.STAGE_NAME == "difficulty_calibration"

    def test_stage_weight(self, agent):
        """Stage ağırlığı kontrolü"""
        assert agent.get_stage_weight() == 0.20

    def test_difficulty_map(self, agent):
        """Zorluk haritası kontrolü"""
        assert agent.DIFFICULTY_MAP["kolay"] < agent.DIFFICULTY_MAP["orta"]
        assert agent.DIFFICULTY_MAP["orta"] < agent.DIFFICULTY_MAP["zor"]

    @pytest.mark.asyncio
    async def test_calculate_irt_parameters(self, agent):
        """IRT parametre hesaplama"""
        params = await agent._calculate_irt_parameters(
            "Bu basit bir soru metni",
            "orta"
        )

        assert "difficulty" in params
        assert "discrimination" in params
        assert "guessing" in params
        assert -4.0 <= params["difficulty"] <= 4.0

    @pytest.mark.asyncio
    async def test_process_with_question_text(self, agent):
        """Soru metni ile işlem"""
        input_data = StageInput(
            question_data={
                "question_text": "x² + 5x + 6 = 0 denkleminin kökleri nedir?",
                "target_difficulty": "orta"
            },
            metadata={},
            previous_scores={}
        )

        output = await agent.process(input_data)

        assert isinstance(output, StageOutput)
        assert "irt_difficulty" in output.question_data or output.errors


class TestDistractorAgent:
    """Distractor Agent testleri"""

    @pytest.fixture
    def agent(self):
        return DistractorAgent()

    def test_stage_name(self, agent):
        """Stage adı kontrolü"""
        assert agent.STAGE_NAME == "distractor_generator"

    def test_stage_weight(self, agent):
        """Stage ağırlığı kontrolü"""
        assert agent.get_stage_weight() == 0.20

    def test_error_categories(self, agent):
        """Hata kategorileri tanımlı mı"""
        assert "matematik" in agent.ERROR_CATEGORIES
        assert "fizik" in agent.ERROR_CATEGORIES
        assert "default" in agent.ERROR_CATEGORIES

    @pytest.mark.asyncio
    async def test_generate_simple_distractors(self, agent):
        """Basit çeldirici üretimi"""
        distractors = agent._generate_simple_distractors("5", "matematik")

        assert len(distractors) == 3
        assert "5" not in distractors  # Doğru cevap olmamalı

    def test_order_options_numeric(self, agent):
        """Sayısal sıralama"""
        options = ["5", "3", "7", "1"]
        ordered, correct_pos = agent._order_options(options)

        assert ordered == ["1", "3", "5", "7"]
        assert correct_pos == 2  # "5" pozisyonu


class TestComplianceAgent:
    """Compliance Agent testleri"""

    @pytest.fixture
    def agent(self):
        return ComplianceAgent()

    def test_stage_name(self, agent):
        """Stage adı kontrolü"""
        assert agent.STAGE_NAME == "osym_compliance"

    def test_stage_weight(self, agent):
        """Stage ağırlığı kontrolü"""
        assert agent.get_stage_weight() == 0.20

    def test_check_format_valid(self, agent):
        """Geçerli format kontrolü"""
        question_data = {
            "question_text": "Bu bir test sorusudur. Doğru cevabı bulunuz.",
            "options": [
                {"label": "A", "text": "Seçenek A"},
                {"label": "B", "text": "Seçenek B"},
                {"label": "C", "text": "Seçenek C"},
                {"label": "D", "text": "Seçenek D"}
            ],
            "correct_answer": "A"
        }

        is_valid, errors = agent._check_format(question_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_check_format_missing_options(self, agent):
        """Eksik seçenek kontrolü"""
        question_data = {
            "question_text": "Test sorusu",
            "options": [
                {"label": "A", "text": "Seçenek A"},
                {"label": "B", "text": "Seçenek B"}
            ],
            "correct_answer": "A"
        }

        is_valid, errors = agent._check_format(question_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_check_word_count(self, agent):
        """Kelime sayısı kontrolü"""
        question_data = {
            "question_text": " ".join(["kelime"] * 100),
            "context": ""
        }

        is_valid, count = agent._check_word_count(question_data)
        assert count == 100
        assert is_valid is True  # 150'nin altında


class TestLanguageQAAgent:
    """Language QA Agent testleri"""

    @pytest.fixture
    def agent(self):
        return LanguageQAAgent()

    def test_stage_name(self, agent):
        """Stage adı kontrolü"""
        assert agent.STAGE_NAME == "language_qa"

    def test_stage_weight(self, agent):
        """Stage ağırlığı kontrolü"""
        assert agent.get_stage_weight() == 0.15

    def test_readability_check(self, agent):
        """Okunabilirlik kontrolü"""
        is_valid, score = agent._check_readability(65)
        assert is_valid is True  # 60-70 aralığında
        assert score == 1.0

        is_valid, score = agent._check_readability(40)
        assert is_valid is False  # 60'ın altında


class TestAllAgentsWeights:
    """Tüm agent ağırlıkları toplamı testi"""

    def test_total_weight_equals_one(self):
        """Toplam ağırlık 1.0 olmalı"""
        agents = [
            ContentGeneratorAgent(),
            DifficultyAgent(),
            DistractorAgent(),
            ComplianceAgent(),
            LanguageQAAgent()
        ]

        total_weight = sum(agent.get_stage_weight() for agent in agents)

        assert abs(total_weight - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
