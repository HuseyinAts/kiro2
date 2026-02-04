"""
Form-Based Interface System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Structured input forms for profile creation
- Step-by-step assessment forms
- Preference selection interfaces
- Progress reporting forms
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FormType(Enum):
    """Form türleri"""

    PROFILE_CREATION = "profile_creation"
    GOAL_SETTING = "goal_setting"
    ASSESSMENT = "assessment"
    LEARNING_STYLE = "learning_style"
    PREFERENCES = "preferences"
    PROGRESS_REPORT = "progress_report"
    FEEDBACK = "feedback"


class FieldType(Enum):
    """Alan türleri"""

    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    TEXTAREA = "textarea"
    RANGE = "range"
    DATE = "date"
    TIME = "time"
    FILE = "file"


class ValidationRule(Enum):
    """Doğrulama kuralları"""

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL_FORMAT = "email_format"
    CUSTOM = "custom"


@dataclass
class FormField:
    """Form alanı"""

    field_id: str
    field_type: FieldType
    label: str
    description: str | None = None
    placeholder: str | None = None
    default_value: Any | None = None
    options: list[dict[str, Any]] | None = None  # Select/radio için seçenekler
    validation_rules: list[dict[str, Any]] | None = None
    conditional_logic: dict[str, Any] | None = None  # Koşullu görünüm
    metadata: dict[str, Any] | None = None


@dataclass
class FormSection:
    """Form bölümü"""

    section_id: str
    title: str
    fields: list[FormField]
    description: str | None = None
    order: int = 0
    conditional_logic: dict[str, Any] | None = None


@dataclass
class FormDefinition:
    """Form tanımı"""

    form_id: str
    form_type: FormType
    title: str
    description: str
    sections: list[FormSection]
    submit_button_text: str = "Gönder"
    allow_save_draft: bool = True
    multi_step: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class FormSubmission:
    """Form gönderimi"""

    submission_id: str
    form_id: str
    user_id: str | None
    session_id: str
    form_data: dict[str, Any]
    validation_errors: list[dict[str, Any]]
    is_complete: bool
    is_draft: bool
    submitted_at: datetime
    metadata: dict[str, Any]


@dataclass
class ValidationResult:
    """Doğrulama sonucu"""

    is_valid: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]


class FormInterface:
    """Form Tabanlı Arayüz Sistemi"""

    def __init__(self):
        self.form_definitions = {}  # form_id -> FormDefinition
        self.form_submissions = {}  # submission_id -> FormSubmission
        self.form_templates = self._load_form_templates()

    def _load_form_templates(self) -> dict[FormType, FormDefinition]:
        """Form şablonlarını yükle"""
        templates = {}

        # Profil Oluşturma Formu
        templates[FormType.PROFILE_CREATION] = FormDefinition(
            form_id="profile_creation_v1",
            form_type=FormType.PROFILE_CREATION,
            title="Öğrenci Profili Oluşturma",
            description="Sana özel bir öğrenme yolu oluşturmak için bazı bilgilere ihtiyacımız var.",
            sections=[
                FormSection(
                    section_id="basic_info",
                    title="Temel Bilgiler",
                    description="Temel bilgilerini öğrenelim",
                    order=1,
                    fields=[
                        FormField(
                            field_id="name",
                            field_type=FieldType.TEXT,
                            label="Adın Soyadın",
                            placeholder="Örn: Ahmet Yılmaz",
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Ad soyad zorunludur",
                                },
                                {
                                    "rule": ValidationRule.MIN_LENGTH.value,
                                    "value": 2,
                                    "message": "En az 2 karakter olmalı",
                                },
                            ],
                        ),
                        FormField(
                            field_id="grade",
                            field_type=FieldType.SELECT,
                            label="Sınıfın",
                            description="Hangi sınıfta okuyorsun?",
                            options=[
                                {"value": "6", "label": "6. Sınıf"},
                                {"value": "7", "label": "7. Sınıf"},
                                {"value": "8", "label": "8. Sınıf"},
                                {"value": "9", "label": "9. Sınıf"},
                                {"value": "10", "label": "10. Sınıf"},
                                {"value": "11", "label": "11. Sınıf"},
                                {"value": "12", "label": "12. Sınıf"},
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Sınıf seçimi zorunludur",
                                }
                            ],
                        ),
                        FormField(
                            field_id="exam_target",
                            field_type=FieldType.RADIO,
                            label="Hedef Sınavın",
                            description="Hangi sınav için hazırlanıyorsun?",
                            options=[
                                {
                                    "value": "LGS",
                                    "label": "LGS (Liselere Geçiş Sınavı)",
                                },
                                {
                                    "value": "YKS",
                                    "label": "YKS (Yükseköğretim Kurumları Sınavı)",
                                },
                                {
                                    "value": "KPSS",
                                    "label": "KPSS (Kamu Personeli Seçme Sınavı)",
                                },
                                {"value": "other", "label": "Diğer/Genel Öğrenme"},
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Hedef sınav seçimi zorunludur",
                                }
                            ],
                        ),
                    ],
                ),
                FormSection(
                    section_id="learning_goals",
                    title="Öğrenme Hedefleri",
                    description="Hangi konularda çalışmak istiyorsun?",
                    order=2,
                    fields=[
                        FormField(
                            field_id="subjects",
                            field_type=FieldType.MULTI_SELECT,
                            label="İlgilendiğin Dersler",
                            description="Birden fazla ders seçebilirsin",
                            options=[
                                {"value": "matematik", "label": "Matematik"},
                                {"value": "fen", "label": "Fen Bilimleri"},
                                {"value": "fizik", "label": "Fizik"},
                                {"value": "kimya", "label": "Kimya"},
                                {"value": "biyoloji", "label": "Biyoloji"},
                                {"value": "turkce", "label": "Türkçe"},
                                {"value": "tarih", "label": "Tarih"},
                                {"value": "cografya", "label": "Coğrafya"},
                                {"value": "edebiyat", "label": "Edebiyat"},
                                {"value": "ingilizce", "label": "İngilizce"},
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "En az bir ders seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="primary_goal",
                            field_type=FieldType.TEXTAREA,
                            label="Ana Öğrenme Hedefin",
                            description="Bu dönem hangi konularda kendini geliştirmek istiyorsun?",
                            placeholder="Örn: Matematik konularında güçlenmek ve YKS'de yüksek puan almak istiyorum.",
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Öğrenme hedefi zorunludur",
                                },
                                {
                                    "rule": ValidationRule.MIN_LENGTH.value,
                                    "value": 10,
                                    "message": "En az 10 karakter yazmalısın",
                                },
                            ],
                        ),
                    ],
                ),
                FormSection(
                    section_id="study_preferences",
                    title="Çalışma Tercihleri",
                    description="Çalışma alışkanlıkların hakkında bilgi ver",
                    order=3,
                    fields=[
                        FormField(
                            field_id="available_time_daily",
                            field_type=FieldType.RANGE,
                            label="Günlük Çalışma Süresi (dakika)",
                            description="Günde ne kadar çalışma zamanın var?",
                            default_value=60,
                            metadata={"min": 15, "max": 480, "step": 15},
                            validation_rules=[
                                {
                                    "rule": ValidationRule.MIN_VALUE.value,
                                    "value": 15,
                                    "message": "En az 15 dakika olmalı",
                                },
                                {
                                    "rule": ValidationRule.MAX_VALUE.value,
                                    "value": 480,
                                    "message": "En fazla 8 saat olabilir",
                                },
                            ],
                        ),
                        FormField(
                            field_id="study_time_preference",
                            field_type=FieldType.RADIO,
                            label="Tercih Ettiğin Çalışma Saati",
                            options=[
                                {"value": "morning", "label": "Sabah (06:00-12:00)"},
                                {
                                    "value": "afternoon",
                                    "label": "Öğleden Sonra (12:00-18:00)",
                                },
                                {"value": "evening", "label": "Akşam (18:00-22:00)"},
                                {"value": "night", "label": "Gece (22:00-06:00)"},
                                {"value": "flexible", "label": "Esnek/Fark etmez"},
                            ],
                            default_value="flexible",
                        ),
                        FormField(
                            field_id="difficulty_areas",
                            field_type=FieldType.MULTI_SELECT,
                            label="Zorlandığın Konular",
                            description="Hangi konularda daha fazla desteğe ihtiyacın var?",
                            options=[
                                {"value": "problem_solving", "label": "Problem Çözme"},
                                {"value": "memorization", "label": "Ezber Konular"},
                                {
                                    "value": "math_operations",
                                    "label": "Matematik İşlemleri",
                                },
                                {
                                    "value": "reading_comprehension",
                                    "label": "Okuduğunu Anlama",
                                },
                                {"value": "time_management", "label": "Zaman Yönetimi"},
                                {"value": "exam_anxiety", "label": "Sınav Kaygısı"},
                                {"value": "concentration", "label": "Konsantrasyon"},
                                {"value": "motivation", "label": "Motivasyon"},
                            ],
                        ),
                    ],
                ),
            ],
            multi_step=True,
            submit_button_text="Profili Oluştur",
        )

        # Öğrenme Stili Formu
        templates[FormType.LEARNING_STYLE] = FormDefinition(
            form_id="learning_style_v1",
            form_type=FormType.LEARNING_STYLE,
            title="Öğrenme Stili Belirleme",
            description="Senin için en uygun öğrenme yöntemini belirleyelim.",
            sections=[
                FormSection(
                    section_id="learning_preferences",
                    title="Öğrenme Tercihleri",
                    description="Aşağıdaki sorulara en doğal hissettiğin şekilde cevap ver",
                    order=1,
                    fields=[
                        FormField(
                            field_id="learning_method",
                            field_type=FieldType.RADIO,
                            label="Yeni bir konuyu öğrenirken hangi yöntemi tercih edersin?",
                            options=[
                                {
                                    "value": "visual",
                                    "label": "Videolar, resimler ve diyagramlar izlerim",
                                },
                                {
                                    "value": "auditory",
                                    "label": "Sesli anlatımları dinlerim",
                                },
                                {
                                    "value": "reading",
                                    "label": "Metinleri okur, notlar alırım",
                                },
                                {
                                    "value": "kinesthetic",
                                    "label": "Uygulayarak ve deneyerek öğrenirim",
                                },
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Bir seçenek seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="memory_method",
                            field_type=FieldType.RADIO,
                            label="Bilgiyi en iyi nasıl hatırlarsın?",
                            options=[
                                {"value": "visual", "label": "Görsel imgeler halinde"},
                                {
                                    "value": "auditory",
                                    "label": "Sesli tekrarlar yaparak",
                                },
                                {"value": "reading", "label": "Yazarak ve okuyarak"},
                                {
                                    "value": "kinesthetic",
                                    "label": "Uygulayarak ve hareket ederek",
                                },
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Bir seçenek seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="problem_solving",
                            field_type=FieldType.RADIO,
                            label="Bir problemi çözerken nasıl yaklaşırsın?",
                            options=[
                                {
                                    "value": "visual",
                                    "label": "Şemalar ve grafikler çizerim",
                                },
                                {
                                    "value": "auditory",
                                    "label": "Kendimle konuşur, sesli düşünürüm",
                                },
                                {
                                    "value": "reading",
                                    "label": "Adım adım yazarak ilerlerim",
                                },
                                {
                                    "value": "kinesthetic",
                                    "label": "Deneme yanılma yöntemiyle çözerim",
                                },
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Bir seçenek seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="study_environment",
                            field_type=FieldType.RADIO,
                            label="Hangi ortamda daha iyi çalışırsın?",
                            options=[
                                {
                                    "value": "visual",
                                    "label": "Renkli, düzenli ve görsel materyallerle dolu",
                                },
                                {
                                    "value": "auditory",
                                    "label": "Müzik veya doğal sesler olan",
                                },
                                {
                                    "value": "reading",
                                    "label": "Sessiz, kitaplarla dolu",
                                },
                                {
                                    "value": "kinesthetic",
                                    "label": "Hareket edebileceğim, rahat",
                                },
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Bir seçenek seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="content_preference",
                            field_type=FieldType.MULTI_SELECT,
                            label="Hangi tür içerikleri tercih edersin? (Birden fazla seçebilirsin)",
                            options=[
                                {"value": "videos", "label": "Eğitim videoları"},
                                {"value": "podcasts", "label": "Podcast'ler"},
                                {"value": "articles", "label": "Makaleler ve yazılar"},
                                {
                                    "value": "interactive",
                                    "label": "Etkileşimli uygulamalar",
                                },
                                {"value": "games", "label": "Eğitsel oyunlar"},
                                {"value": "quizzes", "label": "Testler ve quizler"},
                                {"value": "infographics", "label": "İnfografikler"},
                                {"value": "simulations", "label": "Simülasyonlar"},
                            ],
                        ),
                    ],
                )
            ],
            submit_button_text="Öğrenme Stilimi Belirle",
        )

        # İlerleme Raporu Formu
        templates[FormType.PROGRESS_REPORT] = FormDefinition(
            form_id="progress_report_v1",
            form_type=FormType.PROGRESS_REPORT,
            title="İlerleme Raporu",
            description="Öğrenme sürecin nasıl gidiyor? Geri bildirimini paylaş.",
            sections=[
                FormSection(
                    section_id="progress_assessment",
                    title="İlerleme Değerlendirmesi",
                    order=1,
                    fields=[
                        FormField(
                            field_id="overall_satisfaction",
                            field_type=FieldType.RANGE,
                            label="Genel Memnuniyet (1-10)",
                            description="Öğrenme sürecinden ne kadar memnunsun?",
                            default_value=5,
                            metadata={"min": 1, "max": 10, "step": 1},
                        ),
                        FormField(
                            field_id="difficulty_level",
                            field_type=FieldType.RADIO,
                            label="İçeriklerin zorluk seviyesi nasıl?",
                            options=[
                                {"value": "too_easy", "label": "Çok kolay"},
                                {"value": "easy", "label": "Kolay"},
                                {"value": "just_right", "label": "Tam uygun"},
                                {"value": "hard", "label": "Zor"},
                                {"value": "too_hard", "label": "Çok zor"},
                            ],
                            validation_rules=[
                                {
                                    "rule": ValidationRule.REQUIRED.value,
                                    "message": "Zorluk seviyesi seçmelisin",
                                }
                            ],
                        ),
                        FormField(
                            field_id="time_spent_daily",
                            field_type=FieldType.NUMBER,
                            label="Günlük Ortalama Çalışma Süresi (dakika)",
                            placeholder="Örn: 45",
                            validation_rules=[
                                {
                                    "rule": ValidationRule.MIN_VALUE.value,
                                    "value": 0,
                                    "message": "0'dan küçük olamaz",
                                }
                            ],
                        ),
                        FormField(
                            field_id="completed_resources",
                            field_type=FieldType.NUMBER,
                            label="Tamamladığın Kaynak Sayısı",
                            placeholder="Örn: 5",
                            validation_rules=[
                                {
                                    "rule": ValidationRule.MIN_VALUE.value,
                                    "value": 0,
                                    "message": "0'dan küçük olamaz",
                                }
                            ],
                        ),
                    ],
                ),
                FormSection(
                    section_id="feedback",
                    title="Geri Bildirim",
                    order=2,
                    fields=[
                        FormField(
                            field_id="helpful_resources",
                            field_type=FieldType.MULTI_SELECT,
                            label="En faydalı bulduğun kaynak türleri",
                            options=[
                                {"value": "videos", "label": "Videolar"},
                                {"value": "articles", "label": "Makaleler"},
                                {
                                    "value": "interactive",
                                    "label": "Etkileşimli içerikler",
                                },
                                {"value": "quizzes", "label": "Testler"},
                                {"value": "exercises", "label": "Alıştırmalar"},
                            ],
                        ),
                        FormField(
                            field_id="struggling_topics",
                            field_type=FieldType.TEXTAREA,
                            label="Zorlandığın Konular",
                            description="Hangi konularda daha fazla yardıma ihtiyacın var?",
                            placeholder="Örn: Matematik'te türev konusunda zorlanıyorum...",
                        ),
                        FormField(
                            field_id="suggestions",
                            field_type=FieldType.TEXTAREA,
                            label="Öneriler ve İstekler",
                            description="Öğrenme deneyimini iyileştirmek için önerilerin var mı?",
                            placeholder="Örn: Daha fazla görsel materyal olabilir...",
                        ),
                    ],
                ),
            ],
            submit_button_text="Raporu Gönder",
        )

        return templates

    def get_form_definition(self, form_type: FormType) -> FormDefinition | None:
        """
        Form tanımını getir

        Args:
            form_type: Form türü

        Returns:
            Form tanımı
        """
        return self.form_templates.get(form_type)

    def create_custom_form(self, form_definition: FormDefinition) -> str:
        """
        Özel form oluştur

        Args:
            form_definition: Form tanımı

        Returns:
            Form ID
        """
        try:
            self.form_definitions[form_definition.form_id] = form_definition
            logger.info(f"Custom form created: {form_definition.form_id}")
            return form_definition.form_id

        except Exception as e:
            logger.error(f"Error creating custom form: {e!s}")
            raise

    def validate_form_data(
        self, form_id: str, form_data: dict[str, Any]
    ) -> ValidationResult:
        """
        Form verilerini doğrula

        Args:
            form_id: Form ID
            form_data: Form verileri

        Returns:
            Doğrulama sonucu
        """
        try:
            # Form tanımını bul
            form_def = None
            if form_id in self.form_definitions:
                form_def = self.form_definitions[form_id]
            else:
                # Template'lerde ara
                for template in self.form_templates.values():
                    if template.form_id == form_id:
                        form_def = template
                        break

            if not form_def:
                return ValidationResult(
                    is_valid=False,
                    errors=[{"field": "form", "message": "Form tanımı bulunamadı"}],
                    warnings=[],
                )

            errors = []
            warnings = []

            # Her section ve field için doğrulama
            for section in form_def.sections:
                for field in section.fields:
                    field_value = form_data.get(field.field_id)
                    field_errors = self._validate_field(field, field_value)
                    errors.extend(field_errors)

            return ValidationResult(
                is_valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error validating form data: {e!s}")
            return ValidationResult(
                is_valid=False,
                errors=[{"field": "form", "message": f"Doğrulama hatası: {e!s}"}],
                warnings=[],
            )

    def _validate_field(self, field: FormField, value: Any) -> list[dict[str, Any]]:
        """
        Tek bir alanı doğrula

        Args:
            field: Form alanı
            value: Alan değeri

        Returns:
            Hata listesi
        """
        errors = []

        if not field.validation_rules:
            return errors

        for rule in field.validation_rules:
            rule_type = rule.get("rule")
            rule_value = rule.get("value")
            rule_message = rule.get("message", "Geçersiz değer")

            if rule_type == ValidationRule.REQUIRED.value:
                if (
                    value is None
                    or value == ""
                    or (isinstance(value, list) and len(value) == 0)
                ):
                    errors.append(
                        {
                            "field": field.field_id,
                            "rule": rule_type,
                            "message": rule_message,
                        }
                    )

            elif rule_type == ValidationRule.MIN_LENGTH.value and value:
                if len(str(value)) < rule_value:
                    errors.append(
                        {
                            "field": field.field_id,
                            "rule": rule_type,
                            "message": rule_message,
                        }
                    )

            elif rule_type == ValidationRule.MAX_LENGTH.value and value:
                if len(str(value)) > rule_value:
                    errors.append(
                        {
                            "field": field.field_id,
                            "rule": rule_type,
                            "message": rule_message,
                        }
                    )

            elif rule_type == ValidationRule.MIN_VALUE.value and value is not None:
                try:
                    if float(value) < rule_value:
                        errors.append(
                            {
                                "field": field.field_id,
                                "rule": rule_type,
                                "message": rule_message,
                            }
                        )
                except (ValueError, TypeError):
                    pass

            elif rule_type == ValidationRule.MAX_VALUE.value and value is not None:
                try:
                    if float(value) > rule_value:
                        errors.append(
                            {
                                "field": field.field_id,
                                "rule": rule_type,
                                "message": rule_message,
                            }
                        )
                except (ValueError, TypeError):
                    pass

        return errors

    def submit_form(
        self,
        form_id: str,
        form_data: dict[str, Any],
        user_id: str | None = None,
        session_id: str | None = None,
        is_draft: bool = False,
    ) -> FormSubmission:
        """
        Form gönder

        Args:
            form_id: Form ID
            form_data: Form verileri
            user_id: Kullanıcı ID
            session_id: Oturum ID
            is_draft: Taslak mı

        Returns:
            Form gönderimi
        """
        try:
            # Form verilerini doğrula
            validation_result = self.validate_form_data(form_id, form_data)

            # Submission oluştur
            submission_id = f"sub_{datetime.now().timestamp()}"
            submission = FormSubmission(
                submission_id=submission_id,
                form_id=form_id,
                user_id=user_id,
                session_id=session_id or f"session_{datetime.now().timestamp()}",
                form_data=form_data,
                validation_errors=validation_result.errors,
                is_complete=validation_result.is_valid and not is_draft,
                is_draft=is_draft,
                submitted_at=datetime.now(),
                metadata={
                    "validation_warnings": validation_result.warnings,
                    "ip_address": None,  # Gerçek uygulamada IP adresi
                    "user_agent": None,  # Gerçek uygulamada user agent
                },
            )

            # Submission'ı kaydet
            self.form_submissions[submission_id] = submission

            logger.info(
                f"Form submitted: {form_id} -> {submission_id} (valid: {validation_result.is_valid})"
            )
            return submission

        except Exception as e:
            logger.error(f"Error submitting form: {e!s}")
            raise

    def get_form_submission(self, submission_id: str) -> FormSubmission | None:
        """
        Form gönderimini getir

        Args:
            submission_id: Gönderim ID

        Returns:
            Form gönderimi
        """
        return self.form_submissions.get(submission_id)

    def get_user_submissions(
        self, user_id: str, form_type: FormType | None = None
    ) -> list[FormSubmission]:
        """
        Kullanıcının form gönderimlerini getir

        Args:
            user_id: Kullanıcı ID
            form_type: Form türü filtresi

        Returns:
            Form gönderimleri
        """
        submissions = []

        for submission in self.form_submissions.values():
            if submission.user_id == user_id:
                if form_type is None:
                    submissions.append(submission)
                else:
                    # Form türünü kontrol et
                    form_def = self.get_form_by_id(submission.form_id)
                    if form_def and form_def.form_type == form_type:
                        submissions.append(submission)

        # Tarihe göre sırala (en yeni önce)
        submissions.sort(key=lambda x: x.submitted_at, reverse=True)
        return submissions

    def get_form_by_id(self, form_id: str) -> FormDefinition | None:
        """
        Form ID'ye göre form tanımını getir

        Args:
            form_id: Form ID

        Returns:
            Form tanımı
        """
        # Önce custom form'larda ara
        if form_id in self.form_definitions:
            return self.form_definitions[form_id]

        # Template'lerde ara
        for template in self.form_templates.values():
            if template.form_id == form_id:
                return template

        return None

    def update_form_submission(
        self, submission_id: str, updated_data: dict[str, Any]
    ) -> FormSubmission | None:
        """
        Form gönderimini güncelle

        Args:
            submission_id: Gönderim ID
            updated_data: Güncellenmiş veriler

        Returns:
            Güncellenmiş form gönderimi
        """
        try:
            submission = self.form_submissions.get(submission_id)
            if not submission:
                return None

            # Verileri güncelle
            submission.form_data.update(updated_data)

            # Yeniden doğrula
            validation_result = self.validate_form_data(
                submission.form_id, submission.form_data
            )
            submission.validation_errors = validation_result.errors
            submission.is_complete = (
                validation_result.is_valid and not submission.is_draft
            )

            logger.info(f"Form submission updated: {submission_id}")
            return submission

        except Exception as e:
            logger.error(f"Error updating form submission: {e!s}")
            return None

    def generate_form_analytics(self, form_id: str) -> dict[str, Any]:
        """
        Form analitikleri oluştur

        Args:
            form_id: Form ID

        Returns:
            Analitik verileri
        """
        try:
            submissions = [
                s for s in self.form_submissions.values() if s.form_id == form_id
            ]

            if not submissions:
                return {"total_submissions": 0}

            total_submissions = len(submissions)
            completed_submissions = len([s for s in submissions if s.is_complete])
            draft_submissions = len([s for s in submissions if s.is_draft])

            # Field analitikleri
            field_analytics = {}
            form_def = self.get_form_by_id(form_id)

            if form_def:
                for section in form_def.sections:
                    for field in section.fields:
                        field_id = field.field_id
                        field_values = [
                            s.form_data.get(field_id)
                            for s in submissions
                            if field_id in s.form_data
                        ]

                        field_analytics[field_id] = {
                            "response_count": len(field_values),
                            "response_rate": len(field_values) / total_submissions
                            if total_submissions > 0
                            else 0,
                            "most_common": self._get_most_common_value(field_values)
                            if field_values
                            else None,
                        }

            return {
                "form_id": form_id,
                "total_submissions": total_submissions,
                "completed_submissions": completed_submissions,
                "draft_submissions": draft_submissions,
                "completion_rate": completed_submissions / total_submissions
                if total_submissions > 0
                else 0,
                "field_analytics": field_analytics,
                "submission_dates": [s.submitted_at.isoformat() for s in submissions],
            }

        except Exception as e:
            logger.error(f"Error generating form analytics: {e!s}")
            return {"error": str(e)}

    def _get_most_common_value(self, values: list[Any]) -> Any:
        """En yaygın değeri bul"""
        if not values:
            return None

        # None değerleri filtrele
        filtered_values = [v for v in values if v is not None]
        if not filtered_values:
            return None

        # Frekans hesapla
        from collections import Counter

        counter = Counter(filtered_values)
        return counter.most_common(1)[0][0]


# Singleton instance
form_interface = FormInterface()
