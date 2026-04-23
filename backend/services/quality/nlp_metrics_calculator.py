"""
NLP Metrikleri Hesaplayıcı

BLEU, ROUGE ve BERTScore metriklerini hesaplar.
Soru üretim kalitesini değerlendirmek için kullanılır.

Requirements: REQ-48.53 - REQ-48.56
"""

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class NLPMetrics:
    """NLP metrikleri sonucu"""

    bleu_score: float  # 0-1 arası, akıcılık için
    rouge_1: float  # 0-1 arası, unigram overlap
    rouge_2: float  # 0-1 arası, bigram overlap
    rouge_l: float  # 0-1 arası, longest common subsequence
    bert_score: float  # 0-1 arası, semantik benzerlik
    combined_score: float  # Ağırlıklı ortalama
    details: dict[str, any]  # Detaylı bilgiler


class NLPMetricsCalculator:
    """
    NLP metrikleri hesaplayıcı

    REQ-48.53: BLEU score for fluency (akıcılık)
    REQ-48.54: ROUGE score for content overlap (içerik örtüşmesi)
    REQ-48.55: BERTScore for semantic similarity (semantik benzerlik)
    REQ-48.56: Metrik skorlarını ağırlıklı ortalama ile birleştirme
    """

    # Metrik ağırlıkları (REQ-48.56)
    DEFAULT_WEIGHTS = {
        "bleu": 0.30,  # %30 - Akıcılık
        "rouge": 0.30,  # %30 - İçerik örtüşmesi
        "bert": 0.40,  # %40 - Semantik benzerlik (en önemli)
    }

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        use_bert: bool = False,  # BERTScore hesaplama (opsiyonel, yavaş)
    ):
        """
        Args:
            weights: Özel metrik ağırlıkları
            use_bert: BERTScore hesaplansın mı? (varsayılan: False, basit yaklaşım kullanılır)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.use_bert = use_bert
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Ağırlıkların toplamının 1.0 olduğunu kontrol et"""
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Ağırlıklar toplamı 1.0 olmalı, şu an: {total}")

    def calculate_metrics(self, generated_text: str, reference_text: str) -> NLPMetrics:
        """
        Tüm NLP metriklerini hesapla

        Args:
            generated_text: Üretilen metin (soru)
            reference_text: Referans metin (orijinal/hedef soru)

        Returns:
            NLPMetrics: Tüm metrikler
        """
        # BLEU skoru hesapla (REQ-48.53)
        bleu_score = self.calculate_bleu(generated_text, reference_text)

        # ROUGE skorları hesapla (REQ-48.54)
        rouge_scores = self.calculate_rouge(generated_text, reference_text)

        # BERTScore hesapla (REQ-48.55)
        if self.use_bert:
            bert_score = self._calculate_bert_score_advanced(
                generated_text, reference_text
            )
        else:
            # Basit semantik benzerlik (embedding olmadan)
            bert_score = self._calculate_semantic_similarity_simple(
                generated_text, reference_text
            )

        # Ağırlıklı ortalama hesapla (REQ-48.56)
        combined_score = (
            self.weights["bleu"] * bleu_score
            + self.weights["rouge"]
            * (
                rouge_scores["rouge_1"]
                + rouge_scores["rouge_2"]
                + rouge_scores["rouge_l"]
            )
            / 3
            + self.weights["bert"] * bert_score
        )

        return NLPMetrics(
            bleu_score=round(bleu_score, 4),
            rouge_1=round(rouge_scores["rouge_1"], 4),
            rouge_2=round(rouge_scores["rouge_2"], 4),
            rouge_l=round(rouge_scores["rouge_l"], 4),
            bert_score=round(bert_score, 4),
            combined_score=round(combined_score, 4),
            details={
                "bleu_details": rouge_scores.get("bleu_details", {}),
                "rouge_details": rouge_scores.get("rouge_details", {}),
            },
        )

    def calculate_bleu(
        self, generated_text: str, reference_text: str, max_n: int = 4
    ) -> float:
        """
        BLEU (Bilingual Evaluation Understudy) skoru hesapla

        BLEU akıcılık ve n-gram örtüşmesini ölçer.

        Args:
            generated_text: Üretilen metin
            reference_text: Referans metin
            max_n: Maksimum n-gram boyutu (varsayılan 4)

        Returns:
            BLEU skoru (0-1 arası)
        """
        # Metinleri tokenize et
        gen_tokens = self._tokenize(generated_text)
        ref_tokens = self._tokenize(reference_text)

        if not gen_tokens or not ref_tokens:
            return 0.0

        # Brevity penalty (kısalık cezası)
        bp = self._brevity_penalty(len(gen_tokens), len(ref_tokens))

        # N-gram precision hesapla
        precisions = []
        for n in range(1, max_n + 1):
            precision = self._ngram_precision(gen_tokens, ref_tokens, n)
            precisions.append(precision)

        # Geometric mean
        if all(p > 0 for p in precisions):
            geo_mean = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        else:
            geo_mean = 0.0

        bleu = bp * geo_mean
        return min(1.0, max(0.0, bleu))

    def calculate_rouge(
        self, generated_text: str, reference_text: str
    ) -> dict[str, float]:
        """
        ROUGE (Recall-Oriented Understudy for Gisting Evaluation) skorları hesapla

        ROUGE içerik örtüşmesini ölçer.

        Args:
            generated_text: Üretilen metin
            reference_text: Referans metin

        Returns:
            ROUGE-1, ROUGE-2, ROUGE-L skorları
        """
        gen_tokens = self._tokenize(generated_text)
        ref_tokens = self._tokenize(reference_text)

        if not gen_tokens or not ref_tokens:
            return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0}

        # ROUGE-1 (unigram overlap)
        rouge_1 = self._rouge_n(gen_tokens, ref_tokens, 1)

        # ROUGE-2 (bigram overlap)
        rouge_2 = self._rouge_n(gen_tokens, ref_tokens, 2)

        # ROUGE-L (longest common subsequence)
        rouge_l = self._rouge_l(gen_tokens, ref_tokens)

        return {
            "rouge_1": rouge_1,
            "rouge_2": rouge_2,
            "rouge_l": rouge_l,
            "rouge_details": {
                "gen_length": len(gen_tokens),
                "ref_length": len(ref_tokens),
            },
        }

    def _tokenize(self, text: str) -> list[str]:
        """Metni tokenize et (Türkçe uyumlu)"""
        # Küçük harfe çevir
        text = text.lower()

        # Noktalama işaretlerini ayır
        text = re.sub(r"([.,!?;:])", r" \1 ", text)

        # Çoklu boşlukları tek boşluğa indir
        text = re.sub(r"\s+", " ", text)

        # Token'lara ayır
        tokens = text.strip().split()

        return tokens

    def _brevity_penalty(self, gen_length: int, ref_length: int) -> float:
        """BLEU brevity penalty hesapla"""
        if gen_length >= ref_length:
            return 1.0
        return math.exp(1 - ref_length / gen_length)

    def _ngram_precision(
        self, gen_tokens: list[str], ref_tokens: list[str], n: int
    ) -> float:
        """N-gram precision hesapla"""
        gen_ngrams = self._get_ngrams(gen_tokens, n)
        ref_ngrams = self._get_ngrams(ref_tokens, n)

        if not gen_ngrams:
            return 0.0

        # Clipped count (referansta geçen maksimum sayı kadar say)
        clipped_count = 0
        for ngram in gen_ngrams:
            clipped_count += min(gen_ngrams[ngram], ref_ngrams.get(ngram, 0))

        total_count = sum(gen_ngrams.values())

        if total_count == 0:
            return 0.0

        return clipped_count / total_count

    def _get_ngrams(self, tokens: list[str], n: int) -> Counter:
        """N-gram'ları çıkar ve say"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i : i + n])
            ngrams.append(ngram)
        return Counter(ngrams)

    def _rouge_n(self, gen_tokens: list[str], ref_tokens: list[str], n: int) -> float:
        """ROUGE-N skoru hesapla (F1-score)"""
        gen_ngrams = self._get_ngrams(gen_tokens, n)
        ref_ngrams = self._get_ngrams(ref_tokens, n)

        if not ref_ngrams:
            return 0.0

        # Overlap count
        overlap = 0
        for ngram in gen_ngrams:
            overlap += min(gen_ngrams[ngram], ref_ngrams.get(ngram, 0))

        # Recall
        recall = overlap / sum(ref_ngrams.values()) if ref_ngrams else 0.0

        # Precision
        precision = overlap / sum(gen_ngrams.values()) if gen_ngrams else 0.0

        # F1-score
        if recall + precision == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def _rouge_l(self, gen_tokens: list[str], ref_tokens: list[str]) -> float:
        """ROUGE-L skoru hesapla (longest common subsequence)"""
        lcs_length = self._lcs_length(gen_tokens, ref_tokens)

        if not gen_tokens or not ref_tokens:
            return 0.0

        # Recall
        recall = lcs_length / len(ref_tokens)

        # Precision
        precision = lcs_length / len(gen_tokens)

        # F1-score
        if recall + precision == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def _lcs_length(self, seq1: list[str], seq2: list[str]) -> int:
        """Longest Common Subsequence uzunluğunu hesapla"""
        m, n = len(seq1), len(seq2)

        # DP tablosu
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def _calculate_semantic_similarity_simple(self, text1: str, text2: str) -> float:
        """
        Basit semantik benzerlik hesapla (embedding olmadan)

        Jaccard similarity + kelime örtüşmesi kullanır.
        Gerçek BERTScore için transformers kütüphanesi gerekir.
        """
        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))

        if not tokens1 or not tokens2:
            return 0.0

        # Jaccard similarity
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        if union == 0:
            return 0.0

        jaccard = intersection / union

        # Kelime örtüşme oranı
        overlap_ratio = intersection / min(len(tokens1), len(tokens2))

        # Ortalama
        similarity = (jaccard + overlap_ratio) / 2

        return min(1.0, max(0.0, similarity))

    def _calculate_bert_score_advanced(
        self, generated_text: str, reference_text: str
    ) -> float:
        """
        Gelişmiş BERTScore hesapla (transformers gerektirir)

        Not: Bu fonksiyon şu an basit implementasyon kullanıyor.
        Gerçek BERTScore için bert-score kütüphanesi yüklenmelidir.
        """
        try:
            # BERTScore kütüphanesi varsa kullan
            from bert_score import score

            P, R, F1 = score(
                [generated_text], [reference_text], lang="tr", verbose=False
            )

            return float(F1[0])

        except ImportError:
            # BERTScore yoksa basit yöntemi kullan
            return self._calculate_semantic_similarity_simple(
                generated_text, reference_text
            )

    def batch_calculate(
        self, generated_texts: list[str], reference_texts: list[str]
    ) -> list[NLPMetrics]:
        """
        Toplu metrik hesaplama

        Args:
            generated_texts: Üretilen metinler listesi
            reference_texts: Referans metinler listesi

        Returns:
            NLPMetrics listesi
        """
        if len(generated_texts) != len(reference_texts):
            raise ValueError("Üretilen ve referans metin sayıları eşit olmalı")

        results = []
        for gen, ref in zip(generated_texts, reference_texts):
            metrics = self.calculate_metrics(gen, ref)
            results.append(metrics)

        return results

    def get_average_metrics(self, metrics_list: list[NLPMetrics]) -> dict[str, float]:
        """
        Ortalama metrikleri hesapla

        Args:
            metrics_list: NLPMetrics listesi

        Returns:
            Ortalama metrikler
        """
        if not metrics_list:
            return {}

        avg_bleu = sum(m.bleu_score for m in metrics_list) / len(metrics_list)
        avg_rouge_1 = sum(m.rouge_1 for m in metrics_list) / len(metrics_list)
        avg_rouge_2 = sum(m.rouge_2 for m in metrics_list) / len(metrics_list)
        avg_rouge_l = sum(m.rouge_l for m in metrics_list) / len(metrics_list)
        avg_bert = sum(m.bert_score for m in metrics_list) / len(metrics_list)
        avg_combined = sum(m.combined_score for m in metrics_list) / len(metrics_list)

        return {
            "avg_bleu": round(avg_bleu, 4),
            "avg_rouge_1": round(avg_rouge_1, 4),
            "avg_rouge_2": round(avg_rouge_2, 4),
            "avg_rouge_l": round(avg_rouge_l, 4),
            "avg_bert_score": round(avg_bert, 4),
            "avg_combined": round(avg_combined, 4),
            "count": len(metrics_list),
        }
