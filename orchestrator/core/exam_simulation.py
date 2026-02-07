"""Exam Simulation Engine - YKS sınav simülasyonu.

Tam sınav deneyimi simüle eder:
- TYT/AYT formatlı sınav oluşturma
- Adaptif soru seçimi (CAT veya sabit)
- Süre yönetimi
- Gerçek zamanlı puanlama
- Sınav sonrası analitik
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExamType(Enum):
    """YKS sınav türleri."""

    TYT = "tyt"     # Temel Yeterlilik Testi
    AYT = "ayt"     # Alan Yeterlilik Testi
    YDT = "ydt"     # Yabancı Dil Testi
    CUSTOM = "custom"


class ExamMode(Enum):
    """Sınav modu."""

    FIXED = "fixed"         # Sabit sorular
    ADAPTIVE = "adaptive"   # CAT (Computerized Adaptive Testing)
    DIAGNOSTIC = "diagnostic"  # Tanısal test


class ExamStatus(Enum):
    """Sınav durumu."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"


@dataclass
class ExamQuestion:
    """Sınavdaki bir soru."""

    question_id: str
    subject: str
    topic: str
    difficulty: float = 0.0
    discrimination: float = 1.0
    guessing: float = 0.2
    time_limit_seconds: int = 120
    order: int = 0


@dataclass
class ExamAnswer:
    """Öğrencinin bir soruya cevabı."""

    question_id: str
    selected_answer: str = ""
    is_correct: bool = False
    time_spent_seconds: float = 0.0
    answered_at: str = ""
    skipped: bool = False

    def __post_init__(self) -> None:
        if not self.answered_at:
            self.answered_at = datetime.now(timezone.utc).isoformat()


# YKS sınav formatları
EXAM_FORMATS: dict[str, dict[str, Any]] = {
    "tyt": {
        "total_questions": 120,
        "total_time_minutes": 135,
        "sections": {
            "Türkçe": 40,
            "Sosyal Bilimler": 20,
            "Temel Matematik": 40,
            "Fen Bilimleri": 20,
        },
        "correct_points": 1.25,
        "wrong_penalty": -0.3125,  # 1/4 of correct
    },
    "ayt": {
        "total_questions": 160,
        "total_time_minutes": 180,
        "sections": {
            "Türk Dili ve Edebiyatı": 24,
            "Sosyal Bilimler-1": 16,
            "Matematik": 40,
            "Fen Bilimleri": 40,
            "Sosyal Bilimler-2": 40,
        },
        "correct_points": 1.5,
        "wrong_penalty": -0.375,
    },
}


@dataclass
class ExamConfig:
    """Sınav konfigürasyonu."""

    exam_type: ExamType = ExamType.TYT
    mode: ExamMode = ExamMode.FIXED
    time_limit_minutes: int = 0           # 0 = exam format default
    question_count: int = 0               # 0 = exam format default
    adaptive_start_theta: float = 0.0
    adaptive_se_threshold: float = 0.3    # CAT durma kriteri
    shuffle_questions: bool = False


@dataclass
class ExamSession:
    """Bir sınav oturumu."""

    session_id: str
    student_id: str
    config: ExamConfig = field(default_factory=ExamConfig)
    status: ExamStatus = ExamStatus.NOT_STARTED
    questions: list[ExamQuestion] = field(default_factory=list)
    answers: list[ExamAnswer] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    # Puanlama
    raw_score: float = 0.0
    net_score: float = 0.0
    correct_count: int = 0
    wrong_count: int = 0
    blank_count: int = 0
    estimated_theta: float = 0.0

    # Performans
    total_time_seconds: float = 0.0
    avg_time_per_question: float = 0.0
    section_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "exam_type": self.config.exam_type.value,
            "mode": self.config.mode.value,
            "status": self.status.value,
            "scores": {
                "raw": self.raw_score,
                "net": round(self.net_score, 2),
                "correct": self.correct_count,
                "wrong": self.wrong_count,
                "blank": self.blank_count,
                "theta": round(self.estimated_theta, 3),
            },
            "timing": {
                "total_seconds": round(self.total_time_seconds, 1),
                "avg_per_question": round(self.avg_time_per_question, 1),
            },
            "section_scores": {k: round(v, 2) for k, v in self.section_scores.items()},
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class ExamAnalytics:
    """Sınav sonrası analitik."""

    session_id: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    time_management: str = ""
    difficulty_distribution: dict[str, int] = field(default_factory=dict)
    topic_performance: dict[str, dict[str, float]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "time_management": self.time_management,
            "difficulty_distribution": self.difficulty_distribution,
            "topic_performance": self.topic_performance,
            "recommendations": self.recommendations,
        }


@dataclass
class ExamSimulationEngine:
    """YKS sınav simülasyon motoru.

    Tam sınav deneyimi orkestre eder:
    setup → soru seçimi → puanlama → analitik.

    Example:
        >>> engine = ExamSimulationEngine()
        >>> session = engine.create_session("S001", ExamConfig(exam_type=ExamType.TYT))
        >>> engine.submit_answer(session, ExamAnswer(...))
        >>> engine.finish(session)
        >>> analytics = engine.analyze(session)
    """

    D: float = 1.7  # IRT scaling constant

    def create_session(
        self,
        student_id: str,
        config: ExamConfig,
        question_pool: list[ExamQuestion] | None = None,
    ) -> ExamSession:
        """Yeni sınav oturumu oluştur.

        Args:
            student_id: Öğrenci ID'si.
            config: Sınav konfigürasyonu.
            question_pool: Soru havuzu (adaptive mod için).

        Returns:
            Hazır ExamSession.
        """
        import uuid
        session = ExamSession(
            session_id=str(uuid.uuid4())[:8],
            student_id=student_id,
            config=config,
        )

        # Format default'larını uygula
        fmt_key = config.exam_type.value
        if fmt_key in EXAM_FORMATS:
            fmt = EXAM_FORMATS[fmt_key]
            if config.time_limit_minutes == 0:
                config.time_limit_minutes = fmt["total_time_minutes"]
            if config.question_count == 0:
                config.question_count = fmt["total_questions"]

        # Sorular sağlandıysa ata
        if question_pool:
            if config.mode == ExamMode.ADAPTIVE:
                # CAT: başlangıç sorusu seç (orta zorlukta)
                session.questions = sorted(
                    question_pool, key=lambda q: abs(q.difficulty - config.adaptive_start_theta),
                )[:1]
            else:
                session.questions = question_pool[: config.question_count]

        session.status = ExamStatus.NOT_STARTED
        return session

    def start(self, session: ExamSession) -> None:
        """Sınavı başlat."""
        session.status = ExamStatus.IN_PROGRESS
        session.started_at = datetime.now(timezone.utc).isoformat()

    def submit_answer(self, session: ExamSession, answer: ExamAnswer) -> None:
        """Cevap gönder."""
        if session.status != ExamStatus.IN_PROGRESS:
            return
        session.answers.append(answer)

    def select_next_adaptive(
        self,
        session: ExamSession,
        question_pool: list[ExamQuestion],
    ) -> ExamQuestion | None:
        """CAT modu için sonraki soruyu seç (Fisher Information).

        Args:
            session: Mevcut oturum.
            question_pool: Kullanılabilir sorular.

        Returns:
            En bilgilendirici soru veya None (durma kriteri).
        """
        if session.config.mode != ExamMode.ADAPTIVE:
            return None

        # Mevcut theta tahmin et
        theta = self._estimate_theta_from_session(session)
        answered_ids = {a.question_id for a in session.answers}

        best_q = None
        max_info = 0.0

        for q in question_pool:
            if q.question_id in answered_ids:
                continue
            exp_val = math.exp(self.D * q.discrimination * (theta - q.difficulty))
            p = q.guessing + (1 - q.guessing) * (exp_val / (1 + exp_val))
            info = q.discrimination ** 2 * p * (1 - p)
            if info > max_info:
                max_info = info
                best_q = q

        return best_q

    def finish(self, session: ExamSession) -> None:
        """Sınavı bitir ve puanla."""
        session.completed_at = datetime.now(timezone.utc).isoformat()
        session.status = ExamStatus.COMPLETED
        self._calculate_scores(session)

    def _calculate_scores(self, session: ExamSession) -> None:
        """Net puan ve istatistikleri hesapla."""
        fmt_key = session.config.exam_type.value
        fmt = EXAM_FORMATS.get(fmt_key, {"correct_points": 1.0, "wrong_penalty": -0.25})

        correct = sum(1 for a in session.answers if a.is_correct and not a.skipped)
        wrong = sum(1 for a in session.answers if not a.is_correct and not a.skipped)
        blank = len(session.questions) - len(session.answers) + sum(1 for a in session.answers if a.skipped)

        session.correct_count = correct
        session.wrong_count = wrong
        session.blank_count = blank
        session.raw_score = float(correct)
        session.net_score = correct * fmt["correct_points"] + wrong * fmt["wrong_penalty"]

        # Süre istatistikleri
        total_time = sum(a.time_spent_seconds for a in session.answers)
        session.total_time_seconds = total_time
        answered = len([a for a in session.answers if not a.skipped])
        session.avg_time_per_question = total_time / max(answered, 1)

        # Theta tahmini
        session.estimated_theta = self._estimate_theta_from_session(session)

        # Section bazlı puanlama
        section_correct: dict[str, int] = {}
        section_total: dict[str, int] = {}
        for q in session.questions:
            section_total[q.subject] = section_total.get(q.subject, 0) + 1
        for a in session.answers:
            q_match = next((q for q in session.questions if q.question_id == a.question_id), None)
            if q_match and a.is_correct:
                section_correct[q_match.subject] = section_correct.get(q_match.subject, 0) + 1

        for subj, total in section_total.items():
            c = section_correct.get(subj, 0)
            session.section_scores[subj] = (c / total * 100) if total > 0 else 0.0

    def _estimate_theta_from_session(self, session: ExamSession) -> float:
        """Oturumdaki yanıtlardan theta tahmin et."""
        if not session.answers:
            return session.config.adaptive_start_theta

        theta = 0.0
        for _ in range(20):
            first_deriv = 0.0
            second_deriv = 0.0

            for ans in session.answers:
                if ans.skipped:
                    continue
                q = next((q for q in session.questions if q.question_id == ans.question_id), None)
                if not q:
                    continue

                exp_val = math.exp(self.D * q.discrimination * (theta - q.difficulty))
                p = q.guessing + (1 - q.guessing) * (exp_val / (1 + exp_val))
                p = max(min(p, 0.999), 0.001)

                u = 1.0 if ans.is_correct else 0.0
                first_deriv += q.discrimination * (u - p)
                second_deriv -= q.discrimination ** 2 * p * (1 - p)

            if abs(second_deriv) < 1e-10:
                break
            theta -= first_deriv / second_deriv

        return max(-3.0, min(3.0, theta))

    def analyze(self, session: ExamSession) -> ExamAnalytics:
        """Sınav sonrası detaylı analiz üret.

        Args:
            session: Tamamlanmış sınav oturumu.

        Returns:
            ExamAnalytics with strengths, weaknesses, recommendations.
        """
        analytics = ExamAnalytics(session_id=session.session_id)

        # Konu bazlı performans
        topic_stats: dict[str, dict[str, int]] = {}
        for ans in session.answers:
            q = next((q for q in session.questions if q.question_id == ans.question_id), None)
            if not q:
                continue
            key = f"{q.subject}:{q.topic}"
            if key not in topic_stats:
                topic_stats[key] = {"correct": 0, "total": 0}
            topic_stats[key]["total"] += 1
            if ans.is_correct:
                topic_stats[key]["correct"] += 1

        for key, stats in topic_stats.items():
            rate = stats["correct"] / max(stats["total"], 1)
            analytics.topic_performance[key] = {
                "success_rate": round(rate, 3),
                "correct": stats["correct"],
                "total": stats["total"],
            }
            if rate >= 0.8 and stats["total"] >= 3:
                analytics.strengths.append(key)
            elif rate < 0.5 and stats["total"] >= 3:
                analytics.weaknesses.append(key)

        # Süre yönetimi
        if session.avg_time_per_question > 0:
            fmt_key = session.config.exam_type.value
            fmt = EXAM_FORMATS.get(fmt_key)
            if fmt:
                ideal_time = (fmt["total_time_minutes"] * 60) / fmt["total_questions"]
                ratio = session.avg_time_per_question / ideal_time
                if ratio > 1.3:
                    analytics.time_management = "Çok yavaş - soru başına süreyi azaltmalısın"
                elif ratio < 0.5:
                    analytics.time_management = "Çok hızlı - soruları daha dikkatli okumalısın"
                else:
                    analytics.time_management = "İyi tempo"

        # Zorluk dağılımı
        for q in session.questions:
            if q.difficulty < -1:
                bucket = "kolay"
            elif q.difficulty < 1:
                bucket = "orta"
            else:
                bucket = "zor"
            analytics.difficulty_distribution[bucket] = analytics.difficulty_distribution.get(bucket, 0) + 1

        # Öneriler
        for weak in analytics.weaknesses[:3]:
            analytics.recommendations.append(f"{weak} konusunu tekrar çalış")
        if session.blank_count > len(session.questions) * 0.1:
            analytics.recommendations.append("Boş bırakma oranı yüksek - tahmin stratejisi geliştir")

        return analytics
