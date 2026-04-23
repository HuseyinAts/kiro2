"""
YDT Optik Form Servisi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül YDT sınavları için optik form arayüzü işlevlerini yönetir:
- Dil-specific interface (dile özel arayüz)
- Passage display optimization (metin görüntüleme optimizasyonu)
- Answer marking system (cevap işaretleme sistemi)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.structured_logger import get_logger

logger = get_logger("ydt_optical_form_service")


class AnswerStatus(Enum):
    """Cevap durumu"""

    EMPTY = "empty"  # Boş
    MARKED = "marked"  # İşaretli
    FLAGGED = "flagged"  # Şüpheli işaretli


@dataclass
class OpticalFormAnswer:
    """Optik form cevap modeli"""

    question_number: int
    selected_option: str | None = None  # A, B, C, D, E
    status: AnswerStatus = AnswerStatus.EMPTY
    is_flagged: bool = False  # Şüpheli işaret
    response_time: float | None = None  # Cevaplama süresi (saniye)
    marked_at: datetime | None = None


@dataclass
class PassageSection:
    """Metin bölümü modeli"""

    passage_id: str
    title: str
    content: str
    word_count: int
    question_numbers: list[int]  # Bu metne ait soru numaraları
    estimated_reading_time: int  # Tahmini okuma süresi (dakika)

    # Görüntüleme optimizasyonu
    font_size: str = "medium"  # small, medium, large
    line_spacing: str = "normal"  # compact, normal, relaxed
    highlight_enabled: bool = False


@dataclass
class YDTOpticalForm:
    """YDT optik form modeli"""

    exam_session_id: str
    student_id: str
    language: str  # english, german, french
    total_questions: int = 80

    # Cevaplar
    answers: dict[int, OpticalFormAnswer] = field(default_factory=dict)

    # Metin bölümleri
    passages: list[PassageSection] = field(default_factory=list)

    # Navigasyon
    current_question: int = 1
    current_passage_id: str | None = None

    # İstatistikler
    answered_count: int = 0
    flagged_count: int = 0
    empty_count: int = 80

    # Görüntüleme ayarları
    show_passage_sidebar: bool = True
    passage_position: str = "left"  # left, right, top
    zoom_level: int = 100  # %


class YDTOpticalFormService:
    """
    YDT Optik Form Servisi

    Bu servis YDT sınavları için optik form arayüzü işlevlerini sağlar:
    - Dile özel arayüz düzenleri
    - Metin görüntüleme optimizasyonu
    - Cevap işaretleme ve navigasyon
    """

    def __init__(self):
        # Dil-specific interface ayarları - REQ-1.3, REQ-1.6
        self.language_interface_configs = {
            "english": {
                "name": "English",
                "direction": "ltr",  # left-to-right
                "font_family": "Arial, sans-serif",
                "instructions_language": "en",
            },
            "german": {
                "name": "Deutsch",
                "direction": "ltr",
                "font_family": "Arial, sans-serif",
                "instructions_language": "de",
            },
            "french": {
                "name": "Français",
                "direction": "ltr",
                "font_family": "Arial, sans-serif",
                "instructions_language": "fr",
            },
        }

        # Passage display optimization ayarları - REQ-1.3, REQ-1.6
        self.display_configs = {
            "passage_width": {
                "narrow": "40%",
                "medium": "50%",
                "wide": "60%",
            },
            "font_sizes": {
                "small": "14px",
                "medium": "16px",
                "large": "18px",
            },
            "line_spacings": {
                "compact": "1.2",
                "normal": "1.5",
                "relaxed": "1.8",
            },
        }

    def create_optical_form(
        self,
        exam_session_id: str,
        student_id: str,
        language: str,
        passages: list[PassageSection],
    ) -> YDTOpticalForm:
        """
        YDT optik form oluştur - REQ-1.3, REQ-1.6

        Args:
            exam_session_id: Sınav oturum ID
            student_id: Öğrenci ID
            language: Dil (english, german, french)
            passages: Metin bölümleri

        Returns:
            YDTOpticalForm: Oluşturulan optik form
        """
        optical_form = YDTOpticalForm(
            exam_session_id=exam_session_id,
            student_id=student_id,
            language=language,
            passages=passages,
        )

        # Tüm soruları boş olarak başlat
        for i in range(1, 81):
            optical_form.answers[i] = OpticalFormAnswer(question_number=i)

        logger.info(
            "YDT optik form oluşturuldu",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": student_id,
                "language": language,
                "passages_count": len(passages),
            },
        )

        return optical_form

    def mark_answer(
        self,
        optical_form: YDTOpticalForm,
        question_number: int,
        selected_option: str,
        response_time: float | None = None,
    ) -> bool:
        """
        Cevap işaretle - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form
            question_number: Soru numarası (1-80)
            selected_option: Seçilen şık (A, B, C, D, E)
            response_time: Cevaplama süresi (saniye)

        Returns:
            bool: İşlem başarılı mı?
        """
        try:
            if question_number < 1 or question_number > 80:
                logger.warning(f"Geçersiz soru numarası: {question_number}")
                return False

            if selected_option not in ["A", "B", "C", "D", "E"]:
                logger.warning(f"Geçersiz şık: {selected_option}")
                return False

            answer = optical_form.answers[question_number]

            # Önceki durum
            was_empty = answer.status == AnswerStatus.EMPTY

            # Cevabı işaretle
            answer.selected_option = selected_option
            answer.status = AnswerStatus.MARKED
            answer.response_time = response_time
            answer.marked_at = datetime.now()

            # İstatistikleri güncelle
            if was_empty:
                optical_form.answered_count += 1
                optical_form.empty_count -= 1

            logger.debug(
                "Cevap işaretlendi",
                extra_data={
                    "question_number": question_number,
                    "selected_option": selected_option,
                    "response_time": response_time,
                },
            )

            return True

        except Exception as e:
            logger.error(f"Cevap işaretleme hatası: {e}")
            return False

    def unmark_answer(self, optical_form: YDTOpticalForm, question_number: int) -> bool:
        """
        Cevap işaretini kaldır - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form
            question_number: Soru numarası (1-80)

        Returns:
            bool: İşlem başarılı mı?
        """
        try:
            if question_number < 1 or question_number > 80:
                return False

            answer = optical_form.answers[question_number]

            # Önceki durum
            was_marked = answer.status == AnswerStatus.MARKED

            # İşareti kaldır
            answer.selected_option = None
            answer.status = AnswerStatus.EMPTY
            answer.response_time = None
            answer.marked_at = None

            # İstatistikleri güncelle
            if was_marked:
                optical_form.answered_count -= 1
                optical_form.empty_count += 1

            logger.debug(f"Cevap işareti kaldırıldı: {question_number}")

            return True

        except Exception as e:
            logger.error(f"Cevap işareti kaldırma hatası: {e}")
            return False

    def flag_question(
        self, optical_form: YDTOpticalForm, question_number: int, flagged: bool
    ) -> bool:
        """
        Soruyu şüpheli olarak işaretle - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form
            question_number: Soru numarası (1-80)
            flagged: İşaretli mi?

        Returns:
            bool: İşlem başarılı mı?
        """
        try:
            if question_number < 1 or question_number > 80:
                return False

            answer = optical_form.answers[question_number]

            # Önceki durum
            was_flagged = answer.is_flagged

            # Şüpheli işareti güncelle
            answer.is_flagged = flagged

            # İstatistikleri güncelle
            if flagged and not was_flagged:
                optical_form.flagged_count += 1
            elif not flagged and was_flagged:
                optical_form.flagged_count -= 1

            logger.debug(
                f"Soru şüpheli işareti güncellendi: {question_number} -> {flagged}"
            )

            return True

        except Exception as e:
            logger.error(f"Şüpheli işaretleme hatası: {e}")
            return False

    def navigate_to_question(
        self, optical_form: YDTOpticalForm, question_number: int
    ) -> bool:
        """
        Belirli bir soruya git - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form
            question_number: Soru numarası (1-80)

        Returns:
            bool: İşlem başarılı mı?
        """
        try:
            if question_number < 1 or question_number > 80:
                return False

            optical_form.current_question = question_number

            # İlgili metni bul
            for passage in optical_form.passages:
                if question_number in passage.question_numbers:
                    optical_form.current_passage_id = passage.passage_id
                    break

            logger.debug(f"Soruya gidildi: {question_number}")

            return True

        except Exception as e:
            logger.error(f"Soru navigasyon hatası: {e}")
            return False

    def get_passage_for_question(
        self, optical_form: YDTOpticalForm, question_number: int
    ) -> PassageSection | None:
        """
        Soru için ilgili metni getir - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form
            question_number: Soru numarası

        Returns:
            Optional[PassageSection]: İlgili metin veya None
        """
        for passage in optical_form.passages:
            if question_number in passage.question_numbers:
                return passage

        return None

    def get_answer_grid(
        self, optical_form: YDTOpticalForm
    ) -> dict[int, dict[str, any]]:
        """
        Cevap ızgarasını getir (optik form görünümü için) - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form

        Returns:
            Dict: Cevap ızgarası
        """
        grid = {}

        for question_number, answer in optical_form.answers.items():
            grid[question_number] = {
                "selected": answer.selected_option,
                "status": answer.status.value,
                "flagged": answer.is_flagged,
                "response_time": answer.response_time,
            }

        return grid

    def get_completion_stats(self, optical_form: YDTOpticalForm) -> dict[str, any]:
        """
        Tamamlanma istatistiklerini getir - REQ-1.3, REQ-1.6

        Args:
            optical_form: Optik form

        Returns:
            Dict: İstatistikler
        """
        return {
            "total_questions": optical_form.total_questions,
            "answered": optical_form.answered_count,
            "empty": optical_form.empty_count,
            "flagged": optical_form.flagged_count,
            "completion_percentage": (
                optical_form.answered_count / optical_form.total_questions
            )
            * 100,
        }

    def optimize_passage_display(
        self,
        passage: PassageSection,
        screen_width: int,
        user_preferences: dict | None = None,
    ) -> dict[str, str]:
        """
        Metin görüntüleme optimizasyonu - REQ-1.3, REQ-1.6

        Args:
            passage: Metin bölümü
            screen_width: Ekran genişliği (px)
            user_preferences: Kullanıcı tercihleri

        Returns:
            Dict: Görüntüleme ayarları
        """
        # Varsayılan ayarlar
        display_settings = {
            "font_size": self.display_configs["font_sizes"]["medium"],
            "line_spacing": self.display_configs["line_spacings"]["normal"],
            "passage_width": self.display_configs["passage_width"]["medium"],
        }

        # Kullanıcı tercihlerini uygula
        if user_preferences:
            if "font_size" in user_preferences:
                display_settings["font_size"] = self.display_configs["font_sizes"].get(
                    user_preferences["font_size"], display_settings["font_size"]
                )

            if "line_spacing" in user_preferences:
                display_settings["line_spacing"] = self.display_configs[
                    "line_spacings"
                ].get(
                    user_preferences["line_spacing"], display_settings["line_spacing"]
                )

        # Ekran genişliğine göre otomatik ayarlama
        if screen_width < 768:  # Mobile
            display_settings["passage_width"] = "100%"
            display_settings["font_size"] = self.display_configs["font_sizes"]["small"]
        elif screen_width < 1024:  # Tablet
            display_settings["passage_width"] = self.display_configs["passage_width"][
                "wide"
            ]

        return display_settings

    def get_language_interface_config(self, language: str) -> dict[str, str]:
        """
        Dil-specific interface konfigürasyonunu getir - REQ-1.3, REQ-1.6

        Args:
            language: Dil (english, german, french)

        Returns:
            Dict: Interface konfigürasyonu
        """
        return self.language_interface_configs.get(
            language, self.language_interface_configs["english"]
        )


# Global YDT optical form service instance
ydt_optical_form_service = YDTOpticalFormService()
