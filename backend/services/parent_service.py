"""
Veli (Parent) servis katmanı
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database import ExamSession, User
from models.parent import (
    ChildPerformanceData,
    ParentChildRelation,
    ParentChildRelationCreate,
    ParentChildRelationResponse,
    ParentDashboardData,
    ParentNotification,
    ParentNotificationCreate,
    ParentNotificationResponse,
    WeeklyReport,
    WeeklyReportData,
)


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

        if child.role != "student":
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
            child_name=child.full_name,
            child_email=child.email,
            relation_type=new_relation.relation_type,
            approved=new_relation.approved,
            created_at=new_relation.created_at,
            approved_at=new_relation.approved_at,
        )

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
        """
        Velinin çocuklarını getir
        PERFORMANCE FIX: Eager loading ile N+1 query önlendi
        """

        result = await self.db.execute(
            select(ParentChildRelation)
            .options(selectinload(ParentChildRelation.child))
            .where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.approved == True,  # noqa: E712
                )
            )
        )
        relations = result.scalars().all()

        output = []
        for relation in relations:
            child = relation.child
            if child:
                output.append(
                    ParentChildRelationResponse(
                        id=relation.id,
                        parent_id=relation.parent_id,
                        child_id=relation.child_id,
                        child_name=child.full_name,
                        child_email=child.email,
                        relation_type=relation.relation_type,
                        approved=relation.approved,
                        created_at=relation.created_at,
                        approved_at=relation.approved_at,
                    )
                )

        return output

    async def get_child_performance(
        self, parent_id: str, child_id: str
    ) -> ChildPerformanceData:
        """Çocuğun performans verilerini getir"""

        # İlişki kontrolü
        rel_result = await self.db.execute(
            select(ParentChildRelation).where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == child_id,
                    ParentChildRelation.approved == True,  # noqa: E712
                )
            )
        )
        if not rel_result.scalar_one_or_none():
            raise ValueError("Bu çocuğun verilerine erişim yetkiniz bulunmamaktadır")

        child_result = await self.db.execute(select(User).where(User.id == child_id))
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Çocuk bulunamadı")

        # Son 30 günün verilerini al
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        exam_result = await self.db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.user_id == child_id,
                    ExamSession.completed_at >= thirty_days_ago,
                )
            )
        )
        exam_results = exam_result.scalars().all()

        # Performans hesaplamaları
        total_study_time = sum([r.duration_minutes for r in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([r.score for r in exam_results]) / exams_taken
            if exams_taken > 0
            else 0.0
        )

        last_exam = (
            max(exam_results, key=lambda x: x.completed_at) if exam_results else None
        )

        # Konu analizi (basit implementasyon)
        weak_subjects = ["Matematik", "Fizik"] if average_score < 60 else []
        strong_subjects = ["Türkçe", "Tarih"] if average_score > 80 else []

        recent_achievements = []
        if average_score > 85:
            recent_achievements.append("Yüksek ortalama başarısı")
        if exams_taken > 10:
            recent_achievements.append("Düzenli sınav çözme alışkanlığı")

        return ChildPerformanceData(
            child_id=child_id,
            child_name=child.full_name,
            total_study_time=total_study_time,
            exams_taken=exams_taken,
            average_score=round(average_score, 2),
            last_exam_date=last_exam.completed_at if last_exam else None,
            last_exam_score=last_exam.score if last_exam else None,
            weak_subjects=weak_subjects,
            strong_subjects=strong_subjects,
            recent_achievements=recent_achievements,
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

        exam_result = await self.db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.user_id == child_id,
                    ExamSession.completed_at >= week_start,
                    ExamSession.completed_at <= week_end,
                )
            )
        )
        exam_results = exam_result.scalars().all()

        total_study_time = sum([r.duration_minutes for r in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([r.score for r in exam_results]) / exams_taken
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
            child_name=child.full_name,
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
                    child_name=child.full_name if child else "Bilinmeyen",
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
            except Exception:
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
            select(ParentChildRelation)
            .options(selectinload(ParentChildRelation.child))
            .where(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.approved == False,  # noqa: E712
                )
            )
        )
        pending_approvals = pending_result.scalars().all()

        pending_list = []
        for relation in pending_approvals:
            child = relation.child
            if child:
                pending_list.append(
                    ParentChildRelationResponse(
                        id=relation.id,
                        parent_id=relation.parent_id,
                        child_id=relation.child_id,
                        child_name=child.full_name,
                        child_email=child.email,
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
        message = f"{child.full_name} ile veli ilişkiniz {action}."

        notification = ParentNotification(
            parent_id=parent_id,
            child_id=child_id,
            title=title,
            message=message,
            notification_type="approval",
        )

        self.db.add(notification)
        await self.db.commit()
