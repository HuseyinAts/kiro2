"""
Dynamic Content Generation System
Personalizes content based on student profile and context
"""

import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of educational content"""

    EXPLANATION = "explanation"
    EXAMPLE = "example"
    QUIZ = "quiz"
    FLASHCARD = "flashcard"
    SUMMARY = "summary"
    PRACTICE = "practice"
    VIDEO_SCRIPT = "video_script"
    INTERACTIVE = "interactive"


class DifficultyLevel(Enum):
    """Content difficulty levels"""

    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5


class LearningStyle(Enum):
    """Student learning styles"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


@dataclass
class ContentTemplate:
    """Template for generating content"""

    template_id: str
    content_type: ContentType
    difficulty_range: tuple[int, int]
    learning_styles: list[LearningStyle]
    structure: dict[str, Any]
    variables: list[str]
    examples: list[dict]
    metadata: dict = field(default_factory=dict)


@dataclass
class PersonalizedContent:
    """Generated personalized content"""

    content_id: str
    student_id: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    title: str
    body: str
    media_elements: list[dict] = field(default_factory=list)
    interactive_elements: list[dict] = field(default_factory=list)
    assessments: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


class ContentPersonalizer:
    """Personalize content based on student characteristics"""

    def __init__(self):
        self.style_adaptations = {
            LearningStyle.VISUAL: {
                "use_diagrams": True,
                "use_colors": True,
                "use_charts": True,
                "text_ratio": 0.4,
                "keywords": ["görsel", "şema", "grafik", "resim", "diyagram"],
            },
            LearningStyle.AUDITORY: {
                "use_mnemonics": True,
                "use_rhymes": True,
                "use_stories": True,
                "text_ratio": 0.6,
                "keywords": ["dinle", "ses", "konuş", "anlat", "tartış"],
            },
            LearningStyle.KINESTHETIC: {
                "use_activities": True,
                "use_experiments": True,
                "use_games": True,
                "text_ratio": 0.3,
                "keywords": ["yap", "uygula", "dene", "hareket", "aktivite"],
            },
            LearningStyle.READING_WRITING: {
                "use_lists": True,
                "use_notes": True,
                "use_summaries": True,
                "text_ratio": 0.8,
                "keywords": ["oku", "yaz", "not al", "özetle", "liste"],
            },
        }

        self.difficulty_adjustments = {
            DifficultyLevel.BEGINNER: {
                "vocabulary": "simple",
                "sentence_length": 10,
                "concepts_per_unit": 1,
                "examples_count": 3,
            },
            DifficultyLevel.ELEMENTARY: {
                "vocabulary": "basic",
                "sentence_length": 15,
                "concepts_per_unit": 2,
                "examples_count": 2,
            },
            DifficultyLevel.INTERMEDIATE: {
                "vocabulary": "standard",
                "sentence_length": 20,
                "concepts_per_unit": 3,
                "examples_count": 2,
            },
            DifficultyLevel.ADVANCED: {
                "vocabulary": "advanced",
                "sentence_length": 25,
                "concepts_per_unit": 4,
                "examples_count": 1,
            },
            DifficultyLevel.EXPERT: {
                "vocabulary": "technical",
                "sentence_length": 30,
                "concepts_per_unit": 5,
                "examples_count": 1,
            },
        }

    def adapt_content(
        self,
        base_content: str,
        learning_style: LearningStyle,
        difficulty: DifficultyLevel,
        student_interests: list[str] = None,
    ) -> str:
        """Adapt content to student's learning style and difficulty"""

        style_config = self.style_adaptations[learning_style]
        difficulty_config = self.difficulty_adjustments[difficulty]

        # Simplify or complexify vocabulary
        adapted_content = self._adjust_vocabulary(
            base_content, difficulty_config["vocabulary"]
        )

        # Add style-specific elements
        if style_config.get("use_diagrams"):
            adapted_content = self._add_visual_descriptions(adapted_content)

        if style_config.get("use_stories"):
            adapted_content = self._add_narrative_elements(adapted_content)

        if style_config.get("use_activities"):
            adapted_content = self._add_interactive_suggestions(adapted_content)

        # Personalize with student interests
        if student_interests:
            adapted_content = self._incorporate_interests(
                adapted_content, student_interests
            )

        # Add style keywords
        for keyword in style_config["keywords"]:
            if random.random() < 0.3:  # 30% chance to add keyword
                adapted_content = self._insert_keyword(adapted_content, keyword)

        return adapted_content

    def _adjust_vocabulary(self, content: str, level: str) -> str:
        """Adjust vocabulary complexity"""
        # Simplified implementation - would use NLP in production
        replacements = {
            "simple": {
                "utilize": "use",
                "demonstrate": "show",
                "comprehend": "understand",
                "significant": "important",
                "approximately": "about",
            },
            "basic": {
                "utilize": "use",
                "demonstrate": "show",
                "comprehend": "understand",
            },
            "standard": {},  # No changes
            "advanced": {
                "use": "utilize",
                "show": "demonstrate",
                "understand": "comprehend",
            },
            "technical": {
                "use": "utilize",
                "show": "demonstrate",
                "understand": "comprehend",
                "important": "significant",
                "about": "approximately",
            },
        }

        vocab_map = replacements.get(level, {})
        result = content

        for old_word, new_word in vocab_map.items():
            result = result.replace(old_word, new_word)

        return result

    def _add_visual_descriptions(self, content: str) -> str:
        """Add visual descriptions for visual learners"""
        visual_additions = [
            "\n[CHART] Bunu bir grafik olarak düşünün:",
            "\n[PALETTE] Görsel olarak şöyle canlandırabilirsiniz:",
            "\n📐 Şema halinde gösterirsek:",
            "\n🖼️ Resimli açıklama:",
        ]

        # Add visual description every few sentences
        sentences = content.split(". ")
        result = []

        for i, sentence in enumerate(sentences):
            result.append(sentence)
            if (i + 1) % 3 == 0 and random.random() < 0.5:
                result.append(random.choice(visual_additions))

        return ". ".join(result)

    def _add_narrative_elements(self, content: str) -> str:
        """Add story elements for auditory learners"""
        story_starters = [
            "Bunu bir hikaye gibi düşünelim: ",
            "Örnek bir senaryo: ",
            "Günlük hayattan bir örnek: ",
            "Bir öğrenci şöyle demiş: ",
        ]

        if random.random() < 0.6:
            return random.choice(story_starters) + content
        return content

    def _add_interactive_suggestions(self, content: str) -> str:
        """Add activity suggestions for kinesthetic learners"""
        activities = [
            "\n✋ Şimdi siz deneyin:",
            "\n[TARGET] Pratik yapalım:",
            "\n🏃 Hemen uygulayın:",
            "\n[VIDEO_GAME] Mini aktivite:",
        ]

        # Add activity suggestion at the end
        if random.random() < 0.7:
            return content + random.choice(activities)
        return content

    def _incorporate_interests(self, content: str, interests: list[str]) -> str:
        """Incorporate student interests into examples"""
        if not interests:
            return content

        interest = random.choice(interests)

        # Simple replacement of generic examples with interest-based ones
        generic_to_interest = {
            "örnek": f"{interest} örneği",
            "nesne": f"{interest}",
            "konu": f"{interest} konusu",
        }

        result = content
        for generic, specific in generic_to_interest.items():
            if generic in result and random.random() < 0.5:
                result = result.replace(generic, specific, 1)

        return result

    def _insert_keyword(self, content: str, keyword: str) -> str:
        """Insert learning style keyword naturally"""
        insertion_phrases = {
            "görsel": "Bu konuyu görsel olarak inceleyelim. ",
            "dinle": "Dikkatle dinleyin: ",
            "yap": "Hadi birlikte yapalım: ",
            "oku": "Şimdi okuyalım: ",
        }

        phrase = insertion_phrases.get(keyword.split()[0], "")
        if phrase and random.random() < 0.3:
            return phrase + content
        return content


class DynamicContentGenerator:
    """Generate dynamic educational content"""

    def __init__(self):
        self.personalizer = ContentPersonalizer()
        self.templates = self._load_templates()
        self.content_cache = {}
        self.generation_history = []

    def _load_templates(self) -> dict[str, ContentTemplate]:
        """Load content templates"""
        # In production, load from database or file
        templates = {
            "math_explanation": ContentTemplate(
                template_id="math_exp_001",
                content_type=ContentType.EXPLANATION,
                difficulty_range=(1, 5),
                learning_styles=[ls for ls in LearningStyle],
                structure={
                    "introduction": "{concept} konusunu öğrenelim",
                    "definition": "{concept} şu anlama gelir: {definition}",
                    "steps": ["Adım 1: {step1}", "Adım 2: {step2}"],
                    "example": "Örnek: {example}",
                    "practice": "Şimdi siz deneyin: {practice}",
                },
                variables=[
                    "concept",
                    "definition",
                    "step1",
                    "step2",
                    "example",
                    "practice",
                ],
                examples=[],
            ),
            "science_experiment": ContentTemplate(
                template_id="sci_exp_001",
                content_type=ContentType.INTERACTIVE,
                difficulty_range=(2, 4),
                learning_styles=[LearningStyle.KINESTHETIC, LearningStyle.VISUAL],
                structure={
                    "title": "{experiment_name} Deneyi",
                    "materials": ["Malzeme: {material1}", "Malzeme: {material2}"],
                    "steps": ["Adım: {step}"],
                    "observation": "Ne gözlemlediniz?",
                    "conclusion": "Sonuç: {conclusion}",
                },
                variables=[
                    "experiment_name",
                    "material1",
                    "material2",
                    "step",
                    "conclusion",
                ],
                examples=[],
            ),
        }
        return templates

    async def generate_content(
        self,
        topic: str,
        content_type: ContentType,
        student_profile: dict,
        context: dict | None = None,
    ) -> PersonalizedContent:
        """Generate personalized content for student"""

        # Extract student characteristics
        learning_style = LearningStyle(student_profile.get("learning_style", "visual"))
        difficulty_str = student_profile.get("difficulty_level", "medium")
        difficulty = self._map_difficulty(difficulty_str)
        interests = student_profile.get("subjects_of_interest", [])

        # Generate base content
        base_content = await self._generate_base_content(topic, content_type, context)

        # Personalize content
        personalized = self.personalizer.adapt_content(
            base_content, learning_style, difficulty, interests
        )

        # Add media elements based on learning style
        media_elements = self._generate_media_elements(learning_style, topic)

        # Add interactive elements
        interactive_elements = self._generate_interactive_elements(
            content_type, difficulty, topic
        )

        # Create content ID
        content_id = self._generate_content_id(
            student_profile.get("student_id"), topic, content_type
        )

        # Create personalized content object
        content = PersonalizedContent(
            content_id=content_id,
            student_id=student_profile.get("student_id"),
            content_type=content_type,
            difficulty_level=difficulty,
            title=self._generate_title(topic, content_type),
            body=personalized,
            media_elements=media_elements,
            interactive_elements=interactive_elements,
            assessments=self._generate_assessments(topic, difficulty),
            metadata={
                "topic": topic,
                "learning_style": learning_style.value,
                "context": context,
                "word_count": len(personalized.split()),
            },
        )

        # Cache content
        self.content_cache[content_id] = content
        self.generation_history.append(content_id)

        # Keep only last 100 items in cache
        if len(self.content_cache) > 100:
            oldest = self.generation_history.pop(0)
            del self.content_cache[oldest]

        return content

    async def _generate_base_content(
        self, topic: str, content_type: ContentType, context: dict | None
    ) -> str:
        """Generate base content before personalization"""

        # In production, this would call LLM or retrieve from database
        base_contents = {
            ContentType.EXPLANATION: f"""
            {topic} Konusu Açıklaması
            
            {topic}, matematik ve bilimde önemli bir konudur.
            Bu konuyu öğrenmek için temel kavramları anlamamız gerekir.
            
            Temel Kavramlar:
            1. Tanım ve özellikler
            2. Kullanım alanları
            3. Örnek problemler
            
            Detaylı açıklama:
            {topic} konusu, günlük hayatta sıkça karşılaştığımız durumları anlamamıza yardımcı olur.
            Örneğin, alışveriş yaparken, yemek pişirirken veya oyun oynarken bu bilgileri kullanırız.
            """,
            ContentType.EXAMPLE: f"""
            {topic} Örnek Problem
            
            Soru: {topic} ile ilgili bir problem çözelim.
            
            Problem: Bir öğrenci {topic} konusunu öğreniyor.
            
            Çözüm Adımları:
            1. Problemi anlayalım
            2. Verileri belirleyelim
            3. Formülü uygulayalım
            4. Sonucu kontrol edelim
            
            Cevap: Problem başarıyla çözüldü!
            """,
            ContentType.QUIZ: f"""
            {topic} Mini Quiz
            
            Soru 1: {topic} nedir?
            Soru 2: {topic} nerelerde kullanılır?
            Soru 3: {topic} ile ilgili örnek verin.
            """,
            ContentType.SUMMARY: f"""
            {topic} Özet
            
            Ana Noktalar:
            • {topic} temel bir konudur
            • Günlük hayatta kullanılır
            • Pratik yaparak öğrenilir
            
            Önemli: Düzenli tekrar yapın!
            """,
        }

        return base_contents.get(content_type, f"{topic} hakkında içerik")

    def _map_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """Map string difficulty to enum"""
        mapping = {
            "beginner": DifficultyLevel.BEGINNER,
            "easy": DifficultyLevel.ELEMENTARY,
            "medium": DifficultyLevel.INTERMEDIATE,
            "hard": DifficultyLevel.ADVANCED,
            "expert": DifficultyLevel.EXPERT,
        }
        return mapping.get(difficulty_str, DifficultyLevel.INTERMEDIATE)

    def _generate_media_elements(
        self, learning_style: LearningStyle, topic: str
    ) -> list[dict]:
        """Generate media elements based on learning style"""
        media = []

        if learning_style == LearningStyle.VISUAL:
            media.extend(
                [
                    {
                        "type": "diagram",
                        "description": f"{topic} concept map",
                        "url": f"/media/diagrams/{topic.lower()}_map.png",
                    },
                    {
                        "type": "infographic",
                        "description": f"{topic} infographic",
                        "url": f"/media/infographics/{topic.lower()}.png",
                    },
                ]
            )

        elif learning_style == LearningStyle.AUDITORY:
            media.extend(
                [
                    {
                        "type": "audio",
                        "description": f"{topic} explanation audio",
                        "url": f"/media/audio/{topic.lower()}_explain.mp3",
                    },
                    {
                        "type": "podcast",
                        "description": f"{topic} discussion",
                        "url": f"/media/podcasts/{topic.lower()}.mp3",
                    },
                ]
            )

        elif learning_style == LearningStyle.KINESTHETIC:
            media.extend(
                [
                    {
                        "type": "simulation",
                        "description": f"{topic} interactive simulation",
                        "url": f"/simulations/{topic.lower()}",
                    },
                    {
                        "type": "video",
                        "description": f"{topic} hands-on activity",
                        "url": f"/media/videos/{topic.lower()}_activity.mp4",
                    },
                ]
            )

        return media

    def _generate_interactive_elements(
        self, content_type: ContentType, difficulty: DifficultyLevel, topic: str
    ) -> list[dict]:
        """Generate interactive elements"""
        elements = []

        if content_type in [ContentType.PRACTICE, ContentType.INTERACTIVE]:
            elements.append(
                {
                    "type": "drag_drop",
                    "description": "Match concepts with definitions",
                    "difficulty": difficulty.value,
                    "topic": topic,
                }
            )

            elements.append(
                {
                    "type": "fill_blank",
                    "description": "Complete the sentences",
                    "difficulty": difficulty.value,
                    "topic": topic,
                }
            )

        if difficulty.value >= 3:  # Intermediate and above
            elements.append(
                {
                    "type": "problem_solver",
                    "description": "Step-by-step problem solving",
                    "difficulty": difficulty.value,
                    "topic": topic,
                }
            )

        return elements

    def _generate_assessments(
        self, topic: str, difficulty: DifficultyLevel
    ) -> list[dict]:
        """Generate assessment questions"""
        assessments = []

        # Number of questions based on difficulty
        num_questions = 5 - difficulty.value + 1  # Easier = more questions

        question_types = ["multiple_choice", "true_false", "short_answer"]

        for i in range(num_questions):
            assessments.append(
                {
                    "question_id": f"q_{i+1}",
                    "type": random.choice(question_types),
                    "question": f"{topic} Question {i+1}",
                    "difficulty": difficulty.value,
                    "points": difficulty.value * 2,
                }
            )

        return assessments

    def _generate_title(self, topic: str, content_type: ContentType) -> str:
        """Generate content title"""
        titles = {
            ContentType.EXPLANATION: f"{topic} - Detaylı Açıklama",
            ContentType.EXAMPLE: f"{topic} - Örnekler",
            ContentType.QUIZ: f"{topic} - Quiz",
            ContentType.SUMMARY: f"{topic} - Özet",
            ContentType.PRACTICE: f"{topic} - Pratik",
            ContentType.FLASHCARD: f"{topic} - Bilgi Kartları",
            ContentType.VIDEO_SCRIPT: f"{topic} - Video İçeriği",
            ContentType.INTERACTIVE: f"{topic} - İnteraktif Öğrenme",
        }
        return titles.get(content_type, f"{topic} - İçerik")

    def _generate_content_id(
        self, student_id: str, topic: str, content_type: ContentType
    ) -> str:
        """Generate unique content ID"""
        timestamp = datetime.now().isoformat()
        data = f"{student_id}:{topic}:{content_type.value}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    async def update_content_effectiveness(
        self, content_id: str, metrics: dict[str, Any]
    ):
        """Update content effectiveness metrics for improvement"""
        if content_id in self.content_cache:
            content = self.content_cache[content_id]
            if "effectiveness" not in content.metadata:
                content.metadata["effectiveness"] = {}

            content.metadata["effectiveness"].update(metrics)

            # Use metrics to improve future generation
            self._learn_from_metrics(content, metrics)

    def _learn_from_metrics(
        self, content: PersonalizedContent, metrics: dict[str, Any]
    ):
        """Learn from content effectiveness metrics"""
        engagement_score = metrics.get("engagement", 0)
        completion_rate = metrics.get("completion_rate", 0)
        quiz_score = metrics.get("quiz_score", 0)

        # Simple learning: adjust difficulty if needed
        if quiz_score < 0.5 and content.difficulty_level.value > 1:
            # Content too hard, note for future
            logger.info(f"Content {content.content_id} may be too difficult")
        elif quiz_score > 0.9 and content.difficulty_level.value < 5:
            # Content too easy, note for future
            logger.info(f"Content {content.content_id} may be too easy")

        # Store learning data for future improvements
        # In production, this would update ML models


# Singleton instance
_content_generator = None


def get_content_generator() -> DynamicContentGenerator:
    """Get or create singleton content generator"""
    global _content_generator

    if _content_generator is None:
        _content_generator = DynamicContentGenerator()

    return _content_generator
