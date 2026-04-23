"""
Khan Academy API Entegrasyonu
Yapılandırılmış eğitim içeriği erişimi
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KhanCourse:
    """Khan Academy ders modeli"""

    course_id: str
    title: str
    description: str
    subject: str
    grade_level: str
    topics: list[str]
    total_lessons: int
    estimated_hours: float
    difficulty: str
    language: str
    prerequisites: list[str]
    skills: list[str]


@dataclass
class KhanLesson:
    """Khan Academy ders modeli"""

    lesson_id: str
    title: str
    description: str
    course_id: str
    video_url: str | None
    exercise_url: str | None
    article_url: str | None
    duration_minutes: int
    mastery_points: int
    content_type: str  # video, exercise, article
    difficulty: str
    prerequisites: list[str]


@dataclass
class KhanExercise:
    """Khan Academy alıştırma modeli"""

    exercise_id: str
    title: str
    description: str
    topic: str
    difficulty: str
    question_types: list[str]
    hints_available: bool
    mastery_points: int
    average_time_minutes: int
    prerequisite_skills: list[str]


class KhanAcademyService:
    """Khan Academy API servisi"""

    def __init__(self):
        self.base_url = "https://www.khanacademy.org/api/v1"
        self.turkish_base = "https://tr.khanacademy.org/api/v1"
        self.public_base = "https://www.khanacademy.org/api/internal"
        self.grade_mapping = self._load_grade_mapping()
        self.subject_mapping = self._load_subject_mapping()
        self.session = None
        self.rate_limit_delay = 0.2  # 200ms delay between requests
        self.max_retries = 3
        self.content_cache = {}  # Simple in-memory cache

    def _load_grade_mapping(self) -> dict[str, list[str]]:
        """Sınıf seviyesi haritalaması"""
        return {
            "ilkokul": ["1", "2", "3", "4"],
            "ortaokul": ["5", "6", "7", "8"],
            "lise": ["9", "10", "11", "12"],
            "LGS": ["8"],
            "YKS": ["11", "12"],
        }

    def _load_subject_mapping(self) -> dict[str, str]:
        """Ders haritalaması"""
        return {
            "matematik": "math",
            "fen": "science",
            "fizik": "physics",
            "kimya": "chemistry",
            "biyoloji": "biology",
            "tarih": "history",
            "türkçe": "turkish",
            "ingilizce": "english",
            "bilgisayar": "computing",
            "ekonomi": "economics",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_courses(
        self,
        subject: str,
        grade_level: str | None = None,
        language: str = "tr",
        limit: int = 10,
    ) -> list[KhanCourse]:
        """
        Kurs ara (Gerçek Khan Academy API)

        Args:
            subject: Ders konusu
            grade_level: Sınıf seviyesi
            language: Dil kodu
            limit: Maksimum sonuç

        Returns:
            Kurs listesi
        """
        try:
            # Cache key oluştur
            cache_key = f"courses_{subject}_{grade_level}_{language}_{limit}"
            if cache_key in self.content_cache:
                logger.info(f"Returning cached courses for {subject}")
                return self.content_cache[cache_key]

            # Khan Academy'nin public API'sini kullan
            courses = await self._fetch_topic_tree(subject, language)

            # Sınıf seviyesine göre filtrele
            if grade_level:
                courses = [
                    c for c in courses if self._matches_grade_level(c, grade_level)
                ]

            # Limit uygula
            courses = courses[:limit]

            # Cache'e kaydet
            self.content_cache[cache_key] = courses

            logger.info(f"Found {len(courses)} Khan Academy courses for {subject}")
            return courses

        except Exception as e:
            logger.error(f"Search courses error: {e!s}")
            # Fallback to simulated courses
            return await self._simulate_courses(subject, grade_level, language, limit)

    async def _fetch_topic_tree(
        self, subject: str, language: str = "tr"
    ) -> list[KhanCourse]:
        """
        Khan Academy topic tree'den kursları getir

        Args:
            subject: Ders konusu
            language: Dil kodu

        Returns:
            Kurs listesi
        """
        try:
            session = await self._get_session()

            # Khan Academy'nin public topic tree endpoint'i
            base_url = self.turkish_base if language == "tr" else self.base_url
            url = f"{base_url}/topictree"

            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_topic_tree(data, subject)
                logger.warning(
                    f"Khan Academy API returned status {response.status}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching topic tree: {e!s}")
            return []

    def _parse_topic_tree(
        self, topic_tree: dict[str, Any], subject_filter: str
    ) -> list[KhanCourse]:
        """
        Topic tree'yi parse et ve kursları çıkar

        Args:
            topic_tree: Khan Academy topic tree
            subject_filter: Ders filtresi

        Returns:
            Kurs listesi
        """
        courses = []

        try:
            # Topic tree'yi recursive olarak dolaş
            def extract_courses(node: dict[str, Any], parent_subject: str = ""):
                if not isinstance(node, dict):
                    return

                node_kind = node.get("kind", "")
                node_title = node.get("title", "")
                node_description = node.get("description", "")

                # Subject node ise
                if (
                    node_kind == "Subject"
                    and subject_filter.lower() in node_title.lower()
                ):
                    # Bu subject altındaki topic'leri kurs olarak ekle
                    children = node.get("children", [])
                    for child in children:
                        if child.get("kind") == "Topic":
                            course = self._create_course_from_topic(child, node_title)
                            if course:
                                courses.append(course)

                # Topic node ise ve subject filtresi ile eşleşiyorsa
                elif node_kind == "Topic" and (
                    subject_filter.lower() in node_title.lower()
                    or subject_filter.lower() in parent_subject.lower()
                ):
                    course = self._create_course_from_topic(node, parent_subject)
                    if course:
                        courses.append(course)

                # Alt node'ları işle
                children = node.get("children", [])
                for child in children:
                    extract_courses(
                        child, node_title if node_kind == "Subject" else parent_subject
                    )

            extract_courses(topic_tree)

        except Exception as e:
            logger.error(f"Error parsing topic tree: {e!s}")

        return courses

    def _create_course_from_topic(
        self, topic_node: dict[str, Any], subject: str
    ) -> KhanCourse | None:
        """
        Topic node'dan kurs oluştur

        Args:
            topic_node: Topic node
            subject: Ana ders

        Returns:
            KhanCourse objesi
        """
        try:
            # Topic altındaki içerikleri say
            total_lessons = self._count_content_items(topic_node)

            # Zorluk seviyesini belirle
            difficulty = self._determine_difficulty(topic_node, subject)

            # Konuları çıkar
            topics = self._extract_topics(topic_node)

            course = KhanCourse(
                course_id=topic_node.get("id", ""),
                title=topic_node.get("title", ""),
                description=topic_node.get("description", ""),
                subject=subject,
                grade_level=self._determine_grade_level(topic_node, subject),
                topics=topics,
                total_lessons=total_lessons,
                estimated_hours=total_lessons * 0.5,  # Ortalama 30 dakika per lesson
                difficulty=difficulty,
                language="tr",
                prerequisites=self._extract_prerequisites(topic_node),
                skills=self._extract_skills(topic_node),
            )

            return course

        except Exception as e:
            logger.error(f"Error creating course from topic: {e!s}")
            return None

    def _count_content_items(self, node: dict[str, Any]) -> int:
        """Node altındaki içerik sayısını hesapla"""
        count = 0

        def count_recursive(n):
            nonlocal count
            if isinstance(n, dict):
                kind = n.get("kind", "")
                if kind in ["Video", "Exercise", "Article"]:
                    count += 1

                children = n.get("children", [])
                for child in children:
                    count_recursive(child)

        count_recursive(node)
        return count

    def _determine_difficulty(self, node: dict[str, Any], subject: str) -> str:
        """Zorluk seviyesini belirle"""
        title = node.get("title", "").lower()

        # Başlık bazlı zorluk tespiti
        if any(
            word in title for word in ["temel", "giriş", "başlangıç", "basic", "intro"]
        ):
            return "kolay"
        if any(word in title for word in ["ileri", "advanced", "expert", "uzman"]):
            return "zor"
        return "orta"

    def _determine_grade_level(self, node: dict[str, Any], subject: str) -> str:
        """Sınıf seviyesini belirle"""
        title = node.get("title", "").lower()

        # Başlık bazlı sınıf tespiti
        for grade in ["6", "7", "8", "9", "10", "11", "12"]:
            if f"{grade}." in title or f"grade {grade}" in title:
                return grade

        # Subject bazlı varsayılan seviye
        subject_grades = {
            "matematik": "9",
            "fen": "8",
            "fizik": "11",
            "kimya": "11",
            "biyoloji": "10",
        }

        return subject_grades.get(subject.lower(), "9")

    def _extract_topics(self, node: dict[str, Any]) -> list[str]:
        """Alt konuları çıkar"""
        topics = []

        def extract_recursive(n):
            if isinstance(n, dict):
                kind = n.get("kind", "")
                title = n.get("title", "")

                if kind == "Topic" and title:
                    topics.append(title)

                children = n.get("children", [])
                for child in children:
                    extract_recursive(child)

        extract_recursive(node)
        return topics[:10]  # En fazla 10 topic

    def _extract_prerequisites(self, node: dict[str, Any]) -> list[str]:
        """Önkoşulları çıkar"""
        # Khan Academy API'sinde explicit prerequisite bilgisi yok
        # Başlık bazlı tahmin yapabiliriz
        title = node.get("title", "").lower()

        if "algebra" in title or "cebir" in title:
            return ["Temel matematik"]
        if "calculus" in title or "analiz" in title:
            return ["Algebra", "Fonksiyonlar"]
        if "physics" in title or "fizik" in title:
            return ["Matematik", "Algebra"]

        return []

    def _extract_skills(self, node: dict[str, Any]) -> list[str]:
        """Becerileri çıkar"""
        # Genel beceriler
        return ["Problem çözme", "Analitik düşünme", "Matematiksel modelleme"]

    def _matches_grade_level(self, course: KhanCourse, grade_level: str) -> bool:
        """Kursun sınıf seviyesi ile eşleşip eşleşmediğini kontrol et"""
        return course.grade_level == grade_level or grade_level in course.title

    async def _simulate_courses(
        self, subject: str, grade_level: str | None, language: str, limit: int = 10
    ) -> list[KhanCourse]:
        """Kursları simüle et"""
        sample_courses = [
            KhanCourse(
                course_id="math-8",
                title="8. Sınıf Matematik",
                description="LGS'ye hazırlık için 8. sınıf matematik konuları",
                subject="matematik",
                grade_level="8",
                topics=[
                    "Cebirsel ifadeler",
                    "Denklemler",
                    "Eşitsizlikler",
                    "Üçgenler",
                    "Dönüşüm geometrisi",
                ],
                total_lessons=150,
                estimated_hours=75,
                difficulty="orta",
                language=language,
                prerequisites=["7. sınıf matematik"],
                skills=[
                    "problem çözme",
                    "analitik düşünme",
                    "geometrik görselleştirme",
                ],
            ),
            KhanCourse(
                course_id="science-8",
                title="8. Sınıf Fen Bilimleri",
                description="LGS fen bilimleri konuları",
                subject="fen",
                grade_level="8",
                topics=[
                    "Mevsimler",
                    "DNA ve Genetik",
                    "Basınç",
                    "Madde ve Endüstri",
                    "Elektrik",
                ],
                total_lessons=120,
                estimated_hours=60,
                difficulty="orta",
                language=language,
                prerequisites=["7. sınıf fen"],
                skills=["bilimsel düşünme", "deney tasarlama", "veri analizi"],
            ),
            KhanCourse(
                course_id="physics-11",
                title="11. Sınıf Fizik",
                description="TYT ve AYT fizik konuları",
                subject="fizik",
                grade_level="11",
                topics=[
                    "Kuvvet ve Hareket",
                    "Elektrik ve Manyetizma",
                    "Dalgalar",
                    "Optik",
                ],
                total_lessons=100,
                estimated_hours=50,
                difficulty="zor",
                language=language,
                prerequisites=["10. sınıf fizik", "matematik"],
                skills=["problem çözme", "matematiksel modelleme", "deneysel analiz"],
            ),
            KhanCourse(
                course_id="math-tyt",
                title="TYT Matematik",
                description="Temel Yeterlilik Testi matematik konuları",
                subject="matematik",
                grade_level="12",
                topics=[
                    "Temel kavramlar",
                    "Sayılar",
                    "Cebir",
                    "Geometri",
                    "Veri analizi",
                ],
                total_lessons=200,
                estimated_hours=100,
                difficulty="orta-zor",
                language=language,
                prerequisites=["lise matematik"],
                skills=["hızlı problem çözme", "analitik düşünme"],
            ),
        ]

        # Konuya göre filtrele
        if subject:
            subject_lower = subject.lower()
            courses = [
                c
                for c in sample_courses
                if subject_lower in c.subject.lower()
                or subject_lower in c.title.lower()
            ]
        else:
            courses = sample_courses

        return courses[:limit]

    async def get_course_content(self, course_id: str) -> list[KhanLesson]:
        """
        Kurs içeriğini getir

        Args:
            course_id: Kurs ID

        Returns:
            Ders listesi
        """
        try:
            # Simüle edilmiş dersler
            lessons = [
                KhanLesson(
                    lesson_id=f"{course_id}_lesson_1",
                    title="Cebirsel İfadeler - Giriş",
                    description="Cebirsel ifadelerin temelleri",
                    course_id=course_id,
                    video_url="https://tr.khanacademy.org/video/xxx",
                    exercise_url="https://tr.khanacademy.org/exercise/xxx",
                    article_url=None,
                    duration_minutes=15,
                    mastery_points=100,
                    content_type="video",
                    difficulty="kolay",
                    prerequisites=[],
                ),
                KhanLesson(
                    lesson_id=f"{course_id}_lesson_2",
                    title="Cebirsel İfadeler - Alıştırmalar",
                    description="Cebirsel ifadeler pratik",
                    course_id=course_id,
                    video_url=None,
                    exercise_url="https://tr.khanacademy.org/exercise/yyy",
                    article_url=None,
                    duration_minutes=20,
                    mastery_points=150,
                    content_type="exercise",
                    difficulty="orta",
                    prerequisites=[f"{course_id}_lesson_1"],
                ),
                KhanLesson(
                    lesson_id=f"{course_id}_lesson_3",
                    title="Denklemler - Teori",
                    description="Birinci dereceden denklemler",
                    course_id=course_id,
                    video_url="https://tr.khanacademy.org/video/zzz",
                    exercise_url="https://tr.khanacademy.org/exercise/zzz",
                    article_url="https://tr.khanacademy.org/article/zzz",
                    duration_minutes=25,
                    mastery_points=200,
                    content_type="video",
                    difficulty="orta",
                    prerequisites=[f"{course_id}_lesson_2"],
                ),
            ]

            logger.info(f"Retrieved {len(lessons)} lessons for course {course_id}")
            return lessons

        except Exception as e:
            logger.error(f"Get course content error: {e!s}")
            return []

    async def get_exercises(
        self, topic: str, difficulty: str | None = None, limit: int = 10
    ) -> list[KhanExercise]:
        """
        Alıştırmaları getir

        Args:
            topic: Konu
            difficulty: Zorluk seviyesi
            limit: Maksimum sayı

        Returns:
            Alıştırma listesi
        """
        try:
            # Simüle edilmiş alıştırmalar
            exercises = [
                KhanExercise(
                    exercise_id="ex_001",
                    title="Cebirsel İfadeler - Temel",
                    description="Cebirsel ifadeleri sadeleştirme",
                    topic=topic,
                    difficulty="kolay",
                    question_types=["çoktan seçmeli", "boşluk doldurma"],
                    hints_available=True,
                    mastery_points=50,
                    average_time_minutes=5,
                    prerequisite_skills=[],
                ),
                KhanExercise(
                    exercise_id="ex_002",
                    title="Denklem Çözme",
                    description="Birinci dereceden denklemleri çözme",
                    topic=topic,
                    difficulty="orta",
                    question_types=["açık uçlu", "adım adım çözüm"],
                    hints_available=True,
                    mastery_points=100,
                    average_time_minutes=10,
                    prerequisite_skills=["cebirsel ifadeler"],
                ),
                KhanExercise(
                    exercise_id="ex_003",
                    title="Problem Çözme",
                    description="Denklem kurma problemleri",
                    topic=topic,
                    difficulty="zor",
                    question_types=["problem çözme", "modelleme"],
                    hints_available=True,
                    mastery_points=150,
                    average_time_minutes=15,
                    prerequisite_skills=["denklem çözme"],
                ),
            ]

            # Zorluk filtresi
            if difficulty:
                exercises = [e for e in exercises if e.difficulty == difficulty]

            logger.info(f"Retrieved {len(exercises)} exercises for {topic}")
            return exercises[:limit]

        except Exception as e:
            logger.error(f"Get exercises error: {e!s}")
            return []

    async def get_learning_path(
        self, goal: str, current_level: str, time_available_hours: int
    ) -> dict[str, Any]:
        """
        Öğrenme yolu önerisi

        Args:
            goal: Öğrenme hedefi
            current_level: Mevcut seviye
            time_available_hours: Mevcut zaman (saat)

        Returns:
            Öğrenme yolu
        """
        try:
            # Hedefe göre kurs önerileri
            path = {
                "goal": goal,
                "current_level": current_level,
                "estimated_time": time_available_hours,
                "courses": [],
                "milestones": [],
                "recommendations": [],
            }

            # LGS hedefi
            if "LGS" in goal or "8. sınıf" in goal:
                path["courses"] = [
                    {
                        "course_id": "math-8",
                        "title": "8. Sınıf Matematik",
                        "priority": 1,
                    },
                    {"course_id": "science-8", "title": "8. Sınıf Fen", "priority": 1},
                    {
                        "course_id": "turkish-8",
                        "title": "8. Sınıf Türkçe",
                        "priority": 2,
                    },
                ]
                path["milestones"] = [
                    {"week": 1, "target": "Temel konuları gözden geçir"},
                    {"week": 4, "target": "İlk deneme sınavı"},
                    {"week": 8, "target": "Zayıf konuları pekiştir"},
                    {"week": 12, "target": "Yoğun soru çözümü"},
                ]

            # YKS hedefi
            elif "YKS" in goal or "TYT" in goal or "AYT" in goal:
                path["courses"] = [
                    {"course_id": "math-tyt", "title": "TYT Matematik", "priority": 1},
                    {"course_id": "physics-11", "title": "Fizik", "priority": 2},
                    {"course_id": "chemistry-11", "title": "Kimya", "priority": 2},
                ]
                path["milestones"] = [
                    {"month": 1, "target": "TYT temellerini tamamla"},
                    {"month": 3, "target": "AYT konularına başla"},
                    {"month": 6, "target": "Deneme sınavları"},
                    {"month": 9, "target": "Son tekrar ve eksik tamamlama"},
                ]

            # Genel öneriler
            path["recommendations"] = [
                "Günde en az 2 saat düzenli çalışma",
                "Haftada 1 deneme sınavı",
                "Zayıf konulara ekstra zaman ayırma",
                "Video derslerden sonra mutlaka alıştırma yapma",
            ]

            logger.info(f"Generated learning path for goal: {goal}")
            return path

        except Exception as e:
            logger.error(f"Get learning path error: {e!s}")
            return {}

    async def get_mastery_report(
        self, student_id: str, course_id: str
    ) -> dict[str, Any]:
        """
        Ustalık raporu (simüle edilmiş)

        Args:
            student_id: Öğrenci ID
            course_id: Kurs ID

        Returns:
            Ustalık raporu
        """
        try:
            # Simüle edilmiş rapor
            report = {
                "student_id": student_id,
                "course_id": course_id,
                "overall_mastery": 65,  # Yüzde
                "topics": [
                    {
                        "name": "Cebirsel İfadeler",
                        "mastery": 80,
                        "exercises_completed": 15,
                        "time_spent_minutes": 120,
                    },
                    {
                        "name": "Denklemler",
                        "mastery": 60,
                        "exercises_completed": 10,
                        "time_spent_minutes": 90,
                    },
                    {
                        "name": "Geometri",
                        "mastery": 55,
                        "exercises_completed": 8,
                        "time_spent_minutes": 75,
                    },
                ],
                "strengths": ["Cebirsel ifadeler", "Temel işlemler"],
                "weaknesses": ["Geometri", "Problem çözme"],
                "recommendations": [
                    "Geometri konusuna daha fazla zaman ayır",
                    "Problem çözme videolarını izle",
                    "Günlük 5 problem çöz",
                ],
                "last_activity": datetime.now().isoformat(),
            }

            logger.info(f"Generated mastery report for student {student_id}")
            return report

        except Exception as e:
            logger.error(f"Get mastery report error: {e!s}")
            return {}

    def get_grade_from_exam(self, exam_type: str) -> list[str]:
        """
        Sınav tipinden sınıf seviyelerini getir

        Args:
            exam_type: Sınav tipi (LGS, YKS)

        Returns:
            Sınıf seviyeleri
        """
        return self.grade_mapping.get(exam_type, [])

    def translate_subject(self, subject_tr: str) -> str:
        """
        Türkçe ders adını İngilizce'ye çevir

        Args:
            subject_tr: Türkçe ders adı

        Returns:
            İngilizce ders adı
        """
        return self.subject_mapping.get(subject_tr.lower(), subject_tr)

    async def get_video_transcript(
        self, video_id: str, language: str = "tr"
    ) -> str | None:
        """
        Video transkriptini getir (simüle edilmiş)

        Args:
            video_id: Video ID
            language: Dil kodu

        Returns:
            Transkript metni
        """
        try:
            # Simüle edilmiş transkript
            transcript = """
            Merhaba arkadaşlar, bugün cebirsel ifadeler konusunu işleyeceğiz.
            Cebirsel ifade, en az bir değişken ve sayıların matematiksel işlemlerle
            bir araya gelmesiyle oluşan ifadelerdir. Örneğin, 3x + 5 bir cebirsel ifadedir.
            Burada x değişkenimiz, 3 katsayımız ve 5 sabit terimdir.
            """

            return transcript.strip()

        except Exception as e:
            logger.error(f"Get transcript error: {e!s}")
            return None


# Singleton instance
khan_academy_service = KhanAcademyService()
