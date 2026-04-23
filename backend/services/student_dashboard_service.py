"""
Öğrenci Dashboard Servisi - Database Integration
REFACTORED: Mock data removed, replaced with real database queries
Part of Mock Data Cleanup - Phase 3

PERFORMANCE FIX: Converted from sync SQLAlchemy (.query()) to async (.execute(select()))
Previously: Sync calls blocked event loop for 50-200ms per query
Now: Proper async operations allow concurrent request handling
"""
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Union

from sqlalchemy import Integer, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Database models (SQLAlchemy ORM)
from models import (
    ExamSession,
    Notification,
    StudentAnswer,
    StudentGoal,
    StudentProfile,
    User,
    WeeklyProgress,
)

# Pydantic models (API responses)
from models.dashboard import (
    Bildirim,
    DashboardIstatistikleri,
    Hedef,
    PerformansVerisi,
    ProfilGuncelleme,
    SinavSonucu,
)
from models.question_bank import QuestionBankItem as Question
from models.user import OgrenciProfili
from models.video_analytics import VideoWatchSession

# Type alias for backward compatibility
DBSession = Union[Session, AsyncSession]


class OgrenciDashboardServisi:
    """
    Öğrenci dashboard işlemleri servisi

    REFACTORED (2025-11-17):
    - Removed self.mock_data dictionary
    - All methods now query real database
    - Hybrid approach: DB queries + intelligent defaults for new users
    - Dependency injection: db: Session parameter in all methods
    """

    async def dashboard_istatistikleri_getir(
        self, kullanici_id: str, db: DBSession
    ) -> DashboardIstatistikleri:
        """
        Dashboard ana sayfası istatistiklerini getir

        REFACTORED: Real database queries + intelligent defaults
        - Queries: users, exam_sessions, weekly_progress
        - Fallback: Sensible defaults for new users

        PERFORMANCE FIX: Converted to async SQLAlchemy pattern
        """
        # Helper to handle both sync and async sessions
        async def execute_query(query):
            if hasattr(db, 'execute'):
                # Async session
                result = await db.execute(query)
                return result
            # Sync session fallback
            return db.execute(query)

        # Get user data (XP, level, gamification)
        user_result = await execute_query(
            select(User).where(User.id == kullanici_id)
        )
        user = user_result.scalar_one_or_none() if hasattr(user_result, 'scalar_one_or_none') else user_result.scalars().first()

        # Get exam statistics — combine exam_sessions AND kiro2_cat_sessions
        # exam_sessions.student_id → student_profiles.id (not user_id!)
        # kiro2_cat_sessions.user_id → users.id
        # SAVEPOINT: SQL hata verirse ana transaction'ı zehirlemesin
        from sqlalchemy import text as sa_text
        completed_exams = 0
        avg_score = 0.0
        try:
            async with db.begin_nested():
                cat_stats_result = await db.execute(sa_text("""
                    SELECT
                        (COALESCE(es.cnt, 0) + COALESCE(cs.cnt, 0)) AS total_count,
                        CASE WHEN (COALESCE(es.cnt, 0) + COALESCE(cs.cnt, 0)) > 0
                             THEN COALESCE(es.avg_score, 0)
                             ELSE 0 END AS avg_score
                    FROM
                        (SELECT COUNT(*) AS cnt, AVG(scaled_score) AS avg_score
                         FROM exam_sessions
                         WHERE student_id IN (SELECT id FROM student_profiles WHERE user_id = :uid)
                           AND status = 'completed') es,
                        (SELECT COUNT(*) AS cnt
                         FROM kiro2_cat_sessions
                         WHERE user_id = CAST(:uid AS uuid)
                           AND state = 'completed') cs
                """), {"uid": kullanici_id})
                cat_row = cat_stats_result.first()
                completed_exams = int(cat_row.total_count) if cat_row else 0
                avg_score = float(cat_row.avg_score) if cat_row and cat_row.avg_score else 0.0
        except Exception:
            completed_exams = 0
            avg_score = 0.0

        # Get weekly progress
        current_week = datetime.now().isocalendar()
        week_query = select(WeeklyProgress).where(
            and_(
                WeeklyProgress.user_id == kullanici_id,
                WeeklyProgress.year == current_week.year,
                WeeklyProgress.week_number == current_week.week
            )
        )
        week_result = await execute_query(week_query)
        week_progress = week_result.scalar_one_or_none() if hasattr(week_result, 'scalar_one_or_none') else week_result.scalars().first()

        # Calculate study time (in minutes)
        haftalik_ilerleme = (week_progress.total_time_seconds // 60) if week_progress else 0
        gunluk_seri = week_progress.streak_days if week_progress else 0

        # Get completed lessons (videos) count
        # SAVEPOINT: video_watch_sessions sorgusu başarısız olursa
        # PostgreSQL transaction'ı zehirlemez — sadece savepoint geri alınır
        tamamlanan_dersler = 0
        try:
            async with db.begin_nested():  # SAVEPOINT
                video_count_query = select(func.count(VideoWatchSession.id)).where(
                    and_(
                        VideoWatchSession.user_id == kullanici_id,
                        VideoWatchSession.is_completed == True
                    )
                )
                video_result = await db.execute(video_count_query)
                tamamlanan_dersler = video_result.scalar() or 0
        except Exception:
            tamamlanan_dersler = 0

        # Return real data with intelligent defaults
        return DashboardIstatistikleri(
            tamamlanan_dersler=tamamlanan_dersler or 0,
            toplam_dersler=120,  # Default curriculum size
            tamamlanan_sinavlar=completed_exams,
            ortalama_puan=avg_score,
            toplam_calisma_suresi=haftalik_ilerleme,  # This week's total
            haftalik_hedef=300,  # Default: 5 hours/week
            haftalik_ilerleme=haftalik_ilerleme,
            gunluk_seri=gunluk_seri,
            toplam_puan=user.total_xp if user else 0,
            seviye=user.level if user else 1,
            deneyim=user.total_xp if user else 0,
            sonraki_seviye_deneyim=(user.level + 1) * 1000 if user else 1000,
        )

    async def sinav_gecmisi_getir(
        self,
        kullanici_id: str,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        sinav_tipi: str | None = None,
    ) -> list[SinavSonucu]:
        """
        Öğrencinin sınav geçmişini getir

        REFACTORED v2: Combines exam_sessions + kiro2_cat_sessions
        - exam_sessions.student_id → student_profiles.id (JOIN required)
        - kiro2_cat_sessions.user_id → users.id (direct)
        """
        from sqlalchemy import text as sa_text

        type_filter = "AND exam_type = :sinav_tipi" if sinav_tipi else ""
        type_params = {"sinav_tipi": sinav_tipi} if sinav_tipi else {}

        query = sa_text(f"""
            (SELECT id::text, exam_name::text, exam_type::text, completed_at,
                    scaled_score::float,
                    total_correct::int, total_wrong::int, total_empty::int,
                    duration_minutes::int
             FROM exam_sessions
             WHERE student_id IN (SELECT id FROM student_profiles WHERE user_id = :uid)
               AND status = 'completed' {type_filter}
            )
            UNION ALL
            (SELECT id::text, ('CAT ' || subject_id)::text AS exam_name,
                    'CAT'::text AS exam_type,
                    completed_at, NULL::float AS scaled_score,
                    NULL::int AS total_correct, NULL::int AS total_wrong,
                    NULL::int AS total_empty,
                    (EXTRACT(EPOCH FROM (completed_at - started_at))::int / 60)::int
                        AS duration_minutes
             FROM kiro2_cat_sessions
             WHERE user_id = CAST(:uid AS uuid) AND state = 'completed'
            )
            ORDER BY completed_at DESC NULLS LAST
            LIMIT :lim OFFSET :off
        """)

        try:
            async with db.begin_nested():
                result = await db.execute(
                    query, {"uid": kullanici_id, "lim": limit, "off": offset, **type_params}
                )
                rows = result.fetchall()
        except Exception:
            rows = []

        sinavlar = []
        for row in rows:
            sinavlar.append(
                SinavSonucu(
                    sinav_id=str(row.id),
                    sinav_adi=row.exam_name or "Sınav",
                    sinav_tipi=row.exam_type or "CAT",
                    tarih=row.completed_at,
                    puan=float(row.scaled_score or 0),
                    dogru_sayisi=row.total_correct or 0,
                    yanlis_sayisi=row.total_wrong or 0,
                    bos_sayisi=row.total_empty or 0,
                    sure=row.duration_minutes or 0,
                    konu_performanslari={},
                )
            )
        return sinavlar

    async def _calculate_topic_performance_batch(
        self, exam_session_ids: list[str], db: Session
    ) -> dict[str, dict[str, float]]:
        """
        Batch calculate topic performance for multiple exam sessions in ONE query.

        Returns: {exam_session_id: {topic_id: percentage, ...}, ...}
        """
        if not exam_session_ids:
            return {}

        stmt = (
            select(
                StudentAnswer.exam_session_id,
                Question.primary_topic_id,
                func.count(StudentAnswer.id).label('total'),
                func.sum(func.cast(StudentAnswer.is_correct, Integer)).label('correct'),
            )
            .join(Question, StudentAnswer.question_id == Question.id)
            .where(StudentAnswer.exam_session_id.in_(exam_session_ids))
            .group_by(StudentAnswer.exam_session_id, Question.primary_topic_id)
        )
        topic_result = await db.execute(stmt)
        topic_stats = topic_result.all()

        result: dict[str, dict[str, float]] = {}
        for stat in topic_stats:
            if stat.primary_topic_id and stat.total > 0:
                if stat.exam_session_id not in result:
                    result[stat.exam_session_id] = {}
                correct_count = stat.correct or 0
                percentage = (correct_count / stat.total) * 100
                result[stat.exam_session_id][stat.primary_topic_id] = round(percentage, 1)

        return result

    async def _calculate_subject_performance(self, kullanici_id: str, db, min_questions: int = 10) -> dict[str, float]:
        """
        Calculate overall subject performance across all exams

        Returns: Dictionary mapping subject areas to percentage correct (0-100)
        Only includes subjects with at least min_questions answered
        """
        stmt = (
            select(
                Question.subject_area,
                func.count(StudentAnswer.id).label('total'),
                func.sum(func.cast(StudentAnswer.is_correct, Integer)).label('correct'),
            )
            .join(StudentAnswer, StudentAnswer.question_id == Question.id)
            .join(ExamSession, StudentAnswer.exam_session_id == ExamSession.id)
            .where(
                ExamSession.student_id == kullanici_id,
                ExamSession.status == 'completed',
            )
            .group_by(Question.subject_area)
        )
        result = await db.execute(stmt)
        subject_stats = result.all()

        # Calculate percentage correct per subject
        subject_performance = {}
        for subject_stat in subject_stats:
            if subject_stat.total >= min_questions:
                correct_count = subject_stat.correct or 0
                percentage = (correct_count / subject_stat.total) * 100
                subject_name = subject_stat.subject_area.value if hasattr(subject_stat.subject_area, 'value') else str(subject_stat.subject_area)
                subject_performance[subject_name] = round(percentage, 1)

        return subject_performance

    async def performans_trendi_getir(
        self, kullanici_id: str, db, gun_sayisi: int = 30
    ) -> list[PerformansVerisi]:
        """
        Öğrencinin performans trendini getir

        REFACTORED: Real performance trends from exam_sessions
        - Query: exam_sessions grouped by date
        - Fallback: Empty data for days with no activity (NOT random data!)
        """

        # Get last N days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=gun_sayisi)

        # Query exam_sessions grouped by date
        exam_stmt = (
            select(
                func.date(ExamSession.completed_at).label('date'),
                func.count(ExamSession.id).label('exam_count'),
                func.avg(ExamSession.scaled_score).label('avg_score'),
            )
            .where(
                ExamSession.student_id == kullanici_id,
                ExamSession.completed_at >= start_date,
                ExamSession.status == 'completed',
            )
            .group_by(func.date(ExamSession.completed_at))
        )
        exam_result = await db.execute(exam_stmt)
        daily_exams = exam_result.all()

        # Query completed lessons (videos) grouped by date — table may not exist
        try:
            lesson_stmt = (
                select(
                    func.date(VideoWatchSession.completed_at).label('date'),
                    func.count(VideoWatchSession.id).label('lesson_count'),
                )
                .where(
                    VideoWatchSession.user_id == kullanici_id,
                    VideoWatchSession.completed_at >= start_date,
                    VideoWatchSession.is_completed == True,
                )
                .group_by(func.date(VideoWatchSession.completed_at))
            )
            lesson_result = await db.execute(lesson_stmt)
            daily_lessons = lesson_result.all()

            study_stmt = (
                select(
                    func.date(VideoWatchSession.started_at).label('date'),
                    func.sum(VideoWatchSession.watch_duration).label('total_seconds'),
                )
                .where(
                    VideoWatchSession.user_id == kullanici_id,
                    VideoWatchSession.started_at >= start_date,
                )
                .group_by(func.date(VideoWatchSession.started_at))
            )
            study_result = await db.execute(study_stmt)
            daily_study_time = study_result.all()
        except Exception:
            daily_lessons = []
            daily_study_time = []

        # Convert to dicts for fast lookup
        exam_dict = {str(e.date): e for e in daily_exams}
        lesson_dict = {str(l.date): l for l in daily_lessons}
        study_time_dict = {str(s.date): s for s in daily_study_time}

        # Build daily performance data
        performans_verisi = []
        for i in range(gun_sayisi):
            tarih = start_date + timedelta(days=i)
            tarih_str = tarih.strftime('%Y-%m-%d')

            exam_data = exam_dict.get(tarih_str)
            lesson_data = lesson_dict.get(tarih_str)
            study_data = study_time_dict.get(tarih_str)

            performans_verisi.append(
                PerformansVerisi(
                    tarih=tarih_str,
                    dersler=lesson_data.lesson_count if lesson_data else 0,
                    sinavlar=exam_data.exam_count if exam_data else 0,
                    puan=int(exam_data.avg_score or 0) if exam_data else 0,
                    calisma_suresi=int((study_data.total_seconds or 0) // 60) if study_data else 0,  # Convert to minutes
                )
            )

        return performans_verisi

    async def hedefler_getir(
        self, kullanici_id: str, db, aktif_sadece: bool = False
    ) -> list[Hedef]:
        """
        Öğrencinin hedeflerini getir

        REFACTORED: Real goals from student_goals table
        - Query: student_goals with status filter
        - Fallback: Empty list for new users (can show onboarding)
        """

        conditions = [StudentGoal.user_id == kullanici_id]
        if aktif_sadece:
            conditions.append(StudentGoal.status == 'aktif')

        stmt = select(StudentGoal).where(and_(*conditions)).order_by(StudentGoal.created_at.desc())
        result = await db.execute(stmt)
        goals = result.scalars().all()

        # Convert to Hedef format
        hedefler = []
        for goal in goals:
            hedefler.append(
                Hedef(
                    hedef_id=goal.id,
                    baslik=goal.title,
                    aciklama=goal.description,
                    hedef_tipi=goal.goal_type,
                    hedef_degeri=goal.target_value,
                    mevcut_deger=goal.current_value,
                    baslangic_tarihi=goal.start_date,
                    bitis_tarihi=goal.end_date,
                    durum=goal.status,
                    olusturma_tarihi=goal.created_at,
                )
            )

        return hedefler

    async def hedef_olustur(self, kullanici_id: str, db, hedef_data: Hedef) -> Hedef:
        """
        Yeni hedef oluştur

        REFACTORED: Saves to student_goals table
        """

        # Create new StudentGoal
        new_goal = StudentGoal(
            id=f"hedef_{uuid.uuid4().hex[:8]}",
            user_id=kullanici_id,
            title=hedef_data.baslik,
            description=hedef_data.aciklama,
            goal_type=hedef_data.hedef_tipi,
            target_value=hedef_data.hedef_degeri,
            current_value=hedef_data.mevcut_deger,
            start_date=hedef_data.baslangic_tarihi,
            end_date=hedef_data.bitis_tarihi,
            status=hedef_data.durum,
        )

        db.add(new_goal)
        await db.commit()
        await db.refresh(new_goal)

        # Return as Hedef
        hedef_data.hedef_id = new_goal.id
        hedef_data.olusturma_tarihi = new_goal.created_at

        return hedef_data

    async def hedef_guncelle(
        self, kullanici_id: str, hedef_id: str, db, hedef_data: Hedef
    ) -> Hedef:
        """
        Mevcut hedefi güncelle

        REFACTORED: Updates student_goals table
        """

        stmt = select(StudentGoal).where(
            StudentGoal.id == hedef_id,
            StudentGoal.user_id == kullanici_id,
        )
        result = await db.execute(stmt)
        goal = result.scalars().first()

        if not goal:
            raise ValueError(f"Goal {hedef_id} not found for user {kullanici_id}")

        # Update fields
        goal.title = hedef_data.baslik
        goal.description = hedef_data.aciklama
        goal.target_value = hedef_data.hedef_degeri
        goal.current_value = hedef_data.mevcut_deger
        goal.status = hedef_data.durum
        goal.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(goal)

        hedef_data.hedef_id = hedef_id
        return hedef_data

    async def hedef_sil(self, kullanici_id: str, hedef_id: str, db) -> bool:
        """
        Hedefi sil

        REFACTORED: Deletes from student_goals table
        """

        stmt = select(StudentGoal).where(
            StudentGoal.id == hedef_id,
            StudentGoal.user_id == kullanici_id,
        )
        result = await db.execute(stmt)
        goal = result.scalars().first()

        if not goal:
            return False

        await db.delete(goal)
        await db.commit()

        return True

    async def bildirimler_getir(
        self, kullanici_id: str, db, okunmamis_sadece: bool = False, limit: int = 50
    ) -> list[Bildirim]:
        """
        Öğrencinin bildirimlerini getir

        REFACTORED: Real notifications from notifications table
        - Query: notifications with read filter
        - Fallback: Empty list for new users
        """

        conditions = [Notification.user_id == kullanici_id]
        if okunmamis_sadece:
            conditions.append(Notification.is_read == False)

        stmt = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        # Convert to Bildirim format
        bildirimler = []
        for notif in notifications:
            bildirimler.append(
                Bildirim(
                    bildirim_id=notif.id,
                    baslik=notif.title,
                    mesaj=notif.message,
                    tip=notif.notification_type,
                    okundu=notif.is_read,
                    tarih=notif.created_at,
                    eylem_url=notif.action_url,
                )
            )

        return bildirimler

    async def bildirim_okundu_isaretle(
        self, kullanici_id: str, bildirim_id: str, db
    ) -> bool:
        """
        Bildirimi okundu olarak işaretle

        REFACTORED: Updates notifications table
        """

        stmt = select(Notification).where(
            Notification.id == bildirim_id,
            Notification.user_id == kullanici_id,
        )
        result = await db.execute(stmt)
        notif = result.scalars().first()

        if not notif:
            return False

        notif.is_read = True
        await db.commit()

        return True

    async def ogrenci_profili_getir(
        self, kullanici_id: str, db
    ) -> OgrenciProfili | None:
        """
        Öğrenci profil bilgilerini getir

        REFACTORED: Real student profile from student_profiles table
        - Query: student_profiles + users
        - Fallback: None for users without profile (they can create one)
        """

        stmt = select(StudentProfile).where(StudentProfile.user_id == kullanici_id)
        result = await db.execute(stmt)
        profile = result.scalars().first()

        if not profile:
            return None

        user_stmt = select(User).where(User.id == kullanici_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalars().first()

        # Calculate subject performance to determine strong/weak areas
        subject_performance = await self._calculate_subject_performance(kullanici_id, db, min_questions=10)

        # Determine strong areas (>= 70%) and weak areas (<= 50%)
        guclu_alanlar = [subject for subject, perf in subject_performance.items() if perf >= 70.0]
        zayif_alanlar = [subject for subject, perf in subject_performance.items() if perf <= 50.0]

        return OgrenciProfili(
            ogrenci_id=profile.id,
            kullanici_id=kullanici_id,
            sinif_seviyesi=profile.grade_level or 12,
            okul_adi=profile.school_name or "Okul belirtilmedi",
            hedef_sinav=profile.hedef_sinav or "TYT",
            hedef_universiteler=[profile.target_university] if profile.target_university else [],
            ogrenme_stili=profile.learning_style or "gorsel",
            guclu_alanlar=guclu_alanlar,
            zayif_alanlar=zayif_alanlar,
            gunluk_calisma_hedefi=profile.study_hours_per_day or 120,
            veli_onay=profile.veli_onay,
            olusturma_tarihi=profile.created_at,
            son_guncelleme=profile.updated_at,
        )

    async def profil_guncelle(
        self, kullanici_id: str, db, profil_data: ProfilGuncelleme
    ) -> OgrenciProfili:
        """
        Öğrenci profil bilgilerini güncelle

        REFACTORED: Updates student_profiles table
        """

        stmt = select(StudentProfile).where(StudentProfile.user_id == kullanici_id)
        result = await db.execute(stmt)
        profile = result.scalars().first()

        if not profile:
            raise ValueError("Öğrenci profili bulunamadı")

        # Update fields if provided
        if profil_data.sinif_seviyesi is not None:
            profile.grade_level = profil_data.sinif_seviyesi

        if profil_data.okul_adi is not None:
            profile.school_name = profil_data.okul_adi

        if profil_data.hedef_universiteler is not None and profil_data.hedef_universiteler:
            profile.target_university = profil_data.hedef_universiteler[0]

        if profil_data.gunluk_calisma_hedefi is not None:
            profile.study_hours_per_day = profil_data.gunluk_calisma_hedefi

        # Update timestamp
        profile.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(profile)

        # Return updated profile
        return await self.ogrenci_profili_getir(kullanici_id, db)

    async def dashboard_ozeti_getir(self, kullanici_id: str, db) -> dict[str, Any]:
        """
        Dashboard özet bilgilerini getir

        REFACTORED: All data from real database
        """

        # Get all components (all now from database)
        istatistikler = await self.dashboard_istatistikleri_getir(kullanici_id, db)
        son_sinavlar = await self.sinav_gecmisi_getir(kullanici_id, db, limit=5)
        okunmamis_bildirimler = await self.bildirimler_getir(
            kullanici_id, db, okunmamis_sadece=True, limit=10
        )
        aktif_hedefler = await self.hedefler_getir(kullanici_id, db, aktif_sadece=True)
        bugun_performans = await self.performans_trendi_getir(kullanici_id, db, gun_sayisi=1)

        # Pydantic → dict conversion helper (cache JSON serialization için)
        def _to_dict(obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            if hasattr(obj, 'dict'):
                return obj.dict()
            return obj

        return {
            "istatistikler": _to_dict(istatistikler),
            "son_sinavlar": [_to_dict(s) for s in son_sinavlar],
            "okunmamis_bildirim_sayisi": len(okunmamis_bildirimler),
            "acil_bildirimler": [
                _to_dict(b) for b in okunmamis_bildirimler if b.tip in ["uyari", "hata"]
            ],
            "aktif_hedef_sayisi": len(aktif_hedefler),
            "bugun_calisma_suresi": bugun_performans[0].calisma_suresi
            if bugun_performans
            else 0,
            "haftalik_hedef_yuzdesi": (
                istatistikler.haftalik_ilerleme / istatistikler.haftalik_hedef
            )
            * 100
            if istatistikler.haftalik_hedef > 0
            else 0,
            "seviye_ilerleme_yuzdesi": (
                istatistikler.deneyim / istatistikler.sonraki_seviye_deneyim
            )
            * 100
            if istatistikler.sonraki_seviye_deneyim > 0
            else 0,
        }


# Singleton instance (no __init__ needed now)
ogrenci_dashboard_servisi = OgrenciDashboardServisi()
