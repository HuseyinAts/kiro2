"""
Enhanced Content Manager - Performance Optimized
Teknofest 2025 - Educational Content Management System
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExamType(Enum):
    """Exam types"""

    LGS = "lgs"
    YKS = "yks"
    BOTH = "both"


class DifficultyLevel(Enum):
    """Difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ContentType(Enum):
    """Content types"""

    LESSON = "lesson"
    QUESTION = "question"
    EXAMPLE = "example"
    PRACTICE = "practice"
    VIDEO = "video"
    ARTICLE = "article"


@dataclass
class Question:
    """Question data structure"""

    id: str
    question: str
    options: list[str]
    correct: str
    explanation: str
    difficulty: DifficultyLevel
    time_estimate: int  # seconds
    topic: str
    subtopic: str
    exam_type: ExamType


@dataclass
class Topic:
    """Topic data structure"""

    id: str
    title: str
    subject: str
    grade: int
    exam_type: ExamType
    weight: float  # percentage
    subtopics: list[dict[str, Any]]
    learning_objectives: list[str]
    key_concepts: list[str]


@dataclass
class StudyPlan:
    """Study plan data structure"""

    name: str
    duration_weeks: int
    daily_hours: float
    subjects: dict[str, float]  # subject -> hours per day
    weekly_schedule: dict[str, list[str]]
    milestones: list[dict[str, Any]]


class EnhancedContentManager:
    """Enhanced content management with performance optimizations"""

    def __init__(self, content_dir: str = "backend/content"):
        self.content_dir = Path(content_dir)
        self._content_cache = {}
        self._questions_cache = {}
        self._topics_cache = {}
        self._study_plans_cache = {}

        # Performance settings
        self._cache_ttl = 3600  # 1 hour
        self._max_cache_size = 1000

        # Load content on initialization
        asyncio.create_task(self._load_all_content())

    async def _load_all_content(self):
        """Load all content files asynchronously"""
        try:
            # Load enhanced LGS content
            await self._load_enhanced_lgs_content()

            # Load additional content files
            await self._load_additional_content()

            logger.info("All educational content loaded successfully")

        except Exception as e:
            logger.error(f"Error loading content: {e}")

    async def _load_enhanced_lgs_content(self):
        """Load enhanced LGS content"""
        try:
            content_file = self.content_dir / "enhanced_lgs_content.yaml"

            if content_file.exists():
                with open(content_file, encoding="utf-8") as f:
                    content = yaml.safe_load(f)

                # Cache the content
                self._content_cache["enhanced_lgs"] = content

                # Process and cache questions
                await self._process_questions(content)

                # Process and cache topics
                await self._process_topics(content)

                # Process and cache study plans
                await self._process_study_plans(content)

                logger.info("Enhanced LGS content loaded and processed")

        except Exception as e:
            logger.error(f"Error loading enhanced LGS content: {e}")

    async def _load_additional_content(self):
        """Load additional content files"""
        try:
            # Load original LGS matematik content
            original_file = self.content_dir / "lgs_matematik.yaml"

            if original_file.exists():
                with open(original_file, encoding="utf-8") as f:
                    content = yaml.safe_load(f)

                self._content_cache["lgs_matematik"] = content
                logger.info("Original LGS matematik content loaded")

        except Exception as e:
            logger.error(f"Error loading additional content: {e}")

    async def _process_questions(self, content: dict[str, Any]):
        """Process and cache questions from content"""
        try:
            questions = []

            # Extract questions from all subjects
            subjects = content.get("subjects", {})

            for subject_name, subject_data in subjects.items():
                topics = subject_data.get("topics", {})

                for topic_name, topic_data in topics.items():
                    subtopics = topic_data.get("subtopics", {})

                    for subtopic_name, subtopic_data in subtopics.items():
                        practice_questions = subtopic_data.get("practice_questions", [])

                        for q_data in practice_questions:
                            question = Question(
                                id=q_data.get(
                                    "id",
                                    f"{topic_name}_{subtopic_name}_{len(questions)}",
                                ),
                                question=q_data.get("question", ""),
                                options=q_data.get("options", []),
                                correct=q_data.get("correct", ""),
                                explanation=q_data.get("explanation", ""),
                                difficulty=DifficultyLevel(
                                    q_data.get("difficulty", "medium")
                                ),
                                time_estimate=q_data.get("time_estimate", 120),
                                topic=topic_name,
                                subtopic=subtopic_name,
                                exam_type=ExamType.LGS,
                            )
                            questions.append(question)

            # Cache questions by various criteria
            self._questions_cache["all"] = questions
            self._cache_questions_by_criteria(questions)

            logger.info(f"Processed {len(questions)} questions")

        except Exception as e:
            logger.error(f"Error processing questions: {e}")

    def _cache_questions_by_criteria(self, questions: list[Question]):
        """Cache questions by different criteria for fast retrieval"""
        # By difficulty
        for difficulty in DifficultyLevel:
            self._questions_cache[f"difficulty_{difficulty.value}"] = [
                q for q in questions if q.difficulty == difficulty
            ]

        # By topic
        topics = set(q.topic for q in questions)
        for topic in topics:
            self._questions_cache[f"topic_{topic}"] = [
                q for q in questions if q.topic == topic
            ]

        # By subtopic
        subtopics = set(q.subtopic for q in questions)
        for subtopic in subtopics:
            self._questions_cache[f"subtopic_{subtopic}"] = [
                q for q in questions if q.subtopic == subtopic
            ]

    async def _process_topics(self, content: dict[str, Any]):
        """Process and cache topics from content"""
        try:
            topics = []
            subjects = content.get("subjects", {})

            for subject_name, subject_data in subjects.items():
                topic_data = subject_data.get("topics", {})

                for topic_name, topic_info in topic_data.items():
                    topic = Topic(
                        id=topic_name,
                        title=topic_info.get("title", topic_name),
                        subject=subject_name,
                        grade=8,  # LGS is for 8th grade
                        exam_type=ExamType.LGS,
                        weight=topic_info.get("weight", 0),
                        subtopics=list(topic_info.get("subtopics", {}).keys()),
                        learning_objectives=topic_info.get("learning_objectives", []),
                        key_concepts=topic_info.get("key_concepts", []),
                    )
                    topics.append(topic)

            self._topics_cache["all"] = topics

            # Cache by subject
            subjects = set(t.subject for t in topics)
            for subject in subjects:
                self._topics_cache[f"subject_{subject}"] = [
                    t for t in topics if t.subject == subject
                ]

            logger.info(f"Processed {len(topics)} topics")

        except Exception as e:
            logger.error(f"Error processing topics: {e}")

    async def _process_study_plans(self, content: dict[str, Any]):
        """Process and cache study plans from content"""
        try:
            study_plans = []
            plans_data = content.get("study_recommendations", {})

            # Create study plans from recommendations
            if "daily_schedule" in plans_data and "weekly_plan" in plans_data:
                daily = plans_data["daily_schedule"]
                weekly = plans_data["weekly_plan"]

                plan = StudyPlan(
                    name="LGS Hazırlık Planı",
                    duration_weeks=12,
                    daily_hours=daily.get("total_time", 4),
                    subjects={
                        "matematik": daily.get("distribution", {}).get("matematik", 90)
                        / 60,
                        "fen": daily.get("distribution", {}).get("fen", 90) / 60,
                        "turkce": daily.get("distribution", {}).get("turkce", 60) / 60,
                        "sosyal": daily.get("distribution", {}).get("sosyal", 30) / 60,
                    },
                    weekly_schedule=weekly,
                    milestones=[
                        {"week": 4, "goal": "Temel konuları tamamla"},
                        {"week": 8, "goal": "Orta seviye problemleri çöz"},
                        {"week": 12, "goal": "Deneme sınavlarında hedef puana ulaş"},
                    ],
                )
                study_plans.append(plan)

            self._study_plans_cache["all"] = study_plans
            logger.info(f"Processed {len(study_plans)} study plans")

        except Exception as e:
            logger.error(f"Error processing study plans: {e}")

    @lru_cache(maxsize=100)
    def get_questions_by_topic(
        self, topic: str, difficulty: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get questions by topic with caching"""
        cache_key = f"topic_{topic}"
        questions = self._questions_cache.get(cache_key, [])

        if difficulty:
            questions = [q for q in questions if q.difficulty.value == difficulty]

        # Convert to dict for JSON serialization
        result = []
        for q in questions[:limit]:
            result.append(
                {
                    "id": q.id,
                    "question": q.question,
                    "options": q.options,
                    "correct": q.correct,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value,
                    "time_estimate": q.time_estimate,
                    "topic": q.topic,
                    "subtopic": q.subtopic,
                }
            )

        return result

    @lru_cache(maxsize=50)
    def get_topic_info(self, topic: str) -> dict[str, Any] | None:
        """Get detailed topic information with caching"""
        content = self._content_cache.get("enhanced_lgs", {})
        subjects = content.get("subjects", {})

        for subject_name, subject_data in subjects.items():
            topics = subject_data.get("topics", {})
            if topic in topics:
                topic_data = topics[topic]
                return {
                    "id": topic,
                    "title": topic_data.get("title", topic),
                    "subject": subject_name,
                    "weight": topic_data.get("weight", 0),
                    "subtopics": topic_data.get("subtopics", {}),
                    "difficulty_distribution": topic_data.get(
                        "difficulty_distribution", {}
                    ),
                    "learning_objectives": topic_data.get("learning_objectives", []),
                }

        return None

    def get_study_plan(self, _: str = "default") -> dict[str, Any] | None:
        """Get study plan by name"""
        plans = self._study_plans_cache.get("all", [])

        if plans:
            plan = plans[0]  # Get first plan for now
            return {
                "name": plan.name,
                "duration_weeks": plan.duration_weeks,
                "daily_hours": plan.daily_hours,
                "subjects": plan.subjects,
                "weekly_schedule": plan.weekly_schedule,
                "milestones": plan.milestones,
            }

        return None

    def get_curriculum_coverage(self, subject: str) -> dict[str, Any]:
        """Get curriculum coverage information"""
        content = self._content_cache.get("enhanced_lgs", {})

        if subject in content.get("subjects", {}):
            subject_data = content["subjects"][subject]

            total_questions = subject_data.get("total_questions", 0)
            topics = subject_data.get("topics", {})

            coverage = {
                "subject": subject,
                "total_questions": total_questions,
                "time_allocation": subject_data.get("time_allocation", 0),
                "weight": subject_data.get("weight", 0),
                "topics_count": len(topics),
                "topics": [],
            }

            for topic_name, topic_data in topics.items():
                coverage["topics"].append(
                    {
                        "name": topic_name,
                        "title": topic_data.get("title", topic_name),
                        "weight": topic_data.get("weight", 0),
                        "subtopics_count": len(topic_data.get("subtopics", {})),
                    }
                )

            return coverage

        return {}

    def get_exam_strategies(self) -> dict[str, Any]:
        """Get exam strategies and tips"""
        content = self._content_cache.get("enhanced_lgs", {})
        return content.get("study_recommendations", {}).get("exam_strategies", {})

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance tracking metrics"""
        content = self._content_cache.get("enhanced_lgs", {})
        return content.get("performance_tracking", {})

    async def generate_personalized_content(
        self,
        student_profile: dict[str, Any],
        content_type: ContentType,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> dict[str, Any]:
        """Generate personalized content based on student profile"""
        try:
            # Get base content
            base_content = self.get_topic_info(topic)

            if not base_content:
                return {"error": "Topic not found"}

            # Customize based on student profile
            learning_style = student_profile.get("learning_style", "mixed")
            current_level = student_profile.get("knowledge_level", "beginner")

            # Get appropriate questions
            questions = self.get_questions_by_topic(
                topic=topic, difficulty=difficulty.value, limit=5
            )

            # Prepare personalized response
            personalized_content = {
                "topic": base_content,
                "questions": questions,
                "recommendations": self._get_personalized_recommendations(
                    learning_style, current_level, topic
                ),
                "study_tips": self._get_study_tips(topic, difficulty),
                "estimated_time": self._calculate_study_time(questions, difficulty),
            }

            return personalized_content

        except Exception as e:
            logger.error(f"Error generating personalized content: {e}")
            return {"error": str(e)}

    def _get_personalized_recommendations(
        self, learning_style: str, level: str, topic: str
    ) -> list[str]:
        """Get personalized recommendations based on learning style and level"""
        recommendations = []

        # Learning style specific recommendations
        if learning_style == "visual":
            recommendations.extend(
                [
                    "Konuyu görsel materyallerle çalış",
                    "Diyagramlar ve şekiller çiz",
                    "Renkli kalemler kullan",
                ]
            )
        elif learning_style == "auditory":
            recommendations.extend(
                [
                    "Konuyu sesli tekrar et",
                    "Eğitim videolarını izle",
                    "Arkadaşlarınla tartış",
                ]
            )
        elif learning_style == "kinesthetic":
            recommendations.extend(
                ["Bol pratik yap", "Gerçek örnekler bul", "Hareket ederek çalış"]
            )

        # Level specific recommendations
        if level == "beginner":
            recommendations.extend(
                [
                    "Temel kavramlardan başla",
                    "Basit örneklerle pratik yap",
                    "Acele etme, temeli sağlam at",
                ]
            )
        elif level == "advanced":
            recommendations.extend(
                [
                    "Zor problemlere odaklan",
                    "Farklı çözüm yolları dene",
                    "Zaman sınırı koy",
                ]
            )

        return recommendations

    def _get_study_tips(self, topic: str, difficulty: DifficultyLevel) -> list[str]:
        """Get study tips for specific topic and difficulty"""
        tips = [
            "Düzenli çalışma alışkanlığı edin",
            "Yanlışlarınızı analiz edin",
            "Bol tekrar yapın",
        ]

        # Topic specific tips
        if "matematik" in topic:
            tips.extend(
                [
                    "Formülleri ezberlemek yerine mantığını anla",
                    "Bol soru çöz",
                    "İşlem hatalarına dikkat et",
                ]
            )
        elif "fen" in topic:
            tips.extend(
                [
                    "Deney ve gözlemleri iyi anla",
                    "Günlük hayatla ilişkilendir",
                    "Grafik ve tablo yorumlamayı öğren",
                ]
            )

        return tips

    def _calculate_study_time(
        self, questions: list[dict], difficulty: DifficultyLevel
    ) -> int:
        """Calculate estimated study time in minutes"""
        base_time = len(questions) * 2  # 2 minutes per question

        # Adjust based on difficulty
        if difficulty == DifficultyLevel.EASY:
            return int(base_time * 0.8)
        if difficulty == DifficultyLevel.HARD:
            return int(base_time * 1.5)

        return base_time

    def clear_cache(self):
        """Clear all caches"""
        self._content_cache.clear()
        self._questions_cache.clear()
        self._topics_cache.clear()
        self._study_plans_cache.clear()

        # Clear LRU caches
        self.get_questions_by_topic.cache_clear()
        self.get_topic_info.cache_clear()

        logger.info("All content caches cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "content_cache_size": len(self._content_cache),
            "questions_cache_size": len(self._questions_cache),
            "topics_cache_size": len(self._topics_cache),
            "study_plans_cache_size": len(self._study_plans_cache),
            "lru_cache_info": {
                "get_questions_by_topic": self.get_questions_by_topic.cache_info()._asdict(),
                "get_topic_info": self.get_topic_info.cache_info()._asdict(),
            },
        }


# Singleton instance
content_manager = EnhancedContentManager()
