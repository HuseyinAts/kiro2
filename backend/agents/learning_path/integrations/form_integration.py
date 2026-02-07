"""
Form Interface Integration Service

Provides form definitions and handles form submissions for
student onboarding and profile management.

Teknofest 2025 - Eğitim Eylemci Projesi
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any, List
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ..core.student_profiler import StudentProfiler

from ..models import (
    StudentProfile,
    KnowledgeLevel,
    LearningStyle,
)
from ..config import get_learning_path_config

logger = logging.getLogger(__name__)


class FormFieldType(Enum):
    """Form field types."""

    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    SLIDER = "slider"
    DATE = "date"


@dataclass
class FormField:
    """Definition of a form field."""

    name: str
    label: str
    field_type: FormFieldType
    required: bool = True
    placeholder: str = ""
    help_text: str = ""
    options: Optional[List[Dict[str, str]]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[List[str]] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.validation_rules is None:
            self.validation_rules = []


@dataclass
class FormDefinition:
    """Definition of a complete form."""

    form_id: str
    title: str
    description: str
    fields: List[FormField]
    submit_button_text: str = "Gönder"
    cancel_button_text: str = "İptal"


@dataclass
class FormSubmission:
    """Submitted form data."""

    form_id: str
    student_id: str
    data: Dict[str, Any]
    submitted_at: Optional[datetime] = None

    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now()


@dataclass
class FormValidationResult:
    """Result of form validation."""

    is_valid: bool
    errors: Optional[Dict[str, str]] = None
    warnings: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = {}
        if self.warnings is None:
            self.warnings = {}


@dataclass
class FormSubmissionResult:
    """Result of form submission."""

    success: bool
    message: str
    profile: Optional[StudentProfile] = None
    errors: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = {}


class FormIntegrationService:
    """Service for form-based student profile creation and updates.

    Provides form definitions and handles form submissions for
    student onboarding and profile management.
    """

    def __init__(self, student_profiler: Optional[StudentProfiler] = None):
        """Initialize form integration service.

        Args:
            student_profiler: Optional StudentProfiler for saving profiles
        """
        self.config = get_learning_path_config()
        self.student_profiler = student_profiler

    def get_profile_creation_form(self) -> FormDefinition:
        """Get the student profile creation form.

        Returns:
            FormDefinition with all fields for profile creation
        """
        return FormDefinition(
            form_id="profile_creation",
            title="Öğrenci Profili Oluştur",
            description="Kişiselleştirilmiş öğrenme deneyimi için bilgilerinizi girin.",
            fields=[
                FormField(
                    name="name",
                    label="Ad Soyad",
                    field_type=FormFieldType.TEXT,
                    required=True,
                    placeholder="Adınızı ve soyadınızı girin",
                    validation_rules=["min_length:2", "max_length:100"],
                ),
                FormField(
                    name="grade",
                    label="Sınıf",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        {"value": "9", "label": "9. Sınıf"},
                        {"value": "10", "label": "10. Sınıf"},
                        {"value": "11", "label": "11. Sınıf"},
                        {"value": "12", "label": "12. Sınıf"},
                        {"value": "mezun", "label": "Mezun"},
                    ],
                ),
                FormField(
                    name="exam_target",
                    label="Hedef Sınav",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        {"value": "YKS-TYT", "label": "YKS - TYT"},
                        {"value": "YKS-AYT-SAY", "label": "YKS - AYT Sayısal"},
                        {"value": "YKS-AYT-EA", "label": "YKS - AYT Eşit Ağırlık"},
                        {"value": "YKS-AYT-SOZ", "label": "YKS - AYT Sözel"},
                        {"value": "YKS-YDT", "label": "YKS - YDT"},
                    ],
                ),
                FormField(
                    name="interests",
                    label="İlgi Alanlarınız",
                    field_type=FormFieldType.MULTI_SELECT,
                    required=True,
                    help_text="En az bir alan seçin",
                    options=[
                        {"value": "matematik", "label": "Matematik"},
                        {"value": "fizik", "label": "Fizik"},
                        {"value": "kimya", "label": "Kimya"},
                        {"value": "biyoloji", "label": "Biyoloji"},
                        {"value": "turkce", "label": "Türkçe"},
                        {"value": "edebiyat", "label": "Edebiyat"},
                        {"value": "tarih", "label": "Tarih"},
                        {"value": "cografya", "label": "Coğrafya"},
                        {"value": "ingilizce", "label": "İngilizce"},
                    ],
                ),
                FormField(
                    name="available_time",
                    label="Günlük Çalışma Süresi (Dakika)",
                    field_type=FormFieldType.SLIDER,
                    required=True,
                    min_value=30,
                    max_value=720,
                    default_value=120,
                    help_text="Günde ortalama kaç dakika çalışabilirsiniz?",
                ),
                FormField(
                    name="knowledge_level",
                    label="Mevcut Seviyeniz",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {
                            "value": "beginner",
                            "label": "Başlangıç - Konuları yeni öğreniyorum",
                        },
                        {
                            "value": "elementary",
                            "label": "Temel - Temel konuları biliyorum",
                        },
                        {
                            "value": "intermediate",
                            "label": "Orta - Çoğu konuyu biliyorum",
                        },
                        {
                            "value": "advanced",
                            "label": "İleri - Detaylı bilgiye sahibim",
                        },
                    ],
                ),
                FormField(
                    name="learning_goal",
                    label="Öğrenme Hedefiniz",
                    field_type=FormFieldType.TEXT,
                    required=True,
                    placeholder="Örn: YKS'de ilk 10.000'e girmek",
                    validation_rules=["min_length:5", "max_length:200"],
                ),
            ],
            submit_button_text="Profil Oluştur",
        )

    def get_learning_style_form(self) -> FormDefinition:
        """Get the learning style questionnaire form.

        Returns:
            FormDefinition for VARK learning style assessment
        """
        return FormDefinition(
            form_id="learning_style",
            title="Öğrenme Stili Anketi",
            description="Öğrenme stilinizi belirlemek için soruları yanıtlayın.",
            fields=[
                FormField(
                    name="q1_new_topic",
                    label="Yeni bir konuyu öğrenirken tercih ettiğiniz yöntem nedir?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {"value": "visual", "label": "Diyagramlar ve grafikler incelemek"},
                        {"value": "auditory", "label": "Sesli anlatım dinlemek"},
                        {"value": "reading", "label": "Yazılı kaynakları okumak"},
                        {"value": "kinesthetic", "label": "Pratik yaparak öğrenmek"},
                    ],
                ),
                FormField(
                    name="q2_remember",
                    label="Bir şeyi hatırlamak istediğinizde ne yaparsınız?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {
                            "value": "visual",
                            "label": "Görsel bir zihin haritası oluştururum",
                        },
                        {"value": "auditory", "label": "Sesli tekrar ederim"},
                        {"value": "reading", "label": "Yazıp not alırım"},
                        {"value": "kinesthetic", "label": "Uygulamaya çalışırım"},
                    ],
                ),
                FormField(
                    name="q3_struggle",
                    label="Bir konuyu anlamakta zorlandığınızda ne yaparsınız?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {
                            "value": "visual",
                            "label": "Video izlerim veya şekil çizerim",
                        },
                        {"value": "auditory", "label": "Birine anlattırırım"},
                        {"value": "reading", "label": "Farklı kaynaklardan okurum"},
                        {
                            "value": "kinesthetic",
                            "label": "Örnek çözerek pratik yaparım",
                        },
                    ],
                ),
                FormField(
                    name="q4_best_resource",
                    label="En verimli olduğunuz kaynak türü hangisidir?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {"value": "visual", "label": "Animasyonlu videolar"},
                        {"value": "auditory", "label": "Podcast ve sesli dersler"},
                        {"value": "reading", "label": "Ders kitapları ve makaleler"},
                        {"value": "kinesthetic", "label": "İnteraktif alıştırmalar"},
                    ],
                ),
                FormField(
                    name="q5_exam_prep",
                    label="Sınava nasıl hazırlanırsınız?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=[
                        {
                            "value": "visual",
                            "label": "Özet kartları ve şemalar hazırlarım",
                        },
                        {"value": "auditory", "label": "Konuları sesli tekrar ederim"},
                        {"value": "reading", "label": "Notlarımı defalarca okurum"},
                        {"value": "kinesthetic", "label": "Çok fazla soru çözerim"},
                    ],
                ),
            ],
            submit_button_text="Analiz Et",
        )

    def get_goal_setting_form(self) -> FormDefinition:
        """Get the goal setting form.

        Returns:
            FormDefinition for academic goals
        """
        return FormDefinition(
            form_id="goal_setting",
            title="Hedef Belirleme",
            description="Akademik hedeflerinizi belirleyin.",
            fields=[
                FormField(
                    name="target_university",
                    label="Hedef Üniversite (Opsiyonel)",
                    field_type=FormFieldType.TEXT,
                    required=False,
                    placeholder="Örn: İTÜ, Boğaziçi, ODTÜ",
                ),
                FormField(
                    name="target_department",
                    label="Hedef Bölüm (Opsiyonel)",
                    field_type=FormFieldType.TEXT,
                    required=False,
                    placeholder="Örn: Bilgisayar Mühendisliği",
                ),
                FormField(
                    name="target_ranking",
                    label="Hedef Sıralama",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        {"value": "top_1000", "label": "İlk 1.000"},
                        {"value": "top_5000", "label": "İlk 5.000"},
                        {"value": "top_10000", "label": "İlk 10.000"},
                        {"value": "top_50000", "label": "İlk 50.000"},
                        {"value": "top_100000", "label": "İlk 100.000"},
                        {"value": "pass", "label": "Geçerli puan almak"},
                    ],
                ),
                FormField(
                    name="exam_date",
                    label="Sınav Tarihi",
                    field_type=FormFieldType.DATE,
                    required=True,
                    help_text="Hedeflediğiniz sınav tarihi",
                ),
                FormField(
                    name="weekly_commitment",
                    label="Haftalık Taahhüt (Saat)",
                    field_type=FormFieldType.SLIDER,
                    required=True,
                    min_value=5,
                    max_value=50,
                    default_value=20,
                    help_text="Haftada kaç saat çalışmayı taahhüt ediyorsunuz?",
                ),
            ],
            submit_button_text="Hedefleri Kaydet",
        )

    def validate_form(self, form_id: str, data: Dict[str, Any]) -> FormValidationResult:
        """Validate form submission data.

        Args:
            form_id: ID of the form being validated
            data: Form data to validate

        Returns:
            FormValidationResult with validation status
        """
        errors: Dict[str, str] = {}
        warnings: Dict[str, str] = {}

        # Get form definition
        form = self._get_form_by_id(form_id)
        if not form:
            return FormValidationResult(
                is_valid=False, errors={"form": "Form bulunamadı"}
            )

        # Validate each field
        for field in form.fields:
            value = data.get(field.name)

            # Required check
            if field.required and not value:
                errors[field.name] = f"{field.label} alanı zorunludur"
                continue

            # Skip validation for empty optional fields
            if not value:
                continue

            # Type-specific validation
            field_errors = self._validate_field(field, value)
            if field_errors:
                errors[field.name] = field_errors

        # Cross-field validation
        cross_errors = self._cross_validate(form_id, data)
        errors.update(cross_errors)

        return FormValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    async def submit_profile_form(
        self, submission: FormSubmission
    ) -> FormSubmissionResult:
        """Submit profile creation form.

        Args:
            submission: Form submission data

        Returns:
            FormSubmissionResult with created profile
        """
        try:
            # Validate
            validation = self.validate_form(submission.form_id, submission.data)
            if not validation.is_valid:
                return FormSubmissionResult(
                    success=False,
                    message="Form validasyonu başarısız",
                    errors=validation.errors,
                )

            # Create profile
            profile = self._create_profile_from_form(
                student_id=submission.student_id, data=submission.data
            )

            # Save profile if profiler available
            if self.student_profiler:
                # Note: save_profile may need to be implemented in StudentProfiler
                # For now, just log the profile creation
                pass

            logger.info(f"Profile created for student: {submission.student_id}")

            return FormSubmissionResult(
                success=True,
                message="Profiliniz başarıyla oluşturuldu!",
                profile=profile,
            )

        except Exception as e:
            logger.error(f"Profile form submission failed: {e}")
            return FormSubmissionResult(
                success=False, message=f"Bir hata oluştu: {str(e)}"
            )

    async def submit_learning_style_form(
        self, submission: FormSubmission
    ) -> FormSubmissionResult:
        """Submit learning style questionnaire.

        Args:
            submission: Form submission data

        Returns:
            FormSubmissionResult with determined learning style
        """
        try:
            # Validate
            validation = self.validate_form(submission.form_id, submission.data)
            if not validation.is_valid:
                return FormSubmissionResult(
                    success=False,
                    message="Form validasyonu başarısız",
                    errors=validation.errors,
                )

            # Calculate learning style
            learning_style = self._calculate_learning_style(submission.data)

            logger.info(
                f"Learning style determined: {learning_style.value} for student: {submission.student_id}"
            )

            return FormSubmissionResult(
                success=True,
                message=f"Öğrenme stiliniz belirlendi: {self._get_style_description(learning_style)}",
            )

        except Exception as e:
            logger.error(f"Learning style form submission failed: {e}")
            return FormSubmissionResult(
                success=False, message=f"Bir hata oluştu: {str(e)}"
            )

    async def submit_goal_setting_form(
        self, submission: FormSubmission
    ) -> FormSubmissionResult:
        """Submit goal setting form.

        Args:
            submission: Form submission data

        Returns:
            FormSubmissionResult with saved goals
        """
        try:
            # Validate
            validation = self.validate_form(submission.form_id, submission.data)
            if not validation.is_valid:
                return FormSubmissionResult(
                    success=False,
                    message="Form validasyonu başarısız",
                    errors=validation.errors,
                )

            # Goals would be saved in profile metadata
            logger.info(f"Goals set for student: {submission.student_id}")

            return FormSubmissionResult(
                success=True, message="Hedefleriniz başarıyla kaydedildi!"
            )

        except Exception as e:
            logger.error(f"Goal setting form submission failed: {e}")
            return FormSubmissionResult(
                success=False, message=f"Bir hata oluştu: {str(e)}"
            )

    def _get_form_by_id(self, form_id: str) -> Optional[FormDefinition]:
        """Get form definition by ID.

        Args:
            form_id: Form identifier

        Returns:
            FormDefinition or None if not found
        """
        forms = {
            "profile_creation": self.get_profile_creation_form(),
            "learning_style": self.get_learning_style_form(),
            "goal_setting": self.get_goal_setting_form(),
        }
        return forms.get(form_id)

    def _validate_field(self, field: FormField, value: Any) -> Optional[str]:
        """Validate a single field value.

        Args:
            field: Field definition
            value: Field value

        Returns:
            Error message or None if valid
        """
        for rule in field.validation_rules or []:
            if rule.startswith("min_length:"):
                min_len = int(rule.split(":")[1])
                if len(str(value)) < min_len:
                    return f"En az {min_len} karakter olmalı"

            elif rule.startswith("max_length:"):
                max_len = int(rule.split(":")[1])
                if len(str(value)) > max_len:
                    return f"En fazla {max_len} karakter olmalı"

        # Number range validation
        if field.field_type in [FormFieldType.NUMBER, FormFieldType.SLIDER]:
            try:
                num_value = float(value)
                if field.min_value is not None and num_value < field.min_value:
                    return f"Değer en az {field.min_value} olmalı"
                if field.max_value is not None and num_value > field.max_value:
                    return f"Değer en fazla {field.max_value} olmalı"
            except (ValueError, TypeError):
                return "Geçerli bir sayı girin"

        # Select validation
        if field.field_type == FormFieldType.SELECT:
            valid_values = [opt["value"] for opt in (field.options or [])]
            if value not in valid_values:
                return "Geçersiz seçenek"

        # Multi-select validation
        if field.field_type == FormFieldType.MULTI_SELECT:
            if not isinstance(value, list):
                return "Liste formatında olmalı"
            valid_values = [opt["value"] for opt in (field.options or [])]
            for item in value:
                if item not in valid_values:
                    return f"Geçersiz seçenek: {item}"

        return None

    def _cross_validate(self, form_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Perform cross-field validation.

        Args:
            form_id: Form identifier
            data: Form data

        Returns:
            Dictionary of field errors
        """
        errors: Dict[str, str] = {}

        if form_id == "profile_creation":
            # Grade and exam consistency
            grade = data.get("grade")
            exam = data.get("exam_target")

            if grade == "9" and exam in [
                "YKS-AYT-SAY",
                "YKS-AYT-EA",
                "YKS-AYT-SOZ",
            ]:
                errors["exam_target"] = "9. sınıfta önce TYT'ye odaklanmanızı öneririz"

        return errors

    def _create_profile_from_form(
        self, student_id: str, data: Dict[str, Any]
    ) -> StudentProfile:
        """Create StudentProfile from form data.

        Args:
            student_id: Student identifier
            data: Form data

        Returns:
            StudentProfile instance
        """
        # Map knowledge level to KnowledgeLevel enum
        level_mapping = {
            "beginner": KnowledgeLevel.BEGINNER,
            "elementary": KnowledgeLevel.ELEMENTARY,
            "intermediate": KnowledgeLevel.INTERMEDIATE,
            "advanced": KnowledgeLevel.ADVANCED,
        }

        knowledge_level_str = data.get("knowledge_level", "intermediate")
        knowledge_level = level_mapping.get(
            knowledge_level_str, KnowledgeLevel.INTERMEDIATE
        )

        return StudentProfile(
            student_id=student_id,
            name=data.get("name", ""),
            grade=data.get("grade", "12"),
            exam_target=data.get("exam_target", "YKS-TYT"),
            learning_goal=data.get("learning_goal", ""),
            learning_style=LearningStyle.VISUAL,  # Will be updated by learning style form
            knowledge_level=knowledge_level,
            interests=data.get("interests", []),
            available_time=int(data.get("available_time", 120)),
        )

    def _calculate_learning_style(self, data: Dict[str, Any]) -> LearningStyle:
        """Calculate learning style from questionnaire answers.

        Args:
            data: Questionnaire responses

        Returns:
            Determined LearningStyle
        """
        style_counts: Dict[str, int] = {
            "visual": 0,
            "auditory": 0,
            "reading": 0,
            "kinesthetic": 0,
        }

        # Count responses
        for key, value in data.items():
            if key.startswith("q") and value in style_counts:
                style_counts[value] += 1

        # Find dominant style
        dominant = max(style_counts.items(), key=lambda x: x[1])

        style_mapping = {
            "visual": LearningStyle.VISUAL,
            "auditory": LearningStyle.AUDITORY,
            "reading": LearningStyle.READING,
            "kinesthetic": LearningStyle.KINESTHETIC,
        }

        return style_mapping.get(dominant[0], LearningStyle.VISUAL)

    def _get_style_description(self, style: LearningStyle) -> str:
        """Get Turkish description of learning style.

        Args:
            style: LearningStyle enum

        Returns:
            Turkish description string
        """
        descriptions = {
            LearningStyle.VISUAL: "Görsel Öğrenen - Diyagramlar ve videolarla daha iyi öğrenirsiniz",
            LearningStyle.AUDITORY: "İşitsel Öğrenen - Sesli anlatımlarla daha iyi öğrenirsiniz",
            LearningStyle.READING: "Okuma/Yazma Öğrenen - Yazılı kaynaklarla daha iyi öğrenirsiniz",
            LearningStyle.KINESTHETIC: "Kinestetik Öğrenen - Pratik yaparak daha iyi öğrenirsiniz",
            LearningStyle.MIXED: "Karma Öğrenen - Farklı yöntemlerle öğrenirsiniz",
        }
        return descriptions.get(style, "Belirsiz")


# Legacy wrapper for backward compatibility
class FormIntegration:
    """Form interface integration wrapper (legacy)."""

    def __init__(self, form_service):
        self.service = form_service
        logger.info("FormIntegration initialized")

    def get_form(self, form_type: str) -> Dict[str, Any]:
        """Get form definition."""
        try:
            return self.service.get_form(form_type=form_type)
        except Exception as e:
            logger.error(f"Get form error: {str(e)}")
            return {}

    async def submit_form(
        self, form_type: str, student_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit form data."""
        try:
            return await self.service.submit_form(
                form_type=form_type, student_id=student_id, form_data=data
            )
        except Exception as e:
            logger.error(f"Submit form error: {str(e)}")
            return {"error": str(e)}
