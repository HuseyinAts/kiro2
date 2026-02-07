"""
Uzman İnceleme Kuyruğu Sistemi

Human-in-the-loop review sistemi. Üretilen soruların uzmanlar tarafından
incelenmesi ve onaylanması için kuyruk yönetimi sağlar.

Requirements: REQ-48.57 - REQ-48.60
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ReviewStatus(Enum):
    """İnceleme durumu"""

    PENDING = "pending"  # İnceleme bekliyor
    IN_REVIEW = "in_review"  # İnceleniyor
    APPROVED = "approved"  # Onaylandı
    REJECTED = "rejected"  # Reddedildi
    NEEDS_REVISION = "needs_revision"  # Revizyon gerekiyor


class ReviewPriority(Enum):
    """İnceleme önceliği"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ReviewItem:
    """İnceleme öğesi"""

    id: str
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str]
    subject: str
    difficulty_level: str
    quality_score: float
    status: ReviewStatus
    priority: ReviewPriority
    assigned_to: Optional[str] = None  # Uzman ID
    created_at: datetime = field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    feedback: List[str] = field(default_factory=list)
    reviewer_comments: Optional[str] = None
    revision_count: int = 0


@dataclass
class ExpertProfile:
    """Uzman profili"""

    id: str
    name: str
    email: str
    expertise_subjects: List[str]  # Uzmanlık alanları
    max_concurrent_reviews: int = 10  # Aynı anda maksimum inceleme sayısı
    current_review_count: int = 0
    total_reviews_completed: int = 0
    average_review_time_minutes: float = 0.0
    approval_rate: float = 0.0  # Onaylama oranı


class ExpertReviewQueue:
    """
    Uzman inceleme kuyruğu sistemi

    REQ-48.57: Human-in-the-loop review system
    REQ-48.58: Review assignment algorithm (uzmanlık alanına göre)
    REQ-48.59: Feedback collection interface
    REQ-48.60: Onaylanan soruları soru bankasına ekleme
    """

    def __init__(self):
        """Kuyruk sistemini başlat"""
        self.review_queue: List[ReviewItem] = []
        self.experts: Dict[str, ExpertProfile] = {}
        self.completed_reviews: List[ReviewItem] = []

    def add_to_queue(
        self,
        question_id: str,
        question_text: str,
        options: List[str],
        correct_answer: int,
        explanation: Optional[str],
        subject: str,
        difficulty_level: str,
        quality_score: float,
        priority: ReviewPriority = ReviewPriority.MEDIUM,
    ) -> ReviewItem:
        """
        Soruyu inceleme kuyruğuna ekle (REQ-48.57)

        Args:
            question_id: Soru ID
            question_text: Soru metni
            options: Şıklar
            correct_answer: Doğru cevap indeksi
            explanation: Açıklama
            subject: Ders/konu
            difficulty_level: Zorluk seviyesi
            quality_score: Otomatik kalite skoru
            priority: İnceleme önceliği

        Returns:
            ReviewItem: Oluşturulan inceleme öğesi
        """
        review_item = ReviewItem(
            id=str(uuid.uuid4()),
            question_id=question_id,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            subject=subject,
            difficulty_level=difficulty_level,
            quality_score=quality_score,
            status=ReviewStatus.PENDING,
            priority=priority,
        )

        self.review_queue.append(review_item)

        # Otomatik atama dene
        self._try_auto_assign(review_item)

        return review_item

    def register_expert(
        self,
        expert_id: str,
        name: str,
        email: str,
        expertise_subjects: List[str],
        max_concurrent_reviews: int = 10,
    ) -> ExpertProfile:
        """
        Uzman kaydı oluştur

        Args:
            expert_id: Uzman ID
            name: İsim
            email: E-posta
            expertise_subjects: Uzmanlık alanları (örn: ["Matematik", "Fizik"])
            max_concurrent_reviews: Maksimum eşzamanlı inceleme sayısı

        Returns:
            ExpertProfile: Uzman profili
        """
        expert = ExpertProfile(
            id=expert_id,
            name=name,
            email=email,
            expertise_subjects=expertise_subjects,
            max_concurrent_reviews=max_concurrent_reviews,
        )

        self.experts[expert_id] = expert
        return expert

    def assign_to_expert(self, review_id: str, expert_id: str) -> bool:
        """
        İncelemeyi uzmana ata (REQ-48.58)

        Args:
            review_id: İnceleme ID
            expert_id: Uzman ID

        Returns:
            bool: Atama başarılı mı?
        """
        # İnceleme öğesini bul
        review_item = self._find_review_item(review_id)
        if not review_item:
            return False

        # Uzmanı bul
        expert = self.experts.get(expert_id)
        if not expert:
            return False

        # Uzman kapasitesi kontrolü
        if expert.current_review_count >= expert.max_concurrent_reviews:
            return False

        # Atama yap
        review_item.assigned_to = expert_id
        review_item.assigned_at = datetime.now()
        review_item.status = ReviewStatus.IN_REVIEW
        expert.current_review_count += 1

        return True

    def _try_auto_assign(self, review_item: ReviewItem) -> bool:
        """
        Otomatik uzman ataması dene (REQ-48.58)

        Uzmanlık alanına göre en uygun uzmanı seç.
        """
        # Konuya uygun uzmanları bul
        suitable_experts = [
            expert
            for expert in self.experts.values()
            if review_item.subject in expert.expertise_subjects
            and expert.current_review_count < expert.max_concurrent_reviews
        ]

        if not suitable_experts:
            return False

        # En az yüklü uzmanı seç
        best_expert = min(suitable_experts, key=lambda e: e.current_review_count)

        return self.assign_to_expert(review_item.id, best_expert.id)

    def submit_review(
        self,
        review_id: str,
        expert_id: str,
        status: ReviewStatus,
        reviewer_comments: Optional[str] = None,
        feedback: Optional[List[str]] = None,
    ) -> bool:
        """
        İnceleme sonucunu gönder (REQ-48.59)

        Args:
            review_id: İnceleme ID
            expert_id: Uzman ID
            status: Yeni durum (APPROVED, REJECTED, NEEDS_REVISION)
            reviewer_comments: Uzman yorumları
            feedback: Geri bildirim listesi

        Returns:
            bool: Gönderim başarılı mı?
        """
        # İnceleme öğesini bul
        review_item = self._find_review_item(review_id)
        if not review_item:
            return False

        # Uzman kontrolü
        if review_item.assigned_to != expert_id:
            return False

        # Uzmanı bul
        expert = self.experts.get(expert_id)
        if not expert:
            return False

        # İnceleme sonucunu kaydet
        review_item.status = status
        review_item.reviewed_at = datetime.now()
        review_item.reviewer_comments = reviewer_comments

        if feedback:
            review_item.feedback.extend(feedback)

        # Uzman istatistiklerini güncelle
        expert.current_review_count -= 1
        expert.total_reviews_completed += 1

        # Ortalama inceleme süresini güncelle
        if review_item.assigned_at:
            review_time = (
                review_item.reviewed_at - review_item.assigned_at
            ).total_seconds() / 60
            expert.average_review_time_minutes = (
                expert.average_review_time_minutes
                * (expert.total_reviews_completed - 1)
                + review_time
            ) / expert.total_reviews_completed

        # Onaylama oranını güncelle
        if status == ReviewStatus.APPROVED:
            approved_count = (
                sum(
                    1
                    for r in self.completed_reviews
                    if r.assigned_to == expert_id and r.status == ReviewStatus.APPROVED
                )
                + 1
            )
            expert.approval_rate = approved_count / expert.total_reviews_completed

        # Onaylanmışsa tamamlanmış listesine taşı (REQ-48.60)
        if status == ReviewStatus.APPROVED:
            self.review_queue.remove(review_item)
            self.completed_reviews.append(review_item)

        # Revizyon gerekiyorsa sayacı artır
        elif status == ReviewStatus.NEEDS_REVISION:
            review_item.revision_count += 1
            review_item.status = ReviewStatus.PENDING
            review_item.assigned_to = None
            review_item.assigned_at = None

        # Reddedilmişse kuyruktan çıkar
        elif status == ReviewStatus.REJECTED:
            self.review_queue.remove(review_item)
            self.completed_reviews.append(review_item)

        return True

    def get_pending_reviews(
        self, subject: Optional[str] = None, priority: Optional[ReviewPriority] = None
    ) -> List[ReviewItem]:
        """
        Bekleyen incelemeleri getir

        Args:
            subject: Konu filtresi (opsiyonel)
            priority: Öncelik filtresi (opsiyonel)

        Returns:
            Bekleyen inceleme listesi
        """
        reviews = [r for r in self.review_queue if r.status == ReviewStatus.PENDING]

        if subject:
            reviews = [r for r in reviews if r.subject == subject]

        if priority:
            reviews = [r for r in reviews if r.priority == priority]

        # Önceliğe göre sırala
        reviews.sort(key=lambda r: (r.priority.value, r.created_at), reverse=True)

        return reviews

    def get_expert_reviews(
        self, expert_id: str, status: Optional[ReviewStatus] = None
    ) -> List[ReviewItem]:
        """
        Uzmanın incelemelerini getir

        Args:
            expert_id: Uzman ID
            status: Durum filtresi (opsiyonel)

        Returns:
            İnceleme listesi
        """
        reviews = [r for r in self.review_queue if r.assigned_to == expert_id]

        if status:
            reviews = [r for r in reviews if r.status == status]

        return reviews

    def get_approved_questions(
        self, subject: Optional[str] = None, since: Optional[datetime] = None
    ) -> List[ReviewItem]:
        """
        Onaylanmış soruları getir (REQ-48.60)

        Args:
            subject: Konu filtresi (opsiyonel)
            since: Tarih filtresi (opsiyonel)

        Returns:
            Onaylanmış soru listesi
        """
        approved = [
            r for r in self.completed_reviews if r.status == ReviewStatus.APPROVED
        ]

        if subject:
            approved = [r for r in approved if r.subject == subject]

        if since:
            approved = [r for r in approved if r.reviewed_at and r.reviewed_at >= since]

        return approved

    def get_queue_statistics(self) -> Dict:
        """
        Kuyruk istatistiklerini getir

        Returns:
            İstatistik dictionary
        """
        total_pending = sum(
            1 for r in self.review_queue if r.status == ReviewStatus.PENDING
        )
        total_in_review = sum(
            1 for r in self.review_queue if r.status == ReviewStatus.IN_REVIEW
        )
        total_approved = sum(
            1 for r in self.completed_reviews if r.status == ReviewStatus.APPROVED
        )
        total_rejected = sum(
            1 for r in self.completed_reviews if r.status == ReviewStatus.REJECTED
        )

        # Ortalama inceleme süresi
        review_times = []
        for review in self.completed_reviews:
            if review.assigned_at and review.reviewed_at:
                time_diff = (
                    review.reviewed_at - review.assigned_at
                ).total_seconds() / 60
                review_times.append(time_diff)

        avg_review_time = sum(review_times) / len(review_times) if review_times else 0.0

        # Onaylama oranı
        total_reviewed = total_approved + total_rejected
        approval_rate = (
            (total_approved / total_reviewed * 100) if total_reviewed > 0 else 0.0
        )

        return {
            "total_pending": total_pending,
            "total_in_review": total_in_review,
            "total_approved": total_approved,
            "total_rejected": total_rejected,
            "total_reviewed": total_reviewed,
            "approval_rate_percent": round(approval_rate, 2),
            "average_review_time_minutes": round(avg_review_time, 2),
            "total_experts": len(self.experts),
            "active_experts": sum(
                1 for e in self.experts.values() if e.current_review_count > 0
            ),
        }

    def get_expert_statistics(self, expert_id: str) -> Optional[Dict]:
        """
        Uzman istatistiklerini getir

        Args:
            expert_id: Uzman ID

        Returns:
            İstatistik dictionary veya None
        """
        expert = self.experts.get(expert_id)
        if not expert:
            return None

        return {
            "expert_id": expert.id,
            "name": expert.name,
            "expertise_subjects": expert.expertise_subjects,
            "current_review_count": expert.current_review_count,
            "total_reviews_completed": expert.total_reviews_completed,
            "average_review_time_minutes": round(expert.average_review_time_minutes, 2),
            "approval_rate_percent": round(expert.approval_rate * 100, 2),
            "capacity_utilization_percent": round(
                (expert.current_review_count / expert.max_concurrent_reviews) * 100, 2
            ),
        }

    def _find_review_item(self, review_id: str) -> Optional[ReviewItem]:
        """İnceleme öğesini bul"""
        for review in self.review_queue:
            if review.id == review_id:
                return review
        return None

    def export_approved_to_question_bank(
        self, since: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Onaylanmış soruları soru bankası formatında dışa aktar (REQ-48.60)

        Args:
            since: Tarih filtresi (opsiyonel)

        Returns:
            Soru bankası formatında soru listesi
        """
        approved_questions = self.get_approved_questions(since=since)

        question_bank_format = []
        for review in approved_questions:
            question = {
                "id": review.question_id,
                "question_text": review.question_text,
                "options": review.options,
                "correct_answer": review.correct_answer,
                "explanation": review.explanation,
                "subject": review.subject,
                "difficulty_level": review.difficulty_level,
                "quality_score": review.quality_score,
                "reviewed_by": review.assigned_to,
                "reviewed_at": review.reviewed_at.isoformat()
                if review.reviewed_at
                else None,
                "reviewer_comments": review.reviewer_comments,
                "revision_count": review.revision_count,
            }
            question_bank_format.append(question)

        return question_bank_format
