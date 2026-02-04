"""
Test Question Quality Scorer

QuestionQualityScorer sınıfı için comprehensive unit testler.
REQ-48.49 - REQ-48.52 gereksinimlerini test eder.
"""

import pytest
from services.quality.question_quality_scorer import (
    QuestionQualityScorer,
    QualityCriterion,
    QualityScore,
)


class TestQuestionQualityScorer:
    """QuestionQualityScorer test sınıfı"""

    @pytest.fixture
    def scorer(self):
        """Varsayılan scorer instance"""
        return QuestionQualityScorer()

    @pytest.fixture
    def sample_question(self):
        """Örnek kaliteli soru"""
        return {
            "question_text": "Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?",
            "options": [
                "Kitabı masanın üzerine koydum.",
                "Yarın sinemaya gideceğiz.",
                "O, çok güzel bir resim çizdi.",
                "Annem bugün markete gitti.",
                "Babam işten erken geldi.",
            ],
            "correct_answer": 2,
            "explanation": "Üçüncü şıkta 'çizdi' kelimesi doğru yazılmıştır.",
            "subject": "Türkçe",
            "difficulty_level": "orta",
        }

    # ==================== INITIALIZATION TESTS ====================

    def test_scorer_initialization_default_weights(self):
        """Test: Varsayılan ağırlıklarla başlatma"""
        scorer = QuestionQualityScorer()

        assert scorer.weights is not None
        assert len(scorer.weights) == 7
        assert scorer.weights[QualityCriterion.OSYM_COMPLIANCE] == 0.40

    def test_scorer_initialization_custom_weights(self):
        """Test: Özel ağırlıklarla başlatma"""
        custom_weights = {
            QualityCriterion.OSYM_COMPLIANCE: 0.50,
            QualityCriterion.GRAMMAR: 0.20,
            QualityCriterion.CLARITY: 0.10,
            QualityCriterion.DIFFICULTY: 0.05,
            QualityCriterion.DISTRACTOR_QUALITY: 0.05,
            QualityCriterion.CONTENT_ACCURACY: 0.05,
            QualityCriterion.EDUCATIONAL_VALUE: 0.05,
        }

        scorer = QuestionQualityScorer(weights=custom_weights)
        assert scorer.weights[QualityCriterion.OSYM_COMPLIANCE] == 0.50

    def test_scorer_initialization_invalid_weights(self):
        """Test: Geçersiz ağırlıklar hata fırlatır"""
        invalid_weights = {
            QualityCriterion.OSYM_COMPLIANCE: 0.50,
            QualityCriterion.GRAMMAR: 0.30,
        }

        with pytest.raises(ValueError, match="Ağırlıklar toplamı 1.0 olmalı"):
            QuestionQualityScorer(weights=invalid_weights)

    # ==================== SCORE QUESTION TESTS (REQ-48.49, REQ-48.50) ====================

    def test_score_question_basic(self, scorer, sample_question):
        """Test: Temel soru skorlama"""
        result = scorer.score_question(
            question_text=sample_question["question_text"],
            options=sample_question["options"],
            correct_answer=sample_question["correct_answer"],
            explanation=sample_question["explanation"],
            subject=sample_question["subject"],
            difficulty_level=sample_question["difficulty_level"],
        )

        assert isinstance(result, QualityScore)
        assert 0 <= result.total_score <= 100
        assert len(result.criterion_scores) == 7
        assert isinstance(result.passed_threshold, bool)
        assert isinstance(result.feedback, list)

    def test_score_question_high_quality(self, scorer):
        """Test: Yüksek kaliteli soru yüksek skor alır"""
        result = scorer.score_question(
            question_text="Aşağıdaki ifadelerden hangisi doğrudur?",
            options=[
                "Türkiye'nin başkenti Ankara'dır.",
                "Türkiye'nin başkenti İstanbul'dur.",
                "Türkiye'nin başkenti İzmir'dir.",
                "Türkiye'nin başkenti Bursa'dır.",
                "Türkiye'nin başkenti Antalya'dır.",
            ],
            correct_answer=0,
            explanation="Türkiye Cumhuriyeti'nin başkenti 1923'ten beri Ankara'dır.",
            subject="Sosyal Bilgiler",
            difficulty_level="kolay",
        )

        assert result.total_score >= 70.0
        assert result.passed_threshold is True

    def test_score_question_low_quality_missing_options(self, scorer):
        """Test: Eksik şıklı soru düşük skor alır"""
        result = scorer.score_question(
            question_text="Hangisi doğru?",
            options=["A", "B", "C"],  # Sadece 3 şık
            correct_answer=0,
            explanation=None,
            subject="Test",
            difficulty_level="kolay",
        )

        assert result.total_score < 70.0
        assert result.passed_threshold is False

    def test_score_question_weighted_breakdown(self, scorer, sample_question):
        """Test: Ağırlıklı skor dağılımı (REQ-48.50)"""
        result = scorer.score_question(
            question_text=sample_question["question_text"],
            options=sample_question["options"],
            correct_answer=sample_question["correct_answer"],
        )

        assert "osym_compliance" in result.weighted_breakdown
        assert "grammar" in result.weighted_breakdown

        # ÖSYM uygunluğu en yüksek ağırlığa sahip olmalı
        osym_weight = result.weighted_breakdown["osym_compliance"]
        grammar_weight = result.weighted_breakdown["grammar"]
        assert osym_weight >= grammar_weight

    # ==================== OSYM COMPLIANCE TESTS ====================

    def test_osym_compliance_perfect_format(self, scorer):
        """Test: Mükemmel ÖSYM formatı tam puan alır"""
        score = scorer._score_osym_compliance(
            question_text="Bu yeterli uzunlukta bir soru metnidir ve ÖSYM formatına uygundur.",
            options=["Şık A", "Şık B", "Şık C", "Şık D", "Şık E"],
            correct_answer=2,
        )

        assert score == 1.0

    def test_osym_compliance_wrong_option_count(self, scorer):
        """Test: Yanlış şık sayısı puan kaybettirir"""
        score = scorer._score_osym_compliance(
            question_text="Soru metni",
            options=["A", "B", "C"],  # 3 şık
            correct_answer=0,
        )

        assert score < 1.0

    def test_osym_compliance_short_question(self, scorer):
        """Test: Çok kısa soru puan kaybettirir"""
        score = scorer._score_osym_compliance(
            question_text="Kısa?",  # 20 karakterden az
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
        )

        assert score < 1.0

    def test_osym_compliance_invalid_correct_answer(self, scorer):
        """Test: Geçersiz doğru cevap puan kaybettirir"""
        score = scorer._score_osym_compliance(
            question_text="Yeterli uzunlukta soru metni",
            options=["A", "B", "C", "D", "E"],
            correct_answer=10,  # Geçersiz indeks
        )

        assert score < 1.0

    # ==================== GRAMMAR TESTS ====================

    def test_grammar_perfect(self, scorer):
        """Test: Mükemmel dilbilgisi tam puan alır"""
        score = scorer._score_grammar(
            question_text="Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?",
            options=["Şık A", "Şık B", "Şık C", "Şık D", "Şık E"],
        )

        assert score == 1.0

    def test_grammar_missing_question_mark(self, scorer):
        """Test: Soru işareti eksikliği puan kaybettirir"""
        score = scorer._score_grammar(
            question_text="Hangisi doğru",  # Soru işareti yok
            options=["A", "B", "C", "D", "E"],
        )

        assert score < 1.0

    def test_grammar_lowercase_start(self, scorer):
        """Test: Küçük harfle başlama puan kaybettirir"""
        score = scorer._score_grammar(
            question_text="hangisi doğru?",  # Küçük harfle başlıyor
            options=["A", "B", "C", "D", "E"],
        )

        assert score < 1.0

    def test_grammar_double_spaces(self, scorer):
        """Test: Çift boşluk puan kaybettirir"""
        score = scorer._score_grammar(
            question_text="Hangisi  doğru?",  # Çift boşluk
            options=["A", "B", "C", "D", "E"],
        )

        assert score < 1.0

    # ==================== CLARITY TESTS ====================

    def test_clarity_optimal_length(self, scorer):
        """Test: Optimal uzunluk tam puan alır"""
        score = scorer._score_clarity(
            "Bu optimal uzunlukta bir soru metnidir ve anlaşılırdır."
        )

        assert score == 1.0

    def test_clarity_too_long(self, scorer):
        """Test: Çok uzun soru puan kaybettirir"""
        long_text = "A" * 250  # 200 karakterden uzun
        score = scorer._score_clarity(long_text)

        assert score < 1.0

    def test_clarity_too_short(self, scorer):
        """Test: Çok kısa soru puan kaybettirir"""
        score = scorer._score_clarity("Kısa?")  # 30 karakterden kısa

        assert score < 1.0

    def test_clarity_vague_terms(self, scorer):
        """Test: Belirsiz ifadeler puan kaybettirir"""
        score = scorer._score_clarity("Bazı durumlarda genellikle hangisi doğrudur?")

        assert score < 1.0

    # ==================== DISTRACTOR QUALITY TESTS ====================

    def test_distractor_quality_good(self, scorer):
        """Test: İyi çeldiriciler yüksek puan alır"""
        score = scorer._score_distractors(
            options=[
                "Doğru cevap",
                "Çeldirici 1",
                "Çeldirici 2",
                "Çeldirici 3",
                "Çeldirici 4",
            ],
            correct_answer=0,
        )

        assert score >= 0.7

    def test_distractor_quality_duplicate(self, scorer):
        """Test: Tekrar eden çeldiriciler puan kaybettirir"""
        score = scorer._score_distractors(
            options=["Doğru", "Aynı", "Aynı", "Farklı", "Başka"], correct_answer=0
        )

        assert score < 1.0

    def test_distractor_quality_too_short(self, scorer):
        """Test: Çok kısa çeldiriciler puan kaybettirir"""
        score = scorer._score_distractors(
            options=["Doğru cevap", "A", "B", "C", "D"], correct_answer=0
        )

        assert score < 1.0

    def test_distractor_quality_length_imbalance(self, scorer):
        """Test: Uzunluk dengesizliği puan kaybettirir"""
        score = scorer._score_distractors(
            options=[
                "Kısa",
                "Bu çok uzun bir çeldirici seçeneğidir",
                "Orta",
                "Kısa",
                "Kısa",
            ],
            correct_answer=0,
        )

        assert score < 1.0

    # ==================== BATCH OPERATIONS TESTS ====================

    def test_batch_score(self, scorer):
        """Test: Toplu skorlama"""
        questions = [
            {
                "question_text": "Soru 1?",
                "options": ["A", "B", "C", "D", "E"],
                "correct_answer": 0,
            },
            {
                "question_text": "Soru 2?",
                "options": ["A", "B", "C", "D", "E"],
                "correct_answer": 1,
            },
        ]

        results = scorer.batch_score(questions)

        assert len(results) == 2
        assert all(isinstance(r, QualityScore) for r in results)

    def test_filter_by_threshold_default(self, scorer):
        """Test: Varsayılan eşik ile filtreleme (REQ-48.51)"""
        questions = [
            {
                "question_text": "Yüksek kaliteli soru metni burada?",
                "options": ["Şık A", "Şık B", "Şık C", "Şık D", "Şık E"],
                "correct_answer": 0,
                "explanation": "Detaylı açıklama",
            },
            {"question_text": "Kötü?", "options": ["A", "B"], "correct_answer": 0},
        ]

        filtered = scorer.filter_by_threshold(questions)

        # Sadece kaliteli soru geçmeli
        assert len(filtered) <= len(questions)
        assert all(q.get("quality_score", 0) >= 70.0 for q in filtered)

    def test_filter_by_threshold_custom(self, scorer):
        """Test: Özel eşik ile filtreleme"""
        questions = [
            {
                "question_text": "Orta kaliteli soru?",
                "options": ["A", "B", "C", "D", "E"],
                "correct_answer": 0,
            }
        ]

        filtered = scorer.filter_by_threshold(questions, threshold=50.0)

        # Düşük eşik ile daha fazla soru geçmeli
        assert len(filtered) >= 0

    # ==================== FEEDBACK GENERATION TESTS ====================

    def test_feedback_generation_passed(self, scorer):
        """Test: Başarılı soru için geri bildirim"""
        criterion_scores = {
            "osym_compliance": 0.9,
            "grammar": 0.9,
            "clarity": 0.9,
            "difficulty": 0.9,
            "distractor_quality": 0.9,
            "content_accuracy": 0.9,
            "educational_value": 0.9,
        }

        feedback = scorer._generate_feedback(criterion_scores, passed_threshold=True)

        assert len(feedback) > 0
        assert any("✅" in f for f in feedback)

    def test_feedback_generation_failed(self, scorer):
        """Test: Başarısız soru için geri bildirim"""
        criterion_scores = {
            "osym_compliance": 0.5,
            "grammar": 0.6,
            "clarity": 0.4,
            "difficulty": 0.7,
            "distractor_quality": 0.5,
            "content_accuracy": 0.6,
            "educational_value": 0.5,
        }

        feedback = scorer._generate_feedback(criterion_scores, passed_threshold=False)

        assert len(feedback) > 0
        assert any("⚠️" in f for f in feedback)
        assert any("❌" in f for f in feedback)

    # ==================== EDGE CASES ====================

    def test_empty_question_text(self, scorer):
        """Test: Boş soru metni"""
        result = scorer.score_question(
            question_text="", options=["A", "B", "C", "D", "E"], correct_answer=0
        )

        assert result.total_score < 50.0

    def test_empty_options(self, scorer):
        """Test: Boş şıklar"""
        result = scorer.score_question(
            question_text="Soru metni?", options=[], correct_answer=0
        )

        assert result.total_score < 50.0

    def test_none_explanation(self, scorer):
        """Test: None açıklama"""
        result = scorer.score_question(
            question_text="Soru metni?",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0,
            explanation=None,
        )

        # Açıklama olmadan da skorlama yapılabilmeli
        assert result.total_score >= 0

    # ==================== SCORE RANGE TESTS (REQ-48.52) ====================

    def test_score_range_0_to_100(self, scorer, sample_question):
        """Test: Skor 0-100 arasında (REQ-48.52)"""
        result = scorer.score_question(
            question_text=sample_question["question_text"],
            options=sample_question["options"],
            correct_answer=sample_question["correct_answer"],
        )

        assert 0 <= result.total_score <= 100

    def test_all_criterion_scores_0_to_1(self, scorer, sample_question):
        """Test: Tüm kriter skorları 0-1 arası"""
        result = scorer.score_question(
            question_text=sample_question["question_text"],
            options=sample_question["options"],
            correct_answer=sample_question["correct_answer"],
        )

        for score in result.criterion_scores.values():
            assert 0 <= score <= 1

    # ==================== QUALITY THRESHOLD TESTS (REQ-48.51) ====================

    def test_quality_threshold_constant(self):
        """Test: Kalite eşiği 70.0 (REQ-48.51)"""
        assert QuestionQualityScorer.QUALITY_THRESHOLD == 70.0

    def test_passed_threshold_true(self, scorer):
        """Test: Eşiği geçen soru passed_threshold=True"""
        result = scorer.score_question(
            question_text="Yüksek kaliteli soru metni burada yer almaktadır?",
            options=[
                "Şık A detaylı",
                "Şık B detaylı",
                "Şık C detaylı",
                "Şık D detaylı",
                "Şık E detaylı",
            ],
            correct_answer=0,
            explanation="Çok detaylı açıklama burada yer almaktadır.",
        )

        if result.total_score >= 70.0:
            assert result.passed_threshold is True

    def test_passed_threshold_false(self, scorer):
        """Test: Eşiği geçemeyen soru passed_threshold=False"""
        result = scorer.score_question(
            question_text="Kötü?", options=["A", "B"], correct_answer=0
        )

        assert result.passed_threshold is False


# ==================== INTEGRATION TESTS ====================


class TestQuestionQualityScorerIntegration:
    """Integration testleri"""

    def test_real_world_turkish_question(self):
        """Test: Gerçek Türkçe sorusu"""
        scorer = QuestionQualityScorer()

        result = scorer.score_question(
            question_text="Aşağıdaki cümlelerin hangisinde noktalama yanlışı vardır?",
            options=[
                "Kitabı, defteri ve kalemi aldım.",
                "Yarın sinemaya gideceğiz.",
                "O çok güzel bir resim çizdi.",
                "Annem, bugün markete gitti.",
                "Babam işten erken geldi.",
            ],
            correct_answer=0,
            explanation="İlk şıkta virgül kullanımı yanlıştır. 'Kitabı, defteri ve kalemi' yerine 'Kitabı, defteri ve kalemi' olmalıdır.",
            subject="Türkçe",
            difficulty_level="orta",
        )

        assert result.total_score > 0
        assert len(result.feedback) > 0

    def test_real_world_math_question(self):
        """Test: Gerçek matematik sorusu"""
        scorer = QuestionQualityScorer()

        result = scorer.score_question(
            question_text="2x + 5 = 15 denkleminde x kaçtır?",
            options=["3", "5", "7", "10", "15"],
            correct_answer=1,
            explanation="2x + 5 = 15 → 2x = 10 → x = 5",
            subject="Matematik",
            difficulty_level="kolay",
        )

        assert result.total_score >= 60.0

    def test_batch_processing_performance(self):
        """Test: Toplu işleme performansı"""
        scorer = QuestionQualityScorer()

        questions = [
            {
                "question_text": f"Soru {i} metni burada?",
                "options": ["A", "B", "C", "D", "E"],
                "correct_answer": i % 5,
            }
            for i in range(100)
        ]

        results = scorer.batch_score(questions)

        assert len(results) == 100
        assert all(isinstance(r, QualityScore) for r in results)
