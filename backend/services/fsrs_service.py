"""
FSRS (Free Spaced Repetition Scheduler) Servisi

Bu servis, Türk öğrenci davranışlarına optimize edilmiş FSRS algoritmasını
kullanarak flashcard sistemi ve tekrar zamanlaması yönetimi sağlar.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from algorithms.turkish_optimized_fsrs import (
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)

# Use models from database.py (consolidated location)
from models.database import FSRSCard as DBFSRSCard
from models.database import FSRSReview as DBFSRSReview
from models.database import FSRSSchedule as DBFSRSSchedule
from models.database import FSRSStudentProfile as DBFSRSStudentProfile
from models.database import FSRSStudySession as DBFSRSStudySession
from models.database import FSRSSubjectStats as DBFSRSSubjectStats

logger = logging.getLogger(__name__)


class FSRSService:
    """
    FSRS servisi - Türk öğrenci davranışlarına optimize edilmiş
    flashcard sistemi ve tekrar zamanlaması yönetimi
    """

    def __init__(self):
        self.fsrs_algorithm = TurkishOptimizedFSRS()

    async def create_flashcard(
        self,
        student_id: str,
        subject: str,
        topic: str,
        content: str,
        answer: str,
        db: Session,
    ) -> DBFSRSCard:
        """
        Yeni flashcard oluştur

        Args:
            student_id: Öğrenci ID'si
            subject: Konu (Matematik, Türkçe, vb.)
            topic: Alt konu
            content: Kart içeriği
            answer: Cevap
            db: Database session

        Returns:
            DBFSRSCard: Oluşturulan flashcard
        """
        try:
            # Yeni flashcard oluştur
            new_card = DBFSRSCard(
                student_id=student_id,
                subject=subject,
                topic=topic,
                content=content,
                answer=answer,
                difficulty=0.0,  # Başlangıç zorluğu
                stability=0.0,  # Başlangıç kararlılığı
                retrievability=0.0,
                state="new",
            )

            db.add(new_card)
            db.commit()
            db.refresh(new_card)

            # İlk tekrar zamanlamasını oluştur
            await self._schedule_first_review(new_card, db)

            # İstatistikleri güncelle
            await self._update_student_stats(student_id, subject, db)

            logger.info(f"Yeni flashcard oluşturuldu: {new_card.id}")
            return new_card

        except Exception as e:
            logger.error(f"Flashcard oluşturma hatası: {e}")
            db.rollback()
            raise

    async def review_flashcard(
        self,
        card_id: str,
        grade: int,
        response_time_ms: int,
        student_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Flashcard incelemesi yap ve sonraki tekrar zamanını hesapla

        Args:
            card_id: Flashcard ID'si
            grade: Öğrenci değerlendirmesi (1-4)
            response_time_ms: Yanıt süresi (milisaniye)
            student_id: Öğrenci ID'si
            db: Database session

        Returns:
            Dict: İnceleme sonucu ve sonraki tekrar bilgileri
        """
        try:
            # Kartı getir
            card = db.query(DBFSRSCard).filter(DBFSRSCard.id == card_id).first()
            if not card:
                raise ValueError(f"Kart bulunamadı: {card_id}")

            # Öğrenci bağlamını getir
            student_context = await self._get_student_context(student_id, db)

            # FSRS grade'e dönüştür
            fsrs_grade = FSRSGrade(grade)

            # Algoritma için kart modeli oluştur
            algo_card = FSRSCard(
                id=card.id,
                subject=card.subject,
                difficulty=card.difficulty,
                stability=card.stability,
                retrievability=card.retrievability,
                last_review=card.last_review,
                due_date=card.due_date,
                review_count=card.review_count,
                lapse_count=card.lapse_count,
                elapsed_days=card.elapsed_days,
                scheduled_days=card.scheduled_days,
                reps=card.reps,
                lapses=card.lapses,
                state=card.state,
            )

            # Sonraki tekrar zamanını hesapla
            current_time = datetime.now()
            schedule = self.fsrs_algorithm.calculate_next_review(
                algo_card, fsrs_grade, current_time, student_context
            )

            # İnceleme öncesi durumu kaydet
            pre_difficulty = card.difficulty
            pre_stability = card.stability
            pre_retrievability = card.retrievability

            # Kartı güncelle
            card.difficulty = schedule.difficulty
            card.stability = schedule.stability
            card.retrievability = schedule.retrievability
            card.last_review = current_time
            card.due_date = schedule.scheduled_date
            card.review_count += 1
            card.scheduled_days = schedule.interval_days
            card.reps += 1

            if grade == 1:  # Again
                card.lapses += 1
                card.lapse_count += 1
                card.state = "relearning"
            else:
                if card.state == "new":
                    card.state = "learning"
                else:
                    card.state = "review"

            # İnceleme kaydı oluştur
            review = DBFSRSReview(
                card_id=card_id,
                student_id=student_id,
                grade=grade,
                response_time_ms=response_time_ms,
                pre_difficulty=pre_difficulty,
                pre_stability=pre_stability,
                pre_retrievability=pre_retrievability,
                post_difficulty=card.difficulty,
                post_stability=card.stability,
                post_retrievability=card.retrievability,
            )

            # Zamanlama kaydı oluştur
            db_schedule = DBFSRSSchedule(
                card_id=card_id,
                student_id=student_id,
                scheduled_date=schedule.scheduled_date,
                interval_days=schedule.interval_days,
                grade=grade,
                stability=schedule.stability,
                difficulty=schedule.difficulty,
                retrievability=schedule.retrievability,
                cultural_factors=schedule.cultural_factors,
            )

            db.add(review)
            db.add(db_schedule)
            db.commit()

            # İstatistikleri güncelle
            await self._update_student_stats(student_id, card.subject, db)
            await self._update_subject_stats(student_id, card.subject, grade, db)

            result = {
                "success": True,
                "card_id": card_id,
                "next_review_date": schedule.scheduled_date.isoformat(),
                "interval_days": schedule.interval_days,
                "new_difficulty": card.difficulty,
                "new_stability": card.stability,
                "new_retrievability": card.retrievability,
                "cultural_factors": schedule.cultural_factors,
                "grade_given": grade,
                "response_time_ms": response_time_ms,
            }

            logger.info(f"Flashcard incelendi: {card_id}, Grade: {grade}")
            return result

        except Exception as e:
            logger.error(f"Flashcard inceleme hatası: {e}")
            db.rollback()
            raise

    async def get_due_cards(
        self, student_id: str, limit: int = 20, db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Vadesi gelen kartları getir

        Args:
            student_id: Öğrenci ID'si
            limit: Maksimum kart sayısı
            db: Database session

        Returns:
            List[Dict]: Vadesi gelen kartlar
        """
        try:
            current_time = datetime.now()

            # Vadesi gelen kartları getir
            due_cards = (
                db.query(DBFSRSCard)
                .filter(
                    and_(
                        DBFSRSCard.student_id == student_id,
                        or_(
                            DBFSRSCard.due_date <= current_time,
                            DBFSRSCard.due_date.is_(None),  # Yeni kartlar
                        ),
                    )
                )
                .order_by(DBFSRSCard.due_date.asc().nulls_first())
                .limit(limit)
                .all()
            )

            result = []
            for card in due_cards:
                # Retention olasılığını hesapla
                retention_prob = 0.0
                if card.stability > 0 and card.last_review:
                    days_since_review = (current_time - card.last_review).days
                    retention_prob = self.fsrs_algorithm.predict_retention_probability(
                        FSRSCard(
                            id=card.id,
                            subject=card.subject,
                            difficulty=card.difficulty,
                            stability=card.stability,
                            retrievability=card.retrievability,
                            last_review=card.last_review,
                            due_date=card.due_date,
                            review_count=card.review_count,
                            lapse_count=card.lapse_count,
                            elapsed_days=card.elapsed_days,
                            scheduled_days=card.scheduled_days,
                            reps=card.reps,
                            lapses=card.lapses,
                            state=card.state,
                        ),
                        days_since_review,
                    )

                card_data = {
                    "id": card.id,
                    "subject": card.subject,
                    "topic": card.topic,
                    "content": card.content,
                    "answer": card.answer,
                    "difficulty": card.difficulty,
                    "stability": card.stability,
                    "retrievability": card.retrievability,
                    "due_date": card.due_date.isoformat() if card.due_date else None,
                    "state": card.state,
                    "review_count": card.review_count,
                    "lapse_count": card.lapse_count,
                    "retention_probability": retention_prob,
                    "is_overdue": card.due_date < current_time
                    if card.due_date
                    else False,
                }
                result.append(card_data)

            logger.info(f"Vadesi gelen {len(result)} kart getirildi: {student_id}")
            return result

        except Exception as e:
            logger.error(f"Vadesi gelen kartları getirme hatası: {e}")
            raise

    async def get_study_recommendations(
        self, student_id: str, db: Session
    ) -> Dict[str, Any]:
        """
        Çalışma önerileri getir

        Args:
            student_id: Öğrenci ID'si
            db: Database session

        Returns:
            Dict: Çalışma önerileri
        """
        try:
            # Öğrenci kartlarını getir
            cards = (
                db.query(DBFSRSCard).filter(DBFSRSCard.student_id == student_id).all()
            )

            # Algoritma için kart listesi oluştur
            algo_cards = []
            for card in cards:
                algo_card = FSRSCard(
                    id=card.id,
                    subject=card.subject,
                    difficulty=card.difficulty,
                    stability=card.stability,
                    retrievability=card.retrievability,
                    last_review=card.last_review,
                    due_date=card.due_date,
                    review_count=card.review_count,
                    lapse_count=card.lapse_count,
                    elapsed_days=card.elapsed_days,
                    scheduled_days=card.scheduled_days,
                    reps=card.reps,
                    lapses=card.lapses,
                    state=card.state,
                )
                algo_cards.append(algo_card)

            # Öğrenci bağlamını getir
            student_context = await self._get_student_context(student_id, db)

            # Önerileri hesapla
            recommendations = self.fsrs_algorithm.get_study_recommendations(
                algo_cards, student_context, datetime.now()
            )

            # Ek istatistikler ekle
            total_cards = len(cards)
            new_cards = len([c for c in cards if c.state == "new"])
            learning_cards = len([c for c in cards if c.state == "learning"])
            review_cards = len([c for c in cards if c.state == "review"])

            recommendations.update(
                {
                    "total_cards": total_cards,
                    "new_cards": new_cards,
                    "learning_cards": learning_cards,
                    "review_cards": review_cards,
                    "student_context": {
                        "group_study_preference": student_context.group_study_preference,
                        "family_pressure_level": student_context.family_pressure_level,
                        "exam_anxiety_level": student_context.exam_anxiety_level,
                        "study_consistency": student_context.study_consistency,
                    },
                }
            )

            return recommendations

        except Exception as e:
            logger.error(f"Çalışma önerileri getirme hatası: {e}")
            raise

    async def get_student_statistics(
        self, student_id: str, db: Session
    ) -> Dict[str, Any]:
        """
        Öğrenci FSRS istatistiklerini getir

        Args:
            student_id: Öğrenci ID'si
            db: Database session

        Returns:
            Dict: Öğrenci istatistikleri
        """
        try:
            # Öğrenci profilini getir
            profile = (
                db.query(DBFSRSStudentProfile)
                .filter(DBFSRSStudentProfile.student_id == student_id)
                .first()
            )

            if not profile:
                # Profil yoksa oluştur
                profile = await self._create_student_profile(student_id, db)

            # Konu bazlı istatistikleri getir
            subject_stats = (
                db.query(DBFSRSSubjectStats)
                .filter(DBFSRSSubjectStats.student_id == student_id)
                .all()
            )

            # Son çalışma oturumlarını getir
            recent_sessions = (
                db.query(DBFSRSStudySession)
                .filter(DBFSRSStudySession.student_id == student_id)
                .order_by(desc(DBFSRSStudySession.session_start))
                .limit(10)
                .all()
            )

            # Genel istatistikler
            total_reviews = (
                db.query(func.count(DBFSRSReview.id))
                .filter(DBFSRSReview.student_id == student_id)
                .scalar()
            )

            avg_grade = (
                db.query(func.avg(DBFSRSReview.grade))
                .filter(DBFSRSReview.student_id == student_id)
                .scalar()
                or 0.0
            )

            # Son 30 günlük performans
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_reviews = (
                db.query(DBFSRSReview)
                .filter(
                    and_(
                        DBFSRSReview.student_id == student_id,
                        DBFSRSReview.review_date >= thirty_days_ago,
                    )
                )
                .all()
            )

            recent_success_rate = 0.0
            if recent_reviews:
                successful_reviews = len([r for r in recent_reviews if r.grade >= 3])
                recent_success_rate = successful_reviews / len(recent_reviews)

            result = {
                "profile": {
                    "total_cards": profile.total_cards,
                    "total_reviews": profile.total_reviews,
                    "average_retention": profile.average_retention,
                    "study_streak_days": profile.study_streak_days,
                    "last_study_date": profile.last_study_date.isoformat()
                    if profile.last_study_date
                    else None,
                    "cards_due_today": profile.cards_due_today,
                    "cards_learned_today": profile.cards_learned_today,
                    "study_time_today_minutes": profile.study_time_today_minutes,
                    "target_retention": profile.target_retention,
                    "group_study_preference": profile.group_study_preference,
                    "family_pressure_level": profile.family_pressure_level,
                    "exam_anxiety_level": profile.exam_anxiety_level,
                    "study_consistency": profile.study_consistency,
                },
                "subject_statistics": [
                    {
                        "subject": stat.subject,
                        "total_cards": stat.total_cards,
                        "cards_mastered": stat.cards_mastered,
                        "cards_learning": stat.cards_learning,
                        "cards_difficult": stat.cards_difficult,
                        "average_difficulty": stat.average_difficulty,
                        "average_stability": stat.average_stability,
                        "success_rate": stat.success_rate,
                        "total_study_time_minutes": stat.total_study_time_minutes,
                        "last_studied": stat.last_studied.isoformat()
                        if stat.last_studied
                        else None,
                    }
                    for stat in subject_stats
                ],
                "recent_performance": {
                    "total_reviews": total_reviews,
                    "average_grade": float(avg_grade),
                    "recent_success_rate": recent_success_rate,
                    "recent_reviews_count": len(recent_reviews),
                },
                "recent_sessions": [
                    {
                        "id": session.id,
                        "session_start": session.session_start.isoformat(),
                        "session_end": session.session_end.isoformat()
                        if session.session_end
                        else None,
                        "duration_minutes": session.duration_minutes,
                        "cards_reviewed": session.cards_reviewed,
                        "cards_learned": session.cards_learned,
                        "average_grade": session.average_grade,
                        "session_type": session.session_type,
                    }
                    for session in recent_sessions
                ],
            }

            return result

        except Exception as e:
            logger.error(f"Öğrenci istatistikleri getirme hatası: {e}")
            raise

    async def start_study_session(
        self, student_id: str, db: Session, session_type: str = "regular"
    ) -> str:
        """
        Çalışma oturumu başlat

        Args:
            student_id: Öğrenci ID'si
            session_type: Oturum türü
            db: Database session

        Returns:
            str: Oturum ID'si
        """
        try:
            # Yeni oturum oluştur
            session = DBFSRSStudySession(
                student_id=student_id,
                session_type=session_type,
                session_start=datetime.now(),
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            logger.info(f"Çalışma oturumu başlatıldı: {session.id}")
            return session.id

        except Exception as e:
            logger.error(f"Çalışma oturumu başlatma hatası: {e}")
            db.rollback()
            raise

    async def end_study_session(self, session_id: str, db: Session) -> Dict[str, Any]:
        """
        Çalışma oturumunu sonlandır

        Args:
            session_id: Oturum ID'si
            db: Database session

        Returns:
            Dict: Oturum özeti
        """
        try:
            # Oturumu getir
            session = (
                db.query(DBFSRSStudySession)
                .filter(DBFSRSStudySession.id == session_id)
                .first()
            )

            if not session:
                raise ValueError(f"Oturum bulunamadı: {session_id}")

            # Oturumu sonlandır
            end_time = datetime.now()
            session.session_end = end_time
            session.duration_minutes = int(
                (end_time - session.session_start).total_seconds() / 60
            )

            # Oturum sırasındaki incelemeleri say
            session_reviews = (
                db.query(DBFSRSReview)
                .filter(
                    and_(
                        DBFSRSReview.student_id == session.student_id,
                        DBFSRSReview.review_date >= session.session_start,
                        DBFSRSReview.review_date <= end_time,
                    )
                )
                .all()
            )

            session.cards_reviewed = len(session_reviews)
            session.cards_learned = len([r for r in session_reviews if r.grade >= 3])

            if session_reviews:
                session.average_grade = sum(r.grade for r in session_reviews) / len(
                    session_reviews
                )

            db.commit()

            # Oturum özeti
            summary = {
                "session_id": session_id,
                "duration_minutes": session.duration_minutes,
                "cards_reviewed": session.cards_reviewed,
                "cards_learned": session.cards_learned,
                "average_grade": session.average_grade,
                "success_rate": session.cards_learned / session.cards_reviewed
                if session.cards_reviewed > 0
                else 0.0,
            }

            logger.info(f"Çalışma oturumu sonlandırıldı: {session_id}")
            return summary

        except Exception as e:
            logger.error(f"Çalışma oturumu sonlandırma hatası: {e}")
            db.rollback()
            raise

    async def _get_student_context(
        self, student_id: str, db: Session
    ) -> StudentContext:
        """Öğrenci bağlam bilgilerini getir"""

        # FSRS profili getir
        profile = (
            db.query(DBFSRSStudentProfile)
            .filter(DBFSRSStudentProfile.student_id == student_id)
            .first()
        )

        if not profile:
            # Varsayılan profil oluştur
            profile = await self._create_student_profile(student_id, db)

        return StudentContext(
            student_id=student_id,
            group_study_preference=profile.group_study_preference,
            family_pressure_level=profile.family_pressure_level,
            exam_anxiety_level=profile.exam_anxiety_level,
            study_consistency=profile.study_consistency,
            cultural_background=profile.cultural_background,
            timezone=profile.timezone,
        )

    async def _create_student_profile(
        self, student_id: str, db: Session
    ) -> DBFSRSStudentProfile:
        """Öğrenci FSRS profili oluştur"""

        profile = DBFSRSStudentProfile(
            student_id=student_id,
            target_retention=0.85,
            group_study_preference=False,
            family_pressure_level=0.5,
            exam_anxiety_level=0.5,
            study_consistency=0.5,
            cultural_background="turkish",
            timezone="Europe/Istanbul",
        )

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return profile

    async def _schedule_first_review(self, card: DBFSRSCard, db: Session):
        """İlk tekrar zamanlamasını oluştur"""

        # Yeni kartlar için 1 gün sonra ilk tekrar
        first_review_date = datetime.now() + timedelta(days=1)
        card.due_date = first_review_date
        card.scheduled_days = 1

        # İlk zamanlama kaydı
        schedule = DBFSRSSchedule(
            card_id=card.id,
            student_id=card.student_id,
            scheduled_date=first_review_date,
            interval_days=1,
            stability=0.0,
            difficulty=0.0,
            retrievability=0.0,
            cultural_factors={"initial_schedule": True},
        )

        db.add(schedule)
        db.commit()

    async def _update_student_stats(self, student_id: str, subject: str, db: Session):
        """Öğrenci istatistiklerini güncelle"""

        # Genel profil güncelle
        profile = (
            db.query(DBFSRSStudentProfile)
            .filter(DBFSRSStudentProfile.student_id == student_id)
            .first()
        )

        if profile:
            # Toplam kart sayısını güncelle
            total_cards = (
                db.query(func.count(DBFSRSCard.id))
                .filter(DBFSRSCard.student_id == student_id)
                .scalar()
            )

            profile.total_cards = total_cards
            profile.last_study_date = datetime.now()

            db.commit()

    async def _update_subject_stats(
        self, student_id: str, subject: str, grade: int, db: Session
    ):
        """Konu bazlı istatistikleri güncelle"""

        # Konu istatistiği getir veya oluştur
        subject_stat = (
            db.query(DBFSRSSubjectStats)
            .filter(
                and_(
                    DBFSRSSubjectStats.student_id == student_id,
                    DBFSRSSubjectStats.subject == subject,
                )
            )
            .first()
        )

        if not subject_stat:
            subject_stat = DBFSRSSubjectStats(student_id=student_id, subject=subject)
            db.add(subject_stat)

        # İstatistikleri güncelle
        subject_stat.last_studied = datetime.now()

        # Başarı oranını hesapla
        subject_reviews = (
            db.query(DBFSRSReview)
            .join(DBFSRSCard)
            .filter(
                and_(DBFSRSCard.student_id == student_id, DBFSRSCard.subject == subject)
            )
            .all()
        )

        if subject_reviews:
            successful_reviews = len([r for r in subject_reviews if r.grade >= 3])
            subject_stat.success_rate = successful_reviews / len(subject_reviews)

        db.commit()
