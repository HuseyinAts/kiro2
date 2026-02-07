"""YKS Modül Entegrasyonu - Prediction ↔ Generation ↔ Tracking.

Bağımsız YKS modüllerini birbirine bağlar:
- ScorePrediction → theta dönüşümü → ZPD optimal zorluk
- Generation pipeline → DB kayıt → kalite takibi
- Soru yanıtlama → FSRS güncelleme → Tracking metrikleri
- Tracking → Prediction güncelleme döngüsü

Task 7: YKS modül entegrasyonu
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Score ↔ Theta Conversion
# ---------------------------------------------------------------------------

# YKS puan aralıkları (2024 sistemi)
YKS_SCORE_RANGES: dict[str, tuple[float, float]] = {
    "TYT": (100.0, 500.0),
    "AYT-SAY": (100.0, 500.0),
    "AYT-EA": (100.0, 500.0),
    "AYT-SOZ": (100.0, 500.0),
    "YDT": (100.0, 500.0),
}

# IRT theta aralığı
THETA_RANGE = (-4.0, 4.0)


def score_to_theta(
    predicted_score: float,
    exam_type: str = "TYT",
) -> float:
    """YKS tahmini puanı IRT theta parametresine dönüştür.

    Lineer mapping: puan aralığını [-4, 4] theta aralığına normalize eder.

    Args:
        predicted_score: Tahmini YKS puanı.
        exam_type: Sınav türü (TYT, AYT-SAY, AYT-EA, AYT-SOZ, YDT).

    Returns:
        IRT theta değeri [-4.0, 4.0].
    """
    score_min, score_max = YKS_SCORE_RANGES.get(exam_type, (100.0, 500.0))
    theta_min, theta_max = THETA_RANGE

    # Clamp score
    clamped = max(score_min, min(score_max, predicted_score))

    # Lineer normalizasyon
    normalized = (clamped - score_min) / (score_max - score_min)  # [0, 1]
    theta = theta_min + normalized * (theta_max - theta_min)  # [-4, 4]

    return round(theta, 3)


def theta_to_score(
    theta: float,
    exam_type: str = "TYT",
) -> float:
    """IRT theta değerini tahmini YKS puanına dönüştür.

    Args:
        theta: IRT theta değeri.
        exam_type: Sınav türü.

    Returns:
        Tahmini YKS puanı.
    """
    score_min, score_max = YKS_SCORE_RANGES.get(exam_type, (100.0, 500.0))
    theta_min, theta_max = THETA_RANGE

    clamped = max(theta_min, min(theta_max, theta))
    normalized = (clamped - theta_min) / (theta_max - theta_min)
    score = score_min + normalized * (score_max - score_min)

    return round(score, 1)


def theta_to_difficulty_level(theta: float) -> int:
    """Theta değerinden hedef zorluk seviyesi (1-5) hesapla.

    ZPD optimal: theta civarında, hafif üstünde zorluk hedefle.

    Args:
        theta: Öğrenci yetenek parametresi.

    Returns:
        Zorluk seviyesi 1-5.
    """
    # theta [-4,4] → difficulty [1,5] mapping (orta: theta=0 → diff=3)
    normalized = (theta + 4.0) / 8.0  # [0, 1]
    # Hafif üst challenge: +0.1 shift
    shifted = min(1.0, normalized + 0.1)
    level = int(round(shifted * 4 + 1))
    return max(1, min(5, level))


# ---------------------------------------------------------------------------
# ZPD-Guided Generation Request Builder
# ---------------------------------------------------------------------------


@dataclass
class StudentContext:
    """Öğrenci bağlam bilgisi - generation için."""

    student_id: str = ""
    theta: float = 0.0
    exam_type: str = "TYT"
    predicted_score: float = 300.0
    weak_subjects: list[str] = field(default_factory=list)
    strong_subjects: list[str] = field(default_factory=list)
    target_solo: str = ""
    study_streak_days: int = 0


def build_generation_request(
    context: StudentContext,
    subject: str,
    topic: str = "",
    count: int = 1,
) -> dict[str, Any]:
    """Öğrenci bağlamından generation request parametreleri oluştur.

    ZPD analizine göre optimal zorluk ve SOLO hedefi belirler.

    Args:
        context: Öğrenci bağlamı.
        subject: Hedef ders.
        topic: Hedef konu (opsiyonel).
        count: Üretilecek soru sayısı.

    Returns:
        GenerationRequest parametreleri (dict).
    """
    difficulty = theta_to_difficulty_level(context.theta)

    # Zayıf konularda zorluğu 1 düşür
    if subject in context.weak_subjects and difficulty > 1:
        difficulty -= 1

    # Güçlü konularda zorluğu 1 artır
    if subject in context.strong_subjects and difficulty < 5:
        difficulty += 1

    # SOLO hedef belirleme (theta'ya göre)
    if not context.target_solo:
        if context.theta < -1.5:
            target_solo = "uni"
        elif context.theta < 0.0:
            target_solo = "multi"
        elif context.theta < 1.5:
            target_solo = "relational"
        else:
            target_solo = "extended_abstract"
    else:
        target_solo = context.target_solo

    return {
        "exam_type": context.exam_type,
        "subject": subject,
        "topic": topic,
        "target_difficulty": difficulty,
        "target_solo": target_solo,
        "target_count": count,
    }


# ---------------------------------------------------------------------------
# Generation Result → DB Record Mapper
# ---------------------------------------------------------------------------


def map_generation_to_db(
    question_draft: dict[str, Any],
    generation_run_id: str,
    request_params: dict[str, Any],
) -> dict[str, Any]:
    """Pipeline çıktısını DB kaydına dönüştür.

    QuestionDraft dict → GeneratedQuestion tablo satırı.

    Args:
        question_draft: QuestionDraft.to_dict() çıktısı.
        generation_run_id: İlişkili GenerationRun ID.
        request_params: Orijinal üretim parametreleri.

    Returns:
        GeneratedQuestion model kwargs.
    """
    irt = question_draft.get("irt_params", {})

    return {
        "generation_run_id": generation_run_id,
        "question_text": question_draft.get("question_text", ""),
        "options": question_draft.get("options", {}),
        "correct_answer": question_draft.get("correct_answer", "A"),
        "explanation": question_draft.get("explanation", ""),
        "exam_type": request_params.get("exam_type", "TYT"),
        "subject": request_params.get("subject", ""),
        "topic": request_params.get("topic", ""),
        "solo_label": request_params.get("target_solo", ""),
        "marzano_label": request_params.get("target_marzano", ""),
        "bloom_level": question_draft.get("bloom_level"),
        "irt_difficulty": irt.get("difficulty"),
        "irt_discrimination": irt.get("discrimination"),
        "irt_guessing": irt.get("guessing"),
        "quality_score": question_draft.get("quality_score", 0.0) * 100,
        "judge_verdict": question_draft.get("status", ""),
        "copy_risk_score": question_draft.get("similarity_score", 0.0),
        "is_accepted": question_draft.get("status") == "approved",
    }


# ---------------------------------------------------------------------------
# Question Answer → FSRS Update
# ---------------------------------------------------------------------------


class AnswerQuality(Enum):
    """Öğrenci cevap kalitesi → FSRS rating mapping."""

    WRONG = 1       # AGAIN
    SLOW_CORRECT = 2  # HARD
    CORRECT = 3     # GOOD
    FAST_CORRECT = 4  # EASY


def classify_answer(
    is_correct: bool,
    response_time_seconds: float,
    expected_time_seconds: float = 90.0,
) -> AnswerQuality:
    """Öğrenci cevabını FSRS rating'e dönüştür.

    Args:
        is_correct: Doğru mu?
        response_time_seconds: Cevaplama süresi.
        expected_time_seconds: Beklenen süre.

    Returns:
        AnswerQuality (→ FSRS Rating).
    """
    if not is_correct:
        return AnswerQuality.WRONG

    ratio = response_time_seconds / max(expected_time_seconds, 1.0)
    if ratio < 0.5:
        return AnswerQuality.FAST_CORRECT
    elif ratio > 1.5:
        return AnswerQuality.SLOW_CORRECT
    else:
        return AnswerQuality.CORRECT


@dataclass
class AnswerEvent:
    """Soru yanıtlama olayı."""

    student_id: str
    question_id: str
    subject: str
    is_correct: bool
    response_time_seconds: float
    expected_time_seconds: float = 90.0
    difficulty_level: int = 3
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


def build_fsrs_update(
    event: AnswerEvent,
    current_stability: float = 0.0,
    current_difficulty: float = 5.0,
    elapsed_days: int = 0,
    reps: int = 0,
) -> dict[str, Any]:
    """Cevap olayından FSRS güncelleme parametreleri oluştur.

    Args:
        event: Yanıtlama olayı.
        current_stability: Mevcut kartın stability değeri.
        current_difficulty: Mevcut kartın difficulty değeri.
        elapsed_days: Son review'dan bu yana geçen gün.
        reps: Toplam tekrar sayısı.

    Returns:
        FSRSScheduler.review() için parametreler.
    """
    quality = classify_answer(
        event.is_correct,
        event.response_time_seconds,
        event.expected_time_seconds,
    )

    return {
        "card_id": event.question_id,
        "rating": quality.value,
        "stability": current_stability,
        "difficulty": current_difficulty,
        "elapsed_days": elapsed_days,
        "reps": reps,
    }


# ---------------------------------------------------------------------------
# Tracking Metrics Aggregator
# ---------------------------------------------------------------------------


@dataclass
class SessionMetrics:
    """Tek çalışma oturumu metrikleri."""

    student_id: str = ""
    session_date: str = ""
    questions_attempted: int = 0
    questions_correct: int = 0
    total_time_seconds: float = 0.0
    subjects_covered: list[str] = field(default_factory=list)
    avg_difficulty: float = 3.0
    avg_response_time: float = 0.0

    @property
    def accuracy(self) -> float:
        """Doğruluk oranı [0, 1]."""
        if self.questions_attempted == 0:
            return 0.0
        return self.questions_correct / self.questions_attempted

    @property
    def study_minutes(self) -> float:
        """Çalışma süresi (dakika)."""
        return self.total_time_seconds / 60.0


def aggregate_session(events: list[AnswerEvent]) -> SessionMetrics:
    """Cevap olaylarından oturum metrikleri oluştur.

    Args:
        events: Yanıtlama olayları listesi.

    Returns:
        SessionMetrics.
    """
    if not events:
        return SessionMetrics()

    correct = sum(1 for e in events if e.is_correct)
    total_time = sum(e.response_time_seconds for e in events)
    subjects = list({e.subject for e in events})
    avg_diff = sum(e.difficulty_level for e in events) / len(events)
    avg_resp = total_time / len(events)

    return SessionMetrics(
        student_id=events[0].student_id,
        session_date=events[0].timestamp[:10],
        questions_attempted=len(events),
        questions_correct=correct,
        total_time_seconds=total_time,
        subjects_covered=subjects,
        avg_difficulty=round(avg_diff, 1),
        avg_response_time=round(avg_resp, 1),
    )


def should_update_prediction(
    sessions: list[SessionMetrics],
    min_questions: int = 50,
    min_sessions: int = 5,
) -> bool:
    """Prediction yeniden hesaplanmalı mı?

    Args:
        sessions: Son oturumlar.
        min_questions: Minimum soru sayısı.
        min_sessions: Minimum oturum sayısı.

    Returns:
        True ise yeniden tahmin yapılmalı.
    """
    if len(sessions) < min_sessions:
        return False

    total_questions = sum(s.questions_attempted for s in sessions)
    return total_questions >= min_questions


def estimate_theta_from_sessions(
    sessions: list[SessionMetrics],
    current_theta: float = 0.0,
) -> float:
    """Oturum metriklerinden theta tahmini güncelle.

    Bayesian update: mevcut theta ile yeni performans verilerini birleştirir.

    Args:
        sessions: Son oturumlar.
        current_theta: Mevcut theta değeri.

    Returns:
        Güncellenmiş theta.
    """
    if not sessions:
        return current_theta

    # Ağırlıklı doğruluk (son oturumlar daha önemli)
    total_weight = 0.0
    weighted_accuracy = 0.0
    for i, session in enumerate(sessions):
        weight = 1.0 + i * 0.2  # Yeniler daha ağırlıklı
        weighted_accuracy += session.accuracy * weight
        total_weight += weight

    if total_weight == 0:
        return current_theta

    avg_accuracy = weighted_accuracy / total_weight  # [0, 1]

    # Accuracy → theta offset
    # 0.5 accuracy → 0 offset, 0.8 → +1.2, 0.2 → -1.2
    accuracy_theta = (avg_accuracy - 0.5) * 4.0  # [-2, 2]

    # Zorluk ağırlığı: yüksek zorluktaki başarı daha değerli
    avg_difficulty = sum(s.avg_difficulty for s in sessions) / len(sessions)
    difficulty_factor = (avg_difficulty - 3.0) / 2.0  # [-1, 1]

    new_theta_estimate = accuracy_theta + difficulty_factor * 0.5

    # Bayesian: mevcut theta ile ağırlıklı ortalama (%60 yeni, %40 eski)
    updated = 0.6 * new_theta_estimate + 0.4 * current_theta
    return round(max(-4.0, min(4.0, updated)), 3)


# ---------------------------------------------------------------------------
# Copy Risk Helper (delegates to CopyRiskDetector)
# ---------------------------------------------------------------------------


def check_copy_risk(
    new_text: str,
    reference_questions: dict[str, str] | None = None,
) -> "CopyRiskResult":
    """Yeni soru için copy risk kontrolü.

    CopyRiskDetector'a delege eder (fingerprint + n-gram Jaccard).

    Args:
        new_text: Yeni soru metni.
        reference_questions: {question_id: text} referans soru bankası.

    Returns:
        CopyRiskResult (risk_score, risk_level, exact_match, vb.).
    """
    from copy_risk_detector import CopyRiskDetector, CopyRiskResult

    detector = CopyRiskDetector()
    if reference_questions:
        for qid, text in reference_questions.items():
            detector.add_reference(qid, text)
    return detector.check(new_text)


# ---------------------------------------------------------------------------
# Integration Facade
# ---------------------------------------------------------------------------


class YKSIntegrationService:
    """YKS modülleri arası entegrasyon servisi.

    Kullanım:
        service = YKSIntegrationService()

        # 1. Öğrenci bağlamı oluştur
        ctx = service.create_student_context(predicted_score=350, exam_type="TYT")

        # 2. Soru üretim parametreleri al
        gen_params = service.prepare_generation(ctx, subject="Matematik", topic="Limit")

        # 3. Cevap olayını işle
        fsrs_params = service.process_answer(event)

        # 4. Oturum sonunda theta güncelle
        new_theta = service.update_theta(sessions, current_theta=ctx.theta)
    """

    def create_student_context(
        self,
        student_id: str = "",
        predicted_score: float = 300.0,
        exam_type: str = "TYT",
        weak_subjects: list[str] | None = None,
        strong_subjects: list[str] | None = None,
    ) -> StudentContext:
        """Prediction çıktısından öğrenci bağlamı oluştur."""
        theta = score_to_theta(predicted_score, exam_type)
        return StudentContext(
            student_id=student_id,
            theta=theta,
            exam_type=exam_type,
            predicted_score=predicted_score,
            weak_subjects=weak_subjects or [],
            strong_subjects=strong_subjects or [],
        )

    def prepare_generation(
        self,
        context: StudentContext,
        subject: str,
        topic: str = "",
        count: int = 1,
    ) -> dict[str, Any]:
        """Öğrenci bağlamından üretim parametreleri hazırla."""
        return build_generation_request(context, subject, topic, count)

    def map_result_to_db(
        self,
        question_draft: dict[str, Any],
        generation_run_id: str,
        request_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Pipeline sonucunu DB kaydına dönüştür."""
        return map_generation_to_db(question_draft, generation_run_id, request_params)

    def process_answer(
        self,
        event: AnswerEvent,
        current_stability: float = 0.0,
        current_difficulty: float = 5.0,
        elapsed_days: int = 0,
        reps: int = 0,
    ) -> dict[str, Any]:
        """Soru yanıtını FSRS parametrelerine dönüştür."""
        return build_fsrs_update(
            event, current_stability, current_difficulty, elapsed_days, reps,
        )

    def aggregate_session(self, events: list[AnswerEvent]) -> SessionMetrics:
        """Cevap olaylarından oturum metrikleri oluştur."""
        return aggregate_session(events)

    def update_theta(
        self,
        sessions: list[SessionMetrics],
        current_theta: float = 0.0,
    ) -> float:
        """Oturum verilerinden theta güncelle."""
        return estimate_theta_from_sessions(sessions, current_theta)

    def should_repredict(
        self,
        sessions: list[SessionMetrics],
        min_questions: int = 50,
    ) -> bool:
        """Yeniden tahmin gerekli mi?"""
        return should_update_prediction(sessions, min_questions)
