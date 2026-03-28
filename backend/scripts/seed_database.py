#!/usr/bin/env python3
"""
Database Seeding Script
Türkiye Üniversite Sınavları Hazırlık Platformu için production data seeding
"""

import asyncio
import json
import logging
import os
import sys
from datetime import date

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from core.database import db_manager, get_db_session_context
from models.database import (
    ClassRoom,
    EducationalContent,
    ExamType,
    ParentProfile,
    Question,
    QuestionDifficulty,
    StudentProfile,
    SubjectArea,
    SystemConfiguration,
    TeacherProfile,
    User,
    UserRole,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeding sınıfı"""

    def __init__(self):
        self.seeded_counts = {
            "users": 0,
            "questions": 0,
            "educational_contents": 0,
            "system_configurations": 0,
            "classrooms": 0,
        }

    async def seed_all(self):
        """Tüm seed işlemlerini çalıştır"""
        logger.info("🌱 Database seeding başlatılıyor...")

        try:
            await db_manager.initialize()

            # Seed işlemleri sırasıyla
            await self.seed_system_configurations()
            await self.seed_admin_users()
            await self.seed_sample_teachers()
            await self.seed_sample_students()
            await self.seed_sample_parents()
            await self.seed_sample_questions()
            await self.seed_educational_contents()
            await self.seed_classrooms()

            # Özet rapor
            await self.print_seeding_summary()

            logger.info("[CHECK] Database seeding tamamlandı!")

        except Exception as e:
            logger.error(f"[X] Database seeding hatası: {e!s}")
            raise
        finally:
            await db_manager.close()

    async def seed_system_configurations(self):
        """Sistem konfigürasyonlarını seed et"""
        logger.info("[CLIPBOARD] Sistem konfigürasyonları ekleniyor...")

        configs = [
            {
                "config_key": "platform_name",
                "config_value": "Türkiye Üniversite Sınavları Hazırlık Platformu",
                "config_type": "string",
                "description": "Platform adı",
            },
            {
                "config_key": "platform_version",
                "config_value": "1.0.0",
                "config_type": "string",
                "description": "Platform versiyonu",
            },
            {
                "config_key": "max_exam_duration_minutes",
                "config_value": "210",
                "config_type": "integer",
                "description": "Maksimum sınav süresi (dakika)",
            },
            {
                "config_key": "default_questions_per_exam",
                "config_value": "120",
                "config_type": "integer",
                "description": "Varsayılan sınav soru sayısı",
            },
            {
                "config_key": "enable_revolutionary_features",
                "config_value": "true",
                "config_type": "boolean",
                "description": "Devrimsel özellikleri etkinleştir",
            },
            {
                "config_key": "fsrs_default_parameters",
                "config_value": json.dumps(
                    [
                        0.4,
                        0.7,
                        2.4,
                        5.8,
                        4.93,
                        0.94,
                        0.86,
                        0.01,
                        1.49,
                        0.14,
                        0.94,
                        2.18,
                        0.05,
                        0.34,
                        1.26,
                        0.29,
                        2.61,
                    ]
                ),
                "config_type": "json",
                "description": "FSRS varsayılan parametreleri",
            },
            {
                "config_key": "zpd_cultural_factors",
                "config_value": json.dumps(
                    {
                        "group_learning_preference": 0.8,
                        "teacher_respect_level": 0.9,
                        "family_involvement": 0.7,
                        "peer_competition": 0.6,
                        "authority_acceptance": 0.8,
                    }
                ),
                "config_type": "json",
                "description": "ZPD kültürel faktörler",
            },
        ]

        async with get_db_session_context() as session:
            for config_data in configs:
                # Mevcut konfigürasyon kontrolü
                result = await session.execute(
                    select(SystemConfiguration).where(
                        SystemConfiguration.config_key == config_data["config_key"]
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    config = SystemConfiguration(**config_data)
                    session.add(config)
                    self.seeded_counts["system_configurations"] += 1

            await session.commit()

        logger.info(
            f"[CHECK] {self.seeded_counts['system_configurations']} sistem konfigürasyonu eklendi"
        )

    async def seed_admin_users(self):
        """Admin kullanıcıları seed et"""
        logger.info("👤 Admin kullanıcıları ekleniyor...")

        admin_users = [
            {
                "email": "admin@turkiyesinav.com",
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "first_name": "Platform",
                "last_name": "Yöneticisi",
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True,
            },
            {
                "email": "superadmin@turkiyesinav.com",
                "username": "superadmin",
                "password_hash": self._hash_password("superadmin123"),
                "first_name": "Süper",
                "last_name": "Yönetici",
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True,
            },
        ]

        async with get_db_session_context() as session:
            for user_data in admin_users:
                # Mevcut kullanıcı kontrolü
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    user = User(**user_data)
                    session.add(user)
                    self.seeded_counts["users"] += 1

            await session.commit()

        logger.info(
            f"[CHECK] {len([u for u in admin_users if u['email'] not in ['existing']])} admin kullanıcısı eklendi"
        )

    async def seed_sample_teachers(self):
        """Örnek öğretmenler seed et"""
        logger.info("👨‍🏫 Örnek öğretmenler ekleniyor...")

        teachers = [
            {
                "user": {
                    "email": "matematik.ogretmeni@turkiyesinav.com",
                    "username": "matematik_ogretmeni",
                    "password_hash": self._hash_password("teacher123"),
                    "first_name": "Ahmet",
                    "last_name": "Matematik",
                    "role": UserRole.TEACHER,
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "school_name": "Atatürk Anadolu Lisesi",
                    "subject_areas": {"subjects": ["MATEMATIK"]},
                    "experience_years": 15,
                    "education_level": "Yüksek Lisans",
                },
            },
            {
                "user": {
                    "email": "turkce.ogretmeni@turkiyesinav.com",
                    "username": "turkce_ogretmeni",
                    "password_hash": self._hash_password("teacher123"),
                    "first_name": "Fatma",
                    "last_name": "Türkçe",
                    "role": UserRole.TEACHER,
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "school_name": "Gazi Anadolu Lisesi",
                    "subject_areas": {"subjects": ["TURKCE"]},
                    "experience_years": 12,
                    "education_level": "Lisans",
                },
            },
            {
                "user": {
                    "email": "fizik.ogretmeni@turkiyesinav.com",
                    "username": "fizik_ogretmeni",
                    "password_hash": self._hash_password("teacher123"),
                    "first_name": "Mehmet",
                    "last_name": "Fizik",
                    "role": UserRole.TEACHER,
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "school_name": "Fen Lisesi",
                    "subject_areas": {"subjects": ["FIZIK"]},
                    "experience_years": 8,
                    "education_level": "Yüksek Lisans",
                },
            },
        ]

        async with get_db_session_context() as session:
            for teacher_data in teachers:
                # Mevcut kullanıcı kontrolü
                result = await session.execute(
                    select(User).where(User.email == teacher_data["user"]["email"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Kullanıcı oluştur
                    user = User(**teacher_data["user"])
                    session.add(user)
                    await session.flush()  # ID'yi al

                    # Öğretmen profili oluştur
                    profile_data = teacher_data["profile"].copy()
                    profile_data["user_id"] = user.id
                    profile = TeacherProfile(**profile_data)
                    session.add(profile)

                    self.seeded_counts["users"] += 1

            await session.commit()

        logger.info(f"[CHECK] {len(teachers)} örnek öğretmen eklendi")

    async def seed_sample_students(self):
        """Örnek öğrenciler seed et"""
        logger.info("👨‍[GRADUATION_CAP] Örnek öğrenciler ekleniyor...")

        students = [
            {
                "user": {
                    "email": "ogrenci1@turkiyesinav.com",
                    "username": "ogrenci1",
                    "password_hash": self._hash_password("student123"),
                    "first_name": "Ali",
                    "last_name": "Yılmaz",
                    "role": UserRole.STUDENT,
                    "birth_date": date(2006, 5, 15),
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "grade_level": 12,
                    "school_name": "Atatürk Anadolu Lisesi",
                    "target_university": "İTÜ",
                    "target_department": "Bilgisayar Mühendisliği",
                    "current_level": 7.5,
                    "study_hours_per_day": 6,
                    "preferred_study_time": "evening",
                },
            },
            {
                "user": {
                    "email": "ogrenci2@turkiyesinav.com",
                    "username": "ogrenci2",
                    "password_hash": self._hash_password("student123"),
                    "first_name": "Ayşe",
                    "last_name": "Demir",
                    "role": UserRole.STUDENT,
                    "birth_date": date(2007, 3, 22),
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "grade_level": 11,
                    "school_name": "Gazi Anadolu Lisesi",
                    "target_university": "ODTÜ",
                    "target_department": "Tıp",
                    "current_level": 8.2,
                    "study_hours_per_day": 8,
                    "preferred_study_time": "morning",
                },
            },
            {
                "user": {
                    "email": "ogrenci3@turkiyesinav.com",
                    "username": "ogrenci3",
                    "password_hash": self._hash_password("student123"),
                    "first_name": "Mehmet",
                    "last_name": "Kaya",
                    "role": UserRole.STUDENT,
                    "birth_date": date(2005, 8, 10),
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "grade_level": 12,
                    "school_name": "Fen Lisesi",
                    "target_university": "Boğaziçi",
                    "target_department": "Elektrik Mühendisliği",
                    "current_level": 9.1,
                    "study_hours_per_day": 10,
                    "preferred_study_time": "afternoon",
                },
            },
        ]

        async with get_db_session_context() as session:
            for student_data in students:
                # Mevcut kullanıcı kontrolü
                result = await session.execute(
                    select(User).where(User.email == student_data["user"]["email"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Kullanıcı oluştur
                    user = User(**student_data["user"])
                    session.add(user)
                    await session.flush()  # ID'yi al

                    # Öğrenci profili oluştur
                    profile_data = student_data["profile"].copy()
                    profile_data["user_id"] = user.id
                    profile = StudentProfile(**profile_data)
                    session.add(profile)

                    self.seeded_counts["users"] += 1

            await session.commit()

        logger.info(f"[CHECK] {len(students)} örnek öğrenci eklendi")

    async def seed_sample_parents(self):
        """Örnek veliler seed et"""
        logger.info("👨‍👩‍👧‍👦 Örnek veliler ekleniyor...")

        # Önce öğrenci ID'lerini al
        async with get_db_session_context() as session:
            result = await session.execute(select(StudentProfile.id).limit(2))
            student_ids = [row[0] for row in result.fetchall()]

        if not student_ids:
            logger.warning("⚠️ Veli oluşturmak için öğrenci bulunamadı")
            return

        parents = [
            {
                "user": {
                    "email": "veli1@turkiyesinav.com",
                    "username": "veli1",
                    "password_hash": self._hash_password("parent123"),
                    "first_name": "Hasan",
                    "last_name": "Yılmaz",
                    "role": UserRole.PARENT,
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "children_ids": {"children": [student_ids[0]]}
                    if len(student_ids) > 0
                    else {"children": []},
                    "email_notifications": True,
                    "sms_notifications": False,
                    "weekly_reports": True,
                },
            },
            {
                "user": {
                    "email": "veli2@turkiyesinav.com",
                    "username": "veli2",
                    "password_hash": self._hash_password("parent123"),
                    "first_name": "Zeynep",
                    "last_name": "Demir",
                    "role": UserRole.PARENT,
                    "is_active": True,
                    "is_verified": True,
                },
                "profile": {
                    "children_ids": {"children": [student_ids[1]]}
                    if len(student_ids) > 1
                    else {"children": []},
                    "email_notifications": True,
                    "sms_notifications": True,
                    "weekly_reports": True,
                },
            },
        ]

        async with get_db_session_context() as session:
            for parent_data in parents:
                # Mevcut kullanıcı kontrolü
                result = await session.execute(
                    select(User).where(User.email == parent_data["user"]["email"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Kullanıcı oluştur
                    user = User(**parent_data["user"])
                    session.add(user)
                    await session.flush()  # ID'yi al

                    # Veli profili oluştur
                    profile_data = parent_data["profile"].copy()
                    profile_data["user_id"] = user.id
                    profile = ParentProfile(**profile_data)
                    session.add(profile)

                    self.seeded_counts["users"] += 1

            await session.commit()

        logger.info(f"[CHECK] {len(parents)} örnek veli eklendi")

    async def seed_sample_questions(self):
        """Örnek sorular seed et"""
        logger.info("❓ Örnek sorular ekleniyor...")

        # TYT Matematik soruları
        tyt_matematik_sorular = [
            {
                "question_text": "Bir sayının %25'i 60 ise, bu sayının %40'ı kaçtır?",
                "option_a": "96",
                "option_b": "120",
                "option_c": "144",
                "option_d": "180",
                "correct_answer": "A",
                "explanation": "Sayı x olsun. x'in %25'i = 60 ise x = 240. x'in %40'ı = 240 × 0.4 = 96",
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Yüzdeler",
                "difficulty": QuestionDifficulty.EASY,
                "irt_difficulty": -0.5,
                "irt_discrimination": 1.2,
                "irt_guessing": 0.25,
            },
            {
                "question_text": "f(x) = 2x + 3 fonksiyonu için f(5) değeri kaçtır?",
                "option_a": "10",
                "option_b": "13",
                "option_c": "15",
                "option_d": "18",
                "correct_answer": "B",
                "explanation": "f(5) = 2(5) + 3 = 10 + 3 = 13",
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Fonksiyonlar",
                "difficulty": QuestionDifficulty.EASY,
                "irt_difficulty": -0.8,
                "irt_discrimination": 1.5,
                "irt_guessing": 0.25,
            },
            {
                "question_text": "Bir üçgenin iç açıları toplamı kaç derecedir?",
                "option_a": "90",
                "option_b": "180",
                "option_c": "270",
                "option_d": "360",
                "correct_answer": "B",
                "explanation": "Herhangi bir üçgenin iç açıları toplamı her zaman 180 derecedir.",
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Geometri",
                "difficulty": QuestionDifficulty.EASY,
                "irt_difficulty": -1.2,
                "irt_discrimination": 2.0,
                "irt_guessing": 0.25,
            },
        ]

        # TYT Türkçe soruları
        tyt_turkce_sorular = [
            {
                "question_text": "Aşağıdaki cümlelerden hangisinde yazım yanlışı vardır?",
                "option_a": "Kitabı masanın üzerine koydu.",
                "option_b": "Yarın sınava gireceğim.",
                "option_c": "Bu konuyu çok iyi biliyorum.",
                "option_d": "Okula geç kalmıştım.",
                "correct_answer": "D",
                "explanation": '"Okula geç kalmıştım" cümlesinde "geç" kelimesi "geç kalmak" anlamında kullanıldığında bitişik yazılır: "geçkalmıştım".',
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.TURKCE,
                "topic": "Yazım Kuralları",
                "difficulty": QuestionDifficulty.MEDIUM,
                "irt_difficulty": 0.3,
                "irt_discrimination": 1.3,
                "irt_guessing": 0.25,
            },
            {
                "question_text": '"Güneş doğudan doğar" cümlesinde özne hangisidir?',
                "option_a": "Güneş",
                "option_b": "doğudan",
                "option_c": "doğar",
                "option_d": "Özne yoktur",
                "correct_answer": "A",
                "explanation": 'Cümlede "kim?" sorusunun cevabı olan "Güneş" kelimesi öznedir.',
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.TURKCE,
                "topic": "Cümle Bilgisi",
                "difficulty": QuestionDifficulty.EASY,
                "irt_difficulty": -0.7,
                "irt_discrimination": 1.8,
                "irt_guessing": 0.25,
            },
        ]

        # AYT Matematik soruları
        ayt_matematik_sorular = [
            {
                "question_text": "lim(x→2) (x² - 4)/(x - 2) limitinin değeri kaçtır?",
                "option_a": "0",
                "option_b": "2",
                "option_c": "4",
                "option_d": "Limit yoktur",
                "correct_answer": "C",
                "explanation": "Pay çarpanlarına ayrılır: (x-2)(x+2)/(x-2) = x+2. x→2 için limit = 2+2 = 4",
                "exam_type": ExamType.AYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Limit",
                "difficulty": QuestionDifficulty.MEDIUM,
                "irt_difficulty": 0.8,
                "irt_discrimination": 1.4,
                "irt_guessing": 0.25,
            },
            {
                "question_text": "f(x) = x³ - 3x² + 2x fonksiyonunun türevi f'(x) nedir?",
                "option_a": "3x² - 6x + 2",
                "option_b": "3x² - 6x",
                "option_c": "x² - 6x + 2",
                "option_d": "3x² + 6x + 2",
                "correct_answer": "A",
                "explanation": "Türev kuralları: (x³)' = 3x², (-3x²)' = -6x, (2x)' = 2",
                "exam_type": ExamType.AYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Türev",
                "difficulty": QuestionDifficulty.MEDIUM,
                "irt_difficulty": 0.5,
                "irt_discrimination": 1.6,
                "irt_guessing": 0.25,
            },
        ]

        # Tüm soruları birleştir
        all_questions = (
            tyt_matematik_sorular + tyt_turkce_sorular + ayt_matematik_sorular
        )

        async with get_db_session_context() as session:
            for question_data in all_questions:
                # Mevcut soru kontrolü (aynı metin)
                result = await session.execute(
                    select(Question).where(
                        Question.question_text == question_data["question_text"]
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    question = Question(**question_data)
                    session.add(question)
                    self.seeded_counts["questions"] += 1

            await session.commit()

        logger.info(f"[CHECK] {self.seeded_counts['questions']} örnek soru eklendi")

    async def seed_educational_contents(self):
        """Eğitim içerikleri seed et"""
        logger.info("[BOOKS] Eğitim içerikleri ekleniyor...")

        contents = [
            {
                "title": "TYT Matematik - Fonksiyonlar Konu Anlatımı",
                "description": "Fonksiyonlar konusunun detaylı anlatımı ve örnek sorular",
                "content_type": "video",
                "source_platform": "youtube",
                "source_url": "https://www.youtube.com/watch?v=example1",
                "source_id": "example1",
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Fonksiyonlar",
                "grade_level": 12,
                "difficulty_level": QuestionDifficulty.MEDIUM,
                "educational_score": 8.5,
                "duration_minutes": 45,
                "has_subtitles": True,
                "has_transcript": True,
                "language": "tr",
                "view_count": 15420,
                "like_count": 1250,
                "rating": 4.7,
            },
            {
                "title": "TYT Türkçe - Cümle Bilgisi",
                "description": "Cümle ögeleri ve cümle türleri detaylı anlatım",
                "content_type": "video",
                "source_platform": "youtube",
                "source_url": "https://www.youtube.com/watch?v=example2",
                "source_id": "example2",
                "subject_area": SubjectArea.TURKCE,
                "topic": "Cümle Bilgisi",
                "grade_level": 12,
                "difficulty_level": QuestionDifficulty.EASY,
                "educational_score": 9.2,
                "duration_minutes": 35,
                "has_subtitles": True,
                "has_transcript": True,
                "language": "tr",
                "view_count": 22100,
                "like_count": 1890,
                "rating": 4.9,
            },
            {
                "title": "AYT Matematik - Limit ve Süreklilik",
                "description": "Limit kavramı ve süreklilik konularının kapsamlı anlatımı",
                "content_type": "video",
                "source_platform": "khan_academy",
                "source_url": "https://tr.khanacademy.org/math/limit-continuity",
                "source_id": "limit_continuity_tr",
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Limit",
                "grade_level": 12,
                "difficulty_level": QuestionDifficulty.HARD,
                "educational_score": 9.5,
                "duration_minutes": 60,
                "has_subtitles": True,
                "has_transcript": True,
                "language": "tr",
                "view_count": 8750,
                "like_count": 920,
                "rating": 4.8,
            },
            {
                "title": "TYT Fen Bilimleri - Fizik Hareket",
                "description": "Düzgün doğrusal hareket ve düzgün değişen hareket",
                "content_type": "interactive",
                "source_platform": "eba_tv",
                "source_url": "https://www.eba.gov.tr/fizik-hareket",
                "source_id": "fizik_hareket_12",
                "subject_area": SubjectArea.FEN,
                "topic": "Hareket",
                "grade_level": 12,
                "difficulty_level": QuestionDifficulty.MEDIUM,
                "educational_score": 8.8,
                "duration_minutes": 40,
                "has_subtitles": True,
                "has_transcript": False,
                "language": "tr",
                "view_count": 12300,
                "like_count": 1100,
                "rating": 4.6,
            },
        ]

        async with get_db_session_context() as session:
            for content_data in contents:
                # Mevcut içerik kontrolü
                result = await session.execute(
                    select(EducationalContent).where(
                        EducationalContent.source_url == content_data["source_url"]
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    content = EducationalContent(**content_data)
                    session.add(content)
                    self.seeded_counts["educational_contents"] += 1

            await session.commit()

        logger.info(
            f"[CHECK] {self.seeded_counts['educational_contents']} eğitim içeriği eklendi"
        )

    async def seed_classrooms(self):
        """Sınıflar seed et"""
        logger.info("🏫 Sınıflar ekleniyor...")

        # Önce öğretmen ID'lerini al
        async with get_db_session_context() as session:
            result = await session.execute(
                select(TeacherProfile.id, TeacherProfile.subject_areas)
            )
            teachers = result.fetchall()

        if not teachers:
            logger.warning("⚠️ Sınıf oluşturmak için öğretmen bulunamadı")
            return

        # Öğrenci ID'lerini al
        async with get_db_session_context() as session:
            result = await session.execute(select(StudentProfile.id).limit(3))
            student_ids = [row[0] for row in result.fetchall()]

        classrooms = []
        for teacher in teachers:
            teacher_id, subject_areas = teacher
            if (
                subject_areas
                and "subjects" in subject_areas
                and len(subject_areas["subjects"]) > 0
            ):
                subject = subject_areas["subjects"][0]  # İlk branşı al

                classroom = {
                    "teacher_id": teacher_id,
                    "class_name": f"12-A {subject} Sınıfı",
                    "grade_level": 12,
                    "subject_area": SubjectArea(subject),
                    "school_year": "2024-2025",
                    "student_ids": {
                        "students": student_ids[:2]
                        if len(student_ids) >= 2
                        else student_ids
                    },
                    "is_active": True,
                    "max_students": 30,
                }
                classrooms.append(classroom)

        async with get_db_session_context() as session:
            for classroom_data in classrooms:
                # Mevcut sınıf kontrolü
                result = await session.execute(
                    select(ClassRoom).where(
                        ClassRoom.teacher_id == classroom_data["teacher_id"],
                        ClassRoom.class_name == classroom_data["class_name"],
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    classroom = ClassRoom(**classroom_data)
                    session.add(classroom)
                    self.seeded_counts["classrooms"] += 1

            await session.commit()

        logger.info(f"[CHECK] {self.seeded_counts['classrooms']} sınıf eklendi")

    async def print_seeding_summary(self):
        """Seeding özeti yazdır"""
        logger.info("\n" + "=" * 50)
        logger.info("[CHART] DATABASE SEEDING ÖZETİ")
        logger.info("=" * 50)

        async with get_db_session_context() as session:
            # Toplam sayıları al
            user_count = await session.scalar(select(func.count(User.id)))
            question_count = await session.scalar(select(func.count(Question.id)))
            content_count = await session.scalar(
                select(func.count(EducationalContent.id))
            )
            config_count = await session.scalar(
                select(func.count(SystemConfiguration.id))
            )
            classroom_count = await session.scalar(select(func.count(ClassRoom.id)))

            # Rol bazlı kullanıcı sayıları
            admin_count = await session.scalar(
                select(func.count(User.id)).where(User.role == UserRole.ADMIN)
            )
            teacher_count = await session.scalar(
                select(func.count(User.id)).where(User.role == UserRole.TEACHER)
            )
            student_count = await session.scalar(
                select(func.count(User.id)).where(User.role == UserRole.STUDENT)
            )
            parent_count = await session.scalar(
                select(func.count(User.id)).where(User.role == UserRole.PARENT)
            )

        logger.info(f"👤 Toplam Kullanıcı: {user_count}")
        logger.info(f"   - Admin: {admin_count}")
        logger.info(f"   - Öğretmen: {teacher_count}")
        logger.info(f"   - Öğrenci: {student_count}")
        logger.info(f"   - Veli: {parent_count}")
        logger.info(f"❓ Toplam Soru: {question_count}")
        logger.info(f"[BOOKS] Toplam Eğitim İçeriği: {content_count}")
        logger.info(f"[GEAR] Toplam Sistem Konfigürasyonu: {config_count}")
        logger.info(f"🏫 Toplam Sınıf: {classroom_count}")
        logger.info("=" * 50)

    def _hash_password(self, password: str) -> str:
        """Şifre hash'le (bcrypt)"""
        import bcrypt

        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def main():
    """Ana fonksiyon"""
    seeder = DatabaseSeeder()
    await seeder.seed_all()


if __name__ == "__main__":
    asyncio.run(main())
