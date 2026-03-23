"""
Enhanced Student Assessment System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Interactive assessment questionnaire generator
- 5-10 question quick knowledge tests
- Self-assessment options
- Assessment result analysis and scoring
"""

import json
import logging
import os
import random

# Core services
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_service import llm_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssessmentType(Enum):
    """Assessment türleri"""

    QUICK_TEST = "quick_test"  # 5-10 soruluk hızlı test
    SELF_ASSESSMENT = "self_assessment"  # Öz değerlendirme
    INTERACTIVE_QUESTIONNAIRE = "interactive_questionnaire"  # Etkileşimli anket
    COMPREHENSIVE = "comprehensive"  # Kapsamlı değerlendirme


class QuestionType(Enum):
    """Soru türleri"""

    MULTIPLE_CHOICE = "multiple_choice"  # Çoktan seçmeli
    TRUE_FALSE = "true_false"  # Doğru/Yanlış
    OPEN_ENDED = "open_ended"  # Açık uçlu
    SCALE = "scale"  # Ölçek (1-5)
    RANKING = "ranking"  # Sıralama


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


@dataclass
class Question:
    """Soru modeli"""

    question_id: str
    question_text: str
    question_type: QuestionType
    subject: str
    topic: str
    difficulty: DifficultyLevel
    options: list[str] | None = None  # Çoktan seçmeli için seçenekler
    correct_answer: str | None = None  # Doğru cevap
    explanation: str | None = None  # Açıklama
    points: int = 1  # Puan değeri
    time_limit_seconds: int | None = None  # Süre sınırı
    metadata: dict[str, Any] | None = None


@dataclass
class AssessmentResult:
    """Değerlendirme sonucu"""

    assessment_id: str
    student_id: str
    assessment_type: AssessmentType
    subject: str
    questions: list[Question]
    answers: list[str]
    scores: list[float]  # Her soru için puan (0-1)
    total_score: float  # Toplam puan (0-100)
    time_taken_seconds: int
    knowledge_level: str  # Belirlenen bilgi seviyesi
    strengths: list[str]  # Güçlü konular
    weaknesses: list[str]  # Zayıf konular
    recommendations: list[str]  # Öneriler
    created_at: datetime
    metadata: dict[str, Any]


@dataclass
class SelfAssessmentProfile:
    """Öz değerlendirme profili"""

    student_id: str
    confidence_levels: dict[str, int]  # Konu başına güven seviyesi (1-5)
    experience_levels: dict[str, int]  # Konu başına deneyim seviyesi (1-5)
    interest_levels: dict[str, int]  # Konu başına ilgi seviyesi (1-5)
    learning_preferences: dict[str, Any]  # Öğrenme tercihleri
    goals: list[str]  # Hedefler
    time_availability: int  # Günlük çalışma süresi (dakika)
    created_at: datetime


class AssessmentSystem:
    """Gelişmiş Öğrenci Değerlendirme Sistemi"""

    def __init__(self):
        self.question_bank = {}  # Soru bankası
        self.assessments = {}  # Tamamlanan değerlendirmeler
        self.self_assessments = {}  # Öz değerlendirmeler
        self._load_question_templates()

    def _load_question_templates(self):
        """Soru şablonlarını yükle"""
        self.question_templates = {
            "matematik": {
                "temel": [
                    "Aşağıdaki işlemlerden hangisi doğrudur?",
                    "Bir sayının karesi nedir?",
                    "Kesirler nasıl toplanır?",
                    "Yüzde hesaplama nasıl yapılır?",
                    "Geometrik şekillerin alanı nasıl hesaplanır?",
                ],
                "orta": [
                    "Denklem çözme yöntemlerini açıklayın",
                    "Fonksiyon kavramını tanımlayın",
                    "Türev alma kuralları nelerdir?",
                    "İntegral hesaplama nasıl yapılır?",
                    "Trigonometrik oranlar nelerdir?",
                ],
                "ileri": [
                    "Limit kavramını matematiksel olarak tanımlayın",
                    "Diferansiyel denklemleri çözme yöntemleri",
                    "Matris işlemleri ve determinant hesaplama",
                    "Olasılık teorisi ve istatistik",
                    "Analitik geometri uygulamaları",
                ],
            },
            "fen": {
                "temel": [
                    "Maddenin halleri nelerdir?",
                    "Kuvvet ve hareket arasındaki ilişki nedir?",
                    "Işık nasıl yayılır?",
                    "Ses nasıl oluşur?",
                    "Canlıların temel özellikleri nelerdir?",
                ],
                "orta": [
                    "Kimyasal reaksiyonlar nasıl gerçekleşir?",
                    "Elektrik akımı nedir?",
                    "Hücre bölünmesi nasıl olur?",
                    "Enerji dönüşümleri nasıl gerçekleşir?",
                    "Ekosistem nasıl çalışır?",
                ],
                "ileri": [
                    "Atom yapısı ve periyodik sistem",
                    "Elektromanyetik dalgalar",
                    "Genetik ve kalıtım",
                    "Termodinamik yasaları",
                    "Evrim teorisi",
                ],
            },
        }

    async def generate_interactive_questionnaire(
        self,
        student_id: str,
        goal: str,
        subjects: list[str],
        current_knowledge: dict[str, Any] | None = None,
    ) -> list[Question]:
        """
        Dynamic interactive assessment questionnaire generator

        Args:
            student_id: Öğrenci ID
            goal: Öğrenme hedefi
            subjects: İlgili dersler
            current_knowledge: Mevcut bilgi seviyesi (opsiyonel)

        Returns:
            Dinamik soru listesi
        """
        try:
            # Öğrenci profilini ve geçmiş değerlendirmelerini al
            previous_assessments = self.get_student_assessments(student_id)

            # Dinamik soru seçimi için LLM prompt'u oluştur
            context = f"""
            Öğrenci ID: {student_id}
            Öğrenme Hedefi: {goal}
            İlgili Dersler: {', '.join(subjects)}
            Geçmiş Değerlendirme Sayısı: {len(previous_assessments)}
            """

            if current_knowledge:
                context += f"\nMevcut Bilgi Seviyesi: {json.dumps(current_knowledge, ensure_ascii=False)}"

            if previous_assessments:
                # Son değerlendirmenin zayıf konularını ekle
                last_assessment = previous_assessments[-1]
                context += (
                    f"\nÖnceki Zayıf Konular: {', '.join(last_assessment.weaknesses)}"
                )
                context += (
                    f"\nÖnceki Güçlü Konular: {', '.join(last_assessment.strengths)}"
                )

            prompt = f"""
            {context}
            
            Bu öğrenci için kişiselleştirilmiş bir değerlendirme anketi oluştur.
            
            Kurallar:
            1. 8-12 soru olsun
            2. Farklı soru türleri kullan (çoktan seçmeli, ölçek, açık uçlu)
            3. Öğrencinin hedefine ve seviyesine uygun olsun
            4. Zayıf konulara daha fazla odaklan
            5. Öğrenme stilini belirlemeye yardımcı sorular ekle
            
            JSON formatında yanıtla:
            {{
                "questions": [
                    {{
                        "question": "Soru metni",
                        "type": "multiple_choice/scale/open_ended",
                        "subject": "ders",
                        "topic": "konu",
                        "difficulty": "easy/medium/hard",
                        "options": ["seçenekler"] // sadece multiple_choice ve scale için,
                        "category": "knowledge/confidence/interest/learning_style",
                        "adaptive_follow_up": true/false // Bu soruya göre sonraki soru değişsin mi?
                    }}
                ]
            }}
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.6)

            questions = []
            if result["success"]:
                try:
                    data = json.loads(result["text"])
                    for i, q_data in enumerate(data.get("questions", [])):
                        question_type = self._parse_question_type(
                            q_data.get("type", "multiple_choice")
                        )
                        difficulty = self._parse_difficulty(
                            q_data.get("difficulty", "medium")
                        )

                        question = Question(
                            question_id=f"interactive_{student_id}_{i}_{datetime.now().timestamp()}",
                            question_text=q_data["question"],
                            question_type=question_type,
                            subject=q_data.get("subject", "Genel"),
                            topic=q_data.get("topic", "Değerlendirme"),
                            difficulty=difficulty,
                            options=q_data.get("options"),
                            points=1,
                            time_limit_seconds=120,  # 2 dakika per soru
                            metadata={
                                "assessment_category": q_data.get(
                                    "category", "knowledge"
                                ),
                                "goal": goal,
                                "adaptive_follow_up": q_data.get(
                                    "adaptive_follow_up", False
                                ),
                                "generated_by": "dynamic_llm",
                                "context_used": bool(previous_assessments),
                            },
                        )
                        questions.append(question)

                except json.JSONDecodeError:
                    questions = self._create_fallback_interactive_questions(
                        student_id, goal
                    )
            else:
                questions = self._create_fallback_interactive_questions(
                    student_id, goal
                )

            logger.info(
                f"Generated {len(questions)} dynamic interactive questions for student {student_id}"
            )
            return questions

        except Exception as e:
            logger.error(f"Generate interactive questionnaire error: {e!s}")
            return self._create_fallback_interactive_questions(student_id, goal)

    def _parse_question_type(self, type_str: str) -> QuestionType:
        """Soru türünü parse et"""
        type_mapping = {
            "multiple_choice": QuestionType.MULTIPLE_CHOICE,
            "scale": QuestionType.SCALE,
            "open_ended": QuestionType.OPEN_ENDED,
            "true_false": QuestionType.TRUE_FALSE,
            "ranking": QuestionType.RANKING,
        }
        return type_mapping.get(type_str, QuestionType.MULTIPLE_CHOICE)

    def _parse_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """Zorluk seviyesini parse et"""
        difficulty_mapping = {
            "very_easy": DifficultyLevel.VERY_EASY,
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
            "very_hard": DifficultyLevel.VERY_HARD,
        }
        return difficulty_mapping.get(difficulty_str, DifficultyLevel.MEDIUM)

    async def generate_quick_test(
        self,
        subject: str,
        topic: str | None = None,
        difficulty: DifficultyLevel | None = None,
        question_count: int = 5,
    ) -> list[Question]:
        """
        Hızlı test soruları oluştur (5-10 soru)

        Args:
            subject: Ders konusu
            topic: Spesifik konu (opsiyonel)
            difficulty: Zorluk seviyesi
            question_count: Soru sayısı (5-10)

        Returns:
            Soru listesi
        """
        try:
            if question_count < 5 or question_count > 10:
                question_count = 5

            # Konu-spesifik soru oluşturma
            subject_context = self._get_subject_context(subject, topic)
            difficulty_desc = self._get_difficulty_description(
                difficulty or DifficultyLevel.MEDIUM
            )

            # LLM ile gelişmiş sorular oluştur
            prompt = f"""
            {subject} konusunda {question_count} adet kaliteli test sorusu oluştur.
            
            Konu: {topic or 'Genel'}
            Zorluk Seviyesi: {difficulty_desc}
            Konu Bağlamı: {subject_context}
            
            Soru Kriterleri:
            1. Türkiye eğitim müfredatına uygun
            2. Öğrencinin anlama seviyesini ölçen
            3. Çeldiriciler mantıklı ve öğretici
            4. Net ve anlaşılır soru kökü
            5. Güncel ve ilgi çekici örnekler
            
            Her soru için:
            - Soru metni (açık ve net)
            - 4 seçenek (A, B, C, D) - çeldiriciler mantıklı olsun
            - Doğru cevap
            - Detaylı açıklama (neden doğru, diğerleri neden yanlış)
            - Alt konu/kavram
            - Tahmini çözüm süresi (saniye)
            
            JSON formatında yanıtla:
            {{
                "questions": [
                    {{
                        "question": "Soru metni",
                        "options": ["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"],
                        "correct": "A",
                        "explanation": "Detaylı açıklama",
                        "topic": "Alt konu",
                        "concept": "Ana kavram",
                        "estimated_time": 60
                    }}
                ]
            }}
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.7)

            questions = []
            if result["success"]:
                try:
                    data = json.loads(result["text"])
                    for i, q_data in enumerate(data.get("questions", [])):
                        question = Question(
                            question_id=f"quick_{subject}_{i}_{datetime.now().timestamp()}",
                            question_text=q_data["question"],
                            question_type=QuestionType.MULTIPLE_CHOICE,
                            subject=subject,
                            topic=q_data.get("topic", topic or "Genel"),
                            difficulty=difficulty or DifficultyLevel.MEDIUM,
                            options=q_data["options"],
                            correct_answer=q_data["correct"],
                            explanation=q_data.get("explanation", ""),
                            points=1,
                            time_limit_seconds=60,  # 1 dakika per soru
                            metadata={
                                "generated_by": "llm",
                                "created_at": datetime.now().isoformat(),
                            },
                        )
                        questions.append(question)
                except json.JSONDecodeError:
                    # Fallback: Template'den sorular oluştur
                    questions = self._generate_fallback_questions(
                        subject, question_count, difficulty
                    )
            else:
                questions = self._generate_fallback_questions(
                    subject, question_count, difficulty
                )

            logger.info(
                f"Generated {len(questions)} quick test questions for {subject}"
            )
            return questions

        except Exception as e:
            logger.error(f"Generate quick test error: {e!s}")
            return self._generate_fallback_questions(
                subject, question_count, difficulty
            )

    def _get_subject_context(self, subject: str, topic: str | None = None) -> str:
        """Ders için bağlamsal bilgi sağla"""
        context_map = {
            "matematik": "Türkiye Matematik Müfredatı - problem çözme, mantıksal düşünme, sayısal beceriler",
            "fen": "Fen Bilimleri - gözlem, deney, bilimsel yöntem, doğa olayları",
            "türkçe": "Türk Dili ve Edebiyatı - dil bilgisi, okuma anlama, yazma becerileri",
            "sosyal": "Sosyal Bilgiler - tarih, coğrafya, vatandaşlık, toplum bilinci",
            "ingilizce": "İngilizce - dil becerileri, iletişim, kelime bilgisi, gramer",
            "fizik": "Fizik - doğa yasaları, hareket, enerji, madde özellikleri",
            "kimya": "Kimya - madde yapısı, reaksiyonlar, periyodik sistem",
            "biyoloji": "Biyoloji - canlılar, hücre, genetik, ekoloji",
            "tarih": "Tarih - Türk tarihi, dünya tarihi, medeniyet, kronoloji",
            "coğrafya": "Coğrafya - fiziki coğrafya, beşeri coğrafya, harita bilgisi",
        }

        base_context = context_map.get(
            subject.lower(), f"{subject} - genel akademik içerik"
        )
        if topic:
            return f"{base_context}, özel odak: {topic}"
        return base_context

    def _get_difficulty_description(self, difficulty: DifficultyLevel) -> str:
        """Zorluk seviyesi açıklaması"""
        descriptions = {
            DifficultyLevel.VERY_EASY: "Çok kolay - temel kavramlar, basit hatırlama",
            DifficultyLevel.EASY: "Kolay - temel anlama, basit uygulama",
            DifficultyLevel.MEDIUM: "Orta - kavramsal anlama, uygulama",
            DifficultyLevel.HARD: "Zor - analiz, sentez, karmaşık problem çözme",
            DifficultyLevel.VERY_HARD: "Çok zor - yaratıcı düşünme, uzman seviye",
        }
        return descriptions.get(difficulty, "Orta seviye")

    def _generate_fallback_questions(
        self, subject: str, count: int, difficulty: DifficultyLevel | None
    ) -> list[Question]:
        """Template'den fallback sorular oluştur"""
        questions = []
        templates = self.question_templates.get(subject.lower(), {})

        if not templates:
            # Genel sorular
            for i in range(count):
                question = Question(
                    question_id=f"fallback_{subject}_{i}",
                    question_text=f"{subject} konusunda temel bilginizi değerlendirin (1-5)",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="Genel",
                    difficulty=DifficultyLevel.MEDIUM,
                    options=[
                        "1 - Çok zayıf",
                        "2 - Zayıf",
                        "3 - Orta",
                        "4 - İyi",
                        "5 - Çok iyi",
                    ],
                    points=1,
                )
                questions.append(question)
        else:
            # Template'den sorular seç
            level = (
                "temel"
                if difficulty in [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY]
                else "orta"
            )
            question_texts = templates.get(level, templates.get("temel", []))

            selected_texts = random.sample(
                question_texts, min(count, len(question_texts))
            )

            for i, text in enumerate(selected_texts):
                question = Question(
                    question_id=f"template_{subject}_{i}",
                    question_text=text,
                    question_type=QuestionType.OPEN_ENDED,
                    subject=subject,
                    topic="Genel",
                    difficulty=difficulty or DifficultyLevel.MEDIUM,
                    points=1,
                )
                questions.append(question)

        return questions

    async def create_self_assessment(
        self, student_id: str, subjects: list[str]
    ) -> list[Question]:
        """
        Öz değerlendirme soruları oluştur

        Args:
            student_id: Öğrenci ID
            subjects: Değerlendirilecek dersler

        Returns:
            Öz değerlendirme soruları
        """
        try:
            questions = []

            # Her ders için güven seviyesi soruları
            for subject in subjects:
                # Güven seviyesi
                confidence_q = Question(
                    question_id=f"confidence_{subject}_{student_id}",
                    question_text=f"{subject} konusundaki bilgi seviyenizi nasıl değerlendiriyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="Güven Seviyesi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç bilmiyorum",
                        "2 - Az biliyorum",
                        "3 - Orta seviyede",
                        "4 - İyi biliyorum",
                        "5 - Uzmanım",
                    ],
                    points=1,
                    metadata={"assessment_category": "confidence"},
                )
                questions.append(confidence_q)

                # İlgi seviyesi
                interest_q = Question(
                    question_id=f"interest_{subject}_{student_id}",
                    question_text=f"{subject} dersine olan ilginizi nasıl değerlendiriyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="İlgi Seviyesi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç ilgim yok",
                        "2 - Az ilgim var",
                        "3 - Orta seviyede",
                        "4 - İlgiliyim",
                        "5 - Çok ilgiliyim",
                    ],
                    points=1,
                    metadata={"assessment_category": "interest"},
                )
                questions.append(interest_q)

                # Deneyim seviyesi
                experience_q = Question(
                    question_id=f"experience_{subject}_{student_id}",
                    question_text=f"{subject} konusunda ne kadar deneyiminiz var?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="Deneyim Seviyesi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç deneyimim yok",
                        "2 - Az deneyimim var",
                        "3 - Orta seviyede",
                        "4 - Deneyimliyim",
                        "5 - Çok deneyimliyim",
                    ],
                    points=1,
                    metadata={"assessment_category": "experience"},
                )
                questions.append(experience_q)

            # Genel öğrenme tercihleri
            learning_style_q = Question(
                question_id=f"learning_style_{student_id}",
                question_text="Hangi öğrenme yöntemini tercih edersiniz?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                subject="Genel",
                topic="Öğrenme Stili",
                difficulty=DifficultyLevel.EASY,
                options=[
                    "A) Görsel materyaller (video, resim, grafik)",
                    "B) İşitsel materyaller (ses, müzik, anlatım)",
                    "C) Okuma ve yazma (metin, makale, not)",
                    "D) Uygulamalı çalışma (pratik, proje, deney)",
                ],
                points=1,
                metadata={"assessment_category": "learning_preference"},
            )
            questions.append(learning_style_q)

            # Zaman tercihi
            time_q = Question(
                question_id=f"time_preference_{student_id}",
                question_text="Günde ne kadar süre çalışmayı planlıyorsunuz?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                subject="Genel",
                topic="Zaman Yönetimi",
                difficulty=DifficultyLevel.EASY,
                options=[
                    "A) 30 dakikadan az",
                    "B) 30-60 dakika",
                    "C) 1-2 saat",
                    "D) 2 saatten fazla",
                ],
                points=1,
                metadata={"assessment_category": "time_management"},
            )
            questions.append(time_q)

            logger.info(
                f"Created {len(questions)} self-assessment questions for student {student_id}"
            )
            return questions

        except Exception as e:
            logger.error(f"Create self-assessment error: {e!s}")
            raise

    async def create_interactive_questionnaire(
        self, student_id: str, goal: str
    ) -> list[Question]:
        """
        Etkileşimli anket oluştur

        Args:
            student_id: Öğrenci ID
            goal: Öğrenme hedefi

        Returns:
            Etkileşimli anket soruları
        """
        try:
            # LLM ile hedefe özel sorular oluştur
            prompt = f"""
            Öğrenci hedefi: {goal}
            
            Bu hedefe yönelik etkileşimli bir değerlendirme anketi oluştur.
            10 soru olsun ve farklı türlerde olsun:
            - Çoktan seçmeli
            - Ölçek (1-5)
            - Açık uçlu
            
            JSON formatında yanıtla:
            {{
                "questions": [
                    {{
                        "question": "Soru metni",
                        "type": "multiple_choice/scale/open_ended",
                        "options": ["seçenekler"] // sadece multiple_choice ve scale için,
                        "category": "kategori"
                    }}
                ]
            }}
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.6)

            questions = []
            if result["success"]:
                try:
                    data = json.loads(result["text"])
                    for i, q_data in enumerate(data.get("questions", [])):
                        question_type = QuestionType.MULTIPLE_CHOICE
                        if q_data.get("type") == "scale":
                            question_type = QuestionType.SCALE
                        elif q_data.get("type") == "open_ended":
                            question_type = QuestionType.OPEN_ENDED

                        question = Question(
                            question_id=f"interactive_{student_id}_{i}",
                            question_text=q_data["question"],
                            question_type=question_type,
                            subject="Genel",
                            topic=q_data.get("category", "Hedef Değerlendirme"),
                            difficulty=DifficultyLevel.MEDIUM,
                            options=q_data.get("options"),
                            points=1,
                            metadata={
                                "assessment_category": "interactive",
                                "goal": goal,
                            },
                        )
                        questions.append(question)
                except json.JSONDecodeError:
                    # Fallback sorular
                    questions = self._create_fallback_interactive_questions(
                        student_id, goal
                    )
            else:
                questions = self._create_fallback_interactive_questions(
                    student_id, goal
                )

            logger.info(
                f"Created {len(questions)} interactive questionnaire for student {student_id}"
            )
            return questions

        except Exception as e:
            logger.error(f"Create interactive questionnaire error: {e!s}")
            return self._create_fallback_interactive_questions(student_id, goal)

    def _create_fallback_interactive_questions(
        self, student_id: str, goal: str
    ) -> list[Question]:
        """Fallback etkileşimli sorular"""
        questions = [
            Question(
                question_id=f"interactive_goal_{student_id}",
                question_text=f"'{goal}' hedefinize ulaşmak için ne kadar motive hissediyorsunuz?",
                question_type=QuestionType.SCALE,
                subject="Genel",
                topic="Motivasyon",
                difficulty=DifficultyLevel.EASY,
                options=[
                    "1 - Hiç motive değilim",
                    "2 - Az motive",
                    "3 - Orta",
                    "4 - Motive",
                    "5 - Çok motive",
                ],
                points=1,
            ),
            Question(
                question_id=f"interactive_challenge_{student_id}",
                question_text="Bu hedefe ulaşırken karşılaşabileceğiniz en büyük zorluk ne olabilir?",
                question_type=QuestionType.OPEN_ENDED,
                subject="Genel",
                topic="Zorluklar",
                difficulty=DifficultyLevel.MEDIUM,
                points=1,
            ),
            Question(
                question_id=f"interactive_support_{student_id}",
                question_text="Öğrenme sürecinde hangi tür desteğe ihtiyacınız var?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                subject="Genel",
                topic="Destek",
                difficulty=DifficultyLevel.EASY,
                options=[
                    "A) Kişisel mentor/öğretmen",
                    "B) Çalışma grubu",
                    "C) Online kaynaklar",
                    "D) Pratik uygulamalar",
                ],
                points=1,
            ),
        ]
        return questions

    async def evaluate_assessment_comprehensive(
        self,
        student_id: str,
        assessment_type: AssessmentType,
        questions: list[Question],
        answers: list[str],
        time_taken_seconds: int,
        additional_data: dict[str, Any] | None = None,
    ) -> AssessmentResult:
        """
        Comprehensive assessment evaluation with detailed analysis

        Args:
            student_id: Öğrenci ID
            assessment_type: Değerlendirme türü
            questions: Sorular
            answers: Cevaplar
            time_taken_seconds: Geçen süre
            additional_data: Ek veriler (mouse movements, pause times, etc.)

        Returns:
            Detaylı değerlendirme sonucu
        """
        try:
            scores = []
            correct_count = 0
            topic_performance = {}  # Konu bazında performans
            difficulty_performance = {}  # Zorluk bazında performans
            question_times = []  # Soru başına süre

            # Ortalama soru süresi hesapla
            avg_time_per_question = (
                time_taken_seconds / len(questions) if questions else 0
            )

            # Her soruyu detaylı değerlendir
            for i, (question, answer) in enumerate(
                zip(questions, answers, strict=False)
            ):
                question_score = 0.0

                if question.question_type == QuestionType.MULTIPLE_CHOICE:
                    # Çoktan seçmeli değerlendirme
                    if question.correct_answer and answer == question.correct_answer:
                        question_score = 1.0
                        correct_count += 1
                    else:
                        question_score = 0.0

                elif question.question_type == QuestionType.SCALE:
                    # Ölçek soruları için normalize et
                    try:
                        scale_value = int(answer)
                        question_score = (
                            scale_value / 5.0
                        )  # 1-5 ölçeğini 0-1'e normalize et
                    except (ValueError, TypeError):
                        question_score = 0.5  # Default orta değer

                elif question.question_type == QuestionType.TRUE_FALSE:
                    # Doğru/Yanlış değerlendirme
                    if (
                        question.correct_answer
                        and answer.lower() == question.correct_answer.lower()
                    ):
                        question_score = 1.0
                        correct_count += 1
                    else:
                        question_score = 0.0

                elif question.question_type == QuestionType.OPEN_ENDED:
                    # Açık uçlu sorular için LLM ile değerlendirme
                    question_score = await self._evaluate_open_ended_answer(
                        question, answer
                    )
                    if question_score > 0.7:
                        correct_count += 1
                else:
                    # Diğer soru türleri için orta değer
                    question_score = 0.7 if answer.strip() else 0.0

                scores.append(question_score)

                # Konu bazında performans takibi
                topic = question.topic
                if topic not in topic_performance:
                    topic_performance[topic] = {"scores": [], "count": 0}
                topic_performance[topic]["scores"].append(question_score)
                topic_performance[topic]["count"] += 1

                # Zorluk bazında performans takibi
                difficulty = question.difficulty.value
                if difficulty not in difficulty_performance:
                    difficulty_performance[difficulty] = {"scores": [], "count": 0}
                difficulty_performance[difficulty]["scores"].append(question_score)
                difficulty_performance[difficulty]["count"] += 1

                # Soru süresi tahmini (eşit dağıtım varsayımı)
                estimated_question_time = avg_time_per_question
                question_times.append(estimated_question_time)

            # Toplam puan hesapla
            total_score = (sum(scores) / len(scores)) * 100 if scores else 0

            # Gelişmiş bilgi seviyesi belirleme
            knowledge_level = await self._determine_knowledge_level_advanced(
                total_score,
                topic_performance,
                difficulty_performance,
                time_taken_seconds,
            )

            # Konu bazında güçlü ve zayıf alanları belirle
            strengths, weaknesses = self._analyze_topic_performance(topic_performance)

            # Gelişmiş öneriler oluştur
            recommendations = await self._generate_comprehensive_recommendations(
                student_id,
                knowledge_level,
                strengths,
                weaknesses,
                assessment_type,
                topic_performance,
                difficulty_performance,
            )

            # Sonuç oluştur
            result = AssessmentResult(
                assessment_id=f"assessment_{student_id}_{datetime.now().timestamp()}",
                student_id=student_id,
                assessment_type=assessment_type,
                subject=questions[0].subject if questions else "Genel",
                questions=questions,
                answers=answers,
                scores=scores,
                total_score=total_score,
                time_taken_seconds=time_taken_seconds,
                knowledge_level=knowledge_level,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                created_at=datetime.now(),
                metadata={
                    "correct_count": correct_count,
                    "total_questions": len(questions),
                    "accuracy": correct_count / len(questions) if questions else 0,
                    "avg_time_per_question": avg_time_per_question,
                    "topic_performance": {
                        topic: sum(data["scores"]) / len(data["scores"])
                        for topic, data in topic_performance.items()
                    },
                    "difficulty_performance": {
                        diff: sum(data["scores"]) / len(data["scores"])
                        for diff, data in difficulty_performance.items()
                    },
                    "question_times": question_times,
                    "additional_data": additional_data or {},
                },
            )

            # Sonucu kaydet
            self.assessments[result.assessment_id] = result

            logger.info(
                f"Comprehensive assessment evaluated for student {student_id}: {total_score:.1f}% ({knowledge_level})"
            )
            return result

        except Exception as e:
            logger.error(f"Comprehensive evaluate assessment error: {e!s}")
            raise

    async def evaluate_assessment(
        self,
        student_id: str,
        assessment_type: AssessmentType,
        questions: list[Question],
        answers: list[str],
        time_taken_seconds: int,
    ) -> AssessmentResult:
        """
        Değerlendirme sonuçlarını analiz et

        Args:
            student_id: Öğrenci ID
            assessment_type: Değerlendirme türü
            questions: Sorular
            answers: Cevaplar
            time_taken_seconds: Geçen süre

        Returns:
            Değerlendirme sonucu
        """
        try:
            scores = []
            correct_count = 0

            # Her soruyu değerlendir
            for i, (question, answer) in enumerate(
                zip(questions, answers, strict=False)
            ):
                if question.question_type == QuestionType.MULTIPLE_CHOICE:
                    # Çoktan seçmeli değerlendirme
                    if question.correct_answer and answer == question.correct_answer:
                        scores.append(1.0)
                        correct_count += 1
                    else:
                        scores.append(0.0)
                elif question.question_type == QuestionType.SCALE:
                    # Ölçek soruları için normalize et
                    try:
                        scale_value = int(answer)
                        scores.append(
                            scale_value / 5.0
                        )  # 1-5 ölçeğini 0-1'e normalize et
                    except (ValueError, TypeError):
                        scores.append(0.5)  # Default orta değer
                elif question.question_type == QuestionType.TRUE_FALSE:
                    # Doğru/Yanlış değerlendirme
                    if (
                        question.correct_answer
                        and answer.lower() == question.correct_answer.lower()
                    ):
                        scores.append(1.0)
                        correct_count += 1
                    else:
                        scores.append(0.0)
                else:
                    # Açık uçlu sorular için orta değer (gelecekte LLM ile değerlendirilebilir)
                    scores.append(0.7 if answer.strip() else 0.0)

            # Toplam puan hesapla
            total_score = (sum(scores) / len(scores)) * 100 if scores else 0

            # Bilgi seviyesi belirle
            if total_score >= 90:
                knowledge_level = "expert"
            elif total_score >= 75:
                knowledge_level = "advanced"
            elif total_score >= 60:
                knowledge_level = "intermediate"
            elif total_score >= 40:
                knowledge_level = "elementary"
            else:
                knowledge_level = "beginner"

            # Güçlü ve zayıf konuları belirle
            strengths = []
            weaknesses = []

            for i, (question, score) in enumerate(zip(questions, scores, strict=False)):
                if score >= 0.8:
                    strengths.append(question.topic)
                elif score <= 0.4:
                    weaknesses.append(question.topic)

            # Önerileri oluştur
            recommendations = self._generate_recommendations(
                knowledge_level, strengths, weaknesses, assessment_type
            )

            # Sonuç oluştur
            result = AssessmentResult(
                assessment_id=f"assessment_{student_id}_{datetime.now().timestamp()}",
                student_id=student_id,
                assessment_type=assessment_type,
                subject=questions[0].subject if questions else "Genel",
                questions=questions,
                answers=answers,
                scores=scores,
                total_score=total_score,
                time_taken_seconds=time_taken_seconds,
                knowledge_level=knowledge_level,
                strengths=list(set(strengths)),
                weaknesses=list(set(weaknesses)),
                recommendations=recommendations,
                created_at=datetime.now(),
                metadata={
                    "correct_count": correct_count,
                    "total_questions": len(questions),
                    "accuracy": correct_count / len(questions) if questions else 0,
                },
            )

            # Sonucu kaydet
            self.assessments[result.assessment_id] = result

            logger.info(
                f"Assessment evaluated for student {student_id}: {total_score:.1f}% ({knowledge_level})"
            )
            return result

        except Exception as e:
            logger.error(f"Evaluate assessment error: {e!s}")
            raise

    def _generate_recommendations(
        self,
        knowledge_level: str,
        strengths: list[str],
        weaknesses: list[str],
        assessment_type: AssessmentType,
    ) -> list[str]:
        """Öneriler oluştur"""
        recommendations = []

        if knowledge_level == "beginner":
            recommendations.extend(
                [
                    "Temel kavramlardan başlayın",
                    "Günlük kısa çalışma seansları planlayın",
                    "Görsel materyaller kullanın",
                ]
            )
        elif knowledge_level == "elementary":
            recommendations.extend(
                [
                    "Temel konuları pekiştirin",
                    "Pratik alıştırmalar yapın",
                    "Eksik konulara odaklanın",
                ]
            )
        elif knowledge_level == "intermediate":
            recommendations.extend(
                [
                    "Orta seviye problemler çözün",
                    "Farklı kaynaklardan yararlanın",
                    "Grup çalışması yapın",
                ]
            )
        elif knowledge_level == "advanced":
            recommendations.extend(
                [
                    "Zor problemlere odaklanın",
                    "Başkalarına öğretmeyi deneyin",
                    "Proje tabanlı öğrenme yapın",
                ]
            )
        else:  # expert
            recommendations.extend(
                [
                    "Uzmanlık alanınızı derinleştirin",
                    "Araştırma projeleri yapın",
                    "Mentörlük yapın",
                ]
            )

        # Zayıf konular için özel öneriler
        if weaknesses:
            recommendations.append(
                f"Şu konulara ekstra zaman ayırın: {', '.join(weaknesses[:3])}"
            )

        # Güçlü konular için öneriler
        if strengths:
            recommendations.append(
                f"Güçlü olduğunuz konuları kullanarak diğer konuları öğrenin: {', '.join(strengths[:2])}"
            )

        return recommendations

    async def _evaluate_open_ended_answer(
        self, question: Question, answer: str
    ) -> float:
        """
        Açık uçlu soruları LLM ile değerlendir

        Args:
            question: Soru
            answer: Öğrenci cevabı

        Returns:
            Puan (0.0-1.0)
        """
        if not answer.strip():
            return 0.0

        try:
            prompt = f"""
            Soru: {question.question_text}
            Konu: {question.topic}
            Öğrenci Cevabı: {answer}
            
            Bu açık uçlu soruya verilen cevabı değerlendir:
            
            Değerlendirme Kriterleri:
            1. Doğruluk (0-40 puan)
            2. Eksiksizlik (0-30 puan)
            3. Açıklık (0-20 puan)
            4. Örnekler/Detaylar (0-10 puan)
            
            Toplam 100 üzerinden puan ver ve kısa gerekçe yaz.
            
            JSON formatında yanıtla:
            {{
                "score": 85,
                "reasoning": "Cevap doğru ve eksiksiz, örnekler iyi..."
            }}
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.3)

            if result["success"]:
                try:
                    data = json.loads(result["text"])
                    score = data.get("score", 50) / 100.0  # 0-1 aralığına normalize et
                    return max(0.0, min(1.0, score))  # 0-1 aralığında sınırla
                except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                    pass

            # Fallback: Basit uzunluk ve anahtar kelime analizi
            return self._simple_open_ended_evaluation(question, answer)

        except Exception as e:
            logger.warning(f"Open-ended evaluation error: {e!s}")
            return self._simple_open_ended_evaluation(question, answer)

    def _simple_open_ended_evaluation(self, question: Question, answer: str) -> float:
        """Basit açık uçlu değerlendirme"""
        if not answer.strip():
            return 0.0

        # Basit kriterler
        score = 0.0

        # Uzunluk kontrolü
        if len(answer) > 10:
            score += 0.3
        if len(answer) > 50:
            score += 0.2

        # Konu ile ilgili anahtar kelimeler
        topic_keywords = question.topic.lower().split()
        answer_lower = answer.lower()

        keyword_matches = sum(
            1 for keyword in topic_keywords if keyword in answer_lower
        )
        if keyword_matches > 0:
            score += min(0.5, keyword_matches * 0.2)

        return min(1.0, score)

    async def _determine_knowledge_level_advanced(
        self,
        total_score: float,
        topic_performance: dict[str, dict[str, Any]],
        difficulty_performance: dict[str, dict[str, Any]],
        time_taken: int,
    ) -> str:
        """Gelişmiş bilgi seviyesi belirleme"""

        # Temel puan bazlı seviye
        base_level = "beginner"
        if total_score >= 90:
            base_level = "expert"
        elif total_score >= 75:
            base_level = "advanced"
        elif total_score >= 60:
            base_level = "intermediate"
        elif total_score >= 40:
            base_level = "elementary"

        # Zorluk performansını analiz et
        difficulty_bonus = 0
        if "hard" in difficulty_performance:
            hard_avg = sum(difficulty_performance["hard"]["scores"]) / len(
                difficulty_performance["hard"]["scores"]
            )
            if hard_avg > 0.7:
                difficulty_bonus += 1

        if "very_hard" in difficulty_performance:
            very_hard_avg = sum(difficulty_performance["very_hard"]["scores"]) / len(
                difficulty_performance["very_hard"]["scores"]
            )
            if very_hard_avg > 0.6:
                difficulty_bonus += 2

        # Zaman faktörü (hızlı ve doğru cevap bonus)
        expected_time = len(topic_performance) * 90  # Soru başına 90 saniye beklentisi
        if time_taken < expected_time * 0.7 and total_score > 70:
            difficulty_bonus += 1

        # Seviye ayarlaması
        level_hierarchy = [
            "beginner",
            "elementary",
            "intermediate",
            "advanced",
            "expert",
        ]
        current_index = level_hierarchy.index(base_level)
        adjusted_index = min(len(level_hierarchy) - 1, current_index + difficulty_bonus)

        return level_hierarchy[adjusted_index]

    def _analyze_topic_performance(
        self, topic_performance: dict[str, dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """Konu bazında güçlü ve zayıf alanları analiz et"""
        strengths = []
        weaknesses = []

        for topic, data in topic_performance.items():
            avg_score = sum(data["scores"]) / len(data["scores"])

            if avg_score >= 0.8:
                strengths.append(topic)
            elif avg_score <= 0.4:
                weaknesses.append(topic)

        return strengths, weaknesses

    async def _generate_comprehensive_recommendations(
        self,
        student_id: str,
        knowledge_level: str,
        strengths: list[str],
        weaknesses: list[str],
        assessment_type: AssessmentType,
        topic_performance: dict[str, dict[str, Any]],
        difficulty_performance: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Kapsamlı öneriler oluştur"""

        # Temel öneriler
        base_recommendations = self._generate_recommendations(
            knowledge_level, strengths, weaknesses, assessment_type
        )

        # Gelişmiş öneriler
        advanced_recommendations = []

        # Zorluk bazında öneriler
        if "easy" in difficulty_performance:
            easy_avg = sum(difficulty_performance["easy"]["scores"]) / len(
                difficulty_performance["easy"]["scores"]
            )
            if easy_avg < 0.6:
                advanced_recommendations.append(
                    "Temel kavramlara daha fazla zaman ayırın"
                )

        if "hard" in difficulty_performance:
            hard_avg = sum(difficulty_performance["hard"]["scores"]) / len(
                difficulty_performance["hard"]["scores"]
            )
            if hard_avg > 0.7:
                advanced_recommendations.append(
                    "Zor problemlerle kendinizi daha fazla zorlayabilirsiniz"
                )

        # Konu çeşitliliği önerisi
        if len(topic_performance) < 3:
            advanced_recommendations.append(
                "Daha geniş konu yelpazesinde çalışma yapın"
            )

        # Önceki değerlendirmelerle karşılaştırma
        previous_assessments = self.get_student_assessments(student_id)
        if len(previous_assessments) > 1:
            last_score = previous_assessments[-2].total_score
            current_score = (
                sum(sum(data["scores"]) for data in topic_performance.values())
                / sum(len(data["scores"]) for data in topic_performance.values())
                * 100
            )

            if current_score > last_score + 10:
                advanced_recommendations.append(
                    "Harika ilerleme! Bu tempoda devam edin"
                )
            elif current_score < last_score - 10:
                advanced_recommendations.append(
                    "Son değerlendirmeden düşüş var, çalışma stratejinizi gözden geçirin"
                )

        return base_recommendations + advanced_recommendations

    def get_assessment_result(self, assessment_id: str) -> AssessmentResult | None:
        """Değerlendirme sonucunu getir"""
        return self.assessments.get(assessment_id)

    def get_student_assessments(self, student_id: str) -> list[AssessmentResult]:
        """Öğrencinin tüm değerlendirmelerini getir"""
        return [
            result
            for result in self.assessments.values()
            if result.student_id == student_id
        ]

    async def create_guided_self_assessment_flow(
        self, student_id: str, subjects: list[str], learning_goals: list[str]
    ) -> dict[str, Any]:
        """
        Guided self-assessment flow with step-by-step questions

        Args:
            student_id: Öğrenci ID
            subjects: Değerlendirilecek dersler
            learning_goals: Öğrenme hedefleri

        Returns:
            Adım adım self-assessment flow
        """
        try:
            flow_steps = []

            # Adım 1: Genel motivasyon ve hedef belirleme
            step1_questions = [
                Question(
                    question_id=f"flow_motivation_{student_id}",
                    question_text="Öğrenme hedeflerinize ulaşmak için ne kadar motive hissediyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject="Genel",
                    topic="Motivasyon",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç motive değilim",
                        "2 - Az motive",
                        "3 - Orta",
                        "4 - Motive",
                        "5 - Çok motive",
                    ],
                    points=1,
                    metadata={"step": 1, "category": "motivation"},
                ),
                Question(
                    question_id=f"flow_commitment_{student_id}",
                    question_text="Günde ne kadar süre çalışmaya ayırabileceğinizi düşünüyorsunuz?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    subject="Genel",
                    topic="Zaman Yönetimi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "A) 30 dakikadan az",
                        "B) 30-60 dakika",
                        "C) 1-2 saat",
                        "D) 2 saatten fazla",
                    ],
                    points=1,
                    metadata={"step": 1, "category": "time_commitment"},
                ),
            ]

            flow_steps.append(
                {
                    "step": 1,
                    "title": "Motivasyon ve Zaman Değerlendirmesi",
                    "description": "Öğrenme motivasyonunuzu ve zaman ayırma kapasitenizi değerlendirin",
                    "questions": step1_questions,
                    "estimated_time": 3,
                }
            )

            # Adım 2: Her ders için detaylı self-assessment
            for i, subject in enumerate(subjects):
                step_questions = []

                # Güven seviyesi
                confidence_q = Question(
                    question_id=f"flow_confidence_{subject}_{student_id}",
                    question_text=f"{subject} konusundaki bilgi seviyenizi nasıl değerlendiriyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="Güven Seviyesi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç bilmiyorum",
                        "2 - Az biliyorum",
                        "3 - Orta seviyede",
                        "4 - İyi biliyorum",
                        "5 - Uzmanım",
                    ],
                    points=1,
                    metadata={
                        "step": i + 2,
                        "category": "confidence",
                        "subject": subject,
                    },
                )
                step_questions.append(confidence_q)

                # İlgi seviyesi
                interest_q = Question(
                    question_id=f"flow_interest_{subject}_{student_id}",
                    question_text=f"{subject} dersine olan ilginizi nasıl değerlendiriyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="İlgi Seviyesi",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Hiç ilgim yok",
                        "2 - Az ilgim var",
                        "3 - Orta seviyede",
                        "4 - İlgiliyim",
                        "5 - Çok ilgiliyim",
                    ],
                    points=1,
                    metadata={
                        "step": i + 2,
                        "category": "interest",
                        "subject": subject,
                    },
                )
                step_questions.append(interest_q)

                # Zorluk algısı
                difficulty_q = Question(
                    question_id=f"flow_difficulty_{subject}_{student_id}",
                    question_text=f"{subject} dersini ne kadar zor buluyorsunuz?",
                    question_type=QuestionType.SCALE,
                    subject=subject,
                    topic="Zorluk Algısı",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "1 - Çok kolay",
                        "2 - Kolay",
                        "3 - Orta",
                        "4 - Zor",
                        "5 - Çok zor",
                    ],
                    points=1,
                    metadata={
                        "step": i + 2,
                        "category": "difficulty_perception",
                        "subject": subject,
                    },
                )
                step_questions.append(difficulty_q)

                # Önceki deneyim
                experience_q = Question(
                    question_id=f"flow_experience_{subject}_{student_id}",
                    question_text=f"{subject} konusunda daha önce hangi kaynaklardan yararlandınız?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    subject=subject,
                    topic="Önceki Deneyim",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "A) Sadece okul dersleri",
                        "B) Ders kitapları ve kaynak kitaplar",
                        "C) Online videolar ve kurslar",
                        "D) Özel ders veya kurs",
                    ],
                    points=1,
                    metadata={
                        "step": i + 2,
                        "category": "previous_experience",
                        "subject": subject,
                    },
                )
                step_questions.append(experience_q)

                flow_steps.append(
                    {
                        "step": i + 2,
                        "title": f"{subject} Dersi Değerlendirmesi",
                        "description": f"{subject} dersindeki durumunuzu detaylı olarak değerlendirin",
                        "questions": step_questions,
                        "estimated_time": 5,
                    }
                )

            # Son adım: Öğrenme stili ve tercihler
            final_step_questions = [
                Question(
                    question_id=f"flow_learning_style_{student_id}",
                    question_text="Hangi öğrenme yöntemini en etkili buluyorsunuz?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    subject="Genel",
                    topic="Öğrenme Stili",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "A) Görsel materyaller (video, resim, grafik)",
                        "B) İşitsel materyaller (ses, müzik, anlatım)",
                        "C) Okuma ve yazma (metin, makale, not)",
                        "D) Uygulamalı çalışma (pratik, proje, deney)",
                    ],
                    points=1,
                    metadata={"step": len(subjects) + 2, "category": "learning_style"},
                ),
                Question(
                    question_id=f"flow_study_environment_{student_id}",
                    question_text="Hangi ortamda daha iyi çalışabiliyorsunuz?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    subject="Genel",
                    topic="Çalışma Ortamı",
                    difficulty=DifficultyLevel.EASY,
                    options=[
                        "A) Sessiz ve sakin ortam",
                        "B) Hafif müzik eşliğinde",
                        "C) Grup halinde çalışma",
                        "D) Değişken ortamlar",
                    ],
                    points=1,
                    metadata={
                        "step": len(subjects) + 2,
                        "category": "study_environment",
                    },
                ),
                Question(
                    question_id=f"flow_challenges_{student_id}",
                    question_text="Öğrenme sürecinde karşılaştığınız en büyük zorluk nedir?",
                    question_type=QuestionType.OPEN_ENDED,
                    subject="Genel",
                    topic="Zorluklar",
                    difficulty=DifficultyLevel.MEDIUM,
                    points=1,
                    metadata={"step": len(subjects) + 2, "category": "challenges"},
                ),
            ]

            flow_steps.append(
                {
                    "step": len(subjects) + 2,
                    "title": "Öğrenme Tercihleri ve Zorluklar",
                    "description": "Öğrenme stilinizi ve karşılaştığınız zorlukları belirleyin",
                    "questions": final_step_questions,
                    "estimated_time": 7,
                }
            )

            # Flow özeti
            flow_data = {
                "flow_id": f"guided_self_assessment_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "subjects": subjects,
                "learning_goals": learning_goals,
                "total_steps": len(flow_steps),
                "total_questions": sum(len(step["questions"]) for step in flow_steps),
                "estimated_total_time": sum(
                    step["estimated_time"] for step in flow_steps
                ),
                "steps": flow_steps,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }

            logger.info(
                f"Created guided self-assessment flow for student {student_id}: {len(flow_steps)} steps, {flow_data['total_questions']} questions"
            )
            return flow_data

        except Exception as e:
            logger.error(f"Create guided self-assessment flow error: {e!s}")
            raise


# Singleton instance
assessment_system = AssessmentSystem()
