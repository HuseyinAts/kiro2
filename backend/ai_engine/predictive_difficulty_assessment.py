"""
Predictive Difficulty Assessment System
AI-powered system for predicting and adjusting content difficulty
"""

import asyncio
import logging
import math
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import json

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import scipy.stats as stats

logger = logging.getLogger(__name__)


class DifficultyScale(Enum):
    """Difficulty scale levels"""

    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class AssessmentType(Enum):
    """Types of difficulty assessment"""

    OBJECTIVE = "objektif"  # Based on content characteristics
    SUBJECTIVE = "sübjektif"  # Based on student performance
    PREDICTIVE = "öngörülü"  # Predicted for new content
    ADAPTIVE = "adaptif"  # Real-time adjustment


class ContentDomain(Enum):
    """Content domains for specialized assessment"""

    MATHEMATICS = "matematik"
    PHYSICS = "fizik"
    CHEMISTRY = "kimya"
    BIOLOGY = "biyoloji"
    LANGUAGE = "dil"
    HISTORY = "tarih"


@dataclass
class ContentFeatures:
    """Features used for difficulty assessment"""

    content_id: str
    domain: ContentDomain

    # Text-based features
    text_length: int  # Number of words
    sentence_count: int
    avg_sentence_length: float
    vocabulary_complexity: float  # 0-1
    readability_score: float  # 0-100

    # Concept-based features
    concept_count: int
    concept_depth: float  # How deep/abstract the concepts are
    prerequisite_count: int
    novel_concepts: int  # New concepts not seen before

    # Mathematical features (if applicable)
    formula_count: int = 0
    equation_complexity: float = 0  # 0-1
    calculation_steps: int = 0
    abstract_reasoning_required: float = 0  # 0-1

    # Visual/Media features
    diagram_count: int = 0
    visualization_complexity: float = 0  # 0-1
    interactive_elements: int = 0

    # Pedagogical features
    explanation_depth: float = 0  # 0-1
    example_count: int = 0
    practice_opportunities: int = 0
    scaffolding_level: float = 0  # 0-1

    # Historical data
    avg_completion_time: Optional[float] = None  # minutes
    success_rate: Optional[float] = None  # 0-1
    hint_usage_rate: Optional[float] = None  # 0-1

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentProfile:
    """Student profile for personalized difficulty assessment"""

    student_id: str

    # Academic performance
    overall_gpa: float  # 0-4 scale
    domain_performance: Dict[ContentDomain, float]  # 0-1 performance per domain
    recent_performance_trend: float  # -1 to 1 (declining to improving)

    # Cognitive abilities
    processing_speed: float  # 0-1
    working_memory: float  # 0-1
    abstract_reasoning: float  # 0-1
    attention_span: int  # minutes

    # Learning characteristics
    learning_speed: float  # 0-1 (slow to fast learner)
    persistence_level: float  # 0-1
    help_seeking_tendency: float  # 0-1
    preferred_difficulty: float  # 0-1 (easy to challenging)

    # Experience factors
    content_familiarity: Dict[str, float]  # topic -> familiarity (0-1)
    study_time_available: int  # minutes per session
    motivation_level: float  # 0-1

    # Adaptation history
    difficulty_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DifficultyPrediction:
    """Difficulty prediction result"""

    prediction_id: str
    content_id: str
    student_id: Optional[str]

    # Prediction results
    predicted_difficulty: float  # 1-5 scale
    confidence_interval: Tuple[float, float]  # (lower, upper) bounds
    prediction_confidence: float  # 0-1

    # Component predictions
    objective_difficulty: float  # Content-based difficulty
    subjective_difficulty: Optional[float]  # Student-specific difficulty
    cognitive_load: float  # Expected cognitive load (0-1)

    # Supporting information
    key_difficulty_factors: List[Tuple[str, float]]  # (factor, weight)
    recommended_adjustments: List[str]
    alternative_difficulty_levels: Dict[float, str]  # difficulty -> description

    # Prediction metadata
    model_used: str
    feature_importance: Dict[str, float]
    prediction_date: datetime = field(default_factory=datetime.now)

    # Validation
    actual_difficulty: Optional[float] = None  # Set after student performance
    prediction_error: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DifficultyAdjustment:
    """Difficulty adjustment recommendation"""

    adjustment_id: str
    content_id: str
    student_id: str

    # Current state
    current_difficulty: float
    target_difficulty: float
    adjustment_magnitude: float  # How much to change

    # Adjustment strategies
    content_modifications: Dict[str, Any]
    scaffolding_adjustments: Dict[str, Any]
    support_level_changes: Dict[str, Any]

    # Reasoning
    adjustment_reasoning: List[str]
    expected_outcomes: Dict[str, float]  # metric -> expected value

    # Implementation
    implementation_priority: float  # 0-1 (low to high priority)
    estimated_effort: str  # "low", "medium", "high"

    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PredictiveDifficultyAssessment:
    """AI-powered difficulty assessment and prediction system"""

    def __init__(self):
        self.ready = False
        self.models = {}
        self.scalers = {}
        self.encoders = {}

        # Data storage
        self.content_features_db = {}
        self.student_profiles_db = {}
        self.historical_assessments = []
        self.prediction_history = []

        # Model configurations
        self.model_configs = {
            "objective_difficulty": {
                "model": RandomForestRegressor(n_estimators=100, random_state=42),
                "features": [
                    "text_length",
                    "sentence_count",
                    "vocabulary_complexity",
                    "concept_count",
                    "concept_depth",
                    "formula_count",
                ],
            },
            "cognitive_load": {
                "model": GradientBoostingRegressor(n_estimators=100, random_state=42),
                "features": [
                    "concept_depth",
                    "abstract_reasoning_required",
                    "calculation_steps",
                    "vocabulary_complexity",
                    "explanation_depth",
                ],
            },
            "completion_time": {
                "model": RandomForestRegressor(n_estimators=50, random_state=42),
                "features": [
                    "text_length",
                    "concept_count",
                    "formula_count",
                    "example_count",
                ],
            },
            "success_prediction": {
                "model": LogisticRegression(random_state=42),
                "features": [
                    "predicted_difficulty",
                    "student_ability",
                    "motivation_level",
                ],
            },
        }

        # Domain-specific parameters
        self.domain_parameters = {}

        # Validation metrics
        self.model_performance = {}

    async def initialize(self):
        """Initialize the difficulty assessment system"""
        if self.ready:
            return

        logger.info("Initializing Predictive Difficulty Assessment System...")

        try:
            # Load domain-specific parameters
            await self._load_domain_parameters()

            # Generate sample data for training
            await self._generate_sample_data()

            # Train prediction models
            await self._train_models()

            # Validate models
            await self._validate_models()

            self.ready = True
            logger.info(
                "Predictive Difficulty Assessment System initialized successfully"
            )

        except Exception as e:
            logger.error(f"Failed to initialize difficulty assessment system: {e}")
            raise

    async def _load_domain_parameters(self):
        """Load domain-specific parameters for difficulty assessment"""
        self.domain_parameters = {
            ContentDomain.MATHEMATICS: {
                "base_weights": {
                    "formula_complexity": 0.3,
                    "abstract_reasoning": 0.25,
                    "calculation_steps": 0.2,
                    "concept_depth": 0.15,
                    "vocabulary": 0.1,
                },
                "difficulty_thresholds": {"easy": 2.0, "medium": 3.0, "hard": 4.0},
                "cognitive_load_factors": ["working_memory", "processing_speed"],
            },
            ContentDomain.PHYSICS: {
                "base_weights": {
                    "abstract_reasoning": 0.3,
                    "formula_complexity": 0.25,
                    "visualization_required": 0.2,
                    "concept_integration": 0.15,
                    "mathematical_skill": 0.1,
                },
                "difficulty_thresholds": {"easy": 2.2, "medium": 3.2, "hard": 4.1},
                "cognitive_load_factors": ["abstract_reasoning", "spatial_ability"],
            },
            ContentDomain.LANGUAGE: {
                "base_weights": {
                    "vocabulary_complexity": 0.35,
                    "text_length": 0.25,
                    "grammatical_complexity": 0.2,
                    "cultural_knowledge": 0.15,
                    "reading_level": 0.05,
                },
                "difficulty_thresholds": {"easy": 1.8, "medium": 2.8, "hard": 3.8},
                "cognitive_load_factors": ["language_processing", "memory"],
            },
        }

    async def _generate_sample_data(self):
        """Generate sample data for training and testing"""
        # Generate sample content features
        await self._generate_sample_content_features()

        # Generate sample student profiles
        await self._generate_sample_student_profiles()

        # Generate sample historical assessments
        await self._generate_sample_assessments()

        logger.info("Generated sample data for difficulty assessment")

    async def _generate_sample_content_features(self):
        """Generate sample content features"""
        domains = list(ContentDomain)

        for i in range(100):  # 100 sample contents
            domain = domains[i % len(domains)]

            # Generate realistic features based on domain
            if domain == ContentDomain.MATHEMATICS:
                features = ContentFeatures(
                    content_id=f"math_content_{i+1}",
                    domain=domain,
                    text_length=50 + i * 5,
                    sentence_count=5 + i % 10,
                    avg_sentence_length=10 + (i % 5) * 2,
                    vocabulary_complexity=0.3 + (i % 7) * 0.1,
                    readability_score=60 + (i % 4) * 10,
                    concept_count=2 + i % 5,
                    concept_depth=0.4 + (i % 6) * 0.1,
                    prerequisite_count=i % 4,
                    novel_concepts=i % 3,
                    formula_count=1 + i % 4,
                    equation_complexity=0.3 + (i % 5) * 0.15,
                    calculation_steps=3 + i % 8,
                    abstract_reasoning_required=0.4 + (i % 4) * 0.15,
                    example_count=2 + i % 4,
                    explanation_depth=0.5 + (i % 3) * 0.15,
                )
            elif domain == ContentDomain.PHYSICS:
                features = ContentFeatures(
                    content_id=f"physics_content_{i+1}",
                    domain=domain,
                    text_length=70 + i * 3,
                    sentence_count=6 + i % 8,
                    avg_sentence_length=12 + (i % 4) * 2,
                    vocabulary_complexity=0.4 + (i % 6) * 0.1,
                    readability_score=55 + (i % 5) * 8,
                    concept_count=3 + i % 4,
                    concept_depth=0.5 + (i % 5) * 0.1,
                    prerequisite_count=1 + i % 3,
                    novel_concepts=i % 2,
                    formula_count=2 + i % 3,
                    equation_complexity=0.4 + (i % 4) * 0.15,
                    abstract_reasoning_required=0.6 + (i % 3) * 0.13,
                    diagram_count=1 + i % 3,
                    visualization_complexity=0.5 + (i % 4) * 0.12,
                    example_count=1 + i % 3,
                )
            else:  # Other domains
                features = ContentFeatures(
                    content_id=f"{domain.value}_content_{i+1}",
                    domain=domain,
                    text_length=40 + i * 4,
                    sentence_count=4 + i % 12,
                    avg_sentence_length=8 + (i % 6) * 2,
                    vocabulary_complexity=0.2 + (i % 8) * 0.1,
                    readability_score=65 + (i % 3) * 12,
                    concept_count=1 + i % 6,
                    concept_depth=0.3 + (i % 7) * 0.1,
                    prerequisite_count=i % 3,
                    novel_concepts=i % 2,
                    example_count=1 + i % 5,
                    explanation_depth=0.4 + (i % 4) * 0.15,
                )

            # Add some historical performance data
            features.avg_completion_time = 15 + (i % 20) * 2
            features.success_rate = 0.5 + (i % 5) * 0.1
            features.hint_usage_rate = 0.2 + (i % 4) * 0.15

            self.content_features_db[features.content_id] = features

    async def _generate_sample_student_profiles(self):
        """Generate sample student profiles"""
        for i in range(20):  # 20 sample students
            profile = StudentProfile(
                student_id=f"student_{i+1}",
                overall_gpa=2.0 + (i % 5) * 0.5,
                domain_performance={
                    ContentDomain.MATHEMATICS: 0.4 + (i % 6) * 0.1,
                    ContentDomain.PHYSICS: 0.5 + (i % 5) * 0.1,
                    ContentDomain.CHEMISTRY: 0.45 + (i % 7) * 0.08,
                    ContentDomain.LANGUAGE: 0.6 + (i % 4) * 0.1,
                },
                recent_performance_trend=-0.2 + (i % 5) * 0.1,
                processing_speed=0.4 + (i % 6) * 0.1,
                working_memory=0.5 + (i % 5) * 0.1,
                abstract_reasoning=0.3 + (i % 7) * 0.1,
                attention_span=20 + (i % 8) * 5,
                learning_speed=0.4 + (i % 5) * 0.12,
                persistence_level=0.6 + (i % 4) * 0.1,
                help_seeking_tendency=0.3 + (i % 6) * 0.1,
                preferred_difficulty=0.5 + (i % 3) * 0.15,
                content_familiarity={
                    "algebra": 0.3 + (i % 5) * 0.14,
                    "geometry": 0.4 + (i % 4) * 0.15,
                    "physics_mechanics": 0.35 + (i % 6) * 0.1,
                },
                study_time_available=30 + (i % 7) * 10,
                motivation_level=0.5 + (i % 5) * 0.1,
            )

            self.student_profiles_db[profile.student_id] = profile

    async def _generate_sample_assessments(self):
        """Generate sample historical assessments"""
        content_ids = list(self.content_features_db.keys())
        student_ids = list(self.student_profiles_db.keys())

        for i in range(200):  # 200 sample assessments
            content_id = content_ids[i % len(content_ids)]
            student_id = student_ids[i % len(student_ids)]

            # Simulate realistic difficulty assessment
            content_features = self.content_features_db[content_id]
            student_profile = self.student_profiles_db[student_id]

            # Calculate simulated objective difficulty
            objective_difficulty = self._calculate_simulated_objective_difficulty(
                content_features
            )

            # Calculate simulated subjective difficulty
            subjective_difficulty = self._calculate_simulated_subjective_difficulty(
                objective_difficulty, student_profile, content_features
            )

            assessment = {
                "assessment_id": f"assessment_{i+1}",
                "content_id": content_id,
                "student_id": student_id,
                "objective_difficulty": objective_difficulty,
                "subjective_difficulty": subjective_difficulty,
                "actual_performance": max(
                    0, min(1, subjective_difficulty + np.random.normal(0, 0.1))
                ),
                "completion_time": content_features.avg_completion_time
                * (1 + np.random.normal(0, 0.2)),
                "hint_usage": np.random.random() < content_features.hint_usage_rate,
                "timestamp": datetime.now() - timedelta(days=np.random.randint(1, 365)),
            }

            self.historical_assessments.append(assessment)

    def _calculate_simulated_objective_difficulty(
        self, features: ContentFeatures
    ) -> float:
        """Calculate simulated objective difficulty for sample data"""
        domain_params = self.domain_parameters.get(features.domain, {})
        weights = domain_params.get("base_weights", {})

        # Calculate weighted difficulty
        difficulty = 1.0  # Base difficulty

        # Text complexity contribution
        difficulty += (
            features.vocabulary_complexity * weights.get("vocabulary", 0.1) * 2
        )
        difficulty += features.concept_depth * weights.get("concept_depth", 0.15) * 2

        # Domain-specific contributions
        if features.domain == ContentDomain.MATHEMATICS:
            difficulty += (
                features.equation_complexity
                * weights.get("formula_complexity", 0.3)
                * 2
            )
            difficulty += (
                features.abstract_reasoning_required
                * weights.get("abstract_reasoning", 0.25)
                * 2
            )
            difficulty += (
                features.calculation_steps
                / 10
                * weights.get("calculation_steps", 0.2)
                * 2
            )

        # Normalize to 1-5 scale
        return max(1, min(5, difficulty))

    def _calculate_simulated_subjective_difficulty(
        self,
        objective_difficulty: float,
        student: StudentProfile,
        content: ContentFeatures,
    ) -> float:
        """Calculate simulated subjective difficulty"""

        # Student ability in relevant domain
        domain_ability = student.domain_performance.get(content.domain, 0.5)

        # Adjust for student characteristics
        ability_factor = domain_ability * 2  # Scale to roughly match difficulty scale
        processing_factor = student.processing_speed * 0.5
        motivation_factor = student.motivation_level * 0.3

        # Calculate adjustment
        total_adjustment = ability_factor + processing_factor + motivation_factor

        # Apply adjustment (inverse relationship - higher ability means lower subjective difficulty)
        subjective_difficulty = objective_difficulty + (2.5 - total_adjustment)

        return max(1, min(5, subjective_difficulty))

    async def _train_models(self):
        """Train difficulty prediction models"""
        if not self.historical_assessments:
            logger.warning("No historical assessments available for training")
            return

        # Prepare training data
        training_data = await self._prepare_training_data()

        # Train each model
        for model_name, config in self.model_configs.items():
            try:
                await self._train_single_model(model_name, config, training_data)
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")

    async def _prepare_training_data(self) -> Dict[str, Any]:
        """Prepare training data from historical assessments"""
        feature_rows = []
        target_values = {
            "objective_difficulty": [],
            "cognitive_load": [],
            "completion_time": [],
            "success": [],
        }

        for assessment in self.historical_assessments:
            content_id = assessment["content_id"]
            student_id = assessment["student_id"]

            if (
                content_id not in self.content_features_db
                or student_id not in self.student_profiles_db
            ):
                continue

            content = self.content_features_db[content_id]
            student = self.student_profiles_db[student_id]

            # Extract features
            features = {
                "text_length": content.text_length,
                "sentence_count": content.sentence_count,
                "vocabulary_complexity": content.vocabulary_complexity,
                "concept_count": content.concept_count,
                "concept_depth": content.concept_depth,
                "formula_count": content.formula_count,
                "equation_complexity": content.equation_complexity,
                "calculation_steps": content.calculation_steps,
                "abstract_reasoning_required": content.abstract_reasoning_required,
                "explanation_depth": content.explanation_depth,
                "example_count": content.example_count,
                "predicted_difficulty": assessment["objective_difficulty"],
                "student_ability": student.domain_performance.get(content.domain, 0.5),
                "motivation_level": student.motivation_level,
                "processing_speed": student.processing_speed,
                "working_memory": student.working_memory,
            }

            feature_rows.append(features)

            # Extract targets
            target_values["objective_difficulty"].append(
                assessment["objective_difficulty"]
            )
            target_values["cognitive_load"].append(
                content.concept_depth * content.abstract_reasoning_required
            )
            target_values["completion_time"].append(assessment["completion_time"])
            target_values["success"].append(
                1 if assessment["actual_performance"] > 0.7 else 0
            )

        return {"features": feature_rows, "targets": target_values}

    async def _train_single_model(
        self, model_name: str, config: Dict, training_data: Dict
    ):
        """Train a single prediction model"""
        model = config["model"]
        required_features = config["features"]

        # Extract features and targets
        feature_rows = training_data["features"]
        if model_name in training_data["targets"]:
            targets = training_data["targets"][model_name]
        else:
            logger.warning(f"No target data for {model_name}")
            return

        if not feature_rows or not targets:
            logger.warning(f"Insufficient data for {model_name}")
            return

        # Prepare feature matrix
        feature_matrix = []
        for row in feature_rows:
            feature_vector = [row.get(feature, 0) for feature in required_features]
            feature_matrix.append(feature_vector)

        if not feature_matrix:
            logger.warning(f"No valid features for {model_name}")
            return

        X = np.array(feature_matrix)
        y = np.array(targets[: len(feature_matrix)])  # Match lengths

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = model.predict(X_test_scaled)

        if hasattr(model, "predict_proba"):  # Classification
            from sklearn.metrics import accuracy_score

            score = accuracy_score(y_test, y_pred)
            metric = "Accuracy"
        else:  # Regression
            score = mean_squared_error(y_test, y_pred)
            metric = "MSE"

        # Store model and scaler
        self.models[model_name] = model
        self.scalers[model_name] = scaler

        # Store performance
        self.model_performance[model_name] = {
            "metric": metric,
            "score": score,
            "feature_importance": getattr(model, "feature_importances_", None),
        }

        logger.info(f"Trained {model_name}: {metric} = {score:.3f}")

    async def _validate_models(self):
        """Validate trained models"""
        validation_results = {}

        for model_name, model in self.models.items():
            if model_name in self.model_performance:
                performance = self.model_performance[model_name]
                validation_results[model_name] = {
                    "status": "trained",
                    "performance": performance,
                }
            else:
                validation_results[model_name] = {
                    "status": "failed",
                    "performance": None,
                }

        logger.info(
            f"Model validation complete: {len(validation_results)} models processed"
        )

    async def predict_difficulty(
        self,
        content_id: str,
        student_id: Optional[str] = None,
        assessment_type: AssessmentType = AssessmentType.PREDICTIVE,
    ) -> DifficultyPrediction:
        """Predict difficulty for content and optionally for specific student"""
        if not self.ready:
            await self.initialize()

        content_features = self.content_features_db.get(content_id)
        if not content_features:
            raise ValueError(f"Content features not found: {content_id}")

        logger.info(f"Predicting difficulty for content {content_id}")

        # Generate prediction ID
        prediction_id = (
            f"pred_{content_id}_{student_id or 'general'}_{datetime.now().timestamp()}"
        )

        # Predict objective difficulty
        objective_difficulty = await self._predict_objective_difficulty(
            content_features
        )

        # Predict subjective difficulty if student provided
        subjective_difficulty = None
        if student_id and student_id in self.student_profiles_db:
            student_profile = self.student_profiles_db[student_id]
            subjective_difficulty = await self._predict_subjective_difficulty(
                content_features, student_profile, objective_difficulty
            )

        # Predict cognitive load
        cognitive_load = await self._predict_cognitive_load(content_features)

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            objective_difficulty, content_features
        )

        # Identify key difficulty factors
        key_factors = await self._identify_difficulty_factors(content_features)

        # Generate recommendations
        recommendations = await self._generate_difficulty_recommendations(
            content_features, objective_difficulty, subjective_difficulty
        )

        # Create prediction object
        prediction = DifficultyPrediction(
            prediction_id=prediction_id,
            content_id=content_id,
            student_id=student_id,
            predicted_difficulty=subjective_difficulty or objective_difficulty,
            confidence_interval=confidence_interval,
            prediction_confidence=0.8,  # Could be calculated from model confidence
            objective_difficulty=objective_difficulty,
            subjective_difficulty=subjective_difficulty,
            cognitive_load=cognitive_load,
            key_difficulty_factors=key_factors,
            recommended_adjustments=recommendations,
            alternative_difficulty_levels={
                objective_difficulty - 1: "Basitleştirilmiş",
                objective_difficulty: "Standart",
                objective_difficulty + 1: "Geliştirilmiş",
            },
            model_used="ensemble",
            feature_importance={},  # Would be populated from model
        )

        # Store prediction for future validation
        self.prediction_history.append(prediction)

        return prediction

    async def _predict_objective_difficulty(
        self, content_features: ContentFeatures
    ) -> float:
        """Predict objective difficulty based on content features"""

        if "objective_difficulty" not in self.models:
            # Fallback to rule-based calculation
            return self._calculate_rule_based_difficulty(content_features)

        model = self.models["objective_difficulty"]
        scaler = self.scalers["objective_difficulty"]
        config = self.model_configs["objective_difficulty"]

        # Prepare features
        features = [
            getattr(content_features, feature, 0) for feature in config["features"]
        ]

        # Scale and predict
        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]

        return max(1, min(5, prediction))

    async def _predict_subjective_difficulty(
        self,
        content_features: ContentFeatures,
        student_profile: StudentProfile,
        objective_difficulty: float,
    ) -> float:
        """Predict subjective difficulty for specific student"""

        # Get student ability in content domain
        domain_ability = student_profile.domain_performance.get(
            content_features.domain, 0.5
        )

        # Calculate various adjustment factors
        ability_adjustment = (domain_ability - 0.5) * 2  # Scale to -1 to +1
        processing_adjustment = (student_profile.processing_speed - 0.5) * 0.5
        motivation_adjustment = (student_profile.motivation_level - 0.5) * 0.3
        familiarity_adjustment = 0

        # Check content familiarity
        for topic, familiarity in student_profile.content_familiarity.items():
            if topic in content_features.content_id.lower():
                familiarity_adjustment = (familiarity - 0.5) * 0.5
                break

        # Total adjustment (negative means easier for student)
        total_adjustment = -(
            ability_adjustment
            + processing_adjustment
            + motivation_adjustment
            + familiarity_adjustment
        )

        # Apply adjustment to objective difficulty
        subjective_difficulty = objective_difficulty + total_adjustment

        return max(1, min(5, subjective_difficulty))

    async def _predict_cognitive_load(self, content_features: ContentFeatures) -> float:
        """Predict cognitive load for content"""

        if "cognitive_load" not in self.models:
            # Fallback calculation
            load = (
                content_features.concept_depth * 0.4
                + content_features.abstract_reasoning_required * 0.3
                + content_features.vocabulary_complexity * 0.3
            )
            return max(0, min(1, load))

        model = self.models["cognitive_load"]
        scaler = self.scalers["cognitive_load"]
        config = self.model_configs["cognitive_load"]

        # Prepare features
        features = [
            getattr(content_features, feature, 0) for feature in config["features"]
        ]

        # Scale and predict
        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]

        return max(0, min(1, prediction))

    def _calculate_rule_based_difficulty(
        self, content_features: ContentFeatures
    ) -> float:
        """Calculate difficulty using rule-based approach"""
        domain_params = self.domain_parameters.get(content_features.domain, {})
        weights = domain_params.get("base_weights", {})

        difficulty = 2.0  # Base difficulty (medium)

        # Text complexity
        if content_features.vocabulary_complexity > 0.7:
            difficulty += 0.5
        elif content_features.vocabulary_complexity < 0.3:
            difficulty -= 0.3

        # Concept complexity
        if content_features.concept_depth > 0.7:
            difficulty += 0.7
        elif content_features.concept_depth < 0.3:
            difficulty -= 0.5

        # Domain-specific adjustments
        if content_features.domain == ContentDomain.MATHEMATICS:
            if content_features.formula_count > 3:
                difficulty += 0.5
            if content_features.abstract_reasoning_required > 0.7:
                difficulty += 0.8
            if content_features.calculation_steps > 8:
                difficulty += 0.4

        return max(1, min(5, difficulty))

    def _calculate_confidence_interval(
        self, predicted_difficulty: float, content_features: ContentFeatures
    ) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""

        # Simple confidence interval calculation
        # In practice, this would use model uncertainty
        base_uncertainty = 0.3  # Base uncertainty

        # Increase uncertainty for novel content
        if content_features.novel_concepts > 2:
            base_uncertainty += 0.2

        # Decrease uncertainty if we have historical data
        if content_features.success_rate is not None:
            base_uncertainty -= 0.1

        lower_bound = max(1, predicted_difficulty - base_uncertainty)
        upper_bound = min(5, predicted_difficulty + base_uncertainty)

        return (lower_bound, upper_bound)

    async def _identify_difficulty_factors(
        self, content_features: ContentFeatures
    ) -> List[Tuple[str, float]]:
        """Identify key factors contributing to difficulty"""

        factors = []

        # Vocabulary complexity
        if content_features.vocabulary_complexity > 0.6:
            factors.append(
                ("Karmaşık kelime dağarcığı", content_features.vocabulary_complexity)
            )

        # Concept depth
        if content_features.concept_depth > 0.7:
            factors.append(
                ("Derin kavramsal anlayış gereksinimi", content_features.concept_depth)
            )

        # Abstract reasoning
        if content_features.abstract_reasoning_required > 0.6:
            factors.append(
                (
                    "Soyut düşünme gereksinimi",
                    content_features.abstract_reasoning_required,
                )
            )

        # Mathematical complexity
        if content_features.formula_count > 2:
            factors.append(
                ("Çoklu formül kullanımı", content_features.formula_count / 5)
            )

        # Text length
        if content_features.text_length > 200:
            factors.append(("Uzun metin", min(1.0, content_features.text_length / 300)))

        # Prerequisite requirements
        if content_features.prerequisite_count > 2:
            factors.append(("Çoklu ön koşul", content_features.prerequisite_count / 5))

        # Sort by importance
        factors.sort(key=lambda x: x[1], reverse=True)

        return factors[:5]  # Top 5 factors

    async def _generate_difficulty_recommendations(
        self,
        content_features: ContentFeatures,
        objective_difficulty: float,
        subjective_difficulty: Optional[float],
    ) -> List[str]:
        """Generate recommendations for difficulty adjustment"""

        recommendations = []

        # High difficulty recommendations
        if objective_difficulty > 4.0:
            recommendations.extend(
                [
                    "Konuyu küçük parçalara böl",
                    "Daha fazla örnek ve açıklama ekle",
                    "Görsel yardımcılar kullan",
                    "Adım adım rehberlik sağla",
                ]
            )

        # Vocabulary complexity
        if content_features.vocabulary_complexity > 0.7:
            recommendations.append("Karmaşık terimlerin basit açıklamalarını ekle")

        # Mathematical content
        if content_features.formula_count > 3:
            recommendations.append("Formülleri tek tek açıkla ve örneklerle destekle")

        # Abstract concepts
        if content_features.abstract_reasoning_required > 0.7:
            recommendations.extend(
                ["Somut örneklerle başla", "Analojiler ve metaforlar kullan"]
            )

        # Low scaffolding
        if content_features.scaffolding_level < 0.3:
            recommendations.append("Daha fazla destek ve yönlendirme ekle")

        return recommendations

    async def suggest_difficulty_adjustment(
        self, content_id: str, student_id: str, target_success_rate: float = 0.7
    ) -> DifficultyAdjustment:
        """Suggest difficulty adjustments for optimal learning"""
        if not self.ready:
            await self.initialize()

        # Get current prediction
        prediction = await self.predict_difficulty(content_id, student_id)
        current_difficulty = prediction.predicted_difficulty

        # Get student profile
        student_profile = self.student_profiles_db.get(student_id)
        if not student_profile:
            raise ValueError(f"Student profile not found: {student_id}")

        # Calculate target difficulty based on student ability and desired success rate
        domain_ability = student_profile.domain_performance.get(
            self.content_features_db[content_id].domain, 0.5
        )

        # Target difficulty should be slightly above student ability for optimal challenge
        target_difficulty = (domain_ability * 4) + 1 + (1 - target_success_rate)
        target_difficulty = max(1, min(5, target_difficulty))

        # Calculate adjustment magnitude
        adjustment_magnitude = target_difficulty - current_difficulty

        # Generate specific adjustment strategies
        content_modifications = await self._generate_content_modifications(
            self.content_features_db[content_id], adjustment_magnitude
        )

        scaffolding_adjustments = await self._generate_scaffolding_adjustments(
            adjustment_magnitude, student_profile
        )

        support_adjustments = await self._generate_support_adjustments(
            adjustment_magnitude, student_profile
        )

        # Generate reasoning
        reasoning = await self._generate_adjustment_reasoning(
            current_difficulty, target_difficulty, student_profile
        )

        # Calculate expected outcomes
        expected_outcomes = {
            "success_rate": target_success_rate,
            "engagement": min(
                1.0, student_profile.motivation_level + abs(adjustment_magnitude) * 0.1
            ),
            "completion_time": prediction.content_features_db[
                content_id
            ].avg_completion_time
            * (1 - adjustment_magnitude * 0.1),
        }

        adjustment_id = f"adj_{content_id}_{student_id}_{datetime.now().timestamp()}"

        adjustment = DifficultyAdjustment(
            adjustment_id=adjustment_id,
            content_id=content_id,
            student_id=student_id,
            current_difficulty=current_difficulty,
            target_difficulty=target_difficulty,
            adjustment_magnitude=adjustment_magnitude,
            content_modifications=content_modifications,
            scaffolding_adjustments=scaffolding_adjustments,
            support_level_changes=support_adjustments,
            adjustment_reasoning=reasoning,
            expected_outcomes=expected_outcomes,
            implementation_priority=min(1.0, abs(adjustment_magnitude) / 2),
            estimated_effort="low"
            if abs(adjustment_magnitude) < 0.5
            else "medium"
            if abs(adjustment_magnitude) < 1.0
            else "high",
        )

        return adjustment

    async def _generate_content_modifications(
        self, content_features: ContentFeatures, adjustment_magnitude: float
    ) -> Dict[str, Any]:
        """Generate content modification suggestions"""
        modifications = {}

        if adjustment_magnitude < -0.5:  # Make easier
            modifications.update(
                {
                    "reduce_vocabulary_complexity": True,
                    "add_definitions": True,
                    "increase_examples": True,
                    "break_into_smaller_sections": True,
                    "add_visual_aids": True,
                }
            )
        elif adjustment_magnitude > 0.5:  # Make harder
            modifications.update(
                {
                    "reduce_scaffolding": True,
                    "add_complex_examples": True,
                    "introduce_novel_applications": True,
                    "increase_abstraction_level": True,
                    "add_integration_tasks": True,
                }
            )

        return modifications

    async def _generate_scaffolding_adjustments(
        self, adjustment_magnitude: float, student_profile: StudentProfile
    ) -> Dict[str, Any]:
        """Generate scaffolding adjustment suggestions"""
        adjustments = {}

        if adjustment_magnitude < -0.3:  # Increase scaffolding
            adjustments.update(
                {
                    "add_hints": True,
                    "provide_templates": True,
                    "include_guided_practice": True,
                    "offer_step_by_step_solutions": True,
                }
            )
        elif adjustment_magnitude > 0.3:  # Reduce scaffolding
            adjustments.update(
                {
                    "remove_excessive_hints": True,
                    "encourage_independent_problem_solving": True,
                    "provide_open_ended_tasks": True,
                }
            )

        # Student-specific adjustments
        if student_profile.help_seeking_tendency < 0.3:
            adjustments["make_help_more_accessible"] = True

        return adjustments

    async def _generate_support_adjustments(
        self, adjustment_magnitude: float, student_profile: StudentProfile
    ) -> Dict[str, Any]:
        """Generate support level adjustment suggestions"""
        adjustments = {}

        if student_profile.motivation_level < 0.5:
            adjustments.update(
                {
                    "add_motivational_elements": True,
                    "provide_immediate_feedback": True,
                    "celebrate_small_wins": True,
                }
            )

        if student_profile.attention_span < 30:
            adjustments.update(
                {"create_shorter_segments": True, "add_interactive_breaks": True}
            )

        if adjustment_magnitude < -0.5:
            adjustments.update(
                {
                    "increase_teacher_guidance": True,
                    "provide_additional_resources": True,
                    "offer_peer_support": True,
                }
            )

        return adjustments

    async def _generate_adjustment_reasoning(
        self,
        current_difficulty: float,
        target_difficulty: float,
        student_profile: StudentProfile,
    ) -> List[str]:
        """Generate reasoning for difficulty adjustments"""
        reasoning = []

        difficulty_gap = target_difficulty - current_difficulty

        if abs(difficulty_gap) > 0.5:
            if difficulty_gap > 0:
                reasoning.append(
                    f"İçerik öğrenci seviyesinin {difficulty_gap:.1f} puan altında"
                )
                reasoning.append("Daha fazla zorluk optimal öğrenme için gerekli")
            else:
                reasoning.append(
                    f"İçerik öğrenci seviyesinin {abs(difficulty_gap):.1f} puan üstünde"
                )
                reasoning.append("Basitleştirme başarı oranını artıracak")

        # Student-specific reasoning
        domain_performance = list(student_profile.domain_performance.values())
        avg_performance = np.mean(domain_performance) if domain_performance else 0.5

        if avg_performance < 0.5:
            reasoning.append("Öğrenci genel performansı düşük - ek destek gerekli")
        elif avg_performance > 0.8:
            reasoning.append(
                "Öğrenci yüksek performanslı - daha zorlayıcı içerik uygun"
            )

        if student_profile.motivation_level < 0.5:
            reasoning.append("Düşük motivasyon - başarı deneyimleri artırılmalı")

        return reasoning

    async def update_difficulty_assessment(
        self,
        prediction_id: str,
        actual_performance: float,
        actual_completion_time: Optional[float] = None,
        student_feedback: Optional[Dict[str, Any]] = None,
    ):
        """Update difficulty assessment with actual performance data"""

        # Find the prediction
        prediction = None
        for pred in self.prediction_history:
            if pred.prediction_id == prediction_id:
                prediction = pred
                break

        if not prediction:
            logger.warning(f"Prediction not found: {prediction_id}")
            return

        # Calculate prediction error
        predicted_difficulty = prediction.predicted_difficulty
        # Convert performance to difficulty scale (inverse relationship)
        actual_difficulty = 5 - (
            actual_performance * 4
        )  # 1.0 perf -> 1 diff, 0.0 perf -> 5 diff

        prediction.actual_difficulty = actual_difficulty
        prediction.prediction_error = abs(predicted_difficulty - actual_difficulty)

        # Update model learning (simplified)
        if prediction.prediction_error > 1.0:  # Significant error
            logger.info(
                f"Large prediction error for {prediction_id}: {prediction.prediction_error:.2f}"
            )
            # In a real system, this would trigger model retraining

        # Store for future model improvement
        feedback_data = {
            "prediction_id": prediction_id,
            "content_id": prediction.content_id,
            "student_id": prediction.student_id,
            "predicted_difficulty": predicted_difficulty,
            "actual_difficulty": actual_difficulty,
            "prediction_error": prediction.prediction_error,
            "actual_completion_time": actual_completion_time,
            "student_feedback": student_feedback,
            "timestamp": datetime.now(),
        }

        self.historical_assessments.append(feedback_data)

        logger.info(f"Updated difficulty assessment for {prediction_id}")


# Global instance
predictive_difficulty_assessment = PredictiveDifficultyAssessment()


async def get_difficulty_assessment() -> PredictiveDifficultyAssessment:
    """Get initialized difficulty assessment instance"""
    if not predictive_difficulty_assessment.ready:
        await predictive_difficulty_assessment.initialize()
    return predictive_difficulty_assessment
