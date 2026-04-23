"""
Batch Question Generator Service
Handles batch question generation configuration and coordination
"""

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class BatchQuestionGenerator:
    """
    Service for batch question generation configuration

    Features:
    - Balanced topic distribution
    - Difficulty diversity
    - Bloom taxonomy coverage
    - Quality targets
    """

    def __init__(self):
        # Default topics per subject
        self.topic_library = {
            'Matematik': {
                'TYT': ['Sayılar', 'Denklemler', 'Geometri', 'Fonksiyonlar', 'Olasılık'],
                'AYT': ['Türev', 'İntegral', 'Limit', 'Diziler', 'Trigonometri']
            },
            'Fizik': {
                'TYT': ['Kuvvet', 'Hareket', 'Enerji', 'Elektrik', 'Optik'],
                'AYT': ['Manyetizma', 'Dalga', 'Modern Fizik', 'Termodinamik']
            },
            'Kimya': {
                'TYT': ['Atom', 'Periyodik Tablo', 'Kimyasal Bağlar', 'Mol Kavramı'],
                'AYT': ['Kimyasal Denge', 'Asit-Baz', 'Elektrokimya', 'Organik Kimya']
            },
            'Biyoloji': {
                'TYT': ['Hücre', 'Canlıların Sınıflandırılması', 'Ekosistem'],
                'AYT': ['Genetik', 'Evrim', 'Sinir Sistemi', 'Dolaşım Sistemi']
            },
            'Türkçe': {
                'TYT': ['Anlatım', 'Paragraf', 'Sözcük', 'Cümle'],
                'AYT': ['Edebiyat Tarihi', 'Şiir', 'Roman', 'Nazım']
            }
        }

        # Bloom level distribution targets
        self.bloom_distribution = {
            1: 0.10,  # Hatırlama
            2: 0.20,  # Anlama
            3: 0.30,  # Uygulama
            4: 0.25,  # Analiz
            5: 0.10,  # Değerlendirme
            6: 0.05   # Yaratma
        }

    def create_batch_config(
        self,
        batch_size: int,
        exam_type: str,
        subject: str,
        topics: list[str] | None = None,
        difficulty_range: tuple[float, float] = (0.3, 0.7),
        bloom_levels: list[int] | None = None
    ) -> list[dict[str, Any]]:
        """
        Create batch generation configuration

        Args:
            batch_size: Number of questions (50-500)
            exam_type: TYT/AYT/YDT
            subject: Subject area
            topics: Specific topics (None = use all)
            difficulty_range: (min, max) difficulty
            bloom_levels: Specific Bloom levels (None = distributed)

        Returns:
            List of question configurations
        """
        if not 50 <= batch_size <= 500:
            raise ValueError("Batch size must be between 50 and 500")

        # Get topics
        if topics is None:
            topics = self._get_default_topics(subject, exam_type)

        # Get bloom levels
        if bloom_levels is None:
            bloom_levels = self._distribute_bloom_levels(batch_size)
        else:
            bloom_levels = bloom_levels * (batch_size // len(bloom_levels) + 1)
            bloom_levels = bloom_levels[:batch_size]

        # Generate configs
        configs = []
        topics_list = list(topics)

        for i in range(batch_size):
            # Select topic (round-robin)
            topic = topics_list[i % len(topics_list)]

            # Generate subtopic
            subtopic = self._generate_subtopic(topic, subject)

            # Select difficulty (distributed across range)
            difficulty = self._generate_difficulty(i, batch_size, difficulty_range)

            # Select bloom level
            bloom = bloom_levels[i]

            config = {
                'index': i,
                'topic': topic,
                'subtopic': subtopic,
                'exam_type': exam_type,
                'subject': subject,
                'difficulty': difficulty,
                'bloom_level': bloom
            }

            configs.append(config)

        logger.info(f"Created {batch_size} question configs for {subject}/{exam_type}")
        return configs

    def _get_default_topics(self, subject: str, exam_type: str) -> list[str]:
        """Get default topics for subject/exam_type"""
        if subject in self.topic_library:
            if exam_type in self.topic_library[subject]:
                return self.topic_library[subject][exam_type]
            # Fallback to TYT topics
            return self.topic_library[subject].get('TYT', ['Genel'])
        return ['Genel']

    def _generate_subtopic(self, topic: str, subject: str) -> str:
        """Generate a subtopic based on topic"""
        # Simplified - in production, this would use a comprehensive subtopic database
        subtopic_templates = {
            'Matematik': [
                f"{topic} - Temel Kavramlar",
                f"{topic} - Problemler",
                f"{topic} - Uygulamalar"
            ],
            'Fizik': [
                f"{topic} - Teori",
                f"{topic} - Problemler",
                f"{topic} - Deney"
            ]
        }

        templates = subtopic_templates.get(subject, [f"{topic} - Genel"])
        return random.choice(templates)

    def _distribute_bloom_levels(self, batch_size: int) -> list[int]:
        """Distribute Bloom levels according to target distribution"""
        bloom_levels = []

        for level, ratio in self.bloom_distribution.items():
            count = int(batch_size * ratio)
            bloom_levels.extend([level] * count)

        # Fill remaining with level 3 (Application)
        while len(bloom_levels) < batch_size:
            bloom_levels.append(3)

        # Shuffle to avoid sequential patterns
        random.shuffle(bloom_levels)

        return bloom_levels[:batch_size]

    def _generate_difficulty(
        self,
        index: int,
        total: int,
        difficulty_range: tuple[float, float]
    ) -> float:
        """Generate difficulty value with good distribution"""
        min_diff, max_diff = difficulty_range

        # Use normal distribution around midpoint
        midpoint = (min_diff + max_diff) / 2
        std_dev = (max_diff - min_diff) / 4

        # Generate value with some randomness
        difficulty = random.gauss(midpoint, std_dev)

        # Clamp to range
        difficulty = max(min_diff, min(max_diff, difficulty))

        return round(difficulty, 2)

    def validate_batch_quality(
        self,
        generated_questions: list[dict[str, Any]],
        min_quality_score: float = 0.7
    ) -> dict[str, Any]:
        """
        Validate quality of generated batch

        Args:
            generated_questions: List of generated questions
            min_quality_score: Minimum acceptable quality

        Returns:
            Validation results
        """
        if not generated_questions:
            return {
                'valid': False,
                'reason': 'No questions generated'
            }

        # Check quality scores
        quality_scores = [
            q.get('quality_score', 0)
            for q in generated_questions
            if 'quality_score' in q
        ]

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Check diversity
        topics = set(q.get('topic') for q in generated_questions if 'topic' in q)
        bloom_levels = set(q.get('bloom_level') for q in generated_questions if 'bloom_level' in q)

        return {
            'valid': avg_quality >= min_quality_score,
            'avg_quality': avg_quality,
            'topic_diversity': len(topics),
            'bloom_diversity': len(bloom_levels),
            'total_questions': len(generated_questions),
            'passed_quality_check': sum(1 for s in quality_scores if s >= min_quality_score),
            'recommendations': self._generate_recommendations(
                avg_quality, len(topics), len(bloom_levels)
            )
        }

    def _generate_recommendations(
        self,
        avg_quality: float,
        topic_count: int,
        bloom_count: int
    ) -> list[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if avg_quality < 0.7:
            recommendations.append("Increase quality threshold in generation")

        if topic_count < 3:
            recommendations.append("Increase topic diversity")

        if bloom_count < 4:
            recommendations.append("Include more Bloom taxonomy levels")

        return recommendations

    def estimate_generation_time(self, batch_size: int, method: str = 'ensemble') -> int:
        """
        Estimate batch generation time in seconds

        Args:
            batch_size: Number of questions
            method: Generation method

        Returns:
            Estimated time in seconds
        """
        # Time per question (seconds)
        time_per_question = {
            'ensemble': 8,  # 3 models averaged
            'openai': 3,
            'claude': 4,
            'qwen': 2
        }

        base_time = time_per_question.get(method, 5)

        # Parallel processing reduces time
        # Assume 10 workers
        parallel_factor = min(batch_size, 10)

        estimated_time = (batch_size * base_time) / parallel_factor

        return int(estimated_time)
