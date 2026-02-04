"""
Test NLP Metrics Calculator

NLPMetricsCalculator sınıfı için comprehensive unit testler.
REQ-48.53 - REQ-48.56 gereksinimlerini test eder.
"""

import pytest
import math
from services.quality.nlp_metrics_calculator import NLPMetricsCalculator, NLPMetrics


class TestNLPMetricsCalculator:
    """NLPMetricsCalculator test sınıfı"""

    @pytest.fixture
    def calculator(self):
        """Varsayılan calculator instance"""
        return NLPMetricsCalculator()

    @pytest.fixture
    def sample_texts(self):
        """Örnek metin çiftleri"""
        return {
            "identical": ("Aynı metin", "Aynı metin"),
            "similar": ("Türkiye'nin başkenti Ankara'dır", "Türkiye başkenti Ankara"),
            "different": ("Matematik sorusu", "Tarih konusu"),
            "turkish": ("Güzel bir gün", "Çok güzel bir gün"),
        }

    # ==================== INITIALIZATION TESTS ====================

    def test_calculator_initialization_default(self):
        """Test: Varsayılan başlatma"""
        calc = NLPMetricsCalculator()

        assert calc.weights is not None
        assert len(calc.weights) == 3
        assert calc.weights["bleu"] == 0.30
        assert calc.weights["rouge"] == 0.30
        assert calc.weights["bert"] == 0.40
        assert calc.use_bert is False

    def test_calculator_initialization_custom_weights(self):
        """Test: Özel ağırlıklarla başlatma"""
        custom_weights = {"bleu": 0.40, "rouge": 0.30, "bert": 0.30}

        calc = NLPMetricsCalculator(weights=custom_weights)
        assert calc.weights["bleu"] == 0.40

    def test_calculator_initialization_with_bert(self):
        """Test: BERTScore ile başlatma"""
        calc = NLPMetricsCalculator(use_bert=True)
        assert calc.use_bert is True

    def test_calculator_initialization_invalid_weights(self):
        """Test: Geçersiz ağırlıklar hata fırlatır"""
        invalid_weights = {"bleu": 0.50, "rouge": 0.30, "bert": 0.10}  # Toplam 0.90

        with pytest.raises(ValueError, match="Ağırlıklar toplamı 1.0 olmalı"):
            NLPMetricsCalculator(weights=invalid_weights)

    # ==================== TOKENIZATION TESTS ====================

    def test_tokenize_basic(self, calculator):
        """Test: Temel tokenizasyon"""
        tokens = calculator._tokenize("Merhaba dünya")

        assert tokens == ["merhaba", "dünya"]

    def test_tokenize_with_punctuation(self, calculator):
        """Test: Noktalama işaretleriyle tokenizasyon"""
        tokens = calculator._tokenize("Merhaba, dünya!")

        assert "," in tokens
        assert "!" in tokens

    def test_tokenize_turkish_characters(self, calculator):
        """Test: Türkçe karakterlerle tokenizasyon"""
        tokens = calculator._tokenize("Güzel şehir çok büyük")

        assert "güzel" in tokens
        assert "şehir" in tokens
        assert "çok" in tokens
        assert "büyük" in tokens

    def test_tokenize_multiple_spaces(self, calculator):
        """Test: Çoklu boşluklarla tokenizasyon"""
        tokens = calculator._tokenize("Kelime1    kelime2")

        assert len(tokens) == 2
        assert tokens == ["kelime1", "kelime2"]

    def test_tokenize_empty_string(self, calculator):
        """Test: Boş string tokenizasyonu"""
        tokens = calculator._tokenize("")

        assert tokens == []

    # ==================== BLEU SCORE TESTS (REQ-48.53) ====================

    def test_bleu_identical_texts(self, calculator, sample_texts):
        """Test: Aynı metinler BLEU=1.0 (REQ-48.53)"""
        gen, ref = sample_texts["identical"]
        bleu = calculator.calculate_bleu(gen, ref)

        assert bleu == 1.0

    def test_bleu_similar_texts(self, calculator, sample_texts):
        """Test: Benzer metinler yüksek BLEU"""
        gen, ref = sample_texts["similar"]
        bleu = calculator.calculate_bleu(gen, ref)

        assert 0.3 < bleu < 1.0

    def test_bleu_different_texts(self, calculator, sample_texts):
        """Test: Farklı metinler düşük BLEU"""
        gen, ref = sample_texts["different"]
        bleu = calculator.calculate_bleu(gen, ref)

        assert 0.0 <= bleu < 0.5

    def test_bleu_empty_generated(self, calculator):
        """Test: Boş üretilen metin BLEU=0"""
        bleu = calculator.calculate_bleu("", "Referans metin")

        assert bleu == 0.0

    def test_bleu_empty_reference(self, calculator):
        """Test: Boş referans metin BLEU=0"""
        bleu = calculator.calculate_bleu("Üretilen metin", "")

        assert bleu == 0.0

    def test_bleu_brevity_penalty(self, calculator):
        """Test: Brevity penalty çalışıyor"""
        # Kısa üretilen metin
        short_gen = "Kısa"
        long_ref = "Bu çok uzun bir referans metnidir"

        bleu = calculator.calculate_bleu(short_gen, long_ref)

        # Brevity penalty nedeniyle düşük olmalı
        assert bleu < 0.5

    def test_bleu_max_n_parameter(self, calculator):
        """Test: max_n parametresi"""
        gen = "Bir iki üç dört beş"
        ref = "Bir iki üç dört beş"

        bleu_4 = calculator.calculate_bleu(gen, ref, max_n=4)
        bleu_2 = calculator.calculate_bleu(gen, ref, max_n=2)

        # Her ikisi de yüksek olmalı (aynı metinler)
        assert bleu_4 > 0.8
        assert bleu_2 > 0.8

    # ==================== ROUGE SCORE TESTS (REQ-48.54) ====================

    def test_rouge_identical_texts(self, calculator, sample_texts):
        """Test: Aynı metinler ROUGE=1.0 (REQ-48.54)"""
        gen, ref = sample_texts["identical"]
        rouge = calculator.calculate_rouge(gen, ref)

        assert rouge["rouge_1"] == 1.0
        assert rouge["rouge_2"] == 1.0
        assert rouge["rouge_l"] == 1.0

    def test_rouge_similar_texts(self, calculator, sample_texts):
        """Test: Benzer metinler yüksek ROUGE"""
        gen, ref = sample_texts["similar"]
        rouge = calculator.calculate_rouge(gen, ref)

        assert rouge["rouge_1"] > 0.5
        assert rouge["rouge_2"] >= 0.0
        assert rouge["rouge_l"] > 0.5

    def test_rouge_different_texts(self, calculator, sample_texts):
        """Test: Farklı metinler düşük ROUGE"""
        gen, ref = sample_texts["different"]
        rouge = calculator.calculate_rouge(gen, ref)

        assert rouge["rouge_1"] < 0.5
        assert rouge["rouge_2"] < 0.5
        assert rouge["rouge_l"] < 0.5

    def test_rouge_empty_texts(self, calculator):
        """Test: Boş metinler ROUGE=0"""
        rouge = calculator.calculate_rouge("", "Referans")

        assert rouge["rouge_1"] == 0.0
        assert rouge["rouge_2"] == 0.0
        assert rouge["rouge_l"] == 0.0

    def test_rouge_details(self, calculator):
        """Test: ROUGE detayları"""
        rouge = calculator.calculate_rouge("Test metin", "Test referans")

        assert "rouge_details" in rouge
        assert "gen_length" in rouge["rouge_details"]
        assert "ref_length" in rouge["rouge_details"]

    # ==================== NGRAM TESTS ====================

    def test_get_ngrams_unigram(self, calculator):
        """Test: Unigram çıkarma"""
        tokens = ["bir", "iki", "üç"]
        ngrams = calculator._get_ngrams(tokens, 1)

        assert len(ngrams) == 3
        assert ngrams[("bir",)] == 1
        assert ngrams[("iki",)] == 1
        assert ngrams[("üç",)] == 1

    def test_get_ngrams_bigram(self, calculator):
        """Test: Bigram çıkarma"""
        tokens = ["bir", "iki", "üç"]
        ngrams = calculator._get_ngrams(tokens, 2)

        assert len(ngrams) == 2
        assert ngrams[("bir", "iki")] == 1
        assert ngrams[("iki", "üç")] == 1

    def test_get_ngrams_trigram(self, calculator):
        """Test: Trigram çıkarma"""
        tokens = ["bir", "iki", "üç", "dört"]
        ngrams = calculator._get_ngrams(tokens, 3)

        assert len(ngrams) == 2
        assert ngrams[("bir", "iki", "üç")] == 1
        assert ngrams[("iki", "üç", "dört")] == 1

    def test_get_ngrams_repeated(self, calculator):
        """Test: Tekrar eden n-gramlar"""
        tokens = ["bir", "bir", "iki"]
        ngrams = calculator._get_ngrams(tokens, 1)

        assert ngrams[("bir",)] == 2
        assert ngrams[("iki",)] == 1

    # ==================== LCS TESTS ====================

    def test_lcs_length_identical(self, calculator):
        """Test: Aynı diziler için LCS"""
        seq1 = ["a", "b", "c"]
        seq2 = ["a", "b", "c"]

        lcs = calculator._lcs_length(seq1, seq2)

        assert lcs == 3

    def test_lcs_length_partial_match(self, calculator):
        """Test: Kısmi eşleşme için LCS"""
        seq1 = ["a", "b", "c", "d"]
        seq2 = ["a", "c", "d"]

        lcs = calculator._lcs_length(seq1, seq2)

        assert lcs == 3  # "a", "c", "d"

    def test_lcs_length_no_match(self, calculator):
        """Test: Eşleşme yok için LCS"""
        seq1 = ["a", "b", "c"]
        seq2 = ["x", "y", "z"]

        lcs = calculator._lcs_length(seq1, seq2)

        assert lcs == 0

    def test_lcs_length_empty(self, calculator):
        """Test: Boş diziler için LCS"""
        lcs = calculator._lcs_length([], ["a", "b"])

        assert lcs == 0

    # ==================== SEMANTIC SIMILARITY TESTS (REQ-48.55) ====================

    def test_semantic_similarity_identical(self, calculator, sample_texts):
        """Test: Aynı metinler yüksek semantik benzerlik (REQ-48.55)"""
        gen, ref = sample_texts["identical"]
        similarity = calculator._calculate_semantic_similarity_simple(gen, ref)

        assert similarity == 1.0

    def test_semantic_similarity_similar(self, calculator, sample_texts):
        """Test: Benzer metinler orta semantik benzerlik"""
        gen, ref = sample_texts["similar"]
        similarity = calculator._calculate_semantic_similarity_simple(gen, ref)

        assert 0.3 < similarity < 1.0

    def test_semantic_similarity_different(self, calculator, sample_texts):
        """Test: Farklı metinler düşük semantik benzerlik"""
        gen, ref = sample_texts["different"]
        similarity = calculator._calculate_semantic_similarity_simple(gen, ref)

        assert 0.0 <= similarity < 0.5

    def test_semantic_similarity_empty(self, calculator):
        """Test: Boş metinler için semantik benzerlik"""
        similarity = calculator._calculate_semantic_similarity_simple("", "Test")

        assert similarity == 0.0

    # ==================== CALCULATE METRICS TESTS (REQ-48.56) ====================

    def test_calculate_metrics_complete(self, calculator, sample_texts):
        """Test: Tüm metrikleri hesapla (REQ-48.56)"""
        gen, ref = sample_texts["similar"]
        metrics = calculator.calculate_metrics(gen, ref)

        assert isinstance(metrics, NLPMetrics)
        assert 0 <= metrics.bleu_score <= 1
        assert 0 <= metrics.rouge_1 <= 1
        assert 0 <= metrics.rouge_2 <= 1
        assert 0 <= metrics.rouge_l <= 1
        assert 0 <= metrics.bert_score <= 1
        assert 0 <= metrics.combined_score <= 1

    def test_calculate_metrics_combined_score(self, calculator, sample_texts):
        """Test: Ağırlıklı ortalama combined_score (REQ-48.56)"""
        gen, ref = sample_texts["identical"]
        metrics = calculator.calculate_metrics(gen, ref)

        # Aynı metinler için combined_score yüksek olmalı
        assert metrics.combined_score > 0.8

    def test_calculate_metrics_weights_applied(self, calculator):
        """Test: Ağırlıklar doğru uygulanıyor"""
        gen = "Test metin"
        ref = "Test metin"

        metrics = calculator.calculate_metrics(gen, ref)

        # Manuel hesaplama
        expected_combined = (
            calculator.weights["bleu"] * metrics.bleu_score
            + calculator.weights["rouge"]
            * (metrics.rouge_1 + metrics.rouge_2 + metrics.rouge_l)
            / 3
            + calculator.weights["bert"] * metrics.bert_score
        )

        assert abs(metrics.combined_score - expected_combined) < 0.01

    def test_calculate_metrics_details(self, calculator, sample_texts):
        """Test: Metrik detayları"""
        gen, ref = sample_texts["similar"]
        metrics = calculator.calculate_metrics(gen, ref)

        assert "bleu_details" in metrics.details
        assert "rouge_details" in metrics.details

    # ==================== BATCH OPERATIONS TESTS ====================

    def test_batch_calculate(self, calculator):
        """Test: Toplu metrik hesaplama"""
        generated = ["Metin 1", "Metin 2", "Metin 3"]
        reference = ["Ref 1", "Ref 2", "Ref 3"]

        results = calculator.batch_calculate(generated, reference)

        assert len(results) == 3
        assert all(isinstance(m, NLPMetrics) for m in results)

    def test_batch_calculate_mismatched_lengths(self, calculator):
        """Test: Farklı uzunluklarda listeler hata fırlatır"""
        generated = ["Metin 1", "Metin 2"]
        reference = ["Ref 1"]

        with pytest.raises(ValueError, match="eşit olmalı"):
            calculator.batch_calculate(generated, reference)

    def test_batch_calculate_empty(self, calculator):
        """Test: Boş listelerle toplu hesaplama"""
        results = calculator.batch_calculate([], [])

        assert results == []

    # ==================== AVERAGE METRICS TESTS ====================

    def test_get_average_metrics(self, calculator):
        """Test: Ortalama metrikleri hesapla"""
        metrics_list = [
            NLPMetrics(0.8, 0.7, 0.6, 0.75, 0.85, 0.78, {}),
            NLPMetrics(0.9, 0.8, 0.7, 0.85, 0.90, 0.85, {}),
            NLPMetrics(0.7, 0.6, 0.5, 0.65, 0.75, 0.70, {}),
        ]

        avg = calculator.get_average_metrics(metrics_list)

        assert "avg_bleu" in avg
        assert "avg_rouge_1" in avg
        assert "avg_rouge_2" in avg
        assert "avg_rouge_l" in avg
        assert "avg_bert_score" in avg
        assert "avg_combined" in avg
        assert "count" in avg
        assert avg["count"] == 3

    def test_get_average_metrics_empty(self, calculator):
        """Test: Boş liste için ortalama"""
        avg = calculator.get_average_metrics([])

        assert avg == {}

    def test_get_average_metrics_values(self, calculator):
        """Test: Ortalama değerleri doğru hesaplanıyor"""
        metrics_list = [
            NLPMetrics(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, {}),
            NLPMetrics(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, {}),
        ]

        avg = calculator.get_average_metrics(metrics_list)

        assert avg["avg_bleu"] == 0.75
        assert avg["avg_rouge_1"] == 0.75
        assert avg["avg_bert_score"] == 0.75

    # ==================== EDGE CASES ====================

    def test_very_long_texts(self, calculator):
        """Test: Çok uzun metinler"""
        long_gen = " ".join(["kelime"] * 1000)
        long_ref = " ".join(["kelime"] * 1000)

        metrics = calculator.calculate_metrics(long_gen, long_ref)

        # Aynı kelimeler, yüksek skorlar bekleniyor
        assert metrics.bleu_score > 0.8
        assert metrics.rouge_1 > 0.8

    def test_special_characters(self, calculator):
        """Test: Özel karakterler"""
        gen = "Test @#$% metin!"
        ref = "Test @#$% metin!"

        metrics = calculator.calculate_metrics(gen, ref)

        # Aynı metinler, yüksek skorlar
        assert metrics.combined_score > 0.8

    def test_numbers_in_text(self, calculator):
        """Test: Sayılar içeren metinler"""
        gen = "2x + 5 = 15"
        ref = "2x + 5 = 15"

        metrics = calculator.calculate_metrics(gen, ref)

        assert metrics.bleu_score == 1.0

    # ==================== PRECISION TESTS ====================

    def test_ngram_precision_perfect(self, calculator):
        """Test: Mükemmel n-gram precision"""
        gen_tokens = ["bir", "iki", "üç"]
        ref_tokens = ["bir", "iki", "üç"]

        precision = calculator._ngram_precision(gen_tokens, ref_tokens, 1)

        assert precision == 1.0

    def test_ngram_precision_partial(self, calculator):
        """Test: Kısmi n-gram precision"""
        gen_tokens = ["bir", "iki", "dört"]
        ref_tokens = ["bir", "iki", "üç"]

        precision = calculator._ngram_precision(gen_tokens, ref_tokens, 1)

        assert 0.5 < precision < 1.0

    def test_ngram_precision_no_match(self, calculator):
        """Test: Eşleşme yok n-gram precision"""
        gen_tokens = ["a", "b", "c"]
        ref_tokens = ["x", "y", "z"]

        precision = calculator._ngram_precision(gen_tokens, ref_tokens, 1)

        assert precision == 0.0

    # ==================== ROUGE-N TESTS ====================

    def test_rouge_n_f1_score(self, calculator):
        """Test: ROUGE-N F1-score hesaplama"""
        gen_tokens = ["bir", "iki", "üç"]
        ref_tokens = ["bir", "iki", "dört"]

        rouge_n = calculator._rouge_n(gen_tokens, ref_tokens, 1)

        # 2/3 overlap, F1 hesaplanmalı
        assert 0.5 < rouge_n < 1.0

    def test_rouge_n_empty_reference(self, calculator):
        """Test: Boş referans için ROUGE-N"""
        gen_tokens = ["bir", "iki"]
        ref_tokens = []

        rouge_n = calculator._rouge_n(gen_tokens, ref_tokens, 1)

        assert rouge_n == 0.0


# ==================== INTEGRATION TESTS ====================


class TestNLPMetricsCalculatorIntegration:
    """Integration testleri"""

    def test_real_world_turkish_questions(self):
        """Test: Gerçek Türkçe sorular"""
        calc = NLPMetricsCalculator()

        generated = "Türkiye'nin başkenti Ankara'dır ve en büyük şehri İstanbul'dur."
        reference = "Türkiye başkenti Ankara, en kalabalık şehri İstanbul."

        metrics = calc.calculate_metrics(generated, reference)

        # Benzer anlamlar, orta-yüksek skorlar bekleniyor
        assert metrics.combined_score > 0.4
        assert metrics.bleu_score > 0.2
        assert metrics.rouge_1 > 0.4

    def test_paraphrased_questions(self):
        """Test: Parafraz edilmiş sorular"""
        calc = NLPMetricsCalculator()

        generated = "2 artı 3 eşittir kaçtır?"
        reference = "2 ile 3'ün toplamı nedir?"

        metrics = calc.calculate_metrics(generated, reference)

        # Farklı kelimeler ama aynı anlam
        assert metrics.bert_score > 0.0  # Semantik benzerlik var

    def test_batch_processing_performance(self):
        """Test: Toplu işleme performansı"""
        calc = NLPMetricsCalculator()

        generated = [f"Soru {i} metni" for i in range(50)]
        reference = [f"Referans {i} metni" for i in range(50)]

        results = calc.batch_calculate(generated, reference)

        assert len(results) == 50

        # Ortalama hesapla
        avg = calc.get_average_metrics(results)
        assert "avg_combined" in avg

    def test_quality_comparison(self):
        """Test: Kalite karşılaştırması"""
        calc = NLPMetricsCalculator()

        # İyi üretim
        good_gen = "Türkiye'nin başkenti Ankara'dır."
        # Kötü üretim
        bad_gen = "Başkent şehir yer."

        reference = "Türkiye'nin başkenti Ankara'dır."

        good_metrics = calc.calculate_metrics(good_gen, reference)
        bad_metrics = calc.calculate_metrics(bad_gen, reference)

        # İyi üretim daha yüksek skor almalı
        assert good_metrics.combined_score > bad_metrics.combined_score
