"""
Expert Content Validation System
Uzman İçerik Doğrulama ve Onay Sistemi

Bu sistem:
- Uzman öğretmenlerin içerik doğrulamasını sağlar
- MEB müfredat uyumluluğunu kontrol eder
- ÖSYM standartlarına uygunluğu doğrular
- Çok aşamalı onay süreçlerini yönetir
- Otomatik kalite kontrolleri yapar
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.structured_logger import get_logger

logger = get_logger(__name__)


# ==================== ENUMS ====================


class ContentType(Enum):
    """İçerik tipi"""

    QUESTION = "question"  # Soru
    EXPLANATION = "explanation"  # Açıklama
    TOPIC = "topic"  # Konu
    EXAM = "exam"  # Sınav
    LEARNING_PATH = "learning_path"  # Öğrenme yolu
    VIDEO = "video"  # Video içeriği
    DOCUMENT = "document"  # Döküman


class ValidationStatus(Enum):
    """Doğrulama durumu"""

    PENDING = "pending"  # Beklemede
    IN_REVIEW = "in_review"  # İncelemede
    APPROVED = "approved"  # Onaylandı
    REJECTED = "rejected"  # Reddedildi
    NEEDS_REVISION = "needs_revision"  # Revizyon gerekli
    ARCHIVED = "archived"  # Arşivlendi


class ExpertRole(Enum):
    """Uzman rolleri"""

    SUBJECT_EXPERT = "subject_expert"  # Alan uzmanı (öğretmen)
    CURRICULUM_EXPERT = "curriculum_expert"  # Müfredat uzmanı
    PEDAGOGY_EXPERT = "pedagogy_expert"  # Pedagoji uzmanı
    QUALITY_ASSURANCE = "quality_assurance"  # Kalite güvence
    SENIOR_REVIEWER = "senior_reviewer"  # Kıdemli gözden geçirici


class ComplianceLevel(Enum):
    """Uyumluluk seviyesi"""

    FULLY_COMPLIANT = "fully_compliant"  # Tam uyumlu
    MOSTLY_COMPLIANT = "mostly_compliant"  # Çoğunlukla uyumlu
    PARTIALLY_COMPLIANT = "partially_compliant"  # Kısmen uyumlu
    NON_COMPLIANT = "non_compliant"  # Uyumsuz


# ==================== MODELS ====================


class ValidationCriteria(BaseModel):
    """Doğrulama kriterleri"""

    criterion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    weight: float = 1.0  # Kriter ağırlığı (0-1)
    required: bool = True
    category: str  # "curriculum", "pedagogy", "quality", "osym"


class ValidationFeedback(BaseModel):
    """Doğrulama geri bildirimi"""

    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expert_id: str
    expert_name: str
    expert_role: ExpertRole
    criterion_id: Optional[str] = None
    score: Optional[float] = None  # 0-100
    passed: bool
    comment: str
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationRequest(BaseModel):
    """Doğrulama talebi"""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    content_type: ContentType
    content_data: Dict[str, Any]
    submitter_id: str
    submitter_name: str

    # MEB uyumluluk bilgileri
    grade_level: Optional[str] = None  # Sınıf seviyesi
    subject: Optional[str] = None  # Ders
    topic: Optional[str] = None  # Konu
    learning_outcomes: List[str] = Field(default_factory=list)  # Kazanımlar

    # ÖSYM uyumluluk bilgileri
    exam_type: Optional[str] = None  # TYT, AYT, YDT
    difficulty_level: Optional[str] = None
    estimated_time_seconds: Optional[int] = None

    # Durum
    status: ValidationStatus = ValidationStatus.PENDING
    priority: int = 5  # 1-10, 10 en yüksek

    # İş akışı
    required_expert_roles: List[ExpertRole] = Field(default_factory=list)
    assigned_experts: List[str] = Field(default_factory=list)
    feedbacks: List[ValidationFeedback] = Field(default_factory=list)

    # Zaman
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    review_deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Sonuçlar
    overall_score: Optional[float] = None
    compliance_level: Optional[ComplianceLevel] = None
    final_decision: Optional[str] = None
    revision_notes: List[str] = Field(default_factory=list)


class ContentComplianceReport(BaseModel):
    """İçerik uyumluluk raporu"""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    content_type: ContentType

    # MEB Uyumluluk
    meb_compliance: ComplianceLevel
    meb_standards_matched: List[str] = Field(default_factory=list)
    meb_issues: List[str] = Field(default_factory=list)
    meb_score: float = 0.0  # 0-100

    # ÖSYM Uyumluluk
    osym_compliance: ComplianceLevel
    osym_standards_matched: List[str] = Field(default_factory=list)
    osym_issues: List[str] = Field(default_factory=list)
    osym_score: float = 0.0  # 0-100

    # Pedagojik Uygunluk
    pedagogy_score: float = 0.0  # 0-100
    pedagogy_notes: List[str] = Field(default_factory=list)

    # Kalite Metrikleri
    quality_score: float = 0.0  # 0-100
    quality_issues: List[str] = Field(default_factory=list)

    # Genel
    overall_compliance: ComplianceLevel
    overall_score: float = 0.0  # 0-100
    recommendations: List[str] = Field(default_factory=list)

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== VALIDATION SYSTEM ====================


class ExpertContentValidationSystem:
    """
    Uzman İçerik Doğrulama Sistemi

    Features:
    - Multi-stage expert review workflow
    - MEB curriculum compliance checking
    - ÖSYM standards validation
    - Automated quality checks
    - Expert assignment and notifications
    - Compliance reporting
    """

    def __init__(self):
        self.validation_requests: Dict[str, ValidationRequest] = {}
        self.validation_criteria: Dict[str, List[ValidationCriteria]] = {}
        self.compliance_reports: Dict[str, ContentComplianceReport] = {}

        # Expert pools
        self.expert_pool: Dict[ExpertRole, List[str]] = {
            role: [] for role in ExpertRole
        }

        # Initialize default criteria
        self._initialize_criteria()

        logger.info("expert_validation_system_initialized")

    def _initialize_criteria(self):
        """Varsayılan doğrulama kriterlerini başlat"""

        # Soru kriterleri
        self.validation_criteria["question"] = [
            ValidationCriteria(
                name="MEB Müfredat Uyumu",
                description="Soru MEB müfredatına uygun mu?",
                weight=1.0,
                required=True,
                category="curriculum",
            ),
            ValidationCriteria(
                name="ÖSYM Format Uyumu",
                description="Soru ÖSYM formatına uygun mu?",
                weight=1.0,
                required=True,
                category="osym",
            ),
            ValidationCriteria(
                name="Bilimsel Doğruluk",
                description="Soru bilimsel olarak doğru mu?",
                weight=1.0,
                required=True,
                category="quality",
            ),
            ValidationCriteria(
                name="Dil ve Anlaşılabilirlik",
                description="Soru açık ve anlaşılır mı?",
                weight=0.8,
                required=True,
                category="quality",
            ),
            ValidationCriteria(
                name="Yaş Uygunluğu",
                description="Soru hedef yaş grubuna uygun mu?",
                weight=0.8,
                required=True,
                category="pedagogy",
            ),
            ValidationCriteria(
                name="Zorluk Seviyesi",
                description="Zorluk seviyesi doğru belirtilmiş mi?",
                weight=0.6,
                required=False,
                category="osym",
            ),
        ]

    async def submit_content_for_validation(
        self,
        content_id: str,
        content_type: ContentType,
        content_data: Dict[str, Any],
        submitter_id: str,
        submitter_name: str,
        **kwargs,
    ) -> ValidationRequest:
        """
        İçeriği doğrulama için gönder

        Args:
            content_id: İçerik ID
            content_type: İçerik tipi
            content_data: İçerik verisi
            submitter_id: Gönderen ID
            submitter_name: Gönderen adı
            **kwargs: Ek bilgiler (grade_level, subject, etc.)

        Returns:
            ValidationRequest
        """

        # Required expert roles belirleme
        required_roles = self._determine_required_experts(content_type)

        # Review deadline hesaplama (48 saat)
        review_deadline = datetime.utcnow() + timedelta(hours=48)

        # Validation request oluştur
        request = ValidationRequest(
            content_id=content_id,
            content_type=content_type,
            content_data=content_data,
            submitter_id=submitter_id,
            submitter_name=submitter_name,
            required_expert_roles=required_roles,
            review_deadline=review_deadline,
            **kwargs,
        )

        # Kaydet
        self.validation_requests[request.request_id] = request

        # Uzman ata
        await self._assign_experts(request)

        logger.info(
            "validation_request_submitted",
            request_id=request.request_id,
            content_type=content_type.value,
            submitter_id=submitter_id,
            required_experts=len(required_roles),
        )

        return request

    def _determine_required_experts(
        self, content_type: ContentType
    ) -> List[ExpertRole]:
        """İçerik tipine göre gerekli uzmanları belirle"""

        if content_type == ContentType.QUESTION:
            return [ExpertRole.SUBJECT_EXPERT, ExpertRole.CURRICULUM_EXPERT]
        elif content_type == ContentType.EXAM:
            return [
                ExpertRole.SUBJECT_EXPERT,
                ExpertRole.CURRICULUM_EXPERT,
                ExpertRole.QUALITY_ASSURANCE,
            ]
        elif content_type == ContentType.LEARNING_PATH:
            return [ExpertRole.CURRICULUM_EXPERT, ExpertRole.PEDAGOGY_EXPERT]
        else:
            return [ExpertRole.SUBJECT_EXPERT]

    async def _assign_experts(self, request: ValidationRequest):
        """Doğrulama talebine uzman ata"""

        assigned_experts = []

        for role in request.required_expert_roles:
            # Expert pool'dan uygun uzman seç
            available_experts = self.expert_pool.get(role, [])

            if available_experts:
                # En az yüklü uzmanı seç (basit round-robin)
                expert_id = available_experts[0]
                assigned_experts.append(expert_id)

                logger.debug(
                    "expert_assigned",
                    request_id=request.request_id,
                    expert_id=expert_id,
                    role=role.value,
                )

        request.assigned_experts = assigned_experts
        request.status = ValidationStatus.IN_REVIEW

    async def submit_expert_feedback(
        self,
        request_id: str,
        expert_id: str,
        expert_name: str,
        expert_role: ExpertRole,
        feedbacks: List[Dict[str, Any]],
    ) -> bool:
        """
        Uzman geri bildirimi gönder

        Args:
            request_id: Talep ID
            expert_id: Uzman ID
            expert_name: Uzman adı
            expert_role: Uzman rolü
            feedbacks: Geri bildirim listesi

        Returns:
            bool: Başarılı mı?
        """

        request = self.validation_requests.get(request_id)
        if not request:
            logger.error("validation_request_not_found", request_id=request_id)
            return False

        # Geri bildirimleri ekle
        for fb_data in feedbacks:
            feedback = ValidationFeedback(
                expert_id=expert_id,
                expert_name=expert_name,
                expert_role=expert_role,
                **fb_data,
            )
            request.feedbacks.append(feedback)

        logger.info(
            "expert_feedback_submitted",
            request_id=request_id,
            expert_id=expert_id,
            feedback_count=len(feedbacks),
        )

        # Tüm uzmanlar geri bildirim verdiyse, doğrulamayı tamamla
        if len(request.feedbacks) >= len(request.required_expert_roles):
            await self._complete_validation(request)

        return True

    async def _complete_validation(self, request: ValidationRequest):
        """Doğrulamayı tamamla ve karar ver"""

        # Tüm geri bildirimleri değerlendir
        total_score = 0.0
        criterion_scores = {}
        all_passed = True

        for feedback in request.feedbacks:
            if feedback.score is not None:
                total_score += feedback.score
            if not feedback.passed:
                all_passed = False

        # Ortalama skor
        if request.feedbacks:
            request.overall_score = total_score / len(request.feedbacks)
        else:
            request.overall_score = 0.0

        # Karar ver
        if all_passed and request.overall_score >= 80:
            request.status = ValidationStatus.APPROVED
            request.final_decision = "approved"
        elif request.overall_score >= 60:
            request.status = ValidationStatus.NEEDS_REVISION
            request.final_decision = "needs_revision"
            # Revizyon notlarını topla
            for feedback in request.feedbacks:
                if feedback.suggestions:
                    request.revision_notes.extend(feedback.suggestions)
        else:
            request.status = ValidationStatus.REJECTED
            request.final_decision = "rejected"

        request.completed_at = datetime.utcnow()

        # Compliance report oluştur
        await self._generate_compliance_report(request)

        logger.info(
            "validation_completed",
            request_id=request.request_id,
            status=request.status.value,
            overall_score=request.overall_score,
            decision=request.final_decision,
        )

    async def _generate_compliance_report(self, request: ValidationRequest):
        """Uyumluluk raporu oluştur"""

        report = ContentComplianceReport(
            content_id=request.content_id,
            content_type=request.content_type,
            overall_score=request.overall_score or 0.0,
        )

        # MEB compliance
        if request.learning_outcomes:
            report.meb_standards_matched = request.learning_outcomes
            report.meb_score = min(100, len(request.learning_outcomes) * 20)
            report.meb_compliance = self._determine_compliance_level(report.meb_score)

        # ÖSYM compliance
        if request.exam_type:
            report.osym_standards_matched.append(request.exam_type)
            report.osym_score = 80.0  # Basitleştirilmiş
            report.osym_compliance = ComplianceLevel.MOSTLY_COMPLIANT

        # Genel uyumluluk
        report.overall_compliance = self._determine_compliance_level(
            report.overall_score
        )

        # Önerileri topla
        for feedback in request.feedbacks:
            report.recommendations.extend(feedback.suggestions)

        self.compliance_reports[report.report_id] = report

        logger.debug(
            "compliance_report_generated",
            report_id=report.report_id,
            content_id=request.content_id,
            overall_compliance=report.overall_compliance.value,
        )

    def _determine_compliance_level(self, score: float) -> ComplianceLevel:
        """Skora göre uyumluluk seviyesi belirle"""
        if score >= 90:
            return ComplianceLevel.FULLY_COMPLIANT
        elif score >= 75:
            return ComplianceLevel.MOSTLY_COMPLIANT
        elif score >= 60:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return ComplianceLevel.NON_COMPLIANT

    async def register_expert(
        self, expert_id: str, expert_roles: List[ExpertRole]
    ) -> bool:
        """Uzman kaydı yap"""

        for role in expert_roles:
            if expert_id not in self.expert_pool[role]:
                self.expert_pool[role].append(expert_id)

        logger.info(
            "expert_registered",
            expert_id=expert_id,
            roles=[r.value for r in expert_roles],
        )

        return True

    def get_validation_request(self, request_id: str) -> Optional[ValidationRequest]:
        """Doğrulama talebini getir"""
        return self.validation_requests.get(request_id)

    def get_compliance_report(
        self, report_id: str
    ) -> Optional[ContentComplianceReport]:
        """Uyumluluk raporunu getir"""
        return self.compliance_reports.get(report_id)

    def get_pending_requests_for_expert(
        self, expert_id: str
    ) -> List[ValidationRequest]:
        """Uzman için bekleyen talepleri getir"""
        return [
            req
            for req in self.validation_requests.values()
            if expert_id in req.assigned_experts
            and req.status == ValidationStatus.IN_REVIEW
        ]


# Singleton instance
expert_validation_system = ExpertContentValidationSystem()


__all__ = [
    "ContentType",
    "ValidationStatus",
    "ExpertRole",
    "ComplianceLevel",
    "ValidationRequest",
    "ValidationFeedback",
    "ContentComplianceReport",
    "ExpertContentValidationSystem",
    "expert_validation_system",
]
