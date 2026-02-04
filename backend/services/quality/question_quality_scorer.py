"""
Otomatik Soru Kalite Skorlama Sistemi

Bu modül ÖSYM formatında üretilen soruların kalitesini 0-100 arası skorlar.
Multi-criteria scoring ve weighted scoring kullanır.

Requirements: REQ-48.49 - REQ-48.52
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class QualityCriterion(Enum):
    """Kalite kriterleri"""

    OSYM_COMPLIANCE = "osym_compliance"  # ÖSYM formatına uygunluk
    GRAMMAR = "grammar"  # Dilbilgisi kalitesi
    CLARITY = "clarity"  # Açıklık ve anlaşılırlık
    DIFFICULTY = "difficulty"  # Zorluk seviyesi uygunluğu
    DISTRACTOR_QUALITY = "distractor_quality"  # Çeldirici kalitesi
    CONTENT_ACCURACY = "content_accuracy"  # İçerik doğruluğu
    EDUCATIONAL_VALUE = "educational_value"  # Eğitsel değer


@dataclass
class QualityScore:
    """Kalite skoru sonucu"""

    total_score: float  # 0-100 arası toplam skor
    criterion_scores: Dict[str, float]  # Her kriter için skor
    passed_threshold: bool  # Eşik değeri geçti mi?
    feedback: List[str]  # İyileştirme önerileri
    weighted_breakdown: Dict[str, float]  # Ağırlıklı skor dağılımı


class QuestionQualityScorer:
    """
    Otomatik soru kalite skorlama sistemi

    REQ-48.49: Multi-criteria scoring algorithm
    REQ-48.50: Weighted scoring system (ÖSYM uygunluğu %40)
    REQ-48.51: Quality threshold filtering (minimum 70 puan)
    REQ-48.52: 0-100 arası skor üretimi
    """

    # Kriter ağırlıkları (toplam 100%)
    DEFAULT_WEIGHTS = {
        QualityCriterion.OSYM_COMPLIANCE: 0.40,  # %40 - En önemli
        QualityCriterion.GRAMMAR: 0.15,  # %15
        QualityCriterion.CLARITY: 0.15,  # %15
        QualityCriterion.DIFFICULTY: 0.10,  # %10
        QualityCriterion.DISTRACTOR_QUALITY: 0.10,  # %10
        QualityCriterion.CONTENT_ACCURACY: 0.05,  # %5
        QualityCriterion.EDUCATIONAL_VALUE: 0.05,  # %5
    }

    # Kalite eşik değeri (REQ-48.51)
    QUALITY_THRESHOLD = 70.0

    def __init__(self, weights: Optional[Dict[QualityCriterion, float]] = None):
        """
        Args:
            weights: Özel kriter ağırlıkları (opsiyonel)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Ağırlıkların toplamının 1.0 olduğunu kontrol et"""
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):  # Floating point toleransı
            raise ValueError(f"Ağırlıklar toplamı 1.0 olmalı, şu an: {total}")

    def score_question(
        self,
        question_text: str,
        options: List[str],
        correct_answer: int,
        explanation: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
    ) -> QualityScore:
        """
        Soruyu çok kriterli algoritma ile skorla

        Args:
            question_text: Soru metni
            options: Şıklar listesi (A, B, C, D, E)
            correct_answer: Doğru cevap indeksi (0-4)
            explanation: Çözüm açıklaması
            subject: Ders/konu
            difficulty_level: Zorluk seviyesi

        Returns:
            QualityScore: Detaylı kalite skoru
        """
        # Input validation - Boş veya geçersiz inputlar için düşük skor
        validation_errors = []

        # Boş soru metni kontrolü
        if not question_text or len(question_text.strip()) == 0:
            validation_errors.append("Soru metni boş olamaz")

        # Boş veya yetersiz options kontrolü (ÖSYM standardı: 5 şık, minimum kabul: 4)
        if not options or len(options) == 0:
            validation_errors.append("Şıklar listesi boş olamaz")
        elif len(options) < 4:
            validation_errors.append("ÖSYM formatı için en az 4 şık gereklidir")

        # Geçersiz correct_answer kontrolü
        if options and (correct_answer < 0 or correct_answer >= len(options)):
            validation_errors.append("Doğru cevap indeksi geçersiz")

        # Ciddi validation hatası varsa düşük skor dön
        if validation_errors:
            criterion_scores = {
                QualityCriterion.OSYM_COMPLIANCE.value: 0.0,
                QualityCriterion.GRAMMAR.value: 0.0,
                QualityCriterion.CLARITY.value: 0.0,
                QualityCriterion.DIFFICULTY.value: 0.0,
                QualityCriterion.DISTRACTOR_QUALITY.value: 0.0,
                QualityCriterion.CONTENT_ACCURACY.value: 0.0,
                QualityCriterion.EDUCATIONAL_VALUE.value: 0.0,
            }
            weighted_breakdown = {k: 0.0 for k in criterion_scores.keys()}
            feedback = [f"❌ {err}" for err in validation_errors]
            feedback.insert(0, "⚠️ Soru kalite eşiğini geçemedi (minimum 70 puan)")

            return QualityScore(
                total_score=0.0,
                criterion_scores=criterion_scores,
                passed_threshold=False,
                feedback=feedback,
                weighted_breakdown=weighted_breakdown,
            )

        # Her kriter için skor hesapla
        criterion_scores = {
            QualityCriterion.OSYM_COMPLIANCE.value: self._score_osym_compliance(
                question_text, options, correct_answer
            ),
            QualityCriterion.GRAMMAR.value: self._score_grammar(question_text, options),
            QualityCriterion.CLARITY.value: self._score_clarity(question_text),
            QualityCriterion.DIFFICULTY.value: self._score_difficulty(
                question_text, difficulty_level
            ),
            QualityCriterion.DISTRACTOR_QUALITY.value: self._score_distractors(
                options, correct_answer
            ),
            QualityCriterion.CONTENT_ACCURACY.value: self._score_content_accuracy(
                question_text, explanation
            ),
            QualityCriterion.EDUCATIONAL_VALUE.value: self._score_educational_value(
                question_text, explanation
            ),
        }

        # Ağırlıklı toplam skor hesapla (REQ-48.50)
        weighted_breakdown = {}
        total_score = 0.0

        for criterion, weight in self.weights.items():
            score = criterion_scores[criterion.value]
            weighted_score = score * weight * 100  # 0-100 skalasına çevir
            weighted_breakdown[criterion.value] = weighted_score
            total_score += weighted_score

        # Eşik kontrolü (REQ-48.51)
        passed_threshold = total_score >= self.QUALITY_THRESHOLD

        # Geri bildirim oluştur
        feedback = self._generate_feedback(criterion_scores, passed_threshold)

        return QualityScore(
            total_score=round(total_score, 2),
            criterion_scores=criterion_scores,
            passed_threshold=passed_threshold,
            feedback=feedback,
            weighted_breakdown=weighted_breakdown,
        )

    def _score_osym_compliance(
        self, question_text: str, options: List[str], correct_answer: int
    ) -> float:
        """
        ÖSYM formatına uygunluk skorla (0-1 arası)

        Kontroller:
        - 5 şık var mı? (A, B, C, D, E)
        - Soru metni yeterli uzunlukta mı?
        - Şıklar dengeli uzunlukta mı?
        - Doğru cevap geçerli mi?
        """
        score = 1.0

        # 5 şık kontrolü
        if len(options) != 5:
            score -= 0.3

        # Soru uzunluğu kontrolü (minimum 20 karakter)
        if len(question_text.strip()) < 20:
            score -= 0.2

        # Şık uzunluk dengesi kontrolü
        if options:
            lengths = [len(opt) for opt in options]
            avg_length = sum(lengths) / len(lengths)
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            if variance > 1000:  # Çok dengesiz
                score -= 0.2

        # Doğru cevap geçerliliği
        if not (0 <= correct_answer < len(options)):
            score -= 0.3

        return max(0.0, score)

    def _score_grammar(self, question_text: str, options: List[str]) -> float:
        """
        Dilbilgisi kalitesi skorla (0-1 arası)

        Basit kontroller:
        - Noktalama işaretleri
        - Büyük/küçük harf kullanımı
        - Türkçe karakter kullanımı
        """
        score = 1.0

        # Soru işareti kontrolü
        if "?" not in question_text and not question_text.strip().endswith(":"):
            score -= 0.2

        # Büyük harfle başlama kontrolü
        if question_text and not question_text[0].isupper():
            score -= 0.1

        # Çift boşluk kontrolü
        if "  " in question_text:
            score -= 0.1

        # Şıklarda noktalama kontrolü
        for option in options:
            if option and not option[0].isupper():
                score -= 0.05

        return max(0.0, score)

    def _score_clarity(self, question_text: str) -> float:
        """
        Açıklık ve anlaşılırlık skorla (0-1 arası)

        Kontroller:
        - Cümle uzunluğu
        - Karmaşık kelime kullanımı
        - Belirsiz ifadeler
        """
        score = 1.0

        # Çok uzun cümle kontrolü (>200 karakter)
        if len(question_text) > 200:
            score -= 0.2

        # Çok kısa cümle kontrolü (<30 karakter)
        if len(question_text) < 30:
            score -= 0.2

        # Belirsiz ifadeler
        vague_terms = ["bazı", "birkaç", "genellikle", "çoğunlukla", "yaklaşık"]
        for term in vague_terms:
            if term in question_text.lower():
                score -= 0.1
                break

        return max(0.0, score)

    def _score_difficulty(
        self, question_text: str, difficulty_level: Optional[str]
    ) -> float:
        """
        Zorluk seviyesi uygunluğu skorla (0-1 arası)
        """
        score = 1.0

        # Zorluk seviyesi belirtilmişse kontrol et
        if difficulty_level:
            # Kelime sayısı ile zorluk korelasyonu
            word_count = len(question_text.split())

            if difficulty_level.lower() == "kolay" and word_count > 50:
                score -= 0.2
            elif difficulty_level.lower() == "zor" and word_count < 20:
                score -= 0.2

        return max(0.0, score)

    def _score_distractors(self, options: List[str], correct_answer: int) -> float:
        """
        Çeldirici kalitesi skorla (0-1 arası)

        İyi çeldiriciler:
        - Doğru cevapla benzer uzunlukta
        - Mantıklı ve makul
        - Birbirinden farklı
        """
        score = 1.0

        if not options or correct_answer >= len(options):
            return 0.0

        correct_option = options[correct_answer]
        distractors = [opt for i, opt in enumerate(options) if i != correct_answer]

        # Uzunluk benzerliği kontrolü
        correct_len = len(correct_option)
        for distractor in distractors:
            len_diff = abs(len(distractor) - correct_len)
            if len_diff > correct_len * 0.5:  # %50'den fazla fark
                score -= 0.1

        # Çeldiriciler birbirinden farklı mı?
        unique_distractors = set(distractors)
        if len(unique_distractors) < len(distractors):
            score -= 0.3  # Tekrar eden çeldirici

        # Çok kısa çeldiriciler
        for distractor in distractors:
            if len(distractor.strip()) < 2:
                score -= 0.2

        return max(0.0, score)

    def _score_content_accuracy(
        self, question_text: str, explanation: Optional[str]
    ) -> float:
        """
        İçerik doğruluğu skorla (0-1 arası)

        Basit kontroller (gelişmiş kontroller için domain knowledge gerekli)
        """
        score = 1.0

        # Açıklama var mı?
        if not explanation or len(explanation.strip()) < 10:
            score -= 0.3

        # Matematiksel tutarlılık (basit kontrol)
        if "=" in question_text:
            # Eşitlik işareti varsa, sayısal tutarlılık kontrolü yapılabilir
            pass

        return max(0.0, score)

    def _score_educational_value(
        self, question_text: str, explanation: Optional[str]
    ) -> float:
        """
        Eğitsel değer skorla (0-1 arası)
        """
        score = 1.0

        # Açıklama kalitesi
        if explanation and len(explanation) > 50:
            score += 0.0  # Bonus yok, zaten 1.0
        elif not explanation:
            score -= 0.4

        # Bloom taksonomisi anahtar kelimeleri
        bloom_keywords = [
            "analiz",
            "değerlendir",
            "karşılaştır",
            "açıkla",
            "hesapla",
            "çöz",
            "bul",
            "belirle",
        ]

        has_bloom_keyword = any(
            keyword in question_text.lower() for keyword in bloom_keywords
        )

        if not has_bloom_keyword:
            score -= 0.2

        return max(0.0, score)

    def _generate_feedback(
        self, criterion_scores: Dict[str, float], passed_threshold: bool
    ) -> List[str]:
        """
        İyileştirme önerileri oluştur
        """
        feedback = []

        if not passed_threshold:
            feedback.append("⚠️ Soru kalite eşiğini geçemedi (minimum 70 puan)")

        # Düşük skorlu kriterleri belirle
        for criterion, score in criterion_scores.items():
            if score < 0.7:  # %70'in altı
                feedback.append(self._get_criterion_feedback(criterion, score))

        if not feedback:
            feedback.append("✅ Soru tüm kalite kriterlerini karşılıyor")

        return feedback

    def _get_criterion_feedback(self, criterion: str, score: float) -> str:
        """Kriter bazlı geri bildirim"""
        feedback_map = {
            QualityCriterion.OSYM_COMPLIANCE.value: "ÖSYM formatına uygunluk düşük. 5 şık, dengeli uzunluklar ve geçerli doğru cevap kontrol edin.",
            QualityCriterion.GRAMMAR.value: "Dilbilgisi kalitesi düşük. Noktalama, büyük/küçük harf kullanımını kontrol edin.",
            QualityCriterion.CLARITY.value: "Açıklık düşük. Soru metnini daha net ve anlaşılır hale getirin.",
            QualityCriterion.DIFFICULTY.value: "Zorluk seviyesi uygun değil. Hedef zorluk seviyesine göre ayarlayın.",
            QualityCriterion.DISTRACTOR_QUALITY.value: "Çeldirici kalitesi düşük. Daha makul ve dengeli çeldiriciler ekleyin.",
            QualityCriterion.CONTENT_ACCURACY.value: "İçerik doğruluğu şüpheli. Açıklama ekleyin ve doğruluğu kontrol edin.",
            QualityCriterion.EDUCATIONAL_VALUE.value: "Eğitsel değer düşük. Bloom taksonomisi anahtar kelimeleri ve detaylı açıklama ekleyin.",
        }

        return (
            f"❌ {feedback_map.get(criterion, 'Bilinmeyen kriter')} (Skor: {score:.2f})"
        )

    def batch_score(self, questions: List[Dict]) -> List[QualityScore]:
        """
        Toplu soru skorlama

        Args:
            questions: Soru listesi (her biri dict formatında)

        Returns:
            QualityScore listesi
        """
        results = []

        for q in questions:
            score = self.score_question(
                question_text=q.get("question_text", ""),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", 0),
                explanation=q.get("explanation"),
                subject=q.get("subject"),
                difficulty_level=q.get("difficulty_level"),
            )
            results.append(score)

        return results

    def filter_by_threshold(
        self, questions: List[Dict], threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Kalite eşiğini geçen soruları filtrele (REQ-48.51)

        Args:
            questions: Soru listesi
            threshold: Özel eşik değeri (opsiyonel, varsayılan 70)

        Returns:
            Eşiği geçen sorular
        """
        threshold = threshold or self.QUALITY_THRESHOLD
        scores = self.batch_score(questions)

        filtered = []
        for q, score in zip(questions, scores):
            if score.total_score >= threshold:
                q["quality_score"] = score.total_score
                q["quality_feedback"] = score.feedback
                filtered.append(q)

        return filtered
