"""
Zorluk Seviyesi Sınıflandırma Servisi
Task 74: Difficulty Level Classification System

Bu servis 4 ana özellik sağlar:
- 74.1: 5 seviyeli zorluk sınıflandırması (Çok Kolay/Kolay/Orta/Zor/Çok Zor)
- 74.2: IRT b parametresi bazlı otomatik sınıflandırma
- 74.3: Öğrenci performansı bazlı crowd-sourced zorluk
- 74.4: Gerçek zamanlı dinamik güncelleme
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """5 seviyeli zorluk ölçeği"""

    VERY_EASY = 1  # Çok Kolay
    EASY = 2  # Kolay
    MEDIUM = 3  # Orta
    HARD = 4  # Zor
    VERY_HARD = 5  # Çok Zor


@dataclass
class DifficultyClassification:
    """Zorluk sınıflandırma sonucu"""

    question_id: str
    difficulty_level: DifficultyLevel
    difficulty_score: float  # 1.0-5.0 arası sürekli değer
    classification_method: str
    confidence: float  # 0-1 arası güven skoru
    irt_based_difficulty: float | None = None
    performance_based_difficulty: float | None = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DifficultyThresholds:
    """IRT b parametresi için zorluk eşikleri"""

    very_easy_max: float = -1.5
    easy_max: float = -0.5
    medium_max: float = 0.5
    hard_max: float = 1.5
    # very_hard: > 1.5


class DifficultyClassificationService:
    """
    Zorluk seviyesi sınıflandırma servisi

    Özellikler:
    - IRT parametresi bazlı otomatik sınıflandırma
    - Öğrenci performansı bazlı crowd-sourced zorluk
    - Gerçek zamanlı dinamik güncelleme
    - Görsel zorluk göstergeleri için veri sağlama
    """

    def __init__(self, db: Session):
        self.db = db
        self.thresholds = DifficultyThresholds()
        self.min_responses_for_performance = 30  # Minimum yanıt sayısı
        self.performance_weight = 0.6  # Performans ağırlığı
        self.irt_weight = 0.4  # IRT ağırlığı

    # ========================================================================
    # TASK 74.2: IRT b parametresi bazlı sınıflandırma
    # ========================================================================

    def classify_by_irt(self, irt_difficulty: float) -> DifficultyLevel:
        """
        IRT b parametresine göre zorluk seviyesi belirle

        Args:
            irt_difficulty: IRT b parametresi (-3.0 ile +3.0 arası)

        Returns:
            DifficultyLevel enum değeri
        """
        if irt_difficulty <= self.thresholds.very_easy_max:
            return DifficultyLevel.VERY_EASY
        if irt_difficulty <= self.thresholds.easy_max:
            return DifficultyLevel.EASY
        if irt_difficulty <= self.thresholds.medium_max:
            return DifficultyLevel.MEDIUM
        if irt_difficulty <= self.thresholds.hard_max:
            return DifficultyLevel.HARD
        return DifficultyLevel.VERY_HARD

    def irt_to_difficulty_score(self, irt_difficulty: float) -> float:
        """
        IRT b parametresini 1-5 arası zorluk skoruna dönüştür

        Args:
            irt_difficulty: IRT b parametresi (-3.0 ile +3.0 arası)

        Returns:
            1.0-5.0 arası zorluk skoru
        """
        # IRT b parametresi genellikle -3 ile +3 arasında
        # Bunu 1-5 aralığına normalize et
        normalized = (irt_difficulty + 3.0) / 6.0  # 0-1 aralığına
        score = 1.0 + (normalized * 4.0)  # 1-5 aralığına
        return max(1.0, min(5.0, score))

    def calibrate_thresholds(self, questions_data: list[dict]) -> DifficultyThresholds:
        """
        Soru havuzuna göre IRT eşiklerini kalibre et

        Args:
            questions_data: Soru listesi (her biri irt_difficulty içermeli)

        Returns:
            Kalibre edilmiş DifficultyThresholds
        """
        if not questions_data:
            return self.thresholds

        irt_values = [
            q["irt_difficulty"] for q in questions_data if "irt_difficulty" in q
        ]
        if not irt_values:
            return self.thresholds

        # Percentile bazlı eşik belirleme
        import numpy as np

        irt_array = np.array(irt_values)

        thresholds = DifficultyThresholds(
            very_easy_max=float(np.percentile(irt_array, 20)),
            easy_max=float(np.percentile(irt_array, 40)),
            medium_max=float(np.percentile(irt_array, 60)),
            hard_max=float(np.percentile(irt_array, 80)),
        )

        logger.info(f"Calibrated IRT thresholds: {thresholds}")
        return thresholds

    # ========================================================================
    # TASK 74.3: Öğrenci performansı bazlı zorluk
    # ========================================================================

    def calculate_performance_based_difficulty(
        self, question_id: str, time_window_days: int = 90
    ) -> float | None:
        """
        Öğrenci performansına göre crowd-sourced zorluk hesapla

        Args:
            question_id: Soru ID
            time_window_days: Kaç günlük veri kullanılacak

        Returns:
            1.0-5.0 arası zorluk skoru veya None (yeterli veri yoksa)
        """
        from models.exam import ExamResponse

        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        # Son X gün içindeki yanıtları al
        responses = (
            self.db.query(ExamResponse)
            .filter(
                and_(
                    ExamResponse.question_id == question_id,
                    ExamResponse.created_at >= cutoff_date,
                )
            )
            .all()
        )

        if len(responses) < self.min_responses_for_performance:
            logger.debug(
                f"Insufficient responses for question {question_id}: {len(responses)}"
            )
            return None

        # Başarı oranını hesapla
        correct_count = sum(1 for r in responses if r.is_correct)
        success_rate = correct_count / len(responses)

        # Ortalama yanıt süresini hesapla (saniye)
        avg_time = sum(r.time_spent for r in responses if r.time_spent) / len(responses)

        # Başarı oranını zorluk skoruna çevir (ters orantılı)
        # %100 başarı = 1.0 (çok kolay), %0 başarı = 5.0 (çok zor)
        base_difficulty = 1.0 + (1.0 - success_rate) * 4.0

        # Yanıt süresini de dikkate al (uzun süre = daha zor)
        # Ortalama 60 saniye referans alınır
        time_factor = min(avg_time / 60.0, 2.0)  # Maksimum 2x etki
        time_adjustment = (time_factor - 1.0) * 0.5  # -0.5 ile +0.5 arası

        difficulty = base_difficulty + time_adjustment
        return max(1.0, min(5.0, difficulty))

    def get_success_rate_analysis(
        self, question_id: str, time_window_days: int = 90
    ) -> dict:
        """
        Soru için detaylı başarı oranı analizi

        Returns:
            Analiz sonuçları (success_rate, avg_time, response_count, etc.)
        """
        from models.exam import ExamResponse

        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        responses = (
            self.db.query(ExamResponse)
            .filter(
                and_(
                    ExamResponse.question_id == question_id,
                    ExamResponse.created_at >= cutoff_date,
                )
            )
            .all()
        )

        if not responses:
            return {
                "success_rate": None,
                "avg_time": None,
                "response_count": 0,
                "difficulty_estimate": None,
            }

        correct_count = sum(1 for r in responses if r.is_correct)
        success_rate = correct_count / len(responses)
        avg_time = sum(r.time_spent for r in responses if r.time_spent) / len(responses)

        return {
            "success_rate": success_rate,
            "avg_time": avg_time,
            "response_count": len(responses),
            "correct_count": correct_count,
            "difficulty_estimate": self.calculate_performance_based_difficulty(
                question_id, time_window_days
            ),
        }

    # ========================================================================
    # TASK 74.1: 5 seviyeli sınıflandırma ve görsel göstergeler
    # ========================================================================

    def classify_question(
        self,
        question_id: str,
        irt_difficulty: float | None = None,
        force_recalculate: bool = False,
    ) -> DifficultyClassification:
        """
        Soruyu 5 seviyeli zorluk ölçeğinde sınıflandır

        Hem IRT hem de performans verilerini kullanarak hibrit sınıflandırma yapar.

        Args:
            question_id: Soru ID
            irt_difficulty: IRT b parametresi (yoksa veritabanından alınır)
            force_recalculate: Cache'i atla ve yeniden hesapla

        Returns:
            DifficultyClassification nesnesi
        """
        # IRT bazlı zorluk
        if irt_difficulty is None:
            # Veritabanından al
            from models.question_bank import QuestionBankItem

            question = (
                self.db.query(QuestionBankItem)
                .filter(QuestionBankItem.id == question_id)
                .first()
            )

            if question and question.irt_difficulty is not None:
                irt_difficulty = question.irt_difficulty
            else:
                irt_difficulty = 0.0  # Varsayılan orta zorluk

        irt_score = self.irt_to_difficulty_score(irt_difficulty)

        # Performans bazlı zorluk
        performance_score = self.calculate_performance_based_difficulty(question_id)

        # Hibrit skor hesapla
        if performance_score is not None:
            # Hem IRT hem performans verisi var
            final_score = (
                self.irt_weight * irt_score
                + self.performance_weight * performance_score
            )
            confidence = 0.9
            method = "hybrid"
        else:
            # Sadece IRT verisi var
            final_score = irt_score
            confidence = 0.6
            method = "irt_only"

        # Seviye belirle
        if final_score <= 1.8:
            level = DifficultyLevel.VERY_EASY
        elif final_score <= 2.6:
            level = DifficultyLevel.EASY
        elif final_score <= 3.4:
            level = DifficultyLevel.MEDIUM
        elif final_score <= 4.2:
            level = DifficultyLevel.HARD
        else:
            level = DifficultyLevel.VERY_HARD

        return DifficultyClassification(
            question_id=question_id,
            difficulty_level=level,
            difficulty_score=final_score,
            classification_method=method,
            confidence=confidence,
            irt_based_difficulty=irt_score,
            performance_based_difficulty=performance_score,
            metadata={
                "irt_difficulty": irt_difficulty,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_visual_difficulty_indicator(
        self, difficulty_level: DifficultyLevel
    ) -> dict:
        """
        Görsel zorluk göstergesi için veri sağla

        Returns:
            Frontend için görsel gösterge bilgileri
        """
        indicators = {
            DifficultyLevel.VERY_EASY: {
                "label_tr": "Çok Kolay",
                "label_en": "Very Easy",
                "color": "#4CAF50",  # Yeşil
                "icon": "⭐",
                "stars": 1,
                "emoji": "😊",
                "css_class": "difficulty-very-easy",
            },
            DifficultyLevel.EASY: {
                "label_tr": "Kolay",
                "label_en": "Easy",
                "color": "#8BC34A",  # Açık yeşil
                "icon": "⭐⭐",
                "stars": 2,
                "emoji": "🙂",
                "css_class": "difficulty-easy",
            },
            DifficultyLevel.MEDIUM: {
                "label_tr": "Orta",
                "label_en": "Medium",
                "color": "#FFC107",  # Sarı
                "icon": "⭐⭐⭐",
                "stars": 3,
                "emoji": "😐",
                "css_class": "difficulty-medium",
            },
            DifficultyLevel.HARD: {
                "label_tr": "Zor",
                "label_en": "Hard",
                "color": "#FF9800",  # Turuncu
                "icon": "⭐⭐⭐⭐",
                "stars": 4,
                "emoji": "😰",
                "css_class": "difficulty-hard",
            },
            DifficultyLevel.VERY_HARD: {
                "label_tr": "Çok Zor",
                "label_en": "Very Hard",
                "color": "#F44336",  # Kırmızı
                "icon": "⭐⭐⭐⭐⭐",
                "stars": 5,
                "emoji": "😱",
                "css_class": "difficulty-very-hard",
            },
        }

        return indicators.get(difficulty_level, indicators[DifficultyLevel.MEDIUM])

    # ========================================================================
    # TASK 74.4: Dinamik güncelleme
    # ========================================================================

    def update_difficulty_realtime(
        self, question_id: str, new_response_data: dict
    ) -> DifficultyClassification:
        """
        Yeni yanıt verisi geldiğinde zorluk seviyesini gerçek zamanlı güncelle

        Args:
            question_id: Soru ID
            new_response_data: Yeni yanıt verisi (is_correct, time_spent, etc.)

        Returns:
            Güncellenmiş DifficultyClassification
        """
        # Mevcut sınıflandırmayı al
        current = self.classify_question(question_id, force_recalculate=True)

        # Trend analizi yap
        trend = self.analyze_difficulty_trend(question_id)

        # Eğer belirgin bir trend varsa, zorluk skorunu ayarla
        if trend["trend_direction"] != "stable":
            adjustment = trend["adjustment_factor"]
            current.difficulty_score += adjustment
            current.difficulty_score = max(1.0, min(5.0, current.difficulty_score))

            # Seviyeyi yeniden belirle
            if current.difficulty_score <= 1.8:
                current.difficulty_level = DifficultyLevel.VERY_EASY
            elif current.difficulty_score <= 2.6:
                current.difficulty_level = DifficultyLevel.EASY
            elif current.difficulty_score <= 3.4:
                current.difficulty_level = DifficultyLevel.MEDIUM
            elif current.difficulty_score <= 4.2:
                current.difficulty_level = DifficultyLevel.HARD
            else:
                current.difficulty_level = DifficultyLevel.VERY_HARD

            current.metadata["trend"] = trend
            current.metadata["adjusted"] = True

        return current

    def analyze_difficulty_trend(
        self, question_id: str, recent_days: int = 30, historical_days: int = 90
    ) -> dict:
        """
        Zorluk seviyesi trendini analiz et

        Son 30 günü önceki 60 günle karşılaştırarak trend belirle.

        Returns:
            Trend analizi sonuçları
        """
        from models.exam import ExamResponse

        now = datetime.now()
        recent_cutoff = now - timedelta(days=recent_days)
        historical_cutoff = now - timedelta(days=historical_days)

        # Son 30 günlük veriler
        recent_responses = (
            self.db.query(ExamResponse)
            .filter(
                and_(
                    ExamResponse.question_id == question_id,
                    ExamResponse.created_at >= recent_cutoff,
                )
            )
            .all()
        )

        # Önceki 60 günlük veriler
        historical_responses = (
            self.db.query(ExamResponse)
            .filter(
                and_(
                    ExamResponse.question_id == question_id,
                    ExamResponse.created_at >= historical_cutoff,
                    ExamResponse.created_at < recent_cutoff,
                )
            )
            .all()
        )

        if len(recent_responses) < 10 or len(historical_responses) < 10:
            return {
                "trend_direction": "stable",
                "adjustment_factor": 0.0,
                "confidence": 0.0,
                "reason": "insufficient_data",
            }

        # Başarı oranlarını hesapla
        recent_success = sum(1 for r in recent_responses if r.is_correct) / len(
            recent_responses
        )
        historical_success = sum(1 for r in historical_responses if r.is_correct) / len(
            historical_responses
        )

        # Farkı hesapla
        success_diff = recent_success - historical_success

        # Trend belirle
        if success_diff > 0.15:  # %15'ten fazla artış
            trend = "easier"
            adjustment = -0.3  # Zorluğu azalt
        elif success_diff < -0.15:  # %15'ten fazla azalış
            trend = "harder"
            adjustment = +0.3  # Zorluğu artır
        else:
            trend = "stable"
            adjustment = 0.0

        return {
            "trend_direction": trend,
            "adjustment_factor": adjustment,
            "confidence": min(len(recent_responses) / 50, 1.0),
            "recent_success_rate": recent_success,
            "historical_success_rate": historical_success,
            "success_rate_change": success_diff,
        }

    def batch_update_difficulties(
        self, question_ids: list[str], update_threshold_days: int = 7
    ) -> dict[str, DifficultyClassification]:
        """
        Toplu zorluk güncellemesi yap

        Belirli bir süre güncellenmemiş soruların zorluklarını yeniden hesapla.

        Args:
            question_ids: Güncellenecek soru ID listesi
            update_threshold_days: Kaç günden eski güncellemeler yenilensin

        Returns:
            Soru ID -> DifficultyClassification mapping
        """
        results = {}

        for question_id in question_ids:
            try:
                classification = self.classify_question(
                    question_id, force_recalculate=True
                )
                results[question_id] = classification
            except Exception as e:
                logger.error(f"Failed to update difficulty for {question_id}: {e}", exc_info=True)
                continue

        logger.info(f"Batch updated {len(results)} question difficulties")
        return results

    # ========================================================================
    # Filtreleme ve Arama Desteği
    # ========================================================================

    def filter_questions_by_difficulty(
        self,
        difficulty_levels: list[DifficultyLevel],
        topic_id: str | None = None,
        limit: int = 50,
    ) -> list[str]:
        """
        Zorluk seviyesine göre soruları filtrele

        Args:
            difficulty_levels: İstenen zorluk seviyeleri listesi
            topic_id: Opsiyonel konu filtresi
            limit: Maksimum sonuç sayısı

        Returns:
            Soru ID listesi
        """
        from models.question_bank import QuestionBankItem

        # Zorluk seviyelerini IRT aralıklarına çevir
        irt_ranges = []
        for level in difficulty_levels:
            if level == DifficultyLevel.VERY_EASY:
                irt_ranges.append((-3.0, self.thresholds.very_easy_max))
            elif level == DifficultyLevel.EASY:
                irt_ranges.append(
                    (self.thresholds.very_easy_max, self.thresholds.easy_max)
                )
            elif level == DifficultyLevel.MEDIUM:
                irt_ranges.append(
                    (self.thresholds.easy_max, self.thresholds.medium_max)
                )
            elif level == DifficultyLevel.HARD:
                irt_ranges.append(
                    (self.thresholds.medium_max, self.thresholds.hard_max)
                )
            elif level == DifficultyLevel.VERY_HARD:
                irt_ranges.append((self.thresholds.hard_max, 3.0))

        # Query oluştur
        query = self.db.query(QuestionBankItem.id)

        # Zorluk filtresi
        difficulty_conditions = []
        for min_irt, max_irt in irt_ranges:
            difficulty_conditions.append(
                and_(
                    QuestionBankItem.irt_difficulty >= min_irt,
                    QuestionBankItem.irt_difficulty < max_irt,
                )
            )

        if difficulty_conditions:
            query = query.filter(or_(*difficulty_conditions))

        # Konu filtresi
        if topic_id:
            query = query.filter(QuestionBankItem.primary_topic_id == topic_id)

        # Aktif sorular
        query = query.filter(QuestionBankItem.is_active == True)

        # Limit
        query = query.limit(limit)

        results = query.all()
        return [r.id for r in results]

    def get_difficulty_distribution(
        self, topic_id: str | None = None
    ) -> dict[str, int]:
        """
        Zorluk seviyesi dağılımını al

        Returns:
            Seviye -> soru sayısı mapping
        """
        from models.question_bank import QuestionBankItem

        query = self.db.query(QuestionBankItem)

        if topic_id:
            query = query.filter(QuestionBankItem.primary_topic_id == topic_id)

        query = query.filter(QuestionBankItem.is_active == True)

        questions = query.all()

        distribution = {
            "very_easy": 0,
            "easy": 0,
            "medium": 0,
            "hard": 0,
            "very_hard": 0,
        }

        for q in questions:
            if q.irt_difficulty is None:
                continue

            level = self.classify_by_irt(q.irt_difficulty)

            if level == DifficultyLevel.VERY_EASY:
                distribution["very_easy"] += 1
            elif level == DifficultyLevel.EASY:
                distribution["easy"] += 1
            elif level == DifficultyLevel.MEDIUM:
                distribution["medium"] += 1
            elif level == DifficultyLevel.HARD:
                distribution["hard"] += 1
            elif level == DifficultyLevel.VERY_HARD:
                distribution["very_hard"] += 1

        return distribution


# ============================================================================
# Yardımcı Fonksiyonlar
# ============================================================================


def get_difficulty_label(
    difficulty_level: DifficultyLevel, language: str = "tr"
) -> str:
    """Zorluk seviyesi için etiket al"""
    labels = {
        "tr": {
            DifficultyLevel.VERY_EASY: "Çok Kolay",
            DifficultyLevel.EASY: "Kolay",
            DifficultyLevel.MEDIUM: "Orta",
            DifficultyLevel.HARD: "Zor",
            DifficultyLevel.VERY_HARD: "Çok Zor",
        },
        "en": {
            DifficultyLevel.VERY_EASY: "Very Easy",
            DifficultyLevel.EASY: "Easy",
            DifficultyLevel.MEDIUM: "Medium",
            DifficultyLevel.HARD: "Hard",
            DifficultyLevel.VERY_HARD: "Very Hard",
        },
    }

    return labels.get(language, labels["tr"]).get(difficulty_level, "Orta")


def difficulty_score_to_level(score: float) -> DifficultyLevel:
    """Zorluk skorunu seviyeye çevir"""
    if score <= 1.8:
        return DifficultyLevel.VERY_EASY
    if score <= 2.6:
        return DifficultyLevel.EASY
    if score <= 3.4:
        return DifficultyLevel.MEDIUM
    if score <= 4.2:
        return DifficultyLevel.HARD
    return DifficultyLevel.VERY_HARD
