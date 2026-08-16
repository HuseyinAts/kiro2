"""
Veli (Parent) servis katmanı
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

import json
import secrets
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database import ExamSession, User
from models.enums_db import UserRole
from models.exam_db import StudentAnswer
from models.gamification import ParentChild as ParentChildRelation
from models.gamification import ParentLinkCode
from models.parent import (
    ChildPerformanceData,
    ParentChildRelationCreate,
    ParentChildRelationResponse,
    ParentDashboardData,
    ParentNotification,
    ParentNotificationCreate,
    ParentNotificationResponse,
    WeeklyReport,
    WeeklyReportData,
)
from models.question_bank import QuestionBankItem, QuestionMetadata
from models.study_planner import StudyPlan

# ---------------------------------------------------------------------------
# Saf (DB'siz) KPI toplama yardımcıları
# ---------------------------------------------------------------------------
# Bu fonksiyonlar ExamSession / StudentAnswer / WeeklyGoal benzeri hafif
# nesneler (herhangi bir .attr taşıyan) üzerinde çalışır — gerçek DB gerekmez,
# birim testlerle doğrulanır (tests/unit/test_parent_kpi_aggregation.py).


def _completed_exams_desc(exams: list[Any]) -> list[Any]:
    """`completed_at` dolu sınavları en yeniden eskiye sıralar."""
    completed = [e for e in exams if getattr(e, "completed_at", None) is not None]
    completed.sort(key=lambda e: e.completed_at, reverse=True)
    return completed


def compute_recent_exams(exams: list[Any], limit: int = 5) -> list[dict]:
    """En son `limit` sınavı [{date, score, type, name}] olarak şekillendirir."""
    out: list[dict] = []
    for e in _completed_exams_desc(exams)[:limit]:
        item: dict = {
            "date": e.completed_at,
            "score": round(float(getattr(e, "raw_score", 0.0) or 0.0), 2),
        }
        exam_type = getattr(e, "exam_type", None)
        if exam_type is not None:
            item["type"] = getattr(exam_type, "value", None) or str(exam_type)
        name = getattr(e, "exam_name", None)
        if name is not None:
            item["name"] = name
        out.append(item)
    return out


def compute_weekly_activity(
    exams: list[Any], now: datetime, days: int = 7
) -> tuple[list[dict], float]:
    """Son `days` günün günlük çalışma dakikasını grupla (eski→yeni).

    Returns:
        (activity, week_total_hours). activity her gün için
        {date, label, minutes}; eksik günler 0 dakika ile doldurulur.
    """
    today = now.date()
    day_keys = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    minutes_by_day: dict = dict.fromkeys(day_keys, 0)
    for e in exams:
        completed_at = getattr(e, "completed_at", None)
        if completed_at is None:
            continue
        d = completed_at.date()
        if d in minutes_by_day:
            minutes_by_day[d] += int(getattr(e, "duration_minutes", 0) or 0)
    activity = [
        {"date": d.isoformat(), "label": d.isoformat(), "minutes": minutes_by_day[d]}
        for d in day_keys
    ]
    week_total_hours = round(sum(minutes_by_day.values()) / 60.0, 1)
    return activity, week_total_hours


def compute_net_change(exams: list[Any], limit: int = 5) -> float:
    """En son yarının ort. raw_score'u eksi önceki yarı (işaretli).

    <2 tamamlanmış sınav → 0.0.
    """
    recent_desc = _completed_exams_desc(exams)[:limit]
    if len(recent_desc) < 2:
        return 0.0
    recent_asc = list(reversed(recent_desc))  # eski→yeni
    n = len(recent_asc)
    half = n // 2
    prior = recent_asc[:half]  # eski yarı
    latest = recent_asc[half:]  # yeni yarı (tek sayıda ortadaki yeni tarafta)
    prior_avg = sum(float(e.raw_score or 0.0) for e in prior) / len(prior)
    latest_avg = sum(float(e.raw_score or 0.0) for e in latest) / len(latest)
    return round(latest_avg - prior_avg, 2)


def compute_current_streak(exams: list[Any], now: datetime) -> int:
    """Bugünden (UTC) geriye kesintisiz ≥1 tamamlanmış sınav günü sayısı."""
    active_days = {
        e.completed_at.date()
        for e in exams
        if getattr(e, "completed_at", None) is not None
    }
    streak = 0
    cursor = now.date()
    while cursor in active_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _window_counts(dts: list, now: datetime) -> tuple[int, int]:
    """(bu_hafta, geçen_hafta) sayıları — kayan 7'şer günlük pencereler."""
    this_start = now - timedelta(days=7)
    last_start = now - timedelta(days=14)
    this_week = sum(1 for d in dts if d is not None and this_start < d <= now)
    last_week = sum(1 for d in dts if d is not None and last_start < d <= this_start)
    return this_week, last_week


def compute_exams_delta(exams: list[Any], now: datetime) -> int:
    """Bu hafta - geçen hafta tamamlanan sınav sayısı."""
    dts = [getattr(e, "completed_at", None) for e in exams]
    this_week, last_week = _window_counts(dts, now)
    return this_week - last_week


def compute_solved_delta(answered_at_list: list, now: datetime) -> int:
    """Bu hafta - geçen hafta cevaplanan soru sayısı."""
    this_week, last_week = _window_counts(list(answered_at_list), now)
    return this_week - last_week


def classify_subjects(
    subject_stats: list[tuple[str, int, int]],
    min_questions: int = 3,
    weak_below: float = 50.0,
    strong_at: float = 75.0,
    top_n: int = 3,
) -> tuple[list[str], list[str], list[dict]]:
    """Ders bazlı doğruluktan zayıf/güçlü dersleri ve ilerleme listesini çıkarır.

    Args:
        subject_stats: (subject_area, correct, total) üçlüleri.
        min_questions: Bir dersi yargılamak için gereken min cevaplı soru.
        weak_below: Bu yüzdenin altı zayıf ders.
        strong_at: Bu yüzde ve üstü güçlü ders.
        top_n: Zayıf/güçlü listelerinin maks uzunluğu.

    Returns:
        (weak_subjects, strong_subjects, subject_progress).
        subject_progress: [{subject, mastery, answered}] (mastery yüzde, desc).
    """
    progress: list[dict] = []
    for subject, correct, total in subject_stats:
        if not subject or total < min_questions:
            continue
        pct = round(100.0 * correct / total, 1)
        progress.append({"subject": subject, "mastery": pct, "answered": total})
    progress.sort(key=lambda p: p["mastery"], reverse=True)
    weak = [
        p["subject"]
        for p in sorted(progress, key=lambda p: p["mastery"])
        if p["mastery"] < weak_below
    ][:top_n]
    strong = [p["subject"] for p in progress if p["mastery"] >= strong_at][:top_n]
    return weak, strong, progress


_TR_UPPER = str.maketrans(
    {"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç"}
)


def compute_initials(first_name: str | None, last_name: str | None) -> str:
    """Ad-soyad baş harflerinden 2-harfli kısaltma üretir (Türkçe upper).

    Örn. ("Ali", "Yılmaz") → "AY", ("irem", "şahin") → "İŞ".

    Args:
        first_name: Öğrencinin adı (None/boş olabilir).
        last_name: Öğrencinin soyadı (None/boş olabilir).

    Returns:
        Türkçe büyük harfe çevrilmiş baş harfler (0-2 karakter).
    """

    def _first_letter(name: str | None) -> str:
        s = (name or "").strip()
        return s[0] if s else ""

    initials = _first_letter(first_name) + _first_letter(last_name)
    return initials.translate(_TR_UPPER).upper()


def compute_plan_adherence(goals: list[Any]) -> float | None:
    """Aktif planın uyum yüzdesi = tamamlanan/hedef (soru+tekrar). Hedef 0 → None."""
    total_target = 0
    total_done = 0
    for g in goals:
        total_target += int(getattr(g, "target_questions", 0) or 0) + int(
            getattr(g, "target_reviews", 0) or 0
        )
        total_done += int(getattr(g, "completed_questions", 0) or 0) + int(
            getattr(g, "completed_reviews", 0) or 0
        )
    if total_target <= 0:
        return None
    return round(min(100.0, 100.0 * total_done / total_target), 1)


class ParentService:
    """Veli takip sistemi servis sınıfı"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_parent_child_relation(
        self, parent_id: str, relation_data: ParentChildRelationCreate
    ) -> ParentChildRelationResponse:
        """Veli-çocuk ilişkisi oluştur"""

        # Çocuğu email ile bul
        result = await self.db.execute(
            select(User).where(User.email == relation_data.child_email)
        )
        child = result.scalar_one_or_none()

        if not child:
            raise ValueError("Belirtilen email adresine sahip öğrenci bulunamadı")

        if child.role != UserRole.STUDENT:
            raise ValueError("Sadece öğrenci hesapları ile ilişki kurulabilir")

        # Mevcut ilişki kontrolü
        existing = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == child.id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Bu öğrenci ile zaten bir ilişkiniz bulunmaktadır")

        # Yeni ilişki oluştur
        new_relation = ParentChildRelation(
            parent_id=parent_id,
            child_id=child.id,
            relation_type=relation_data.relation_type,
            approved=False,  # Onay bekliyor
        )

        self.db.add(new_relation)
        await self.db.commit()
        await self.db.refresh(new_relation)

        # Çocuğa bildirim gönder
        await self._send_approval_request_notification(child.id, parent_id)

        return ParentChildRelationResponse(
            id=new_relation.id,
            parent_id=new_relation.parent_id,
            child_id=new_relation.child_id,
            child_name=f"{child.first_name} {child.last_name}",
            child_email=child.email,
            relation_type=new_relation.relation_type,
            approved=new_relation.approved,
            created_at=new_relation.created_at,
            approved_at=new_relation.approved_at,
        )

    # ------------------------------------------------------------------
    # Kod-tabanlı veli-öğrenci bağlama (6-hane, 10dk TTL)
    # ------------------------------------------------------------------

    async def _unique_link_code(self, now: datetime) -> str:
        """Aktif (tüketilmemiş, süresi geçmemiş) kodlar arasında benzersiz üret.

        Args:
            now: Şu anki tz-aware zaman (süre karşılaştırması için).

        Returns:
            Çakışmayan 6-hane kod (baştaki sıfırlar korunur, örn. "004217").

        Raises:
            ValueError: 50 denemede benzersiz kod üretilemezse.
        """
        for _ in range(50):
            code = f"{secrets.randbelow(1_000_000):06d}"
            existing = await self.db.execute(
                select(ParentLinkCode.id).where(
                    and_(
                        ParentLinkCode.code == code,
                        ParentLinkCode.consumed == False,  # noqa: E712
                        ParentLinkCode.expires_at > now,
                    )
                )
            )
            if existing.first() is None:
                return code
        raise ValueError("Benzersiz bağlantı kodu üretilemedi, tekrar deneyin")

    async def generate_link_code(self, student_id: str) -> dict[str, Any]:
        """Öğrenci için 6-hane kısa-ömürlü bağlantı kodu üret (10 dk geçerli).

        Öğrencinin önceki tüketilmemiş kodları geçersiz kılınır (tek aktif kod).

        Args:
            student_id: Kodu üreten öğrencinin id'si.

        Returns:
            {"code": "<6-hane>", "expires_at": datetime} (tz-aware UTC).
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=10)

        # Önceki tüketilmemiş kodları geçersiz kıl (tek aktif kod invariantı).
        await self.db.execute(
            update(ParentLinkCode)
            .where(
                and_(
                    ParentLinkCode.student_id == student_id,
                    ParentLinkCode.consumed == False,  # noqa: E712
                )
            )
            .values(consumed=True, consumed_at=now)
        )

        code = await self._unique_link_code(now)

        row = ParentLinkCode(
            code=code,
            student_id=student_id,
            expires_at=expires_at,
            consumed=False,
        )
        self.db.add(row)
        await self.db.commit()
        return {"code": code, "expires_at": expires_at}

    async def verify_link_code(self, parent_id: str, code: str) -> dict[str, Any]:
        """Veli girdisi 6-hane kodu doğrula ve ilişkiyi başlat.

        Geçersiz/süresi geçmiş/tüketilmiş kod veya öğrenci-olmayan hedef →
        {"valid": False}. Geçerli → mevcut ilişki döndürülür ya da yeni
        ParentChild(approved=False) oluşturulup öğrenciye onay bildirimi gider,
        ardından kod tüketilir.

        Args:
            parent_id: Kodu giren velinin id'si.
            code: 6-hane bağlantı kodu.

        Returns:
            {"valid": False} VEYA
            {"valid": True, "child_name", "child_initials", "relation_id"}.
        """
        now = datetime.now(UTC)
        clean = (code or "").strip()

        result = await self.db.execute(
            select(ParentLinkCode).where(
                and_(
                    ParentLinkCode.code == clean,
                    ParentLinkCode.consumed == False,  # noqa: E712
                    ParentLinkCode.expires_at > now,
                )
            )
        )
        link = result.scalar_one_or_none()
        if link is None:
            return {"valid": False}

        # Öğrenciyi çöz — sadece STUDENT hesabı ile ilişki kurulabilir.
        child_result = await self.db.execute(
            select(User).where(User.id == link.student_id)
        )
        child = child_result.scalar_one_or_none()
        if child is None or child.role != UserRole.STUDENT:
            return {"valid": False}

        # Mevcut ilişki varsa onu kullan, yoksa oluştur (approved=False) + bildir.
        existing = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == child.id,
                )
            )
        )
        relation = existing.scalar_one_or_none()
        if relation is None:
            relation = ParentChildRelation(
                parent_id=parent_id,
                child_id=child.id,
                relation_type="parent",
                approved=False,
            )
            self.db.add(relation)
            await self.db.flush()  # relation.id
            await self._send_approval_request_notification(child.id, parent_id)

        # Kodu tüket (tek kullanımlık).
        link.consumed = True
        link.consumed_at = now
        await self.db.commit()

        return {
            "valid": True,
            "child_name": f"{child.first_name} {child.last_name}",
            "child_initials": compute_initials(child.first_name, child.last_name),
            "relation_id": str(relation.id),
        }

    async def approve_parent_child_relation(
        self, child_id: str, relation_id: int, approved: bool
    ) -> bool:
        """Veli-çocuk ilişkisini onayla/reddet"""

        result = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.id == relation_id,
                    ParentChildRelation.child_id == child_id,
                    ParentChildRelation.approved == False,  # noqa: E712
                )
            )
        )
        relation = result.scalar_one_or_none()

        if not relation:
            raise ValueError("Onay bekleyen ilişki bulunamadı")

        if approved:
            relation.approved = True
            relation.approved_at = datetime.now(UTC)

            # Veliye onay bildirimi gönder
            await self._send_approval_confirmation_notification(
                relation.parent_id, child_id, True
            )
        else:
            # İlişkiyi sil (reddedildi)
            await self.db.delete(relation)

            # Veliye red bildirimi gönder
            await self._send_approval_confirmation_notification(
                relation.parent_id, child_id, False
            )

        await self.db.commit()
        return True

    async def get_parent_children(
        self, parent_id: str
    ) -> list[ParentChildRelationResponse]:
        """Velinin çocuklarını getir - Raw SQL ile ORM mapper bypass"""
        from sqlalchemy import text

        result = await self.db.execute(
            text("""
                SELECT pc.id, pc.parent_id, pc.child_id, pc.approved,
                       pc.relation_type, pc.created_at, pc.approved_at,
                       u.email as child_email,
                       COALESCE(u.first_name || ' ' || u.last_name, u.email) as child_name
                FROM parent_child pc
                LEFT JOIN users u ON u.id = pc.child_id
                WHERE pc.parent_id = :parent_id AND pc.approved = TRUE
            """),
            {"parent_id": parent_id},
        )
        rows = result.fetchall()
        output = []
        for row in rows:
            output.append(
                ParentChildRelationResponse(
                    id=row.id,
                    parent_id=row.parent_id,
                    child_id=row.child_id,
                    child_name=row.child_name or "Bilinmeyen",
                    child_email=row.child_email or "",
                    relation_type=row.relation_type or "parent",
                    approved=row.approved,
                    created_at=row.created_at,
                    approved_at=row.approved_at,
                )
            )
        return output

    async def get_child_performance(
        self, parent_id: str, child_id: str
    ) -> ChildPerformanceData:
        """Çocuğun performans verilerini getir"""

        # İlişki kontrolü
        from sqlalchemy import text as _text

        rel_result = await self.db.execute(
            _text(
                "SELECT id FROM parent_child WHERE parent_id=:pid AND child_id=:cid AND approved=TRUE"
            ),
            {"pid": parent_id, "cid": child_id},
        )
        if not rel_result.fetchone():
            raise ValueError("Bu çocuğun verilerine erişim yetkiniz bulunmamaktadır")

        child_result = await self.db.execute(select(User).where(User.id == child_id))
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Çocuk bulunamadı")

        # Son 30 günün verilerini al
        now = datetime.now(UTC)
        thirty_days_ago = now - timedelta(days=30)

        # student_profiles.id == users.id olduğundan student_id = child_id
        # FIX 2026-04-02: user_id → student_id, score → raw_score
        exam_result = await self.db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.student_id == child_id,
                    ExamSession.completed_at >= thirty_days_ago,
                )
            )
        )
        exam_results = list(exam_result.scalars().all())

        # Performans hesaplamaları
        total_study_time = sum([r.duration_minutes or 0 for r in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([r.raw_score or 0 for r in exam_results]) / exams_taken
            if exams_taken > 0
            else 0.0
        )

        last_exam = (
            max(exam_results, key=lambda x: x.completed_at) if exam_results else None
        )

        # ExamSession tabanlı KPI'lar (saf yardımcılar)
        recent_exams = compute_recent_exams(exam_results)
        weekly_activity, week_total_hours = compute_weekly_activity(exam_results, now)
        net_change = compute_net_change(exam_results)
        current_streak = compute_current_streak(exam_results, now)
        exams_taken_delta = compute_exams_delta(exam_results, now)

        # StudentAnswer → question_bank: çözülen soru + ders bazlı doğruluk.
        # NOT: question_id FK'si zaten question_bank'e bağlı (legacy `questions`
        # tablosuna değil). Kalite/is_active filtresi UYGULANMAZ: bu, öğrencinin
        # GERÇEK geçmiş performansını ölçen bir istatistik yolu — status filtresi
        # cevapların çoğunu (unverified/pending) düşürüp doğruluğu çarpıtırdı.
        answers_stmt = (
            select(
                QuestionMetadata.subject_area,
                StudentAnswer.selected_answer,
                StudentAnswer.is_correct,
                StudentAnswer.answered_at,
            )
            .join(ExamSession, StudentAnswer.exam_session_id == ExamSession.id)
            .join(QuestionBankItem, StudentAnswer.question_id == QuestionBankItem.id)
            .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
            .where(ExamSession.student_id == child_id)
        )
        answer_rows = (await self.db.execute(answers_stmt)).all()

        subj_correct: dict[str, int] = defaultdict(int)
        subj_total: dict[str, int] = defaultdict(int)
        answered_dates: list = []
        solved_questions = 0
        for subject_area, selected_answer, is_correct, answered_at in answer_rows:
            if selected_answer is not None:  # gerçekten cevaplanmış
                solved_questions += 1
                answered_dates.append(answered_at)
            if subject_area and is_correct is not None:  # notlanmış → doğruluk
                subj_total[subject_area] += 1
                if is_correct:
                    subj_correct[subject_area] += 1

        subject_stats = [(s, subj_correct[s], subj_total[s]) for s in subj_total]
        weak_subjects, strong_subjects, subject_progress = classify_subjects(
            subject_stats
        )
        solved_questions_delta = compute_solved_delta(answered_dates, now)

        # Aktif çalışma planı uyumu
        plan_result = await self.db.execute(
            select(StudyPlan)
            .options(selectinload(StudyPlan.weekly_goals))
            .where(
                and_(StudyPlan.student_id == child_id, StudyPlan.is_active == True)  # noqa: E712
            )
            .order_by(desc(StudyPlan.created_at))
        )
        active_plan = plan_result.scalars().first()
        plan_adherence = (
            compute_plan_adherence(active_plan.weekly_goals) if active_plan else None
        )

        recent_achievements = []
        if average_score > 85:
            recent_achievements.append("Yüksek ortalama başarısı")
        if exams_taken > 10:
            recent_achievements.append("Düzenli sınav çözme alışkanlığı")

        return ChildPerformanceData(
            child_id=child_id,
            child_name=f"{child.first_name} {child.last_name}",
            total_study_time=total_study_time,
            exams_taken=exams_taken,
            average_score=round(average_score, 2),
            last_exam_date=last_exam.completed_at if last_exam else None,
            last_exam_score=last_exam.raw_score if last_exam else None,
            weak_subjects=weak_subjects,
            strong_subjects=strong_subjects,
            recent_achievements=recent_achievements,
            recent_exams=recent_exams,
            weekly_activity=weekly_activity,
            week_total_hours=week_total_hours,
            net_change=net_change,
            current_streak=current_streak,
            exams_taken_delta=exams_taken_delta,
            solved_questions=solved_questions,
            solved_questions_delta=solved_questions_delta,
            subject_progress=subject_progress,
            plan_adherence=plan_adherence,
        )

    async def generate_weekly_report(self, child_id: str) -> WeeklyReportData:
        """Haftalık rapor oluştur"""

        today = datetime.now(UTC)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        child_result = await self.db.execute(select(User).where(User.id == child_id))
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Çocuk bulunamadı")

        # FIX 2026-04-02: user_id → student_id, score → raw_score
        exam_result = await self.db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.student_id == child_id,
                    ExamSession.completed_at >= week_start,
                    ExamSession.completed_at <= week_end,
                )
            )
        )
        exam_results = exam_result.scalars().all()

        total_study_time = sum([r.duration_minutes or 0 for r in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([r.raw_score or 0 for r in exam_results]) / exams_taken
            if exams_taken > 0
            else 0.0
        )

        subjects_studied = ["Matematik", "Türkçe", "Fen"] if exams_taken > 0 else []

        achievements = []
        if average_score > 80:
            achievements.append("Bu hafta yüksek ortalama yakaladı")
        if exams_taken >= 5:
            achievements.append("Düzenli çalışma alışkanlığı gösterdi")

        performance_trend = "stable"
        if average_score > 75:
            performance_trend = "improving"
        elif average_score < 50:
            performance_trend = "declining"

        recommendations = []
        if average_score < 60:
            recommendations.append("Zayıf konularda ek çalışma yapması önerilir")
        if exams_taken < 3:
            recommendations.append("Daha fazla deneme sınavı çözmesi faydalı olacaktır")

        # Veritabanına kaydet
        weekly_report = WeeklyReport(
            child_id=child_id,
            week_start=week_start,
            week_end=week_end,
            total_study_time=total_study_time,
            exams_taken=exams_taken,
            average_score=average_score,
            subjects_studied=json.dumps(subjects_studied),
            achievements=json.dumps(achievements),
        )

        self.db.add(weekly_report)
        await self.db.commit()

        return WeeklyReportData(
            child_id=child_id,
            child_name=f"{child.first_name} {child.last_name}",
            week_start=week_start,
            week_end=week_end,
            total_study_time=total_study_time,
            exams_taken=exams_taken,
            average_score=round(average_score, 2),
            subjects_studied=subjects_studied,
            achievements=achievements,
            performance_trend=performance_trend,
            recommendations=recommendations,
        )

    async def create_notification(
        self, parent_id: str, notification_data: ParentNotificationCreate
    ) -> ParentNotificationResponse:
        """Veli bildirimi oluştur"""

        # İlişki kontrolü
        rel_result = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == notification_data.child_id,
                    ParentChildRelation.approved == True,  # noqa: E712
                )
            )
        )
        if not rel_result.scalar_one_or_none():
            raise ValueError(
                "Bu çocuk için bildirim oluşturma yetkiniz bulunmamaktadır"
            )

        child_result = await self.db.execute(
            select(User).where(User.id == notification_data.child_id)
        )
        child = child_result.scalar_one_or_none()

        notification = ParentNotification(
            parent_id=parent_id,
            child_id=notification_data.child_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return ParentNotificationResponse(
            id=notification.id,
            child_id=notification.child_id,
            child_name=child.full_name if child else "Bilinmeyen",
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )

    async def get_parent_notifications(
        self, parent_id: str, unread_only: bool = False
    ) -> list[ParentNotificationResponse]:
        """
        Veli bildirimlerini getir
        PERFORMANCE FIX: Eager loading ile N+1 query önlendi
        """

        stmt = (
            select(ParentNotification)
            .options(selectinload(ParentNotification.child))
            .where(ParentNotification.parent_id == parent_id)
            .order_by(desc(ParentNotification.created_at))
        )

        if unread_only:
            stmt = stmt.where(ParentNotification.is_read == False)  # noqa: E712

        result = await self.db.execute(stmt)
        notifications = result.scalars().all()

        output = []
        for notification in notifications:
            child = notification.child
            output.append(
                ParentNotificationResponse(
                    id=notification.id,
                    child_id=notification.child_id,
                    child_name=f"{child.first_name} {child.last_name}"
                    if child
                    else "Bilinmeyen",
                    title=notification.title,
                    message=notification.message,
                    notification_type=notification.notification_type,
                    is_read=notification.is_read,
                    created_at=notification.created_at,
                    read_at=notification.read_at,
                )
            )

        return output

    async def mark_notification_as_read(
        self, parent_id: str, notification_id: int
    ) -> bool:
        """Bildirimi okundu olarak işaretle"""

        result = await self.db.execute(
            select(ParentNotification).where(
                and_(
                    ParentNotification.id == notification_id,
                    ParentNotification.parent_id == parent_id,
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Bildirim bulunamadı")

        notification.is_read = True
        notification.read_at = datetime.now(UTC)

        await self.db.commit()
        return True

    async def get_parent_dashboard_data(self, parent_id: str) -> ParentDashboardData:
        """Veli dashboard verilerini getir"""

        children_relations = await self.get_parent_children(parent_id)
        children_performance = []

        for relation in children_relations:
            try:
                performance = await self.get_child_performance(
                    parent_id, relation.child_id
                )
                children_performance.append(performance)
            except Exception:  # nosec B112 - tek cocugun sorgu hatasi tum paneli dusurmemeli
                continue

        unread_notifications = await self.get_parent_notifications(
            parent_id, unread_only=True
        )

        recent_notifications = await self.get_parent_notifications(parent_id)
        recent_notifications = recent_notifications[:5]

        weekly_summary = {
            "total_children": len(children_relations),
            "active_children": len(
                [c for c in children_performance if c.exams_taken > 0]
            ),
            "average_performance": sum([c.average_score for c in children_performance])
            / len(children_performance)
            if children_performance
            else 0,
        }

        # Bekleyen onaylar
        pending_result = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.approved == False,  # noqa: E712
                )
            )
        )
        pending_approvals = pending_result.scalars().all()

        pending_list = []
        for relation in pending_approvals:
            if relation.child_id:
                child_result = await self.db.execute(
                    select(User).where(User.id == relation.child_id)
                )
                pending_child = child_result.scalar_one_or_none()
                pending_list.append(
                    ParentChildRelationResponse(
                        id=relation.id,
                        parent_id=relation.parent_id,
                        child_id=relation.child_id,
                        child_name=f"{pending_child.first_name} {pending_child.last_name}"
                        if pending_child
                        else "Bilinmeyen",
                        child_email=pending_child.email if pending_child else "",
                        relation_type=relation.relation_type,
                        approved=relation.approved,
                        created_at=relation.created_at,
                        approved_at=relation.approved_at,
                    )
                )

        return ParentDashboardData(
            children=children_performance,
            unread_notifications=len(unread_notifications),
            recent_notifications=recent_notifications,
            weekly_summary=weekly_summary,
            pending_approvals=pending_list,
        )

    async def _send_approval_request_notification(
        self, child_id: str, parent_id: str
    ) -> None:
        """Onay isteği bildirimi gönder"""
        # Çocuğa sistem bildirimi gönder (basit implementasyon)
        # Gerçek uygulamada email/SMS gönderilebilir

    async def _send_approval_confirmation_notification(
        self, parent_id: str, child_id: str, approved: bool
    ) -> None:
        """Onay sonucu bildirimi gönder"""
        child_result = await self.db.execute(select(User).where(User.id == child_id))
        child = child_result.scalar_one_or_none()
        if not child:
            return

        title = "Veli İlişkisi Onaylandı" if approved else "Veli İlişkisi Reddedildi"
        action = "onaylandı" if approved else "reddedildi"
        message = f"{child.first_name} {child.last_name} ile veli ilişkiniz {action}."

        notification = ParentNotification(
            parent_id=parent_id,
            child_id=child_id,
            title=title,
            message=message,
            notification_type="approval",
        )

        self.db.add(notification)
        await self.db.commit()
