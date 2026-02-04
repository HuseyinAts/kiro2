"""
Models Test Dosyası
Tüm Pydantic modellerinin testleri
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

# Model importları
from models import (
    # User modelleri
    User,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserRole,
    # Student modelleri
    Student,
    StudentProfile,
    StudentCreate,
    StudentUpdate,
    OgrenciProfili,
    # Learning Style modelleri
    LearningStyle,
    VARKProfile,
    FelderSilvermanProfile,
    HybridLearningProfile,
    LearningStyleDetectionResult,
    # Sınav modelleri
    SinavTipi,
    SinavDurumu,
    SinavSorusu,
    SinavOturumu,
    SinavCevabi,
    SinavSonucu,
    # Soru modelleri
    Question,
    QuestionCreate,
    QuestionUpdate,
    QuestionDifficulty,
    QuestionType,
    # Content modelleri
    MakaleIcerik,
    VideoIcerik,
    ContentType,
    # ZPD modelleri
    ZPDLevel,
    ZPDCalculation,
    TurkishCulturalFactors,
    # IRT modelleri
    IRTParameters,
    IRTAnalysis,
    MorphologicalComplexity,
    # Performance modelleri
    PerformanceMetrics,
    StudySession,
    ProgressReport,
    # Enum'lar
    Konu,
    DifficultyLevel,
    QuestionStatus,
    ExamStatus,
)


# Fixtures
@pytest.fixture
def sample_user_data():
    """Örnek kullanıcı verisi"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecurePass123!",
        "role": UserRole.STUDENT,
    }


@pytest.fixture
def sample_student_data():
    """Örnek öğrenci verisi"""
    return {
        "user_id": str(uuid4()),
        "name": "Ali Veli",
        "grade": 11,
        "school": "Atatürk Lisesi",
        "target_university": "Boğaziçi Üniversitesi",
        "target_department": "Bilgisayar Mühendisliği",
        "study_hours_per_day": 6,
        "exam_date": datetime.now() + timedelta(days=180),
    }


@pytest.fixture
def sample_question_data():
    """Örnek soru verisi"""
    return {
        "question_text": "2x + 5 = 15 denkleminde x kaçtır?",
        "options": ["3", "5", "7", "10"],
        "correct_answer": "5",
        "subject": "Matematik",
        "topic": "Denklemler",
        "difficulty": QuestionDifficulty.MEDIUM,
        "points": 4,
        "explanation": "2x + 5 = 15 => 2x = 10 => x = 5",
    }


# User Model Testleri
class TestUserModels:
    """Kullanıcı modelleri testleri"""

    def test_user_creation(self, sample_user_data):
        """User modelinin oluşturulması"""
        user = UserCreate(**sample_user_data)

        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.role == UserRole.STUDENT

    def test_user_email_validation(self):
        """Email validasyonu"""
        with pytest.raises(ValueError):
            UserCreate(
                username="test",
                email="invalid_email",
                password="Pass123!",
                full_name="Test",
            )

    def test_user_password_validation(self):
        """Şifre validasyonu"""
        with pytest.raises(ValueError):
            UserCreate(
                username="test",
                email="test@test.com",
                password="weak",  # Zayıf şifre
                full_name="Test",
            )

    def test_user_role_enum(self):
        """UserRole enum testi"""
        assert UserRole.STUDENT.value == "student"
        assert UserRole.TEACHER.value == "teacher"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.PARENT.value == "parent"


# Student Model Testleri
class TestStudentModels:
    """Öğrenci modelleri testleri"""

    def test_student_creation(self, sample_student_data):
        """Student modelinin oluşturulması"""
        student = Student(**sample_student_data)

        assert student.name == "Ali Veli"
        assert student.grade == 11
        assert student.study_hours_per_day == 6

    def test_student_grade_validation(self):
        """Sınıf seviyesi validasyonu"""
        with pytest.raises(ValueError):
            Student(
                user_id=str(uuid4()),
                name="Test",
                grade=13,  # Geçersiz sınıf
                school="Test Lisesi",
            )

    def test_student_profile_creation(self):
        """StudentProfile oluşturulması"""
        profile = StudentProfile(
            student_id=str(uuid4()),
            strengths=["Matematik", "Fizik"],
            weaknesses=["Tarih"],
            learning_style="visual",
            preferred_study_time="morning",
            concentration_span=45,
        )

        assert len(profile.strengths) == 2
        assert profile.concentration_span == 45


# Learning Style Model Testleri
class TestLearningStyleModels:
    """Öğrenme stili modelleri testleri"""

    def test_vark_profile_creation(self):
        """VARK profili oluşturulması"""
        vark = VARKProfile(visual=0.7, auditory=0.5, reading=0.8, kinesthetic=0.4)

        assert vark.visual == 0.7
        assert vark.get_dominant_style() == "reading"

    def test_felder_silverman_profile(self):
        """Felder-Silverman profili"""
        felder = FelderSilvermanProfile(
            active_reflective=0.3,
            sensing_intuitive=-0.2,
            visual_verbal=0.6,
            sequential_global=-0.4,
        )

        assert felder.active_reflective == 0.3
        assert felder.is_active() == True
        assert felder.is_intuitive() == True

    def test_hybrid_learning_profile(self):
        """Hibrit öğrenme profili"""
        hybrid = HybridLearningProfile(
            student_id=str(uuid4()),
            vark_code="VR",
            felder_code="AIVG",
            hybrid_code="VR-AIVG",
            confidence_level=0.85,
            last_updated=datetime.now(),
        )

        assert hybrid.hybrid_code == "VR-AIVG"
        assert hybrid.confidence_level == 0.85
        assert hybrid.is_high_confidence() == True


# Sınav Model Testleri
class TestExamModels:
    """Sınav modelleri testleri"""

    def test_sinav_tipi_enum(self):
        """SinavTipi enum testi"""
        assert SinavTipi.TYT.value == "TYT"
        assert SinavTipi.AYT.value == "AYT"
        assert SinavTipi.YDT.value == "YDT"

    def test_sinav_sorusu_creation(self):
        """SinavSorusu oluşturulması"""
        soru = SinavSorusu(
            soru_id=str(uuid4()),
            soru_metni="Test sorusu",
            secenekler=["A", "B", "C", "D"],
            dogru_cevap="B",
            konu="Matematik",
            zorluk=3,
            puan=4,
            sure_saniye=60,
        )

        assert soru.dogru_cevap == "B"
        assert soru.puan == 4
        assert len(soru.secenekler) == 4

    def test_sinav_oturumu_creation(self):
        """SinavOturumu oluşturulması"""
        oturum = SinavOturumu(
            sinav_id=str(uuid4()),
            ogrenci_id=str(uuid4()),
            sinav_tipi=SinavTipi.TYT,
            toplam_soru_sayisi=120,
            sure_dakika=165,
            baslangic_zamani=datetime.now(),
            durum=SinavDurumu.DEVAM_EDIYOR,
        )

        assert oturum.toplam_soru_sayisi == 120
        assert oturum.sure_dakika == 165
        assert oturum.durum == SinavDurumu.DEVAM_EDIYOR

    def test_sinav_sonucu_calculation(self):
        """SinavSonucu net hesaplaması"""
        sonuc = SinavSonucu(
            sonuc_id=str(uuid4()),
            sinav_id=str(uuid4()),
            ogrenci_id=str(uuid4()),
            dogru_sayisi=80,
            yanlis_sayisi=20,
            bos_sayisi=20,
            toplam_soru=120,
        )

        # Net hesaplama: Doğru - (Yanlış/4)
        expected_net = 80 - (20 / 4)
        assert sonuc.calculate_net() == expected_net
        assert sonuc.calculate_success_rate() == (expected_net / 120) * 100


# Question Model Testleri
class TestQuestionModels:
    """Soru modelleri testleri"""

    def test_question_creation(self, sample_question_data):
        """Question modelinin oluşturulması"""
        question = Question(**sample_question_data)

        assert question.question_text == sample_question_data["question_text"]
        assert question.correct_answer == "5"
        assert question.difficulty == QuestionDifficulty.MEDIUM

    def test_question_difficulty_enum(self):
        """QuestionDifficulty enum testi"""
        assert QuestionDifficulty.VERY_EASY.value == 1
        assert QuestionDifficulty.EASY.value == 2
        assert QuestionDifficulty.MEDIUM.value == 3
        assert QuestionDifficulty.HARD.value == 4
        assert QuestionDifficulty.VERY_HARD.value == 5

    def test_question_validation(self):
        """Soru validasyonu"""
        with pytest.raises(ValueError):
            Question(
                question_text="",  # Boş soru metni
                options=["A", "B"],  # Az seçenek
                correct_answer="C",  # Seçeneklerde yok
                subject="Math",
                topic="Test",
            )


# Content Model Testleri
class TestContentModels:
    """İçerik modelleri testleri"""

    def test_makale_icerik_creation(self):
        """MakaleIcerik oluşturulması"""
        makale = MakaleIcerik(
            baslik="Python Programlama",
            icerik="Python öğrenme içeriği...",
            ozet="Python temelleri",
            yazar="Ahmet Yılmaz",
            kategori="Programlama",
            etiketler=["python", "programlama", "temel"],
            okunma_suresi=15,
            goruntuleme_sayisi=150,
            begeni_sayisi=45,
        )

        assert makale.baslik == "Python Programlama"
        assert makale.okunma_suresi == 15
        assert len(makale.etiketler) == 3
        assert makale.aktif == True

    def test_video_icerik_creation(self):
        """VideoIcerik oluşturulması"""
        video = VideoIcerik(
            baslik="Matematik - Türev",
            video_url="https://youtube.com/watch?v=abc123",
            aciklama="Türev konusu detaylı anlatım",
            sure=1200,  # 20 dakika
            kategori="Matematik",
            etiketler=["matematik", "türev", "calculus"],
            izlenme_sayisi=500,
        )

        assert video.baslik == "Matematik - Türev"
        assert video.sure == 1200
        assert video.izlenme_sayisi == 500
        assert video.get_duration_minutes() == 20

    def test_content_type_enum(self):
        """ContentType enum testi"""
        assert ContentType.MAKALE.value == "makale"
        assert ContentType.VIDEO.value == "video"
        assert ContentType.QUIZ.value == "quiz"
        assert ContentType.INFOGRAFIK.value == "infografik"


# ZPD Model Testleri
class TestZPDModels:
    """ZPD (Zone of Proximal Development) modelleri testleri"""

    def test_zpd_level_creation(self):
        """ZPD seviyesi oluşturulması"""
        zpd = ZPDLevel(
            student_id=str(uuid4()),
            subject="Matematik",
            current_level=6.5,
            lower_bound=5.0,
            upper_bound=8.0,
            optimal_challenge=7.0,
            confidence=0.85,
        )

        assert zpd.current_level == 6.5
        assert zpd.is_in_zone(7.0) == True
        assert zpd.is_too_easy(4.0) == True
        assert zpd.is_too_hard(9.0) == True

    def test_turkish_cultural_factors(self):
        """Türk kültürel faktörleri"""
        factors = TurkishCulturalFactors(
            group_study_preference=0.8,
            teacher_respect_level=0.95,
            family_involvement=0.7,
            competitive_spirit=0.6,
            collective_identity=0.85,
        )

        assert factors.group_study_preference == 0.8
        assert factors.calculate_cultural_coefficient() > 0


# IRT Model Testleri
class TestIRTModels:
    """IRT (Item Response Theory) modelleri testleri"""

    def test_irt_parameters_creation(self):
        """IRT parametreleri oluşturulması"""
        irt = IRTParameters(
            question_id=str(uuid4()),
            discrimination=1.2,
            difficulty=0.5,
            guessing=0.25,
            upper_asymptote=0.95,
        )

        assert irt.discrimination == 1.2
        assert irt.difficulty == 0.5
        assert irt.guessing == 0.25

    def test_irt_probability_calculation(self):
        """IRT olasılık hesaplaması"""
        irt = IRTParameters(
            question_id=str(uuid4()), discrimination=1.0, difficulty=0.0, guessing=0.2
        )

        # Theta = 0 için olasılık hesapla
        prob = irt.calculate_probability(theta=0.0)
        assert 0.2 <= prob <= 1.0

    def test_morphological_complexity(self):
        """Morfolojik karmaşıklık analizi"""
        morph = MorphologicalComplexity(
            word="öğrencilerimizden",
            root="öğrenci",
            suffixes=["ler", "imiz", "den"],
            complexity_score=0.75,
        )

        assert morph.root == "öğrenci"
        assert len(morph.suffixes) == 3
        assert morph.complexity_score == 0.75


# Performance Model Testleri
class TestPerformanceModels:
    """Performans modelleri testleri"""

    def test_performance_metrics_creation(self):
        """PerformanceMetrics oluşturulması"""
        metrics = PerformanceMetrics(
            student_id=str(uuid4()),
            subject="Fizik",
            accuracy=0.78,
            speed=0.65,
            consistency=0.82,
            improvement_rate=0.15,
            study_efficiency=0.70,
        )

        assert metrics.accuracy == 0.78
        assert metrics.get_overall_score() > 0

    def test_study_session_creation(self):
        """StudySession oluşturulması"""
        session = StudySession(
            session_id=str(uuid4()),
            student_id=str(uuid4()),
            subject="Kimya",
            topic="Periyodik Tablo",
            start_time=datetime.now(),
            duration_minutes=45,
            questions_solved=15,
            correct_answers=12,
            focus_score=0.85,
        )

        assert session.duration_minutes == 45
        assert session.calculate_accuracy() == 0.8
        assert session.is_productive() == True

    def test_progress_report_generation(self):
        """ProgressReport oluşturulması"""
        report = ProgressReport(
            student_id=str(uuid4()),
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_study_hours=120,
            subjects_studied=["Matematik", "Fizik", "Kimya"],
            average_accuracy=0.75,
            strongest_subject="Matematik",
            weakest_subject="Kimya",
            improvement_areas=["Kimya formülleri", "İntegral"],
            recommendations=["Kimya'ya daha fazla zaman ayır"],
        )

        assert report.total_study_hours == 120
        assert len(report.subjects_studied) == 3
        assert report.strongest_subject == "Matematik"


# Validation ve Edge Case Testleri
class TestValidationAndEdgeCases:
    """Validasyon ve edge case testleri"""

    def test_empty_string_validation(self):
        """Boş string validasyonu"""
        with pytest.raises(ValueError):
            User(username="", email="test@test.com", password="Pass123!")

    def test_negative_number_validation(self):
        """Negatif sayı validasyonu"""
        with pytest.raises(ValueError):
            Question(
                question_text="Test",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                points=-5,  # Negatif puan
                subject="Test",
            )

    def test_future_date_validation(self):
        """Gelecek tarih validasyonu"""
        with pytest.raises(ValueError):
            StudySession(
                session_id=str(uuid4()),
                student_id=str(uuid4()),
                start_time=datetime.now() + timedelta(days=1),  # Gelecek tarih
                duration_minutes=30,
                subject="Test",
            )

    def test_percentage_bounds_validation(self):
        """Yüzde değerleri sınır kontrolü"""
        with pytest.raises(ValueError):
            PerformanceMetrics(
                student_id=str(uuid4()),
                subject="Test",
                accuracy=1.5,  # %150 olamaz
                speed=0.8,
            )

    def test_list_max_length_validation(self):
        """Liste maksimum uzunluk kontrolü"""
        with pytest.raises(ValueError):
            Question(
                question_text="Test",
                options=["A", "B", "C", "D", "E", "F", "G", "H"],  # Çok fazla seçenek
                correct_answer="A",
                subject="Test",
            )


# Integration Testleri
class TestModelIntegration:
    """Model entegrasyon testleri"""

    def test_user_student_relationship(self):
        """User ve Student ilişkisi"""
        user = User(
            id=str(uuid4()),
            username="ali_veli",
            email="ali@test.com",
            role=UserRole.STUDENT,
        )

        student = Student(
            user_id=user.id, name="Ali Veli", grade=11, school="Test Lisesi"
        )

        assert student.user_id == user.id

    def test_exam_question_relationship(self):
        """Sınav ve soru ilişkisi"""
        questions = [
            SinavSorusu(
                soru_id=str(uuid4()),
                soru_metni=f"Soru {i}",
                secenekler=["A", "B", "C", "D"],
                dogru_cevap="A",
                konu="Test",
                puan=4,
            )
            for i in range(10)
        ]

        exam = SinavOturumu(
            sinav_id=str(uuid4()),
            ogrenci_id=str(uuid4()),
            sinav_tipi=SinavTipi.TYT,
            sorular=questions,
            toplam_soru_sayisi=len(questions),
        )

        assert len(exam.sorular) == 10
        assert exam.calculate_total_points() == 40

    def test_learning_performance_relationship(self):
        """Öğrenme stili ve performans ilişkisi"""
        learning_style = HybridLearningProfile(
            student_id=str(uuid4()), hybrid_code="V-ASVS", confidence_level=0.9
        )

        performance = PerformanceMetrics(
            student_id=learning_style.student_id,
            subject="Matematik",
            accuracy=0.85,
            learning_style_match=0.9,
        )

        assert performance.student_id == learning_style.student_id
        assert performance.is_style_compatible(learning_style.hybrid_code)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
