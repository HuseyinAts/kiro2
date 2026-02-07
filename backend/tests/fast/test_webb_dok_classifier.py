"""Fast tests for Webb DOK classifier service (no DB required)."""

from __future__ import annotations


class TestWebbDOKClassifierBasic:
    """Basic tests for Webb DOK classifier without full model imports."""

    def test_module_imports(self):
        """Test that the module can be imported."""
        from services.taxonomy.webb_dok_classifier import (
            WebbDOKResult,
            classify_webb_dok,
            estimate_dok_from_bloom,
        )

        assert callable(classify_webb_dok)
        assert callable(estimate_dok_from_bloom)
        assert WebbDOKResult is not None

    def test_recall_level_question(self):
        """Test DOK Level 1 (RECALL) classification."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Asiret nedir? Tanımını yazınız."
        result = classify_webb_dok(question)

        assert result.level == WebbDOKLevel.RECALL
        assert result.confidence > 0.0
        assert len(result.matched_patterns) > 0
        assert "hatirlama" in result.rationale.lower() or "yeniden" in result.rationale.lower()

    def test_skill_level_question(self):
        """Test DOK Level 2 (SKILL) classification."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Aşağıdaki denklemi çözünüz: 2x + 5 = 13"
        result = classify_webb_dok(question)

        assert result.level == WebbDOKLevel.SKILL
        assert result.confidence > 0.0
        # Note: may have 0 patterns if defaulting to SKILL (common for YKS questions)

    def test_strategic_level_question(self):
        """Test DOK Level 3 (STRATEGIC) classification."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Neden bu sonuca ulaştınız? Gerekçenizi açıklayınız."
        result = classify_webb_dok(question)

        assert result.level == WebbDOKLevel.STRATEGIC
        assert result.confidence > 0.0
        assert len(result.matched_patterns) > 0

    def test_extended_level_question(self):
        """Test DOK Level 4 (EXTENDED) classification."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Farklı disiplinlerden yararlanarak yeni bir model tasarlayınız."
        result = classify_webb_dok(question)

        assert result.level == WebbDOKLevel.EXTENDED
        assert result.confidence > 0.0
        assert len(result.matched_patterns) > 0

    def test_no_clear_pattern_defaults_to_skill(self):
        """Test that questions with no clear patterns default to SKILL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Bu bir test sorusudur."
        result = classify_webb_dok(question)

        assert result.level == WebbDOKLevel.SKILL
        assert result.confidence < 0.5  # Low confidence
        assert len(result.matched_patterns) == 0

    def test_classify_with_options(self):
        """Test classification with multiple choice options."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Asiret nedir?"
        options = ["A) Kavim", "B) Aile", "C) Kabile", "D) Soy"]
        result = classify_webb_dok(question, options)

        assert result.level == WebbDOKLevel.RECALL
        assert result.confidence > 0.0

    def test_to_dict_conversion(self):
        """Test WebbDOKResult to_dict() method."""
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "Tanımını yazınız."
        result = classify_webb_dok(question)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "level" in result_dict
        assert "confidence" in result_dict
        assert "matched_patterns" in result_dict
        assert "rationale" in result_dict
        assert result_dict["level"] == result.level.value


class TestBloomToDoKEstimation:
    """Test Bloom taxonomy to Webb DOK estimation."""

    def test_bloom_remember_to_recall(self):
        """Test Bloom 'remember' maps to DOK RECALL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("remember")
        assert dok == WebbDOKLevel.RECALL

    def test_bloom_hatirlama_to_recall(self):
        """Test Turkish 'hatirlama' maps to DOK RECALL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("hatirlama")
        assert dok == WebbDOKLevel.RECALL

    def test_bloom_apply_to_skill(self):
        """Test Bloom 'apply' maps to DOK SKILL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("apply")
        assert dok == WebbDOKLevel.SKILL

    def test_bloom_uygulama_to_skill(self):
        """Test Turkish 'uygulama' maps to DOK SKILL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("uygulama")
        assert dok == WebbDOKLevel.SKILL

    def test_bloom_analyze_to_strategic(self):
        """Test Bloom 'analyze' maps to DOK STRATEGIC."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("analyze")
        assert dok == WebbDOKLevel.STRATEGIC

    def test_bloom_analiz_to_strategic(self):
        """Test Turkish 'analiz' maps to DOK STRATEGIC."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("analiz")
        assert dok == WebbDOKLevel.STRATEGIC

    def test_bloom_create_to_extended(self):
        """Test Bloom 'create' maps to DOK EXTENDED."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("create")
        assert dok == WebbDOKLevel.EXTENDED

    def test_bloom_yaratma_to_extended(self):
        """Test Turkish 'yaratma' maps to DOK EXTENDED."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("yaratma")
        assert dok == WebbDOKLevel.EXTENDED

    def test_bloom_unknown_defaults_to_skill(self):
        """Test unknown Bloom level defaults to SKILL."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import estimate_dok_from_bloom

        dok = estimate_dok_from_bloom("unknown_level")
        assert dok == WebbDOKLevel.SKILL


class TestTurkishNormalization:
    """Test Turkish text normalization in Webb DOK classifier."""

    def test_uppercase_turkish_i(self):
        """Test Turkish İ normalization."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "İSTANBUL nedir?"
        result = classify_webb_dok(question)
        # Should classify correctly despite uppercase İ
        assert result.level == WebbDOKLevel.RECALL

    def test_lowercase_turkish_i(self):
        """Test Turkish ı normalization."""
        from models.question_generation import WebbDOKLevel
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "DIYARBAKIR nasıl yazılır?"
        result = classify_webb_dok(question)
        # "nasıl yazılır" is procedural, typically SKILL or default
        assert result.level in [WebbDOKLevel.RECALL, WebbDOKLevel.SKILL]

    def test_mixed_case_patterns(self):
        """Test pattern matching with mixed case."""
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        question = "TANıMLAYıNıZ ve AÇIKLAYINIZ."
        result = classify_webb_dok(question)
        # Should detect both patterns despite mixed case
        assert len(result.matched_patterns) > 0
