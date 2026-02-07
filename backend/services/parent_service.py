# -*- coding: utf-8 -*-
"""
Veli (Parent) servis katmanı
Türkiye Üniversite Sınavları Hazırlık Platformu için veli takip sistemi
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List

from models.database import ExamSession
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
from models.database import User
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload


class ParentService:
    """Veli takip sistemi servis sınıfı"""

    def __init__(self, db: Session):
        self.db = db

    async def create_parent_child_relation(
        self, parent_id: int, relation_data: ParentChildRelationCreate
    ) -> ParentChildRelationResponse:
        """Veli-çocuk ilişkisi oluştur"""

        # Çocuğu email ile bul
        child = (
            self.db.query(User).filter(User.email == relation_data.child_email).first()
        )

        if not child:
            raise ValueError("Belirtilen email adresine sahip öğrenci bulunamadı")

        if child.role != "student":
            raise ValueError("Sadece öğrenci hesapları ile ilişki kurulabilir")

        # Mevcut ilişki kontrolü
        existing_relation = (
            self.db.query(ParentChildRelation)
            .filter(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == child.id,
                )
            )
            .first()
        )

        if existing_relation:
            raise ValueError("Bu öğrenci ile zaten bir ilişkiniz bulunmaktadır")

        # Yeni ilişki oluştur
        new_relation = ParentChildRelation(
            parent_id=parent_id,
            child_id=child.id,
            relation_type=relation_data.relation_type,
            approved=False,  # Onay bekliyor
        )

        self.db.add(new_relation)
        self.db.commit()
        self.db.refresh(new_relation)

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
        self, child_id: int, relation_id: int, approved: bool
    ) -> bool:
        """Veli-çocuk ilişkisini onayla/reddet"""

        relation = (
            self.db.query(ParentChildRelation)
            .filter(
                and_(
                    ParentChildRelation.id == relation_id,
                    ParentChildRelation.child_id == child_id,
                    ParentChildRelation.approved == False,
                )
            )
            .first()
        )

        if not relation:
            raise ValueError("Onay bekleyen ilişki bulunamadı")

        if approved:
            relation.approved = True
            relation.approved_at = datetime.now(timezone.utc)

            # Veliye onay bildirimi gönder
            await self._send_approval_confirmation_notification(
                relation.parent_id, child_id, True
            )
        else:
            # İlişkiyi sil (reddedildi)
            self.db.delete(relation)

            # Veliye red bildirimi gönder
            await self._send_approval_confirmation_notification(
                relation.parent_id, child_id, False
            )

        self.db.commit()
        return True

    async def get_parent_children(
        self, parent_id: int
    ) -> List[ParentChildRelationResponse]:
        """
        Velinin çocuklarını getir
        PERFORMANCE FIX: Eager loading ile N+1 query önlendi
        """

        # PERFORMANCE FIX: child'ı eager load et (N+1 engellendi)
        relations = (
            self.db.query(ParentChildRelation)
            .options(joinedload(ParentChildRelation.child))
            .filter(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.approved == True,
                )
            )
            .all()
        )

        result = []
        for relation in relations:
            # child zaten yüklü (joinedload sayesinde)
            child = relation.child
            if child:
                result.append(
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

        return result

    async def get_child_performance(
        self, parent_id: int, child_id: int
    ) -> ChildPerformanceData:
        """Çocuğun performans verilerini getir"""

        # İlişki kontrolü
        relation = (
            self.db.query(ParentChildRelation)
            .filter(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == child_id,
                    ParentChildRelation.approved == True,
                )
            )
            .first()
        )

        if not relation:
            raise ValueError("Bu çocuğun verilerine erişim yetkiniz bulunmamaktadır")

        child = self.db.query(User).filter(User.id == child_id).first()
        if not child:
            raise ValueError("Çocuk bulunamadı")

        # Son 30 günün verilerini al
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # Sınav sonuçları
        exam_results = (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.user_id == child_id,
                    ExamSession.completed_at >= thirty_days_ago,
                )
            )
            .all()
        )

        # Performans hesaplamaları
        total_study_time = sum([result.duration_minutes for result in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([result.score for result in exam_results]) / exams_taken
            if exams_taken > 0
            else 0.0
        )

        # Son sınav bilgileri
        last_exam = (
            max(exam_results, key=lambda x: x.completed_at) if exam_results else None
        )

        # Konu analizi (basit implementasyon)
        weak_subjects = ["Matematik", "Fizik"] if average_score < 60 else []
        strong_subjects = ["Türkçe", "Tarih"] if average_score > 80 else []

        # Son başarılar
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

    async def generate_weekly_report(self, child_id: int) -> WeeklyReportData:
        """Haftalık rapor oluştur"""

        # Bu haftanın başlangıç ve bitiş tarihleri
        today = datetime.now(timezone.utc)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        child = self.db.query(User).filter(User.id == child_id).first()
        if not child:
            raise ValueError("Çocuk bulunamadı")

        # Bu haftanın sınav sonuçları
        exam_results = (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.user_id == child_id,
                    ExamSession.completed_at >= week_start,
                    ExamSession.completed_at <= week_end,
                )
            )
            .all()
        )

        # Haftalık istatistikler
        total_study_time = sum([result.duration_minutes for result in exam_results])
        exams_taken = len(exam_results)
        average_score = (
            sum([result.score for result in exam_results]) / exams_taken
            if exams_taken > 0
            else 0.0
        )

        # Çalışılan konular (basit implementasyon)
        subjects_studied = ["Matematik", "Türkçe", "Fen"] if exams_taken > 0 else []

        # Başarılar
        achievements = []
        if average_score > 80:
            achievements.append("Bu hafta yüksek ortalama yakaladı")
        if exams_taken >= 5:
            achievements.append("Düzenli çalışma alışkanlığı gösterdi")

        # Performans trendi (basit hesaplama)
        performance_trend = "stable"
        if average_score > 75:
            performance_trend = "improving"
        elif average_score < 50:
            performance_trend = "declining"

        # Öneriler
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
        self.db.commit()

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
        self, parent_id: int, notification_data: ParentNotificationCreate
    ) -> ParentNotificationResponse:
        """Veli bildirimi oluştur"""

        # İlişki kontrolü
        relation = (
            self.db.query(ParentChildRelation)
            .filter(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.child_id == notification_data.child_id,
                    ParentChildRelation.approved == True,
                )
            )
            .first()
        )

        if not relation:
            raise ValueError(
                "Bu çocuk için bildirim oluşturma yetkiniz bulunmamaktadır"
            )

        child = (
            self.db.query(User).filter(User.id == notification_data.child_id).first()
        )

        notification = ParentNotification(
            parent_id=parent_id,
            child_id=notification_data.child_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return ParentNotificationResponse(
            id=notification.id,
            child_id=notification.child_id,
            child_name=child.full_name,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )

    async def get_parent_notifications(
        self, parent_id: int, unread_only: bool = False
    ) -> List[ParentNotificationResponse]:
        """
        Veli bildirimlerini getir
        PERFORMANCE FIX: Eager loading ile N+1 query önlendi
        """

        # PERFORMANCE FIX: child'ı eager load et (N+1 engellendi)
        query = (
            self.db.query(ParentNotification)
            .options(joinedload(ParentNotification.child))
            .filter(ParentNotification.parent_id == parent_id)
        )

        if unread_only:
            query = query.filter(ParentNotification.is_read == False)

        notifications = query.order_by(desc(ParentNotification.created_at)).all()

        result = []
        for notification in notifications:
            # child zaten yüklü (joinedload sayesinde)
            child = notification.child
            result.append(
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

        return result

    async def mark_notification_as_read(
        self, parent_id: int, notification_id: int
    ) -> bool:
        """Bildirimi okundu olarak işaretle"""

        notification = (
            self.db.query(ParentNotification)
            .filter(
                and_(
                    ParentNotification.id == notification_id,
                    ParentNotification.parent_id == parent_id,
                )
            )
            .first()
        )

        if not notification:
            raise ValueError("Bildirim bulunamadı")

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    async def get_parent_dashboard_data(self, parent_id: int) -> ParentDashboardData:
        """Veli dashboard verilerini getir"""

        # Çocukları getir
        children_relations = await self.get_parent_children(parent_id)
        children_performance = []

        for relation in children_relations:
            try:
                performance = await self.get_child_performance(
                    parent_id, relation.child_id
                )
                children_performance.append(performance)
            except Exception:
                # Hata durumunda boş performans verisi ekle
                continue

        # Okunmamış bildirimler
        unread_notifications = await self.get_parent_notifications(
            parent_id, unread_only=True
        )

        # Son bildirimler (son 5)
        recent_notifications = await self.get_parent_notifications(parent_id)
        recent_notifications = recent_notifications[:5]

        # Haftalık özet
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
        # PERFORMANCE FIX: child'ı eager load et (N+1 engellendi)
        pending_approvals = (
            self.db.query(ParentChildRelation)
            .options(joinedload(ParentChildRelation.child))
            .filter(
                and_(
                    ParentChildRelation.parent_id == parent_id,
                    ParentChildRelation.approved == False,
                )
            )
            .all()
        )

        pending_list = []
        for relation in pending_approvals:
            # child zaten yüklü (joinedload sayesinde)
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

    async def _send_approval_request_notification(self, child_id: int, parent_id: int):
        """Onay isteği bildirimi gönder"""
        parent = self.db.query(User).filter(User.id == parent_id).first()

        # Çocuğa sistem bildirimi gönder (basit implementasyon)
        # Gerçek uygulamada email/SMS gönderilebilir

    async def _send_approval_confirmation_notification(
        self, parent_id: int, child_id: int, approved: bool
    ):
        """Onay sonucu bildirimi gönder"""
        child = self.db.query(User).filter(User.id == child_id).first()

        title = "Veli İlişkisi Onaylandı" if approved else "Veli İlişkisi Reddedildi"
        message = f"{child.full_name} ile veli ilişkiniz {'onaylandı' if approved else 'reddedildi'}."

        notification = ParentNotification(
            parent_id=parent_id,
            child_id=child_id,
            title=title,
            message=message,
            notification_type="approval",
        )

        self.db.add(notification)
        self.db.commit()
