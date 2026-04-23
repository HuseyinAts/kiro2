"""
YDT (Yabancı Dil Testi) Sınav Servisi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül YDT sınavlarına özel işlevleri yönetir:
- İngilizce, Almanca, Fransızca dil desteği
- Reading comprehension (okuma anlama) soruları
- Grammar (dilbilgisi) ve vocabulary (kelime bilgisi) soruları
- Passage-based (metin tabanlı) soru yapısı
"""

from dataclasses import dataclass
from enum import Enum

from core.structured_logger import get_logger

logger = get_logger("ydt_exam_service")


class YDTLanguage(Enum):
    """YDT dil seçenekleri - REQ-1.3"""

    ENGLISH = "english"  # İngilizce
    GERMAN = "german"  # Almanca
    FRENCH = "french"  # Fransızca


class YDTQuestionType(Enum):
    """YDT soru türleri - REQ-1.3"""

    READING_COMPREHENSION = "reading_comprehension"  # Okuma anlama
    GRAMMAR = "grammar"  # Dilbilgisi
    VOCABULARY = "vocabulary"  # Kelime bilgisi
    PASSAGE_BASED = "passage_based"  # Metin tabanlı


@dataclass
class YDTPassage:
    """YDT metin (passage) modeli"""

    passage_id: str
    language: YDTLanguage
    title: str
    content: str
    difficulty_level: str  # kolay, orta, zor
    word_count: int
    topic: str  # Konu (örn: "Science", "History", "Literature")

    # Meta veriler
    source: str | None = None
    author: str | None = None
    year: int | None = None


@dataclass
class YDTQuestion:
    """YDT soru modeli"""

    question_id: str
    language: YDTLanguage
    question_type: YDTQuestionType
    question_text: str
    correct_answer: str
    difficulty_level: str
    topic: str
    skill_tested: str  # Test edilen beceri (örn: "inference", "main idea", "vocabulary in context")
    options: list[str] = None  # A, B, C, D, E seçenekleri

    # Passage-based sorular için
    passage_id: str | None = None
    passage_reference: str | None = None  # Metinde hangi bölüme atıfta bulunuyor

    # Metadata
    explanation: str | None = None

    def __post_init__(self):
        """Post-initialization to set default mutable values"""
        if self.options is None:
            self.options = []


class YDTExamService:
    """
    YDT Sınav Servisi

    Bu servis YDT sınavlarına özel işlevleri sağlar:
    - Dil bazlı soru seçimi (İngilizce, Almanca, Fransızca)
    - Reading comprehension passage yönetimi
    - Grammar ve vocabulary soru yapılandırması
    """

    def __init__(self):
        # YDT sınav konfigürasyonu - REQ-1.3
        self.ydt_config = {
            "total_questions": 80,
            "duration_minutes": 120,  # 2 saat
            "question_distribution": {
                "reading_comprehension": 50,  # %62.5 - Okuma anlama (passage-based)
                "grammar": 20,  # %25 - Dilbilgisi
                "vocabulary": 10,  # %12.5 - Kelime bilgisi
            },
        }

        # Dil bazlı konfigürasyonlar
        self.language_configs = {
            YDTLanguage.ENGLISH: {
                "name": "İngilizce",
                "code": "EN",
                "subject_code": "INGILIZCE",
            },
            YDTLanguage.GERMAN: {
                "name": "Almanca",
                "code": "DE",
                "subject_code": "ALMANCA",
            },
            YDTLanguage.FRENCH: {
                "name": "Fransızca",
                "code": "FR",
                "subject_code": "FRANSIZCA",
            },
        }

    def get_language_config(self, language: YDTLanguage) -> dict:
        """
        Dil konfigürasyonunu getir

        Args:
            language: YDT dil seçeneği

        Returns:
            dict: Dil konfigürasyonu
        """
        return self.language_configs.get(
            language, self.language_configs[YDTLanguage.ENGLISH]
        )

    def get_question_distribution(self) -> dict:
        """
        YDT soru dağılımını getir

        Returns:
            dict: Soru türü bazlı dağılım
        """
        return self.ydt_config["question_distribution"]

    def validate_ydt_exam_structure(
        self, questions: list[YDTQuestion], language: YDTLanguage
    ) -> tuple[bool, str]:
        """
        YDT sınav yapısını doğrula

        Args:
            questions: Sınav soruları
            language: Seçilen dil

        Returns:
            tuple[bool, str]: (Geçerli mi?, Hata mesajı)
        """
        try:
            # Toplam soru sayısı kontrolü - REQ-1.3
            if len(questions) != self.ydt_config["total_questions"]:
                return (
                    False,
                    f"YDT sınavı {self.ydt_config['total_questions']} soru içermelidir",
                )

            # Dil kontrolü
            for question in questions:
                if question.language != language:
                    return False, f"Tüm sorular {language.value} dilinde olmalıdır"

            # Soru türü dağılımı kontrolü
            question_type_counts = {
                "reading_comprehension": 0,
                "grammar": 0,
                "vocabulary": 0,
            }

            for question in questions:
                q_type = (
                    question.question_type.value
                    if isinstance(question.question_type, YDTQuestionType)
                    else question.question_type
                )
                if q_type in question_type_counts:
                    question_type_counts[q_type] += 1

            expected_dist = self.ydt_config["question_distribution"]

            # Okuma anlama kontrolü
            if (
                question_type_counts[YDTQuestionType.READING_COMPREHENSION]
                < expected_dist["reading_comprehension"] - 5
            ):
                return False, "Okuma anlama soruları yetersiz"

            # Dilbilgisi kontrolü
            if (
                question_type_counts[YDTQuestionType.GRAMMAR]
                < expected_dist["grammar"] - 5
            ):
                return False, "Dilbilgisi soruları yetersiz"

            # Kelime bilgisi kontrolü
            if (
                question_type_counts[YDTQuestionType.VOCABULARY]
                < expected_dist["vocabulary"] - 3
            ):
                return False, "Kelime bilgisi soruları yetersiz"

            logger.info(
                "YDT sınav yapısı doğrulandı",
                extra_data={
                    "language": language.value
                    if isinstance(language, YDTLanguage)
                    else language,
                    "total_questions": len(questions),
                    "distribution": question_type_counts,
                },
            )

            return True, "YDT sınav yapısı geçerli"

        except Exception as e:
            error_msg = f"Doğrulama hatası: {e!s}"
            logger.error(f"YDT sınav yapısı doğrulama hatası: {error_msg}")
            return False, error_msg

    def calculate_reading_time_suggestion(
        self, passage: YDTPassage, questions_count: int
    ) -> int:
        """
        Metin okuma süresi önerisi hesapla - REQ-1.3, REQ-1.6

        Args:
            passage: Metin
            questions_count: Metne ait soru sayısı

        Returns:
            int: Önerilen okuma süresi (dakika)
        """
        # Ortalama okuma hızı: 200-250 kelime/dakika
        # YDT için daha yavaş okuma varsayımı: 150 kelime/dakika
        reading_speed = 150

        # Metin okuma süresi
        reading_time = passage.word_count / reading_speed

        # Soru başına ek süre (1.5 dakika)
        question_time = questions_count * 1.5

        # Toplam önerilen süre
        total_time = reading_time + question_time

        return max(5, int(total_time))  # Minimum 5 dakika

    def get_time_warnings(self, remaining_minutes: int) -> str | None:
        """
        Süre uyarıları getir - REQ-1.3, REQ-1.6

        Args:
            remaining_minutes: Kalan süre (dakika)

        Returns:
            Optional[str]: Uyarı mesajı
        """
        if remaining_minutes <= 5:
            return "⚠️ Son 5 dakika! Lütfen cevaplarınızı kontrol edin."
        if remaining_minutes <= 15:
            return "⏰ 15 dakika kaldı. Boş bıraktığınız soruları gözden geçirin."
        if remaining_minutes <= 30:
            return "📝 30 dakika kaldı. Zamanınızı iyi yönetin."

        return None

    def generate_completion_warning(
        self, answered_count: int, total_questions: int, remaining_minutes: int
    ) -> str | None:
        """
        Tamamlama uyarısı oluştur - REQ-1.3, REQ-1.6

        Args:
            answered_count: Cevaplanan soru sayısı
            total_questions: Toplam soru sayısı
            remaining_minutes: Kalan süre (dakika)

        Returns:
            Optional[str]: Uyarı mesajı
        """
        unanswered = total_questions - answered_count

        if unanswered == 0:
            return "✅ Tüm soruları cevapladınız. İsterseniz cevaplarınızı gözden geçirebilirsiniz."

        if remaining_minutes <= 10 and unanswered > 10:
            return f"⚠️ {unanswered} soru boş! Kalan süre: {remaining_minutes} dakika. Hızlı cevap vermeye çalışın."

        if remaining_minutes <= 5 and unanswered > 0:
            return f"🚨 UYARI: {unanswered} soru boş! Son {remaining_minutes} dakika!"

        return None


# Global YDT exam service instance
ydt_exam_service = YDTExamService()
