"""
Öğrenci Davranış Analitiği ve Learning Analytics Sistemi
Öğrenci etkileşimlerini analiz eder ve öğrenme kalıplarını tespit eder
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Etkileşim türleri"""

    QUESTION_ASKED = "question_asked"
    ANSWER_RECEIVED = "answer_received"
    CONTENT_VIEWED = "content_viewed"
    QUIZ_STARTED = "quiz_started"
    QUIZ_COMPLETED = "quiz_completed"
    STUDY_SESSION_STARTED = "study_session_started"
    STUDY_SESSION_ENDED = "study_session_ended"
    FEEDBACK_GIVEN = "feedback_given"
    HELP_REQUESTED = "help_requested"
    RESOURCE_ACCESSED = "resource_accessed"


class LearningOutcome(Enum):
    """Öğrenme sonuçları"""

    MASTERY_ACHIEVED = "mastery_achieved"
    IMPROVEMENT_SHOWN = "improvement_shown"
    STRUGGLING = "struggling"
    DISENGAGED = "disengaged"
    CONFUSED = "confused"
    MOTIVATED = "motivated"


class StudyPattern(Enum):
    """Çalışma kalıpları"""

    CONSISTENT = "consistent"
    CRAMMING = "cramming"
    SPORADIC = "sporadic"
    PROCRASTINATING = "procrastinating"
    INTENSIVE = "intensive"
    BALANCED = "balanced"


@dataclass
class LearningInteraction:
    """Öğrenme etkileşimi"""

    student_id: str
    interaction_type: InteractionType
    timestamp: datetime
    session_id: str
    content_id: str | None = None
    subject: str | None = None
    topic: str | None = None
    difficulty_level: int | None = None
    duration_seconds: int | None = None
    success_rate: float | None = None
    confidence_level: int | None = None
    emotional_state: str | None = None
    learning_style: str | None = None
    device_type: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Dict formatına çevir"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["interaction_type"] = self.interaction_type.value
        return data


@dataclass
class LearningSession:
    """Öğrenme oturumu"""

    session_id: str
    student_id: str
    start_time: datetime
    end_time: datetime | None = None
    total_duration_minutes: int | None = None
    interactions_count: int = 0
    subjects_covered: list[str] = field(default_factory=list)
    topics_covered: list[str] = field(default_factory=list)
    average_success_rate: float | None = None
    engagement_score: float | None = None
    learning_outcomes: list[LearningOutcome] = field(default_factory=list)
    notes: str | None = None


@dataclass
class StudentProfile:
    """Öğrenci profili analizi"""

    student_id: str
    total_study_time_hours: float
    total_sessions: int
    average_session_duration_minutes: float
    preferred_study_times: list[int]  # Saat bazında
    preferred_subjects: list[str]
    learning_style: str
    study_pattern: StudyPattern
    engagement_level: float  # 0-1 arası
    mastery_levels: dict[str, float]  # Konu bazında ustalık seviyeleri
    difficulty_preferences: dict[str, int]  # Konu bazında tercih edilen zorluk
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    last_updated: datetime


class LearningAnalyticsEngine:
    """Öğrenme analitiği motoru"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.interaction_buffer: list[LearningInteraction] = []
        self.active_sessions: dict[str, LearningSession] = {}
        self.student_profiles: dict[str, StudentProfile] = {}

        # Analiz parametreleri
        self.engagement_threshold = 0.7
        self.mastery_threshold = 0.8
        self.session_timeout_minutes = 30

    async def record_interaction(
        self,
        student_id: str,
        interaction_type: InteractionType,
        session_id: str,
        **kwargs,
    ) -> None:
        """Öğrenci etkileşimini kaydet"""
        interaction = LearningInteraction(
            student_id=student_id,
            interaction_type=interaction_type,
            timestamp=datetime.now(),
            session_id=session_id,
            **kwargs,
        )

        self.interaction_buffer.append(interaction)

        # Aktif oturum güncelle
        await self._update_active_session(interaction)

        # Buffer doluysa veritabanına kaydet
        if len(self.interaction_buffer) >= 100:
            await self._flush_interactions()

    async def _update_active_session(self, interaction: LearningInteraction):
        """Aktif oturumu güncelle"""
        session_id = interaction.session_id

        if session_id not in self.active_sessions:
            # Yeni oturum başlat
            self.active_sessions[session_id] = LearningSession(
                session_id=session_id,
                student_id=interaction.student_id,
                start_time=interaction.timestamp,
            )

        session = self.active_sessions[session_id]
        session.interactions_count += 1

        # Konu ve dersleri ekle
        if interaction.subject and interaction.subject not in session.subjects_covered:
            session.subjects_covered.append(interaction.subject)

        if interaction.topic and interaction.topic not in session.topics_covered:
            session.topics_covered.append(interaction.topic)

        # Oturum sonu kontrolü
        if interaction.interaction_type == InteractionType.STUDY_SESSION_ENDED:
            await self._end_session(session_id)

    async def _end_session(self, session_id: str):
        """Oturumu sonlandır"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        session.total_duration_minutes = int(
            (session.end_time - session.start_time).total_seconds() / 60
        )

        # Oturum analizini yap
        await self._analyze_session(session)

        # Oturumu veritabanına kaydet
        await self._save_session(session)

        # Aktif oturumlardan çıkar
        del self.active_sessions[session_id]

    async def _analyze_session(self, session: LearningSession):
        """Oturum analizini yap"""
        # Son etkileşimleri getir
        interactions = await self._get_session_interactions(session.session_id)

        if not interactions:
            return

        # Başarı oranını hesapla
        success_rates = [
            i.success_rate for i in interactions if i.success_rate is not None
        ]
        if success_rates:
            session.average_success_rate = statistics.mean(success_rates)

        # Engagement score hesapla
        session.engagement_score = await self._calculate_engagement_score(interactions)

        # Öğrenme sonuçlarını belirle
        session.learning_outcomes = await self._determine_learning_outcomes(
            session, interactions
        )

    async def _calculate_engagement_score(
        self, interactions: list[LearningInteraction]
    ) -> float:
        """Engagement score hesapla"""
        if not interactions:
            return 0.0

        score = 0.0
        total_weight = 0.0

        # Etkileşim türü ağırlıkları
        interaction_weights = {
            InteractionType.QUESTION_ASKED: 0.8,
            InteractionType.CONTENT_VIEWED: 0.4,
            InteractionType.QUIZ_COMPLETED: 1.0,
            InteractionType.FEEDBACK_GIVEN: 0.9,
            InteractionType.HELP_REQUESTED: 0.6,
            InteractionType.RESOURCE_ACCESSED: 0.5,
        }

        for interaction in interactions:
            weight = interaction_weights.get(interaction.interaction_type, 0.3)

            # Süre faktörü
            if interaction.duration_seconds:
                duration_factor = min(
                    1.0, interaction.duration_seconds / 300
                )  # 5 dakika max
                weight *= duration_factor

            # Güven seviyesi faktörü
            if interaction.confidence_level:
                confidence_factor = interaction.confidence_level / 5.0
                weight *= confidence_factor

            score += weight
            total_weight += 1.0

        return min(1.0, score / total_weight) if total_weight > 0 else 0.0

    async def _determine_learning_outcomes(
        self, session: LearningSession, interactions: list[LearningInteraction]
    ) -> list[LearningOutcome]:
        """Öğrenme sonuçlarını belirle"""
        outcomes = []

        # Başarı oranına göre
        if session.average_success_rate:
            if session.average_success_rate >= 0.9:
                outcomes.append(LearningOutcome.MASTERY_ACHIEVED)
            elif session.average_success_rate >= 0.7:
                outcomes.append(LearningOutcome.IMPROVEMENT_SHOWN)
            elif session.average_success_rate < 0.5:
                outcomes.append(LearningOutcome.STRUGGLING)

        # Engagement'a göre
        if session.engagement_score:
            if session.engagement_score >= 0.8:
                outcomes.append(LearningOutcome.MOTIVATED)
            elif session.engagement_score < 0.3:
                outcomes.append(LearningOutcome.DISENGAGED)

        # Yardım isteme sıklığına göre
        help_requests = [
            i
            for i in interactions
            if i.interaction_type == InteractionType.HELP_REQUESTED
        ]
        if len(help_requests) > len(interactions) * 0.3:
            outcomes.append(LearningOutcome.CONFUSED)

        return outcomes

    async def analyze_student_profile(self, student_id: str) -> StudentProfile:
        """Öğrenci profilini analiz et"""
        # Son 30 günlük verileri getir
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        interactions = await self._get_student_interactions(
            student_id, start_date, end_date
        )
        sessions = await self._get_student_sessions(student_id, start_date, end_date)

        if not interactions:
            return self._create_empty_profile(student_id)

        # Temel istatistikler
        total_study_time = sum(s.total_duration_minutes or 0 for s in sessions) / 60.0
        total_sessions = len(sessions)
        avg_session_duration = (
            statistics.mean(
                [s.total_duration_minutes for s in sessions if s.total_duration_minutes]
            )
            if sessions
            else 0
        )

        # Tercih edilen çalışma saatleri
        study_hours = [i.timestamp.hour for i in interactions]
        preferred_times = self._find_preferred_times(study_hours)

        # Tercih edilen dersler
        subjects = [i.subject for i in interactions if i.subject]
        preferred_subjects = self._find_most_common(subjects, 5)

        # Öğrenme stili analizi
        learning_style = await self._analyze_learning_style(interactions)

        # Çalışma kalıbı analizi
        study_pattern = await self._analyze_study_pattern(sessions)

        # Engagement seviyesi
        engagement_level = await self._calculate_overall_engagement(interactions)

        # Ustalık seviyeleri
        mastery_levels = await self._calculate_mastery_levels(student_id, interactions)

        # Zorluk tercihleri
        difficulty_preferences = await self._analyze_difficulty_preferences(
            interactions
        )

        # Güçlü ve zayıf yönler
        strengths, weaknesses = await self._identify_strengths_weaknesses(
            student_id, mastery_levels
        )

        # Öneriler
        recommendations = await self._generate_recommendations(
            student_id, mastery_levels, study_pattern, engagement_level
        )

        profile = StudentProfile(
            student_id=student_id,
            total_study_time_hours=total_study_time,
            total_sessions=total_sessions,
            average_session_duration_minutes=avg_session_duration,
            preferred_study_times=preferred_times,
            preferred_subjects=preferred_subjects,
            learning_style=learning_style,
            study_pattern=study_pattern,
            engagement_level=engagement_level,
            mastery_levels=mastery_levels,
            difficulty_preferences=difficulty_preferences,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            last_updated=datetime.now(),
        )

        # Cache'e kaydet
        self.student_profiles[student_id] = profile

        return profile

    def _find_preferred_times(self, hours: list[int]) -> list[int]:
        """Tercih edilen çalışma saatlerini bul"""
        if not hours:
            return []

        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1

        # En çok kullanılan 3 saati döndür
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    def _find_most_common(self, items: list[str], limit: int) -> list[str]:
        """En yaygın öğeleri bul"""
        if not items:
            return []

        counts = defaultdict(int)
        for item in items:
            counts[item] += 1

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [item for item, count in sorted_items[:limit]]

    async def _analyze_learning_style(
        self, interactions: list[LearningInteraction]
    ) -> str:
        """Öğrenme stilini analiz et"""
        style_indicators = defaultdict(int)

        for interaction in interactions:
            if interaction.learning_style:
                style_indicators[interaction.learning_style] += 1

            # Etkileşim türüne göre stil çıkarımı
            if interaction.interaction_type == InteractionType.CONTENT_VIEWED:
                if interaction.context.get("content_type") == "video":
                    style_indicators["visual"] += 1
                elif interaction.context.get("content_type") == "audio":
                    style_indicators["auditory"] += 1
                elif interaction.context.get("content_type") == "text":
                    style_indicators["reading"] += 1

        if not style_indicators:
            return "mixed"

        return max(style_indicators.items(), key=lambda x: x[1])[0]

    async def _analyze_study_pattern(
        self, sessions: list[LearningSession]
    ) -> StudyPattern:
        """Çalışma kalıbını analiz et"""
        if not sessions:
            return StudyPattern.SPORADIC

        # Oturum sürelerini analiz et
        durations = [
            s.total_duration_minutes for s in sessions if s.total_duration_minutes
        ]
        if not durations:
            return StudyPattern.SPORADIC

        avg_duration = statistics.mean(durations)
        duration_std = statistics.stdev(durations) if len(durations) > 1 else 0

        # Oturum sıklığını analiz et
        session_dates = [s.start_time.date() for s in sessions]
        unique_dates = set(session_dates)
        days_with_study = len(unique_dates)
        total_days = (
            (max(session_dates) - min(session_dates)).days + 1 if session_dates else 1
        )
        study_frequency = days_with_study / total_days

        # Kalıp belirleme
        if study_frequency > 0.8 and duration_std < avg_duration * 0.3:
            return StudyPattern.CONSISTENT
        if avg_duration > 120 and study_frequency < 0.3:
            return StudyPattern.CRAMMING
        if study_frequency < 0.4:
            return StudyPattern.SPORADIC
        if avg_duration > 180:
            return StudyPattern.INTENSIVE
        if study_frequency > 0.6 and avg_duration < 90:
            return StudyPattern.BALANCED
        return StudyPattern.PROCRASTINATING

    async def _calculate_overall_engagement(
        self, interactions: list[LearningInteraction]
    ) -> float:
        """Genel engagement seviyesini hesapla"""
        if not interactions:
            return 0.0

        engagement_scores = []

        # Her etkileşim için engagement hesapla
        for interaction in interactions:
            score = 0.5  # Base score

            # Etkileşim türü bonusu
            if interaction.interaction_type in [
                InteractionType.QUESTION_ASKED,
                InteractionType.QUIZ_COMPLETED,
                InteractionType.FEEDBACK_GIVEN,
            ]:
                score += 0.3

            # Süre bonusu
            if interaction.duration_seconds and interaction.duration_seconds > 60:
                score += min(0.2, interaction.duration_seconds / 600)

            # Güven seviyesi bonusu
            if interaction.confidence_level and interaction.confidence_level >= 4:
                score += 0.1

            engagement_scores.append(min(1.0, score))

        return statistics.mean(engagement_scores)

    async def _calculate_mastery_levels(
        self, student_id: str, interactions: list[LearningInteraction]
    ) -> dict[str, float]:
        """Konu bazında ustalık seviyelerini hesapla"""
        topic_performance = defaultdict(list)

        for interaction in interactions:
            if interaction.topic and interaction.success_rate is not None:
                topic_performance[interaction.topic].append(interaction.success_rate)

        mastery_levels = {}
        for topic, performances in topic_performance.items():
            if performances:
                # Son performansları daha ağırlıklı hesapla
                weighted_scores = []
                for i, score in enumerate(performances):
                    weight = (i + 1) / len(performances)  # Son skorlar daha ağırlıklı
                    weighted_scores.extend([score] * int(weight * 10))

                mastery_levels[topic] = statistics.mean(weighted_scores)

        return mastery_levels

    async def _analyze_difficulty_preferences(
        self, interactions: list[LearningInteraction]
    ) -> dict[str, int]:
        """Zorluk tercihlerini analiz et"""
        topic_difficulties = defaultdict(list)

        for interaction in interactions:
            if (
                interaction.topic
                and interaction.difficulty_level is not None
                and interaction.success_rate is not None
                and interaction.success_rate > 0.7
            ):  # Başarılı olan zorluklara odaklan
                topic_difficulties[interaction.topic].append(
                    interaction.difficulty_level
                )

        preferences = {}
        for topic, difficulties in topic_difficulties.items():
            if difficulties:
                # En çok başarılı olunan zorluk seviyesi
                difficulty_counts = defaultdict(int)
                for diff in difficulties:
                    difficulty_counts[diff] += 1

                preferences[topic] = max(difficulty_counts.items(), key=lambda x: x[1])[
                    0
                ]

        return preferences

    async def _identify_strengths_weaknesses(
        self, student_id: str, mastery_levels: dict[str, float]
    ) -> tuple[list[str], list[str]]:
        """Güçlü ve zayıf yönleri belirle"""
        if not mastery_levels:
            return [], []

        # Ustalık seviyelerine göre sırala
        sorted_topics = sorted(mastery_levels.items(), key=lambda x: x[1], reverse=True)

        # Güçlü yönler (üst %30)
        strong_count = max(1, len(sorted_topics) // 3)
        strengths = [
            topic for topic, level in sorted_topics[:strong_count] if level >= 0.7
        ]

        # Zayıf yönler (alt %30)
        weak_count = max(1, len(sorted_topics) // 3)
        weaknesses = [
            topic for topic, level in sorted_topics[-weak_count:] if level < 0.6
        ]

        return strengths, weaknesses

    async def _generate_recommendations(
        self,
        student_id: str,
        mastery_levels: dict[str, float],
        study_pattern: StudyPattern,
        engagement_level: float,
    ) -> list[str]:
        """Kişiselleştirilmiş öneriler oluştur"""
        recommendations = []

        # Ustalık seviyesi önerileri
        weak_topics = [topic for topic, level in mastery_levels.items() if level < 0.6]
        if weak_topics:
            recommendations.append(
                f"Bu konularda daha fazla çalışma yapmanız önerilir: {', '.join(weak_topics[:3])}"
            )

        # Çalışma kalıbı önerileri
        if study_pattern == StudyPattern.CRAMMING:
            recommendations.append(
                "Sınav öncesi yoğun çalışma yerine düzenli kısa çalışma seansları daha etkili olacaktır"
            )
        elif study_pattern == StudyPattern.SPORADIC:
            recommendations.append(
                "Daha düzenli çalışma programı oluşturmanız başarınızı artıracaktır"
            )
        elif study_pattern == StudyPattern.PROCRASTINATING:
            recommendations.append(
                "Çalışmayı erteleme eğiliminizi azaltmak için küçük hedefler belirleyin"
            )

        # Engagement önerileri
        if engagement_level < 0.5:
            recommendations.append(
                "Motivasyonunuzu artırmak için farklı öğrenme yöntemleri deneyebilirsiniz"
            )

        # Genel öneriler
        if len(mastery_levels) > 0:
            avg_mastery = statistics.mean(mastery_levels.values())
            if avg_mastery > 0.8:
                recommendations.append(
                    "Harika ilerleme gösteriyorsunuz! Daha zor konulara geçmeyi deneyebilirsiniz"
                )
            elif avg_mastery < 0.5:
                recommendations.append(
                    "Temel konuları pekiştirmeye odaklanmanız faydalı olacaktır"
                )

        return recommendations

    def _create_empty_profile(self, student_id: str) -> StudentProfile:
        """Boş profil oluştur"""
        return StudentProfile(
            student_id=student_id,
            total_study_time_hours=0.0,
            total_sessions=0,
            average_session_duration_minutes=0.0,
            preferred_study_times=[],
            preferred_subjects=[],
            learning_style="unknown",
            study_pattern=StudyPattern.SPORADIC,
            engagement_level=0.0,
            mastery_levels={},
            difficulty_preferences={},
            strengths=[],
            weaknesses=[],
            recommendations=[
                "Çalışmaya başlamak için bir konu seçin ve ilk oturumunuzu başlatın"
            ],
            last_updated=datetime.now(),
        )

    async def _flush_interactions(self):
        """Etkileşimleri veritabanına kaydet"""
        if not self.interaction_buffer:
            return

        try:
            # Batch insert için SQL hazırla
            interactions_data = [
                interaction.to_dict() for interaction in self.interaction_buffer
            ]

            # Veritabanına kaydet (örnek SQL)
            query = """
                INSERT INTO learning_interactions 
                (student_id, interaction_type, timestamp, session_id, content_id, 
                 subject, topic, difficulty_level, duration_seconds, success_rate,
                 confidence_level, emotional_state, learning_style, device_type, context)
                VALUES 
                (:student_id, :interaction_type, :timestamp, :session_id, :content_id,
                 :subject, :topic, :difficulty_level, :duration_seconds, :success_rate,
                 :confidence_level, :emotional_state, :learning_style, :device_type, :context)
            """

            await self.db_session.execute(text(query), interactions_data)
            await self.db_session.commit()

            logger.info(
                f"Flushed {len(self.interaction_buffer)} interactions to database"
            )
            self.interaction_buffer.clear()

        except Exception as e:
            logger.error(f"Error flushing interactions: {e}")
            await self.db_session.rollback()

    async def _save_session(self, session: LearningSession):
        """Oturumu veritabanına kaydet"""
        try:
            session_data = asdict(session)
            session_data["learning_outcomes"] = [
                outcome.value for outcome in session.learning_outcomes
            ]

            query = """
                INSERT INTO learning_sessions
                (session_id, student_id, start_time, end_time, total_duration_minutes,
                 interactions_count, subjects_covered, topics_covered, average_success_rate,
                 engagement_score, learning_outcomes, notes)
                VALUES
                (:session_id, :student_id, :start_time, :end_time, :total_duration_minutes,
                 :interactions_count, :subjects_covered, :topics_covered, :average_success_rate,
                 :engagement_score, :learning_outcomes, :notes)
            """

            await self.db_session.execute(text(query), session_data)
            await self.db_session.commit()

        except Exception as e:
            logger.error(f"Error saving session: {e}")
            await self.db_session.rollback()

    async def _get_session_interactions(
        self, session_id: str
    ) -> list[LearningInteraction]:
        """Oturum etkileşimlerini getir"""
        # Bu method veritabanından veri çekecek şekilde implement edilmeli
        return [i for i in self.interaction_buffer if i.session_id == session_id]

    async def _get_student_interactions(
        self, student_id: str, start_date: datetime, end_date: datetime
    ) -> list[LearningInteraction]:
        """Öğrenci etkileşimlerini getir"""
        # Bu method veritabanından veri çekecek şekilde implement edilmeli
        return [
            i
            for i in self.interaction_buffer
            if i.student_id == student_id and start_date <= i.timestamp <= end_date
        ]

    async def _get_student_sessions(
        self, student_id: str, start_date: datetime, end_date: datetime
    ) -> list[LearningSession]:
        """Öğrenci oturumlarını getir"""
        # Bu method veritabanından veri çekecek şekilde implement edilmeli
        return [
            s
            for s in self.active_sessions.values()
            if s.student_id == student_id and start_date <= s.start_time <= end_date
        ]

    async def get_class_analytics(self, class_id: str) -> dict[str, Any]:
        """Sınıf analitiği"""
        # Sınıftaki tüm öğrencilerin profillerini analiz et
        # Bu method implement edilecek

    async def get_system_analytics(self) -> dict[str, Any]:
        """Sistem geneli analitiği"""
        # Tüm sistem için genel istatistikler
        # Bu method implement edilecek


# Singleton instance
_learning_analytics_engine = None


def get_learning_analytics_engine(db_session: AsyncSession) -> LearningAnalyticsEngine:
    """Learning analytics engine singleton'ını getir"""
    global _learning_analytics_engine

    if _learning_analytics_engine is None:
        _learning_analytics_engine = LearningAnalyticsEngine(db_session)

    return _learning_analytics_engine
