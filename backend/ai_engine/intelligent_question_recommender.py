"""
Intelligent Question Recommendation System
AI-powered question recommendations based on student performance and learning patterns
"""

import asyncio
import logging
import math
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import json

from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Question difficulty levels"""

    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class QuestionType(Enum):
    """Question types"""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    ESSAY = "essay"
    CALCULATION = "calculation"
    INTERPRETATION = "interpretation"


class LearningObjective(Enum):
    """Learning objectives for recommendations"""

    KNOWLEDGE_ACQUISITION = "knowledge"
    SKILL_PRACTICE = "practice"
    CONCEPT_REINFORCEMENT = "reinforcement"
    WEAKNESS_IMPROVEMENT = "weakness"
    ADVANCED_CHALLENGE = "challenge"
    EXAM_PREPARATION = "exam_prep"


@dataclass
class StudentProfile:
    """Comprehensive student profile for personalization"""

    student_id: str
    grade_level: int
    subjects: List[str]

    # Performance metrics
    overall_performance: float  # 0-1
    subject_performances: Dict[str, float]
    topic_performances: Dict[str, float]
    difficulty_preferences: Dict[DifficultyLevel, float]

    # Learning patterns
    learning_style: str  # visual, auditory, kinesthetic, mixed
    study_time_patterns: Dict[str, float]  # hour of day -> efficiency
    optimal_session_length: int  # minutes
    attention_span: float  # 0-1

    # Cognitive metrics
    processing_speed: float  # 0-1
    working_memory_capacity: float  # 0-1
    metacognitive_awareness: float  # 0-1
    motivation_level: float  # 0-1

    # Recent activity
    recent_topics: List[str]
    recent_difficulties: List[DifficultyLevel]
    recent_performance_trend: float  # -1 to 1 (declining to improving)
    last_activity: datetime

    # Weaknesses and strengths
    weak_areas: List[str]
    strong_areas: List[str]
    learning_gaps: List[str]

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionMetadata:
    """Rich question metadata for intelligent recommendations"""

    question_id: str
    subject: str
    topic: str
    subtopic: Optional[str]

    # Content characteristics
    difficulty_level: DifficultyLevel
    question_type: QuestionType
    cognitive_load: float  # 0-1
    time_estimate: int  # seconds

    # Educational attributes
    bloom_taxonomy_level: str  # remember, understand, apply, analyze, evaluate, create
    prerequisite_topics: List[str]
    learning_objectives: List[LearningObjective]
    concepts_tested: List[str]

    # Statistical data
    average_performance: float  # 0-1
    completion_rate: float  # 0-1
    discrimination_index: float  # -1 to 1
    item_response_theory_params: Dict[str, float]  # a, b, c parameters

    # Engagement metrics
    student_ratings: float  # 0-5
    teacher_ratings: float  # 0-5
    engagement_score: float  # 0-1

    # Adaptive features
    adaptive_difficulty: float  # 0-1 (dynamically adjusted)
    success_rate_by_ability: Dict[str, float]  # ability_level -> success_rate

    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationContext:
    """Context for generating recommendations"""

    learning_objective: LearningObjective
    target_subject: Optional[str] = None
    target_topic: Optional[str] = None
    session_duration: Optional[int] = None  # minutes
    max_questions: int = 10
    difficulty_range: Tuple[DifficultyLevel, DifficultyLevel] = (
        DifficultyLevel.EASY,
        DifficultyLevel.HARD,
    )
    exclude_recent: bool = True
    focus_weaknesses: bool = True
    challenge_level: float = 0.7  # 0-1 (0=easy, 1=challenging)


@dataclass
class QuestionRecommendation:
    """Individual question recommendation with reasoning"""

    question_id: str
    question_metadata: QuestionMetadata
    recommendation_score: float  # 0-1
    confidence: float  # 0-1

    # Reasoning
    primary_reason: str
    reasoning_factors: Dict[str, float]
    expected_performance: float  # 0-1
    learning_value: float  # 0-1

    # Personalization
    difficulty_match: float  # 0-1
    interest_match: float  # 0-1
    timing_appropriateness: float  # 0-1

    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligentQuestionRecommender:
    """AI-powered question recommendation engine"""

    def __init__(self):
        self.ready = False
        self.models = {}
        self.scalers = {}
        self.student_profiles = {}
        self.question_database = {}
        self.interaction_history = []

        # ML models for different aspects
        self.performance_predictor = None
        self.difficulty_classifier = None
        self.engagement_predictor = None
        self.clustering_model = None

        # Feature extractors
        self.feature_extractors = {}

    async def initialize(self):
        """Initialize the recommendation system"""
        if self.ready:
            return

        logger.info("Initializing Intelligent Question Recommender...")

        try:
            # Initialize ML models
            await self._initialize_ml_models()

            # Load student profiles and question database
            await self._load_student_data()
            await self._load_question_database()

            # Initialize feature extractors
            await self._initialize_feature_extractors()

            self.ready = True
            logger.info("Intelligent Question Recommender initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize recommender: {e}")
            raise

    async def _initialize_ml_models(self):
        """Initialize machine learning models"""
        # Performance prediction model
        self.performance_predictor = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )

        # Difficulty classification model
        self.difficulty_classifier = GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, random_state=42
        )

        # Engagement prediction model
        self.engagement_predictor = RandomForestRegressor(
            n_estimators=50, max_depth=8, random_state=42
        )

        # Student clustering model
        self.clustering_model = KMeans(n_clusters=8, random_state=42)

        # Scalers for feature normalization
        self.scalers["performance"] = StandardScaler()
        self.scalers["difficulty"] = StandardScaler()
        self.scalers["engagement"] = StandardScaler()

    async def _load_student_data(self):
        """Load and process student data"""
        # This would typically load from database
        # For now, we'll create sample data
        sample_students = await self._generate_sample_student_profiles()

        for profile in sample_students:
            self.student_profiles[profile.student_id] = profile

    async def _load_question_database(self):
        """Load question database with metadata"""
        # This would typically load from database
        # For now, we'll create sample questions
        sample_questions = await self._generate_sample_questions()

        for question in sample_questions:
            self.question_database[question.question_id] = question

    async def _initialize_feature_extractors(self):
        """Initialize feature extraction functions"""
        self.feature_extractors = {
            "student_performance": self._extract_performance_features,
            "question_content": self._extract_content_features,
            "temporal": self._extract_temporal_features,
            "interaction": self._extract_interaction_features,
        }

    async def recommend_questions(
        self, student_id: str, context: RecommendationContext
    ) -> List[QuestionRecommendation]:
        """Generate intelligent question recommendations"""

        if not self.ready:
            await self.initialize()

        if student_id not in self.student_profiles:
            raise ValueError(f"Student profile not found: {student_id}")

        student_profile = self.student_profiles[student_id]

        logger.info(f"Generating recommendations for student {student_id}")

        # Step 1: Filter candidate questions
        candidate_questions = await self._filter_candidate_questions(
            student_profile, context
        )

        # Step 2: Extract features for each candidate
        candidate_features = await self._extract_candidate_features(
            student_profile, candidate_questions, context
        )

        # Step 3: Score each candidate question
        scored_candidates = await self._score_candidates(
            student_profile, candidate_features, context
        )

        # Step 4: Apply diversity and sequencing
        final_recommendations = await self._optimize_recommendation_sequence(
            scored_candidates, context
        )

        # Step 5: Generate explanations and reasoning
        enriched_recommendations = await self._enrich_recommendations(
            final_recommendations, student_profile, context
        )

        logger.info(f"Generated {len(enriched_recommendations)} recommendations")

        return enriched_recommendations[: context.max_questions]

    async def _filter_candidate_questions(
        self, student_profile: StudentProfile, context: RecommendationContext
    ) -> List[QuestionMetadata]:
        """Filter questions based on basic criteria"""

        candidates = []

        for question in self.question_database.values():
            # Subject filter
            if context.target_subject and question.subject != context.target_subject:
                continue

            # Topic filter
            if context.target_topic and question.topic != context.target_topic:
                continue

            # Difficulty range filter
            if not (
                context.difficulty_range[0].value
                <= question.difficulty_level.value
                <= context.difficulty_range[1].value
            ):
                continue

            # Exclude recent questions
            if context.exclude_recent and self._is_recent_question(
                student_profile, question.question_id
            ):
                continue

            # Check prerequisites
            if not self._meets_prerequisites(student_profile, question):
                continue

            candidates.append(question)

        return candidates

    async def _extract_candidate_features(
        self,
        student_profile: StudentProfile,
        candidates: List[QuestionMetadata],
        context: RecommendationContext,
    ) -> Dict[str, np.ndarray]:
        """Extract features for candidate questions"""

        features = {
            "performance_features": [],
            "content_features": [],
            "temporal_features": [],
            "interaction_features": [],
        }

        for question in candidates:
            # Performance-related features
            perf_features = await self.feature_extractors["student_performance"](
                student_profile, question
            )
            features["performance_features"].append(perf_features)

            # Content-related features
            content_features = await self.feature_extractors["question_content"](
                question, context
            )
            features["content_features"].append(content_features)

            # Temporal features
            temporal_features = await self.feature_extractors["temporal"](
                student_profile, question
            )
            features["temporal_features"].append(temporal_features)

            # Interaction features
            interaction_features = await self.feature_extractors["interaction"](
                student_profile, question
            )
            features["interaction_features"].append(interaction_features)

        # Convert to numpy arrays
        for key in features:
            features[key] = np.array(features[key])

        return features

    async def _extract_performance_features(
        self, student_profile: StudentProfile, question: QuestionMetadata
    ) -> List[float]:
        """Extract performance-related features"""

        features = []

        # Subject performance
        subject_perf = student_profile.subject_performances.get(question.subject, 0.5)
        features.append(subject_perf)

        # Topic performance
        topic_perf = student_profile.topic_performances.get(question.topic, 0.5)
        features.append(topic_perf)

        # Difficulty preference
        difficulty_pref = student_profile.difficulty_preferences.get(
            question.difficulty_level, 0.5
        )
        features.append(difficulty_pref)

        # Performance trend
        features.append(student_profile.recent_performance_trend)

        # Cognitive metrics
        features.extend(
            [
                student_profile.processing_speed,
                student_profile.working_memory_capacity,
                student_profile.metacognitive_awareness,
                student_profile.motivation_level,
            ]
        )

        # Weakness/strength alignment
        is_weak_area = 1.0 if question.topic in student_profile.weak_areas else 0.0
        is_strong_area = 1.0 if question.topic in student_profile.strong_areas else 0.0
        features.extend([is_weak_area, is_strong_area])

        return features

    async def _extract_content_features(
        self, question: QuestionMetadata, context: RecommendationContext
    ) -> List[float]:
        """Extract content-related features"""

        features = []

        # Basic question properties
        features.append(question.difficulty_level.value / 5.0)
        features.append(question.cognitive_load)
        features.append(question.time_estimate / 3600.0)  # Normalize to hours

        # Quality metrics
        features.extend(
            [
                question.average_performance,
                question.completion_rate,
                question.discrimination_index,
                question.student_ratings / 5.0,
                question.teacher_ratings / 5.0,
                question.engagement_score,
            ]
        )

        # IRT parameters
        irt_params = question.item_response_theory_params
        features.extend(
            [
                irt_params.get("a", 1.0),  # discrimination
                irt_params.get("b", 0.0),  # difficulty
                irt_params.get("c", 0.0),  # guessing
            ]
        )

        # Question type encoding
        question_types = list(QuestionType)
        type_encoding = [
            1.0 if question.question_type == qt else 0.0 for qt in question_types
        ]
        features.extend(type_encoding)

        # Learning objective alignment
        objective_alignment = (
            1.0 if context.learning_objective in question.learning_objectives else 0.0
        )
        features.append(objective_alignment)

        return features

    async def _extract_temporal_features(
        self, student_profile: StudentProfile, question: QuestionMetadata
    ) -> List[float]:
        """Extract temporal features"""

        features = []

        # Time since last activity
        time_since_activity = (
            datetime.now() - student_profile.last_activity
        ).total_seconds() / 3600.0
        features.append(min(time_since_activity, 24.0) / 24.0)  # Normalize to days

        # Current hour efficiency
        current_hour = datetime.now().hour
        hour_efficiency = student_profile.study_time_patterns.get(
            str(current_hour), 0.5
        )
        features.append(hour_efficiency)

        # Session timing
        optimal_length = (
            student_profile.optimal_session_length / 60.0
        )  # Convert to hours
        features.append(optimal_length)

        # Attention span
        features.append(student_profile.attention_span)

        return features

    async def _extract_interaction_features(
        self, student_profile: StudentProfile, question: QuestionMetadata
    ) -> List[float]:
        """Extract interaction history features"""

        features = []

        # Recent interaction patterns
        recent_difficulties = [
            d.value for d in student_profile.recent_difficulties[-5:]
        ]
        if recent_difficulties:
            avg_recent_difficulty = np.mean(recent_difficulties) / 5.0
            difficulty_variance = np.var(recent_difficulties) / 25.0
        else:
            avg_recent_difficulty = 0.5
            difficulty_variance = 0.0

        features.extend([avg_recent_difficulty, difficulty_variance])

        # Topic familiarity
        topic_recent_count = student_profile.recent_topics.count(question.topic)
        topic_familiarity = min(topic_recent_count / 10.0, 1.0)
        features.append(topic_familiarity)

        return features

    async def _score_candidates(
        self,
        student_profile: StudentProfile,
        features: Dict[str, np.ndarray],
        context: RecommendationContext,
    ) -> List[Tuple[QuestionMetadata, float, Dict[str, float]]]:
        """Score candidate questions using ML models"""

        scored_candidates = []
        candidates = list(self.question_database.values())

        for i, question in enumerate(
            candidates[: len(features["performance_features"])]
        ):
            # Combine all features
            all_features = np.concatenate(
                [
                    features["performance_features"][i],
                    features["content_features"][i],
                    features["temporal_features"][i],
                    features["interaction_features"][i],
                ]
            )

            # Calculate component scores
            scores = {}

            # Performance prediction score
            scores["performance"] = await self._predict_performance(all_features)

            # Engagement score
            scores["engagement"] = await self._predict_engagement(all_features)

            # Learning value score
            scores["learning_value"] = await self._calculate_learning_value(
                student_profile, question, context
            )

            # Difficulty appropriateness
            scores["difficulty_match"] = await self._calculate_difficulty_match(
                student_profile, question, context
            )

            # Interest alignment
            scores["interest"] = await self._calculate_interest_alignment(
                student_profile, question
            )

            # Combine scores with weights
            weights = {
                "performance": 0.25,
                "engagement": 0.20,
                "learning_value": 0.25,
                "difficulty_match": 0.20,
                "interest": 0.10,
            }

            total_score = sum(scores[key] * weights[key] for key in scores)

            scored_candidates.append((question, total_score, scores))

        # Sort by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return scored_candidates

    async def _predict_performance(self, features: np.ndarray) -> float:
        """Predict student performance on question"""
        if self.performance_predictor is None:
            return 0.7  # Default prediction

        try:
            # This would use a trained model
            # For now, return a simulated prediction
            return min(max(np.random.normal(0.7, 0.15), 0.0), 1.0)
        except Exception:
            return 0.7

    async def _predict_engagement(self, features: np.ndarray) -> float:
        """Predict student engagement with question"""
        if self.engagement_predictor is None:
            return 0.7  # Default prediction

        try:
            # This would use a trained model
            # For now, return a simulated prediction
            return min(max(np.random.normal(0.7, 0.1), 0.0), 1.0)
        except Exception:
            return 0.7

    async def _calculate_learning_value(
        self,
        student_profile: StudentProfile,
        question: QuestionMetadata,
        context: RecommendationContext,
    ) -> float:
        """Calculate learning value of question for student"""

        value = 0.0

        # Weakness targeting
        if context.focus_weaknesses and question.topic in student_profile.weak_areas:
            value += 0.3

        # Concept coverage
        gap_coverage = len(
            set(question.concepts_tested) & set(student_profile.learning_gaps)
        )
        value += gap_coverage * 0.1

        # Bloom's taxonomy alignment
        bloom_levels = [
            "remember",
            "understand",
            "apply",
            "analyze",
            "evaluate",
            "create",
        ]
        if question.bloom_taxonomy_level in bloom_levels:
            level_index = bloom_levels.index(question.bloom_taxonomy_level)
            # Higher-order thinking skills are more valuable
            value += (level_index / len(bloom_levels)) * 0.2

        # Objective alignment
        if context.learning_objective in question.learning_objectives:
            value += 0.2

        # Quality metrics
        value += question.discrimination_index * 0.1
        value += question.engagement_score * 0.1

        return min(value, 1.0)

    async def _calculate_difficulty_match(
        self,
        student_profile: StudentProfile,
        question: QuestionMetadata,
        context: RecommendationContext,
    ) -> float:
        """Calculate how well question difficulty matches student ability"""

        # Get student ability in subject/topic
        subject_ability = student_profile.subject_performances.get(
            question.subject, 0.5
        )
        topic_ability = student_profile.topic_performances.get(question.topic, 0.5)
        overall_ability = (subject_ability + topic_ability) / 2

        # Adjust for context challenge level
        target_difficulty = overall_ability + (context.challenge_level - 0.5) * 0.4
        target_difficulty = max(0.1, min(0.9, target_difficulty))

        # Calculate match score
        question_difficulty = question.difficulty_level.value / 5.0
        difficulty_diff = abs(target_difficulty - question_difficulty)

        # Convert to similarity score
        match_score = 1.0 - (
            difficulty_diff / 0.5
        )  # Normalize by max possible difference

        return max(0.0, match_score)

    async def _calculate_interest_alignment(
        self, student_profile: StudentProfile, question: QuestionMetadata
    ) -> float:
        """Calculate interest alignment score"""

        interest = 0.5  # Base interest

        # Strong areas are more interesting
        if question.topic in student_profile.strong_areas:
            interest += 0.2

        # Recent topics might be less interesting (variety preference)
        recent_topic_count = student_profile.recent_topics.count(question.topic)
        if recent_topic_count > 3:
            interest -= 0.1 * (recent_topic_count - 3)

        # High-rated questions are more interesting
        interest += (question.student_ratings / 5.0) * 0.2

        return max(0.0, min(1.0, interest))

    async def _optimize_recommendation_sequence(
        self,
        scored_candidates: List[Tuple[QuestionMetadata, float, Dict[str, float]]],
        context: RecommendationContext,
    ) -> List[Tuple[QuestionMetadata, float, Dict[str, float]]]:
        """Optimize the sequence of recommendations for diversity and flow"""

        if len(scored_candidates) <= context.max_questions:
            return scored_candidates

        # Select top candidates with diversity
        selected = []
        used_topics = set()
        used_difficulties = set()

        for question, score, component_scores in scored_candidates:
            # Diversity check
            topic_diversity = question.topic not in used_topics
            difficulty_diversity = question.difficulty_level not in used_difficulties

            # Accept if high score or adds diversity
            if (
                len(selected) < context.max_questions // 2
                or topic_diversity  # Take top half regardless
                or difficulty_diversity
            ):
                selected.append((question, score, component_scores))
                used_topics.add(question.topic)
                used_difficulties.add(question.difficulty_level)

                if len(selected) >= context.max_questions:
                    break

        return selected

    async def _enrich_recommendations(
        self,
        recommendations: List[Tuple[QuestionMetadata, float, Dict[str, float]]],
        student_profile: StudentProfile,
        context: RecommendationContext,
    ) -> List[QuestionRecommendation]:
        """Enrich recommendations with explanations and reasoning"""

        enriched = []

        for i, (question, score, component_scores) in enumerate(recommendations):
            # Generate primary reason
            primary_reason = await self._generate_primary_reason(
                question, component_scores, context
            )

            # Calculate additional metrics
            expected_performance = component_scores.get("performance", 0.7)
            learning_value = component_scores.get("learning_value", 0.5)
            difficulty_match = component_scores.get("difficulty_match", 0.5)
            interest_match = component_scores.get("interest", 0.5)

            # Calculate confidence based on score distribution
            confidence = min(score, 0.95)  # Cap confidence at 95%

            # Timing appropriateness
            timing = await self._calculate_timing_appropriateness(
                student_profile, question, i
            )

            recommendation = QuestionRecommendation(
                question_id=question.question_id,
                question_metadata=question,
                recommendation_score=score,
                confidence=confidence,
                primary_reason=primary_reason,
                reasoning_factors=component_scores,
                expected_performance=expected_performance,
                learning_value=learning_value,
                difficulty_match=difficulty_match,
                interest_match=interest_match,
                timing_appropriateness=timing,
            )

            enriched.append(recommendation)

        return enriched

    async def _generate_primary_reason(
        self,
        question: QuestionMetadata,
        component_scores: Dict[str, float],
        context: RecommendationContext,
    ) -> str:
        """Generate primary reason for recommendation"""

        # Find the highest scoring component
        max_component = max(component_scores.items(), key=lambda x: x[1])
        component_name, score = max_component

        reasons = {
            "performance": f"Bu soru seviyenize uygun ve başarı şansınız yüksek",
            "engagement": f"Bu tür sorularla daha çok ilgileniyor ve odaklanıyorsunuz",
            "learning_value": f"Bu soru zayıf olduğunuz alanları güçlendirmeye yardımcı olacak",
            "difficulty_match": f"Zorluk seviyesi şu anda optimal öğrenme alanınızda",
            "interest": f"İlgi alanınıza uygun ve motivasyonunuzu artıracak",
        }

        return reasons.get(component_name, "Genel performansınıza uygun bir soru")

    async def _calculate_timing_appropriateness(
        self, student_profile: StudentProfile, question: QuestionMetadata, position: int
    ) -> float:
        """Calculate timing appropriateness"""

        # Start with base appropriateness
        appropriateness = 0.7

        # Consider time of day
        current_hour = datetime.now().hour
        hour_efficiency = student_profile.study_time_patterns.get(
            str(current_hour), 0.5
        )
        appropriateness += (hour_efficiency - 0.5) * 0.3

        # Consider question position in sequence
        if position == 0:  # First question should be engaging
            appropriateness += question.engagement_score * 0.2
        elif position < 3:  # Early questions should build confidence
            if question.difficulty_level.value <= 3:
                appropriateness += 0.1

        # Consider estimated time
        if question.time_estimate <= student_profile.optimal_session_length * 60:
            appropriateness += 0.1

        return max(0.0, min(1.0, appropriateness))

    def _is_recent_question(
        self, student_profile: StudentProfile, question_id: str
    ) -> bool:
        """Check if question was recently attempted"""
        # Simple implementation - would check interaction history
        return False

    def _meets_prerequisites(
        self, student_profile: StudentProfile, question: QuestionMetadata
    ) -> bool:
        """Check if student meets question prerequisites"""
        # Check if student has covered prerequisite topics
        for prereq in question.prerequisite_topics:
            if prereq not in student_profile.topic_performances:
                return False
            if student_profile.topic_performances[prereq] < 0.6:  # Minimum proficiency
                return False
        return True

    async def _generate_sample_student_profiles(self) -> List[StudentProfile]:
        """Generate sample student profiles for testing"""
        profiles = []

        for i in range(5):
            profile = StudentProfile(
                student_id=f"student_{i+1}",
                grade_level=10 + (i % 3),
                subjects=["matematik", "fizik", "kimya"],
                overall_performance=0.6 + (i * 0.1),
                subject_performances={
                    "matematik": 0.5 + (i * 0.1),
                    "fizik": 0.6 + (i * 0.05),
                    "kimya": 0.7 - (i * 0.05),
                },
                topic_performances={
                    "cebir": 0.6 + (i * 0.1),
                    "geometri": 0.5 + (i * 0.05),
                    "analiz": 0.7 - (i * 0.1),
                },
                difficulty_preferences={
                    DifficultyLevel.EASY: 0.8 - (i * 0.1),
                    DifficultyLevel.MEDIUM: 0.6 + (i * 0.05),
                    DifficultyLevel.HARD: 0.4 + (i * 0.1),
                },
                learning_style=["visual", "auditory", "kinesthetic"][i % 3],
                study_time_patterns={
                    str(h): 0.5 + 0.3 * math.sin(h * math.pi / 12) for h in range(24)
                },
                optimal_session_length=30 + (i * 10),
                attention_span=0.6 + (i * 0.08),
                processing_speed=0.5 + (i * 0.1),
                working_memory_capacity=0.6 + (i * 0.05),
                metacognitive_awareness=0.4 + (i * 0.15),
                motivation_level=0.7 - (i * 0.05),
                recent_topics=["cebir", "geometri"],
                recent_difficulties=[DifficultyLevel.MEDIUM, DifficultyLevel.EASY],
                recent_performance_trend=0.1 * (i - 2),
                last_activity=datetime.now() - timedelta(hours=i),
                weak_areas=["analiz"] if i % 2 == 0 else ["geometri"],
                strong_areas=["cebir"] if i % 2 == 0 else ["analiz"],
                learning_gaps=["ileri_matematik"] if i > 2 else [],
            )
            profiles.append(profile)

        return profiles

    async def _generate_sample_questions(self) -> List[QuestionMetadata]:
        """Generate sample questions for testing"""
        questions = []
        subjects = ["matematik", "fizik", "kimya"]
        topics = [
            "cebir",
            "geometri",
            "analiz",
            "mekanik",
            "termodinamik",
            "atomik_yapı",
        ]

        for i in range(20):
            question = QuestionMetadata(
                question_id=f"q_{i+1}",
                subject=subjects[i % len(subjects)],
                topic=topics[i % len(topics)],
                subtopic=f"alt_konu_{i % 3}",
                difficulty_level=list(DifficultyLevel)[i % 5],
                question_type=list(QuestionType)[i % len(QuestionType)],
                cognitive_load=0.3 + (i % 5) * 0.15,
                time_estimate=60 + (i % 10) * 30,
                bloom_taxonomy_level=["remember", "understand", "apply", "analyze"][
                    i % 4
                ],
                prerequisite_topics=[topics[(i - 1) % len(topics)]] if i > 0 else [],
                learning_objectives=[
                    list(LearningObjective)[i % len(LearningObjective)]
                ],
                concepts_tested=[f"kavram_{i % 5}"],
                average_performance=0.4 + (i % 6) * 0.1,
                completion_rate=0.7 + (i % 4) * 0.075,
                discrimination_index=-0.2 + (i % 6) * 0.2,
                item_response_theory_params={
                    "a": 0.5 + (i % 4) * 0.375,
                    "b": -2 + (i % 5) * 1.0,
                    "c": 0.1 + (i % 3) * 0.1,
                },
                student_ratings=2 + (i % 4),
                teacher_ratings=3 + (i % 3),
                engagement_score=0.4 + (i % 6) * 0.1,
                adaptive_difficulty=0.3 + (i % 5) * 0.15,
                success_rate_by_ability={
                    "low": 0.3 + (i % 3) * 0.1,
                    "medium": 0.6 + (i % 3) * 0.1,
                    "high": 0.8 + (i % 2) * 0.1,
                },
                tags=[f"tag_{i % 3}"],
            )
            questions.append(question)

        return questions


# Global instance
intelligent_recommender = IntelligentQuestionRecommender()


async def get_question_recommender() -> IntelligentQuestionRecommender:
    """Get initialized question recommender"""
    if not intelligent_recommender.ready:
        await intelligent_recommender.initialize()
    return intelligent_recommender
