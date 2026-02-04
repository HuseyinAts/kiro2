"""
Test Data Factories
Factory pattern for creating test data easily
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker

# Initialize Faker with Turkish locale
fake = Faker("tr_TR")


# ==================== USER FACTORIES ====================


class UserFactory:
    """Factory for creating test users"""

    @staticmethod
    def create_user_data(
        email: str = None,
        ad_soyad: str = None,
        rol: str = "ogrenci",
        aktif: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create user data dict"""
        return {
            "id": str(uuid.uuid4()),
            "email": email or fake.email(),
            "ad_soyad": ad_soyad or fake.name(),
            "rol": rol,
            "aktif": aktif,
            "kayit_tarihi": datetime.now(),
            "son_giris": None,
            **kwargs,
        }

    @staticmethod
    def create_admin(**kwargs):
        """Create admin user data"""
        return UserFactory.create_user_data(
            rol="admin",
            email=kwargs.pop("email", "admin@test.com"),
            ad_soyad=kwargs.pop("ad_soyad", "Test Admin"),
            **kwargs,
        )

    @staticmethod
    def create_student(**kwargs):
        """Create student user data"""
        return UserFactory.create_user_data(
            rol="ogrenci",
            email=kwargs.pop("email", None) or fake.email(),
            ad_soyad=kwargs.pop("ad_soyad", None) or fake.name(),
            **kwargs,
        )

    @staticmethod
    def create_teacher(**kwargs):
        """Create teacher user data"""
        return UserFactory.create_user_data(
            rol="ogretmen",
            email=kwargs.pop("email", "teacher@test.com"),
            ad_soyad=kwargs.pop("ad_soyad", "Test Teacher"),
            **kwargs,
        )

    @staticmethod
    def create_parent(**kwargs):
        """Create parent user data"""
        return UserFactory.create_user_data(
            rol="veli",
            email=kwargs.pop("email", "parent@test.com"),
            ad_soyad=kwargs.pop("ad_soyad", "Test Parent"),
            **kwargs,
        )

    @staticmethod
    def create_batch(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple users"""
        return [UserFactory.create_user_data(**kwargs) for _ in range(count)]


# ==================== QUESTION FACTORIES ====================


class QuestionFactory:
    """Factory for creating test questions"""

    SAMPLE_QUESTIONS = {
        "matematik": "2x + 5 = 15 denkleminde x kaçtır?",
        "turkce": "Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?",
        "fen": "Bir cismin hızı 10 m/s ise 5 saniyede kaç metre yol alır?",
        "sosyal": "Osmanlı Devleti'nin kuruluş tarihi aşağıdakilerden hangisidir?",
    }

    SAMPLE_OPTIONS = {
        "A": "Seçenek A",
        "B": "Seçenek B",
        "C": "Seçenek C",
        "D": "Seçenek D",
        "E": "Seçenek E",
    }

    @staticmethod
    def create_question_data(
        konu: str = "Matematik",
        alt_konu: str = "Denklemler",
        zorluk_seviyesi: str = "orta",
        dogru_cevap: str = "A",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create question data dict"""
        soru_metni = kwargs.pop(
            "soru_metni",
            QuestionFactory.SAMPLE_QUESTIONS.get(konu.lower(), "Test sorusu?"),
        )

        return {
            "soru_id": str(uuid.uuid4()),
            "konu": konu,
            "alt_konu": alt_konu,
            "zorluk_seviyesi": zorluk_seviyesi,
            "soru_metni": soru_metni,
            "secenekler": QuestionFactory.SAMPLE_OPTIONS.copy(),
            "dogru_cevap": dogru_cevap,
            "aciklama": "Test sorusu açıklaması",
            "irt_a_parametresi": 1.0,
            "irt_b_parametresi": 0.0,
            "irt_c_parametresi": 0.25,
            "aktif": True,
            "olusturma_tarihi": datetime.now(),
            **kwargs,
        }

    @staticmethod
    def create_easy_question(**kwargs):
        """Create easy question"""
        return QuestionFactory.create_question_data(zorluk_seviyesi="kolay", **kwargs)

    @staticmethod
    def create_hard_question(**kwargs):
        """Create hard question"""
        return QuestionFactory.create_question_data(zorluk_seviyesi="zor", **kwargs)

    @staticmethod
    def create_batch(
        count: int = 10, konu: str = "Matematik", **kwargs
    ) -> List[Dict[str, Any]]:
        """Create multiple questions"""
        return [
            QuestionFactory.create_question_data(konu=konu, **kwargs)
            for _ in range(count)
        ]

    @staticmethod
    def create_mixed_difficulty_batch(
        count: int = 15, **kwargs
    ) -> List[Dict[str, Any]]:
        """Create questions with mixed difficulty"""
        questions = []
        difficulties = ["kolay", "orta", "zor"]

        for i in range(count):
            questions.append(
                QuestionFactory.create_question_data(
                    zorluk_seviyesi=difficulties[i % 3], **kwargs
                )
            )

        return questions


# ==================== EXAM FACTORIES ====================


class ExamFactory:
    """Factory for creating test exams"""

    @staticmethod
    def create_exam_data(
        sinav_tipi: str = "TYT",
        baslik: str = "Test Sınavı",
        sure_dakika: int = 120,
        toplam_soru: int = 40,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create exam data dict"""
        return {
            "sinav_id": str(uuid.uuid4()),
            "sinav_tipi": sinav_tipi,
            "baslik": baslik,
            "sure_dakika": sure_dakika,
            "toplam_soru_sayisi": toplam_soru,
            "baslangic_zamani": datetime.now(),
            "bitis_zamani": None,
            "durum": "devam_ediyor",
            "aktif": True,
            **kwargs,
        }

    @staticmethod
    def create_tyt_exam(**kwargs):
        """Create TYT exam"""
        return ExamFactory.create_exam_data(
            sinav_tipi="TYT",
            baslik="TYT Deneme Sınavı",
            sure_dakika=135,
            toplam_soru=120,
            **kwargs,
        )

    @staticmethod
    def create_ayt_exam(**kwargs):
        """Create AYT exam"""
        return ExamFactory.create_exam_data(
            sinav_tipi="AYT",
            baslik="AYT Deneme Sınavı",
            sure_dakika=180,
            toplam_soru=80,
            **kwargs,
        )

    @staticmethod
    def create_completed_exam(**kwargs):
        """Create completed exam"""
        return ExamFactory.create_exam_data(
            durum="tamamlandi", bitis_zamani=datetime.now(), **kwargs
        )


# ==================== EXAM RESULT FACTORIES ====================


class ExamResultFactory:
    """Factory for creating exam results"""

    @staticmethod
    def create_result_data(
        toplam_dogru: int = 30, toplam_yanlis: int = 5, toplam_bos: int = 5, **kwargs
    ) -> Dict[str, Any]:
        """Create exam result data"""
        net_puan = toplam_dogru - (toplam_yanlis / 4)

        return {
            "sonuc_id": str(uuid.uuid4()),
            "toplam_dogru": toplam_dogru,
            "toplam_yanlis": toplam_yanlis,
            "toplam_bos": toplam_bos,
            "net_puan": net_puan,
            "yuzdelik_dilim": 75.0,
            "zpd_alt_sinir": 5.0,
            "zpd_ust_sinir": 8.0,
            "optimal_zorluk": 6.5,
            "irt_yetenek_seviyesi": 0.5,
            "hesaplama_tarihi": datetime.now(),
            **kwargs,
        }

    @staticmethod
    def create_high_score_result(**kwargs):
        """Create high score result"""
        return ExamResultFactory.create_result_data(
            toplam_dogru=35,
            toplam_yanlis=2,
            toplam_bos=3,
            yuzdelik_dilim=95.0,
            **kwargs,
        )

    @staticmethod
    def create_low_score_result(**kwargs):
        """Create low score result"""
        return ExamResultFactory.create_result_data(
            toplam_dogru=15,
            toplam_yanlis=15,
            toplam_bos=10,
            yuzdelik_dilim=25.0,
            **kwargs,
        )


# ==================== EDUCATIONAL CONTENT FACTORIES ====================


class ContentFactory:
    """Factory for creating educational content"""

    @staticmethod
    def create_content_data(
        baslik: str = None,
        icerik_tipi: str = "video",
        konu: str = "Matematik",
        url: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create content data"""
        return {
            "icerik_id": str(uuid.uuid4()),
            "baslik": baslik or fake.sentence(nb_words=6),
            "aciklama": fake.text(max_nb_chars=200),
            "icerik_tipi": icerik_tipi,
            "konu": konu,
            "alt_konu": kwargs.pop("alt_konu", "Genel"),
            "zorluk_seviyesi": kwargs.pop("zorluk_seviyesi", "orta"),
            "url": url or f"https://youtube.com/watch?v={fake.lexify('??????????')}",
            "sure_dakika": kwargs.pop("sure_dakika", 15),
            "kalite_skoru": kwargs.pop("kalite_skoru", 0.8),
            "aktif": True,
            "olusturma_tarihi": datetime.now(),
            **kwargs,
        }

    @staticmethod
    def create_video_content(**kwargs):
        """Create video content"""
        return ContentFactory.create_content_data(icerik_tipi="video", **kwargs)

    @staticmethod
    def create_article_content(**kwargs):
        """Create article content"""
        return ContentFactory.create_content_data(
            icerik_tipi="metin", url=None, **kwargs
        )

    @staticmethod
    def create_batch(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple content items"""
        return [ContentFactory.create_content_data(**kwargs) for _ in range(count)]


# ==================== COMBINED FACTORIES ====================


class TestDataBuilder:
    """
    Builder for creating complete test scenarios
    Combines multiple factories
    """

    @staticmethod
    def create_student_with_exams(
        exam_count: int = 3,
    ) -> Dict[str, Any]:
        """
        Create a student with exam history

        Returns:
            {
                'student': user_data,
                'exams': [exam_data, ...],
                'results': [result_data, ...]
            }
        """
        student = UserFactory.create_student()
        exams = []
        results = []

        for i in range(exam_count):
            exam = ExamFactory.create_completed_exam(ogrenci_id=student["id"])
            exams.append(exam)

            result = ExamResultFactory.create_result_data(
                sinav_id=exam["sinav_id"], ogrenci_id=student["id"]
            )
            results.append(result)

        return {"student": student, "exams": exams, "results": results}

    @staticmethod
    def create_exam_with_questions(
        question_count: int = 40,
    ) -> Dict[str, Any]:
        """
        Create an exam with questions

        Returns:
            {
                'exam': exam_data,
                'questions': [question_data, ...]
            }
        """
        exam = ExamFactory.create_exam_data()
        questions = QuestionFactory.create_mixed_difficulty_batch(count=question_count)

        return {"exam": exam, "questions": questions}

    @staticmethod
    def create_complete_test_scenario() -> Dict[str, Any]:
        """
        Create complete test scenario with all entities

        Returns:
            {
                'students': [...],
                'teachers': [...],
                'questions': [...],
                'exams': [...],
                'results': [...],
                'content': [...]
            }
        """
        return {
            "students": UserFactory.create_batch(10, rol="ogrenci"),
            "teachers": [UserFactory.create_teacher() for _ in range(3)],
            "questions": QuestionFactory.create_batch(100),
            "exams": [ExamFactory.create_exam_data() for _ in range(5)],
            "results": [ExamResultFactory.create_result_data() for _ in range(20)],
            "content": ContentFactory.create_batch(50),
        }


# ==================== HELPER FUNCTIONS ====================


def reset_faker_seed(seed: int = 42):
    """Reset Faker seed for reproducible tests"""
    Faker.seed(seed)


def create_time_series_data(
    factory_func,
    count: int,
    start_date: datetime = None,
    interval_days: int = 1,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Create time series data using any factory

    Args:
        factory_func: Factory function to use
        count: Number of items
        start_date: Start date (default: 30 days ago)
        interval_days: Days between items
        **kwargs: Additional factory arguments
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)

    items = []
    for i in range(count):
        item = factory_func(**kwargs)
        item["olusturma_tarihi"] = start_date + timedelta(days=i * interval_days)
        items.append(item)

    return items
