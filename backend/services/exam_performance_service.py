"""
Sınav Performans Analizi Servisi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu servis sınav performansı analizi, zayıflık tespiti ve çalışma önerileri sağlar:
- Detaylı performans görselleştirmesi
- Konu bazlı zayıflık analizi
- Çalışma önerileri üretimi
- Ulusal ortalamalarla karşılaştırma
"""

import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import selectinload

from core.database import get_async_session
from core.structured_logger import get_logger
from models.database import (
    ExamSession,
    ExamType,
    Question,
    QuestionDifficulty,
    StudentAnswer,
)

logger = get_logger("exam_performance_service")


class WeaknessLevel(Enum):
    """Zayıflık seviyesi"""

    CRITICAL = "critical"  # %0-40 başarı
    MODERATE = "moderate"  # %40-60 başarı
    MINOR = "minor"  # %60-75 başarı
    STRONG = "strong"  # %75+ başarı


class StudyPriority(Enum):
    """Çalışma önceliği"""

    URGENT = "urgent"  # Acil çalışılması gereken
    HIGH = "high"  # Yüksek öncelik
    MEDIUM = "medium"  # Orta öncelik
    LOW = "low"  # Düşük öncelik


@dataclass
class SubjectWeakness:
    """Konu zayıflığı analizi"""

    subject: str
    topic: str
    weakness_level: WeaknessLevel
    success_rate: float
    total_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    average_response_time: float
    difficulty_distribution: Dict[str, int]
    improvement_potential: float  # 0-1 arası gelişim potansiyeli


@dataclass
class StudyRecommendation:
    """Çalışma önerisi"""

    subject: str
    topic: str
    priority: StudyPriority
    recommended_study_hours: int
    recommended_resources: List[Dict[str, Any]]
    practice_question_count: int
    difficulty_focus: QuestionDifficulty
    explanation: str


@dataclass
class PerformanceComparison:
    """Performans karşılaştırması"""

    student_score: float
    class_average: Optional[float]
    school_average: Optional[float]
    national_average: float
    percentile: float
    ranking_info: Dict[str, Any]


@dataclass
class DetailedPerformanceAnalysis:
    """Detaylı performans analizi"""

    exam_session_id: str
    student_id: str
    exam_type: ExamType
    overall_performance: Dict[str, Any]
    subject_performances: List[Dict[str, Any]]
    weaknesses: List[SubjectWeakness]
    study_recommendations: List[StudyRecommendation]
    performance_comparison: PerformanceComparison
    time_analysis: Dict[str, Any]
    improvement_trends: Dict[str, Any]
    next_exam_prediction: Dict[str, Any]


class ExamPerformanceService:
    """Sınav performans analizi servisi"""

    def __init__(self):
        # Ulusal ortalama veriler (ÖSYM istatistiklerinden)
        self.national_averages = {
            ExamType.TYT: {
                "TURKCE": 65.2,
                "MATEMATIK": 58.7,
                "FEN": 62.1,
                "SOSYAL": 67.8,
                "overall": 63.5,
            },
            ExamType.AYT: {
                "MATEMATIK": 55.3,
                "FIZIK": 52.1,
                "KIMYA": 59.4,
                "BIYOLOJI": 61.2,
                "EDEBIYAT": 68.9,
                "TARIH": 64.7,
                "COGRAFYA": 66.1,
                "FELSEFE": 63.2,
                "overall": 61.4,
            },
            ExamType.YDT: {"INGILIZCE": 48.7, "overall": 48.7},
        }

        # Çalışma önerisi şablonları
        self.study_templates = {
            WeaknessLevel.CRITICAL: {
                "study_hours": 15,
                "practice_questions": 200,
                "difficulty_focus": QuestionDifficulty.EASY,
                "explanation": "Bu konuda temel kavramları güçlendirmeniz gerekiyor. Kolay sorularla başlayıp kademeli olarak zorluk artırın.",
            },
            WeaknessLevel.MODERATE: {
                "study_hours": 10,
                "practice_questions": 150,
                "difficulty_focus": QuestionDifficulty.MEDIUM,
                "explanation": "Orta seviye sorularla pratik yaparak konuyu pekiştirin.",
            },
            WeaknessLevel.MINOR: {
                "study_hours": 6,
                "practice_questions": 100,
                "difficulty_focus": QuestionDifficulty.MEDIUM,
                "explanation": "Zor sorularla kendinizi test edin ve hız kazanmaya odaklanın.",
            },
        }

    async def analyze_exam_performance(
        self, exam_session_id: str, include_comparisons: bool = True
    ) -> DetailedPerformanceAnalysis:
        """
        Sınav performansının detaylı analizini yap

        Args:
            exam_session_id: Sınav oturum ID'si
            include_comparisons: Karşılaştırma verilerini dahil et

        Returns:
            DetailedPerformanceAnalysis: Detaylı performans analizi
        """
        try:
            async with get_async_session() as db_session:
                # Sınav oturumu bilgilerini getir
                exam_result = await db_session.execute(
                    select(ExamSession)
                    .options(selectinload(ExamSession.student))
                    .where(ExamSession.id == exam_session_id)
                )
                exam_session = exam_result.scalar_one_or_none()

                if not exam_session:
                    raise ValueError("Sınav oturumu bulunamadı")

                if exam_session.status != "completed":
                    raise ValueError("Sınav henüz tamamlanmamış")

                # Genel performans analizi
                overall_performance = await self._analyze_overall_performance(
                    db_session, exam_session
                )

                # Konu bazlı performans analizi
                subject_performances = await self._analyze_subject_performances(
                    db_session, exam_session
                )

                # Zayıflık analizi
                weaknesses = await self._identify_weaknesses(
                    db_session, exam_session, subject_performances
                )

                # Çalışma önerileri
                study_recommendations = await self._generate_study_recommendations(
                    db_session, exam_session, weaknesses
                )

                # Performans karşılaştırması
                performance_comparison = None
                if include_comparisons:
                    performance_comparison = await self._compare_performance(
                        db_session, exam_session, overall_performance
                    )

                # Zaman analizi
                time_analysis = await self._analyze_time_usage(db_session, exam_session)

                # Gelişim trendi
                improvement_trends = await self._analyze_improvement_trends(
                    db_session, exam_session
                )

                # Sonraki sınav tahmini
                next_exam_prediction = await self._predict_next_exam_performance(
                    db_session, exam_session, improvement_trends
                )

                analysis = DetailedPerformanceAnalysis(
                    exam_session_id=exam_session_id,
                    student_id=exam_session.student_id,
                    exam_type=exam_session.exam_type,
                    overall_performance=overall_performance,
                    subject_performances=subject_performances,
                    weaknesses=weaknesses,
                    study_recommendations=study_recommendations,
                    performance_comparison=performance_comparison,
                    time_analysis=time_analysis,
                    improvement_trends=improvement_trends,
                    next_exam_prediction=next_exam_prediction,
                )

                logger.info(
                    f"Performans analizi tamamlandı",
                    extra_data={
                        "exam_session_id": exam_session_id,
                        "student_id": exam_session.student_id,
                        "overall_score": overall_performance["raw_score"],
                        "weakness_count": len(weaknesses),
                    },
                )

                return analysis

        except Exception as e:
            logger.error(
                f"Performans analizi hatası: {e}",
                extra_data={"exam_session_id": exam_session_id},
            )
            raise

    async def _analyze_overall_performance(
        self, db_session, exam_session: ExamSession
    ) -> Dict[str, Any]:
        """Genel performans analizi"""

        # Temel metrikler
        total_questions = exam_session.total_questions
        correct_answers = exam_session.total_correct
        wrong_answers = exam_session.total_wrong
        empty_answers = exam_session.total_empty

        # Net hesaplama (ÖSYM sistemi)
        net_score = correct_answers - (wrong_answers / 4)
        raw_score = (
            (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        )

        # Cevaplama oranı
        answered_questions = correct_answers + wrong_answers
        answer_rate = (
            (answered_questions / total_questions) * 100 if total_questions > 0 else 0
        )

        # Doğruluk oranı (cevaplanan sorular içinde)
        accuracy_rate = (
            (correct_answers / answered_questions) * 100
            if answered_questions > 0
            else 0
        )

        # Ortalama cevaplama süresi
        time_result = await db_session.execute(
            select(func.avg(StudentAnswer.response_time_seconds)).where(
                StudentAnswer.exam_session_id == exam_session.id
            )
        )
        avg_response_time = time_result.scalar() or 0.0

        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "empty_answers": empty_answers,
            "net_score": round(net_score, 2),
            "raw_score": round(raw_score, 2),
            "answer_rate": round(answer_rate, 2),
            "accuracy_rate": round(accuracy_rate, 2),
            "average_response_time": round(avg_response_time, 2),
            "estimated_ability": exam_session.estimated_ability,
            "confidence_level": exam_session.ability_confidence,
        }

    async def _analyze_subject_performances(
        self, db_session, exam_session: ExamSession
    ) -> List[Dict[str, Any]]:
        """Konu bazlı performans analizi"""

        # Konu bazlı istatistikleri getir
        subject_stats_result = await db_session.execute(
            select(
                Question.subject_area,
                Question.topic,
                func.count(Question.id).label("total_questions"),
                func.sum(
                    func.case(
                        (StudentAnswer.selected_answer == Question.correct_answer, 1),
                        else_=0,
                    )
                ).label("correct_answers"),
                func.sum(
                    func.case(
                        (
                            and_(
                                StudentAnswer.selected_answer
                                != Question.correct_answer,
                                StudentAnswer.selected_answer.isnot(None),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("wrong_answers"),
                func.sum(
                    func.case((StudentAnswer.selected_answer.is_(None), 1), else_=0)
                ).label("empty_answers"),
                func.avg(StudentAnswer.response_time_seconds).label(
                    "avg_response_time"
                ),
                func.avg(Question.irt_difficulty).label("avg_difficulty"),
            )
            .select_from(Question)
            .join(StudentAnswer, Question.id == StudentAnswer.question_id)
            .where(StudentAnswer.exam_session_id == exam_session.id)
            .group_by(Question.subject_area, Question.topic)
        )

        # FIX N+1: Fetch all difficulty distributions in one query
        all_difficulties_result = await db_session.execute(
            select(
                Question.subject_area,
                Question.topic,
                Question.difficulty,
                func.count(Question.id).label("count"),
            )
            .select_from(Question)
            .join(StudentAnswer, Question.id == StudentAnswer.question_id)
            .where(StudentAnswer.exam_session_id == exam_session.id)
            .group_by(Question.subject_area, Question.topic, Question.difficulty)
        )

        # Create lookup dictionary: (subject_area, topic) -> {difficulty: count}
        difficulty_lookup = {}
        for diff_row in all_difficulties_result:
            key = (diff_row.subject_area, diff_row.topic)
            if key not in difficulty_lookup:
                difficulty_lookup[key] = {}
            difficulty_lookup[key][diff_row.difficulty.value] = diff_row.count

        subject_performances = []

        for row in subject_stats_result:
            total = row.total_questions
            correct = row.correct_answers or 0
            wrong = row.wrong_answers or 0
            empty = row.empty_answers or 0

            success_rate = (correct / total) * 100 if total > 0 else 0
            net_score = correct - (wrong / 4)

            # FIX N+1: Use pre-fetched difficulty distribution
            key = (row.subject_area, row.topic)
            difficulty_distribution = difficulty_lookup.get(key, {})

            subject_performances.append(
                {
                    "subject": row.subject_area.value,
                    "topic": row.topic,
                    "total_questions": total,
                    "correct_answers": correct,
                    "wrong_answers": wrong,
                    "empty_answers": empty,
                    "success_rate": round(success_rate, 2),
                    "net_score": round(net_score, 2),
                    "average_response_time": round(row.avg_response_time or 0, 2),
                    "average_difficulty": round(row.avg_difficulty or 0, 2),
                    "difficulty_distribution": difficulty_distribution,
                }
            )

        return subject_performances

    async def _identify_weaknesses(
        self,
        db_session,
        exam_session: ExamSession,
        subject_performances: List[Dict[str, Any]],
    ) -> List[SubjectWeakness]:
        """Zayıflık tespiti"""

        weaknesses = []

        for performance in subject_performances:
            success_rate = performance["success_rate"]

            # Zayıflık seviyesi belirleme
            if success_rate < 40:
                weakness_level = WeaknessLevel.CRITICAL
            elif success_rate < 60:
                weakness_level = WeaknessLevel.MODERATE
            elif success_rate < 75:
                weakness_level = WeaknessLevel.MINOR
            else:
                continue  # Güçlü alan, zayıflık listesine ekleme

            # Gelişim potansiyeli hesaplama
            improvement_potential = self._calculate_improvement_potential(
                performance, exam_session.exam_type
            )

            weakness = SubjectWeakness(
                subject=performance["subject"],
                topic=performance["topic"],
                weakness_level=weakness_level,
                success_rate=success_rate,
                total_questions=performance["total_questions"],
                correct_answers=performance["correct_answers"],
                wrong_answers=performance["wrong_answers"],
                empty_answers=performance["empty_answers"],
                average_response_time=performance["average_response_time"],
                difficulty_distribution=performance["difficulty_distribution"],
                improvement_potential=improvement_potential,
            )

            weaknesses.append(weakness)

        # Gelişim potansiyeline göre sırala (en yüksek potansiyel önce)
        weaknesses.sort(key=lambda x: x.improvement_potential, reverse=True)

        return weaknesses

    def _calculate_improvement_potential(
        self, performance: Dict[str, Any], exam_type: ExamType
    ) -> float:
        """Gelişim potansiyeli hesaplama"""

        success_rate = performance["success_rate"]
        total_questions = performance["total_questions"]
        empty_answers = performance["empty_answers"]
        avg_difficulty = performance["average_difficulty"]

        # Temel potansiyel (100 - mevcut başarı oranı)
        base_potential = (100 - success_rate) / 100

        # Soru sayısı faktörü (daha fazla soru = daha güvenilir analiz)
        question_factor = min(1.0, total_questions / 20)

        # Boş cevap faktörü (boş cevaplar gelişim fırsatı)
        empty_factor = (
            (empty_answers / total_questions) * 0.3 if total_questions > 0 else 0
        )

        # Zorluk faktörü (orta zorluk sorularda daha yüksek potansiyel)
        difficulty_factor = 1.0 - abs(avg_difficulty - 0.5)  # 0.5 orta zorluk

        # Ulusal ortalama faktörü
        national_avg = self.national_averages.get(exam_type, {}).get(
            performance["subject"], 60.0
        )
        national_factor = max(0, (national_avg - success_rate) / 100)

        # Toplam potansiyel hesaplama
        potential = (
            base_potential * 0.4
            + question_factor * 0.2
            + empty_factor * 0.1
            + difficulty_factor * 0.15
            + national_factor * 0.15
        )

        return min(1.0, max(0.0, potential))

    async def _generate_study_recommendations(
        self, db_session, exam_session: ExamSession, weaknesses: List[SubjectWeakness]
    ) -> List[StudyRecommendation]:
        """Çalışma önerileri üretimi"""

        recommendations = []

        for weakness in weaknesses:
            # Öncelik belirleme
            if weakness.weakness_level == WeaknessLevel.CRITICAL:
                priority = StudyPriority.URGENT
            elif weakness.weakness_level == WeaknessLevel.MODERATE:
                priority = StudyPriority.HIGH
            else:
                priority = StudyPriority.MEDIUM

            # Şablon bilgilerini al
            template = self.study_templates[weakness.weakness_level]

            # Çalışma saati ayarlama (gelişim potansiyeline göre)
            base_hours = template["study_hours"]
            adjusted_hours = int(base_hours * weakness.improvement_potential)

            # Soru sayısı ayarlama
            base_questions = template["practice_questions"]
            adjusted_questions = int(base_questions * weakness.improvement_potential)

            # Kaynak önerileri (basit implementasyon)
            recommended_resources = await self._get_recommended_resources(
                db_session, weakness.subject, weakness.topic
            )

            recommendation = StudyRecommendation(
                subject=weakness.subject,
                topic=weakness.topic,
                priority=priority,
                recommended_study_hours=max(3, adjusted_hours),
                recommended_resources=recommended_resources,
                practice_question_count=max(50, adjusted_questions),
                difficulty_focus=template["difficulty_focus"],
                explanation=template["explanation"],
            )

            recommendations.append(recommendation)

        return recommendations

    async def _get_recommended_resources(
        self, db_session, subject: str, topic: str
    ) -> List[Dict[str, Any]]:
        """Önerilen kaynakları getir"""

        # Basit implementasyon - gerçek uygulamada içerik veritabanından çekilecek
        resources = [
            {
                "type": "video",
                "title": f"{topic} - Konu Anlatımı",
                "source": "EBA TV",
                "duration_minutes": 25,
                "difficulty": "easy",
                "url": f"https://eba.gov.tr/video/{subject}/{topic}",
            },
            {
                "type": "practice",
                "title": f"{topic} - Soru Bankası",
                "source": "Platform",
                "question_count": 100,
                "difficulty": "mixed",
                "url": f"/practice/{subject}/{topic}",
            },
            {
                "type": "article",
                "title": f"{topic} - Detaylı Açıklama",
                "source": "Khan Academy TR",
                "reading_time": 15,
                "difficulty": "medium",
                "url": f"https://tr.khanacademy.org/{subject}/{topic}",
            },
        ]

        return resources

    async def _compare_performance(
        self, db_session, exam_session: ExamSession, overall_performance: Dict[str, Any]
    ) -> PerformanceComparison:
        """Performans karşılaştırması"""

        student_score = overall_performance["raw_score"]

        # Ulusal ortalama
        national_average = self.national_averages.get(exam_session.exam_type, {}).get(
            "overall", 60.0
        )

        # Sınıf ortalaması (basit implementasyon)
        class_average = None
        school_average = None

        # Yüzdelik dilim hesaplama (basit implementasyon)
        if student_score >= national_average:
            percentile = (
                50
                + ((student_score - national_average) / (100 - national_average)) * 50
            )
        else:
            percentile = (student_score / national_average) * 50

        percentile = max(1, min(99, percentile))

        # Sıralama bilgileri
        ranking_info = {
            "estimated_rank": int(
                (100 - percentile) * 1000
            ),  # 100,000 öğrenci varsayımı
            "total_participants": 100000,
            "better_than_percent": round(percentile, 1),
        }

        return PerformanceComparison(
            student_score=student_score,
            class_average=class_average,
            school_average=school_average,
            national_average=national_average,
            percentile=round(percentile, 2),
            ranking_info=ranking_info,
        )

    async def _analyze_time_usage(
        self, db_session, exam_session: ExamSession
    ) -> Dict[str, Any]:
        """Zaman kullanım analizi"""

        # Toplam süre
        total_duration = exam_session.time_spent_seconds
        exam_duration_minutes = exam_session.duration_minutes

        # Ortalama soru başına süre
        avg_time_per_question = (
            total_duration / exam_session.total_questions
            if exam_session.total_questions > 0
            else 0
        )

        # Konu bazlı zaman analizi
        time_by_subject_result = await db_session.execute(
            select(
                Question.subject_area,
                func.avg(StudentAnswer.response_time_seconds).label("avg_time"),
                func.count(StudentAnswer.id).label("question_count"),
            )
            .select_from(Question)
            .join(StudentAnswer, Question.id == StudentAnswer.question_id)
            .where(StudentAnswer.exam_session_id == exam_session.id)
            .group_by(Question.subject_area)
        )

        time_by_subject = {}
        for row in time_by_subject_result:
            time_by_subject[row.subject_area.value] = {
                "average_time": round(row.avg_time or 0, 2),
                "question_count": row.question_count,
            }

        # Hız analizi
        speed_analysis = {
            "too_fast": 0,  # < 30 saniye
            "optimal": 0,  # 30-120 saniye
            "too_slow": 0,  # > 120 saniye
        }

        speed_result = await db_session.execute(
            select(StudentAnswer.response_time_seconds).where(
                StudentAnswer.exam_session_id == exam_session.id
            )
        )

        for row in speed_result:
            time_seconds = row.response_time_seconds or 0
            if time_seconds < 30:
                speed_analysis["too_fast"] += 1
            elif time_seconds <= 120:
                speed_analysis["optimal"] += 1
            else:
                speed_analysis["too_slow"] += 1

        return {
            "total_duration_seconds": total_duration,
            "total_duration_minutes": round(total_duration / 60, 2),
            "exam_duration_minutes": exam_duration_minutes,
            "time_utilization_percent": round(
                (total_duration / (exam_duration_minutes * 60)) * 100, 2
            ),
            "average_time_per_question": round(avg_time_per_question, 2),
            "time_by_subject": time_by_subject,
            "speed_analysis": speed_analysis,
        }

    async def _analyze_improvement_trends(
        self, db_session, exam_session: ExamSession
    ) -> Dict[str, Any]:
        """Gelişim trendi analizi"""

        # Son 5 sınavdaki performansı getir
        recent_exams_result = await db_session.execute(
            select(ExamSession)
            .where(
                and_(
                    ExamSession.student_id == exam_session.student_id,
                    ExamSession.exam_type == exam_session.exam_type,
                    ExamSession.status == "completed",
                )
            )
            .order_by(desc(ExamSession.completed_at))
            .limit(5)
        )

        recent_exams = recent_exams_result.scalars().all()

        if len(recent_exams) < 2:
            return {
                "trend": "insufficient_data",
                "improvement_rate": 0.0,
                "consistency": 0.0,
                "recent_scores": [],
            }

        # Skorları çıkar
        scores = [exam.raw_score for exam in recent_exams]
        scores.reverse()  # Kronolojik sıra

        # Trend hesaplama (basit linear regression)
        n = len(scores)
        x_values = list(range(n))

        # Ortalamalar
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)

        # Eğim hesaplama
        numerator = sum((x_values[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # Trend belirleme
        if slope > 2:
            trend = "improving"
        elif slope < -2:
            trend = "declining"
        else:
            trend = "stable"

        # Tutarlılık (standart sapma)
        consistency = 100 - (statistics.stdev(scores) if len(scores) > 1 else 0)
        consistency = max(0, min(100, consistency))

        return {
            "trend": trend,
            "improvement_rate": round(slope, 2),
            "consistency": round(consistency, 2),
            "recent_scores": scores,
            "score_variance": round(
                statistics.variance(scores) if len(scores) > 1 else 0, 2
            ),
        }

    async def _predict_next_exam_performance(
        self, db_session, exam_session: ExamSession, improvement_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sonraki sınav performans tahmini"""

        current_score = exam_session.raw_score
        improvement_rate = improvement_trends.get("improvement_rate", 0)
        consistency = improvement_trends.get("consistency", 50)

        # Basit tahmin modeli
        predicted_score = current_score + improvement_rate

        # Güven aralığı (tutarlılığa göre)
        confidence_interval = (100 - consistency) / 10

        lower_bound = max(0, predicted_score - confidence_interval)
        upper_bound = min(100, predicted_score + confidence_interval)

        # Hedef belirleme
        target_score = min(100, current_score + 10)  # %10 artış hedefi

        # Hedef ulaşılabilirlik
        if improvement_rate > 0:
            weeks_to_target = max(
                1, int((target_score - current_score) / improvement_rate)
            )
        else:
            weeks_to_target = None

        return {
            "predicted_score": round(predicted_score, 2),
            "confidence_interval": {
                "lower": round(lower_bound, 2),
                "upper": round(upper_bound, 2),
            },
            "target_score": target_score,
            "weeks_to_target": weeks_to_target,
            "probability_of_improvement": min(100, max(0, 50 + improvement_rate * 10)),
        }


# Singleton instance
exam_performance_service = ExamPerformanceService()
