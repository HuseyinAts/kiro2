"""
ML-Based Performance Analytics Engine
Advanced analytics for student performance prediction and insights
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    IsolationForest,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Performance metrics for analysis"""

    ACCURACY = "accuracy"
    COMPLETION_RATE = "completion_rate"
    TIME_EFFICIENCY = "time_efficiency"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    IMPROVEMENT_RATE = "improvement_rate"
    MASTERY_LEVEL = "mastery_level"


class PredictionTimeframe(Enum):
    """Prediction timeframes"""

    NEXT_SESSION = "next_session"
    ONE_WEEK = "one_week"
    ONE_MONTH = "one_month"
    SEMESTER = "semester"
    YEAR = "year"


class AnalyticsInsightType(Enum):
    """Types of analytics insights"""

    PERFORMANCE_TREND = "performance_trend"
    LEARNING_PATTERN = "learning_pattern"
    RISK_FACTOR = "risk_factor"
    OPPORTUNITY = "opportunity"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"


@dataclass
class StudentPerformanceData:
    """Comprehensive student performance data"""

    student_id: str
    timestamp: datetime

    # Performance metrics
    score: float  # 0-100
    completion_time: int  # minutes
    attempts_count: int
    correct_answers: int
    total_questions: int

    # Context data
    subject: str
    topic: str
    difficulty_level: str
    content_type: str  # video, quiz, article, etc.
    session_duration: int  # minutes

    # Behavioral data
    clicks_count: int
    pause_count: int
    replay_count: int
    help_requests: int

    # Engagement metrics
    attention_score: float  # 0-1
    interaction_frequency: float
    resource_usage: dict[str, int]

    # Environmental factors
    time_of_day: str
    day_of_week: str
    device_type: str

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformancePrediction:
    """Performance prediction result"""

    student_id: str
    metric: PerformanceMetric
    predicted_value: float
    confidence: float  # 0-1
    timeframe: PredictionTimeframe

    # Contributing factors
    key_factors: list[tuple[str, float]]  # (factor_name, importance)
    risk_factors: list[str]
    improvement_opportunities: list[str]

    # Prediction metadata
    model_used: str
    prediction_date: datetime
    data_points_used: int

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsInsight:
    """Analytics insight"""

    insight_id: str
    student_id: str
    insight_type: AnalyticsInsightType
    priority: str  # high, medium, low

    # Insight content
    title: str
    description: str
    evidence: list[str]
    recommendations: list[str]

    # Metrics
    confidence: float
    impact_potential: float  # 0-1
    urgency: float  # 0-1

    # Context
    affected_subjects: list[str]
    timeframe: str
    created_at: datetime = field(default_factory=datetime.now)

    metadata: dict[str, Any] = field(default_factory=dict)


class MLPerformanceAnalytics:
    """ML-powered performance analytics engine"""

    def __init__(self):
        self.ready = False
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}

        # Data storage
        self.performance_data = []
        self.predictions_history = []
        self.insights_history = []

        # Model configurations
        self.model_configs = {
            "performance_predictor": {
                "model": RandomForestRegressor(n_estimators=100, random_state=42),
                "features": [
                    "completion_time",
                    "attempts_count",
                    "session_duration",
                    "attention_score",
                    "help_requests",
                    "difficulty_encoded",
                ],
            },
            "engagement_predictor": {
                "model": GradientBoostingClassifier(n_estimators=100, random_state=42),
                "features": [
                    "clicks_count",
                    "pause_count",
                    "replay_count",
                    "interaction_frequency",
                    "time_of_day_encoded",
                ],
            },
            "risk_classifier": {
                "model": LogisticRegression(random_state=42),
                "features": [
                    "score_trend",
                    "completion_rate",
                    "engagement_trend",
                    "help_frequency",
                    "time_efficiency",
                ],
            },
            "anomaly_detector": {
                "model": IsolationForest(contamination=0.1, random_state=42),
                "features": [
                    "score",
                    "completion_time",
                    "attempts_count",
                    "attention_score",
                ],
            },
        }

    async def initialize(self):
        """Initialize the analytics engine"""
        if self.ready:
            return

        logger.info("Initializing ML Performance Analytics Engine...")

        try:
            # Initialize encoders and scalers
            await self._initialize_preprocessing()

            # Load or create sample data for training
            await self._load_training_data()

            # Train initial models
            await self._train_models()

            self.ready = True
            logger.info("ML Performance Analytics Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize analytics engine: {e}")
            raise

    async def _initialize_preprocessing(self):
        """Initialize preprocessing components"""
        # Standard scalers for numerical features
        self.scalers = {
            "numerical": StandardScaler(),
            "time_features": StandardScaler(),
            "engagement_features": StandardScaler(),
        }

        # Label encoders for categorical features
        self.encoders = {
            "subject": LabelEncoder(),
            "topic": LabelEncoder(),
            "difficulty": LabelEncoder(),
            "content_type": LabelEncoder(),
            "time_of_day": LabelEncoder(),
            "day_of_week": LabelEncoder(),
            "device_type": LabelEncoder(),
        }

    async def _load_training_data(self):
        """Load or generate training data"""
        # For now, generate sample training data
        # In production, this would load from database
        await self._generate_sample_training_data()

    async def _generate_sample_training_data(self):
        """Generate sample training data for development"""
        np.random.seed(42)

        subjects = ["matematik", "fizik", "kimya", "biyoloji"]
        topics = ["cebir", "geometri", "mekanik", "termodinamik", "organik", "hücre"]
        difficulties = ["kolay", "orta", "zor"]
        content_types = ["video", "quiz", "article", "interactive"]
        times_of_day = ["sabah", "öğlen", "akşam", "gece"]
        days_of_week = [
            "pazartesi",
            "salı",
            "çarşamba",
            "perşembe",
            "cuma",
            "cumartesi",
            "pazar",
        ]
        devices = ["desktop", "tablet", "mobile"]

        sample_data = []

        for i in range(1000):  # Generate 1000 sample records
            # Create realistic correlations
            difficulty_factor = np.random.choice([0.3, 0.6, 0.9])  # Easy, medium, hard
            student_ability = np.random.beta(2, 3)  # Most students are average

            # Score influenced by student ability and difficulty
            base_score = student_ability * 100
            difficulty_penalty = (1 - difficulty_factor) * 20
            score = max(
                0, min(100, base_score - difficulty_penalty + np.random.normal(0, 10))
            )

            # Time influenced by difficulty and score
            base_time = 20 + difficulty_factor * 40
            time_variance = (100 - score) / 100 * 20
            completion_time = max(5, base_time + time_variance + np.random.normal(0, 5))

            # Attempts based on score
            attempts = (
                1 if score > 70 else (2 if score > 40 else np.random.randint(2, 5))
            )

            # Engagement metrics
            attention_score = min(1.0, (score / 100) * 0.8 + np.random.normal(0, 0.1))
            clicks_count = int(completion_time * np.random.uniform(1, 3))

            data_point = StudentPerformanceData(
                student_id=f"student_{i % 50 + 1}",
                timestamp=datetime.now() - timedelta(days=np.random.randint(0, 365)),
                score=score,
                completion_time=int(completion_time),
                attempts_count=attempts,
                correct_answers=int((score / 100) * 10),
                total_questions=10,
                subject=np.random.choice(subjects),
                topic=np.random.choice(topics),
                difficulty_level=np.random.choice(difficulties),
                content_type=np.random.choice(content_types),
                session_duration=int(completion_time * np.random.uniform(1.2, 2.0)),
                clicks_count=clicks_count,
                pause_count=int(np.random.poisson(2)),
                replay_count=int(np.random.poisson(1)),
                help_requests=int(np.random.poisson(0.5)),
                attention_score=attention_score,
                interaction_frequency=clicks_count / completion_time,
                resource_usage={
                    "hints": np.random.randint(0, 3),
                    "examples": np.random.randint(0, 5),
                },
                time_of_day=np.random.choice(times_of_day),
                day_of_week=np.random.choice(days_of_week),
                device_type=np.random.choice(devices),
            )

            sample_data.append(data_point)

        self.performance_data = sample_data
        logger.info(f"Generated {len(sample_data)} sample training records")

    async def _train_models(self):
        """Train ML models on available data"""
        if not self.performance_data:
            logger.warning("No training data available")
            return

        # Convert data to DataFrame for easier processing
        df = await self._prepare_dataframe()

        # Train each model
        for model_name, config in self.model_configs.items():
            try:
                await self._train_single_model(model_name, config, df)
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")

    async def _prepare_dataframe(self) -> pd.DataFrame:
        """Prepare data for ML training"""
        data_dict = []

        for record in self.performance_data:
            row = {
                "student_id": record.student_id,
                "score": record.score,
                "completion_time": record.completion_time,
                "attempts_count": record.attempts_count,
                "session_duration": record.session_duration,
                "clicks_count": record.clicks_count,
                "pause_count": record.pause_count,
                "replay_count": record.replay_count,
                "help_requests": record.help_requests,
                "attention_score": record.attention_score,
                "interaction_frequency": record.interaction_frequency,
                "subject": record.subject,
                "topic": record.topic,
                "difficulty_level": record.difficulty_level,
                "content_type": record.content_type,
                "time_of_day": record.time_of_day,
                "day_of_week": record.day_of_week,
                "device_type": record.device_type,
            }
            data_dict.append(row)

        df = pd.DataFrame(data_dict)

        # Encode categorical variables
        categorical_columns = [
            "subject",
            "topic",
            "difficulty_level",
            "content_type",
            "time_of_day",
            "day_of_week",
            "device_type",
        ]

        for col in categorical_columns:
            if col in df.columns:
                encoded_col = f"{col}_encoded"
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                df[encoded_col] = self.encoders[col].fit_transform(df[col])

        # Create derived features
        df["completion_rate"] = df["score"] / 100
        df["time_efficiency"] = 100 / (df["completion_time"] + 1)
        df["help_frequency"] = df["help_requests"] / (df["session_duration"] + 1)
        df["engagement_score"] = (df["clicks_count"] + df["attention_score"] * 10) / 2

        # Calculate trends (simplified for sample data)
        df["score_trend"] = df.groupby("student_id")["score"].pct_change().fillna(0)
        df["engagement_trend"] = (
            df.groupby("student_id")["engagement_score"].pct_change().fillna(0)
        )

        return df

    async def _train_single_model(
        self, model_name: str, config: dict, df: pd.DataFrame
    ):
        """Train a single ML model"""
        model = config["model"]
        features = config["features"]

        # Check if all features exist
        available_features = [f for f in features if f in df.columns]
        if len(available_features) != len(features):
            missing = set(features) - set(available_features)
            logger.warning(f"Missing features for {model_name}: {missing}")
            features = available_features

        if not features:
            logger.error(f"No valid features for {model_name}")
            return

        X = df[features].fillna(0)

        # Define target variable based on model type
        if model_name == "performance_predictor":
            y = df["score"]
        elif model_name == "engagement_predictor":
            y = (df["engagement_score"] > df["engagement_score"].median()).astype(int)
        elif model_name == "risk_classifier":
            y = (df["score"] < 60).astype(int)  # At-risk if score < 60
        elif model_name == "anomaly_detector":
            # Anomaly detection doesn't need y
            model.fit(X)
            self.models[model_name] = model
            logger.info(f"Trained {model_name} (unsupervised)")
            return

        # Split data for supervised learning
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
        if hasattr(model, "predict_proba"):
            y_pred = model.predict(X_test_scaled)
            score = accuracy_score(y_test, y_pred)
            metric = "Accuracy"
        else:
            y_pred = model.predict(X_test_scaled)
            score = -mean_squared_error(y_test, y_pred)  # Negative MSE for maximization
            metric = "Negative MSE"

        # Store model and scaler
        self.models[model_name] = model
        self.scalers[model_name] = scaler

        # Store feature importance
        if hasattr(model, "feature_importances_"):
            self.feature_importance[model_name] = dict(
                zip(features, model.feature_importances_)
            )

        logger.info(f"Trained {model_name}: {metric} = {score:.3f}")

    async def predict_performance(
        self,
        student_id: str,
        timeframe: PredictionTimeframe,
        context: dict[str, Any] | None = None,
    ) -> list[PerformancePrediction]:
        """Predict student performance"""
        if not self.ready:
            await self.initialize()

        predictions = []

        # Get student's historical data
        student_data = [d for d in self.performance_data if d.student_id == student_id]
        if not student_data:
            logger.warning(f"No historical data for student {student_id}")
            return predictions

        # Prepare features for prediction
        latest_data = student_data[-1]  # Most recent record
        features = await self._extract_prediction_features(
            latest_data, student_data, context
        )

        # Make predictions for different metrics
        metrics_to_predict = [
            PerformanceMetric.ACCURACY,
            PerformanceMetric.COMPLETION_RATE,
            PerformanceMetric.ENGAGEMENT,
        ]

        for metric in metrics_to_predict:
            prediction = await self._predict_single_metric(
                student_id, metric, timeframe, features, student_data
            )
            if prediction:
                predictions.append(prediction)

        return predictions

    async def _extract_prediction_features(
        self,
        latest_data: StudentPerformanceData,
        student_history: list[StudentPerformanceData],
        context: dict[str, Any] | None,
    ) -> dict[str, float]:
        """Extract features for prediction"""
        features = {}

        # Current performance features
        features["completion_time"] = latest_data.completion_time
        features["attempts_count"] = latest_data.attempts_count
        features["session_duration"] = latest_data.session_duration
        features["attention_score"] = latest_data.attention_score
        features["help_requests"] = latest_data.help_requests
        features["clicks_count"] = latest_data.clicks_count
        features["pause_count"] = latest_data.pause_count
        features["replay_count"] = latest_data.replay_count
        features["interaction_frequency"] = latest_data.interaction_frequency

        # Historical trends
        if len(student_history) >= 2:
            recent_scores = [d.score for d in student_history[-5:]]
            features["score_trend"] = (
                np.mean(np.diff(recent_scores)) if len(recent_scores) > 1 else 0
            )
            features["avg_score"] = np.mean(recent_scores)
            features["score_std"] = np.std(recent_scores)
        else:
            features["score_trend"] = 0
            features["avg_score"] = latest_data.score
            features["score_std"] = 0

        # Derived features
        features["completion_rate"] = latest_data.score / 100
        features["time_efficiency"] = 100 / (latest_data.completion_time + 1)
        features["help_frequency"] = latest_data.help_requests / (
            latest_data.session_duration + 1
        )
        features["engagement_score"] = (
            latest_data.clicks_count + latest_data.attention_score * 10
        ) / 2
        features["engagement_trend"] = 0  # Simplified for now

        # Encode categorical features
        try:
            if "difficulty_level" in self.encoders:
                features["difficulty_encoded"] = self.encoders[
                    "difficulty_level"
                ].transform([latest_data.difficulty_level])[0]
            if "time_of_day" in self.encoders:
                features["time_of_day_encoded"] = self.encoders[
                    "time_of_day"
                ].transform([latest_data.time_of_day])[0]
        except ValueError as e:
            logger.warning(f"Encoding error: {e}")
            features["difficulty_encoded"] = 0
            features["time_of_day_encoded"] = 0

        # Context features
        if context:
            features.update(context)

        return features

    async def _predict_single_metric(
        self,
        student_id: str,
        metric: PerformanceMetric,
        timeframe: PredictionTimeframe,
        features: dict[str, float],
        student_history: list[StudentPerformanceData],
    ) -> PerformancePrediction | None:
        """Predict a single performance metric"""

        # Map metric to model
        model_mapping = {
            PerformanceMetric.ACCURACY: "performance_predictor",
            PerformanceMetric.COMPLETION_RATE: "performance_predictor",
            PerformanceMetric.ENGAGEMENT: "engagement_predictor",
        }

        model_name = model_mapping.get(metric)
        if not model_name or model_name not in self.models:
            return None

        model = self.models[model_name]
        model_config = self.model_configs[model_name]
        required_features = model_config["features"]

        # Prepare feature vector
        feature_vector = []
        available_features = []

        for feature_name in required_features:
            if feature_name in features:
                feature_vector.append(features[feature_name])
                available_features.append(feature_name)
            else:
                feature_vector.append(0)  # Default value for missing features

        if not feature_vector:
            return None

        # Scale features
        scaler = self.scalers.get(model_name)
        if scaler:
            feature_vector = scaler.transform([feature_vector])[0]

        # Make prediction
        try:
            if hasattr(model, "predict_proba"):
                prediction_proba = model.predict_proba([feature_vector])[0]
                predicted_value = prediction_proba[1]  # Probability of positive class
                confidence = max(prediction_proba)
            else:
                predicted_value = model.predict([feature_vector])[0]
                confidence = 0.75  # Default confidence for regression

            # Adjust prediction based on timeframe
            predicted_value = self._adjust_for_timeframe(predicted_value, timeframe)

            # Get feature importance
            feature_importance = self.feature_importance.get(model_name, {})
            key_factors = [
                (f, feature_importance.get(f, 0)) for f in available_features
            ]
            key_factors.sort(key=lambda x: x[1], reverse=True)

            # Identify risk factors and opportunities
            risk_factors = await self._identify_risk_factors(features, student_history)
            opportunities = await self._identify_opportunities(
                features, student_history
            )

            return PerformancePrediction(
                student_id=student_id,
                metric=metric,
                predicted_value=float(predicted_value),
                confidence=float(confidence),
                timeframe=timeframe,
                key_factors=key_factors[:5],  # Top 5 factors
                risk_factors=risk_factors,
                improvement_opportunities=opportunities,
                model_used=model_name,
                prediction_date=datetime.now(),
                data_points_used=len(student_history),
            )

        except Exception as e:
            logger.error(f"Prediction error for {metric}: {e}")
            return None

    def _adjust_for_timeframe(
        self, predicted_value: float, timeframe: PredictionTimeframe
    ) -> float:
        """Adjust prediction based on timeframe"""
        # Simple adjustment factors
        timeframe_adjustments = {
            PredictionTimeframe.NEXT_SESSION: 1.0,
            PredictionTimeframe.ONE_WEEK: 0.95,
            PredictionTimeframe.ONE_MONTH: 0.9,
            PredictionTimeframe.SEMESTER: 0.8,
            PredictionTimeframe.YEAR: 0.7,
        }

        adjustment = timeframe_adjustments.get(timeframe, 1.0)
        return predicted_value * adjustment

    async def _identify_risk_factors(
        self, features: dict[str, float], student_history: list[StudentPerformanceData]
    ) -> list[str]:
        """Identify risk factors for the student"""
        risk_factors = []

        # Low attention score
        if features.get("attention_score", 1) < 0.5:
            risk_factors.append("Düşük dikkat seviyesi")

        # High help requests
        if features.get("help_frequency", 0) > 0.1:
            risk_factors.append("Sık yardım talebi")

        # Declining performance trend
        if features.get("score_trend", 0) < -5:
            risk_factors.append("Düşen performans trendi")

        # Long completion times
        if features.get("completion_time", 0) > 60:
            risk_factors.append("Uzun tamamlanma süreleri")

        # Multiple attempts
        if features.get("attempts_count", 1) > 2:
            risk_factors.append("Çoklu denemeler")

        return risk_factors

    async def _identify_opportunities(
        self, features: dict[str, float], student_history: list[StudentPerformanceData]
    ) -> list[str]:
        """Identify improvement opportunities"""
        opportunities = []

        # High engagement but low performance
        if (
            features.get("engagement_score", 0) > 7
            and features.get("avg_score", 0) < 70
        ):
            opportunities.append("Yüksek motivasyonu performansa dönüştürme")

        # Good performance trend
        if features.get("score_trend", 0) > 5:
            opportunities.append("Pozitif momentum sürdürme")

        # Fast completion with good accuracy
        if (
            features.get("time_efficiency", 0) > 2
            and features.get("completion_rate", 0) > 0.8
        ):
            opportunities.append("Zorluk seviyesi artırma")

        # Low help requests with good performance
        if (
            features.get("help_frequency", 1) < 0.05
            and features.get("avg_score", 0) > 80
        ):
            opportunities.append("Bağımsız öğrenme becerilerini geliştirme")

        return opportunities

    async def generate_insights(
        self, student_id: str, analysis_period: int = 30  # days
    ) -> list[AnalyticsInsight]:
        """Generate analytics insights for a student"""
        if not self.ready:
            await self.initialize()

        insights = []

        # Get student data for analysis period
        cutoff_date = datetime.now() - timedelta(days=analysis_period)
        student_data = [
            d
            for d in self.performance_data
            if d.student_id == student_id and d.timestamp >= cutoff_date
        ]

        if not student_data:
            return insights

        # Generate different types of insights
        insights.extend(
            await self._analyze_performance_trends(student_id, student_data)
        )
        insights.extend(await self._analyze_learning_patterns(student_id, student_data))
        insights.extend(await self._detect_anomalies(student_id, student_data))
        insights.extend(await self._identify_risk_students(student_id, student_data))

        # Sort by priority and impact
        insights.sort(
            key=lambda x: (x.priority == "high", x.impact_potential, x.urgency),
            reverse=True,
        )

        return insights

    async def _analyze_performance_trends(
        self, student_id: str, data: list[StudentPerformanceData]
    ) -> list[AnalyticsInsight]:
        """Analyze performance trends"""
        insights = []

        if len(data) < 3:
            return insights

        # Calculate trend
        scores = [d.score for d in sorted(data, key=lambda x: x.timestamp)]
        times = list(range(len(scores)))

        # Simple linear regression for trend
        if len(scores) >= 2:
            slope = np.polyfit(times, scores, 1)[0]

            if slope > 2:  # Improving
                insight = AnalyticsInsight(
                    insight_id=f"trend_{student_id}_{datetime.now().timestamp()}",
                    student_id=student_id,
                    insight_type=AnalyticsInsightType.PERFORMANCE_TREND,
                    priority="medium",
                    title="Performans Artışı",
                    description=f"Son {len(scores)} aktivitede {slope:.1f} puan/aktivite artış gösteriyor",
                    evidence=[
                        f"Ortalama puan artışı: {slope:.1f}",
                        f"En son puan: {scores[-1]:.1f}",
                    ],
                    recommendations=[
                        "Bu pozitif trendi sürdürmek için çalışma rutinini koruyun",
                        "Zorluk seviyesini artırmayı değerlendirin",
                    ],
                    confidence=0.8,
                    impact_potential=0.7,
                    urgency=0.5,
                    affected_subjects=list(set(d.subject for d in data)),
                )
                insights.append(insight)

            elif slope < -2:  # Declining
                insight = AnalyticsInsight(
                    insight_id=f"trend_{student_id}_{datetime.now().timestamp()}",
                    student_id=student_id,
                    insight_type=AnalyticsInsightType.PERFORMANCE_TREND,
                    priority="high",
                    title="Performans Düşüşü",
                    description=f"Son {len(scores)} aktivitede {abs(slope):.1f} puan/aktivite düşüş gösteriyor",
                    evidence=[
                        f"Ortalama puan düşüşü: {slope:.1f}",
                        f"En son puan: {scores[-1]:.1f}",
                    ],
                    recommendations=[
                        "Öğrenme stratejilerini gözden geçirin",
                        "Ek destek alın",
                        "Daha fazla pratik yapın",
                    ],
                    confidence=0.8,
                    impact_potential=0.9,
                    urgency=0.8,
                    affected_subjects=list(set(d.subject for d in data)),
                )
                insights.append(insight)

        return insights

    async def _analyze_learning_patterns(
        self, student_id: str, data: list[StudentPerformanceData]
    ) -> list[AnalyticsInsight]:
        """Analyze learning patterns"""
        insights = []

        # Time of day analysis
        time_performance = {}
        for d in data:
            if d.time_of_day not in time_performance:
                time_performance[d.time_of_day] = []
            time_performance[d.time_of_day].append(d.score)

        # Find best time of day
        if len(time_performance) > 1:
            avg_by_time = {
                time: np.mean(scores) for time, scores in time_performance.items()
            }
            best_time = max(avg_by_time, key=avg_by_time.get)
            worst_time = min(avg_by_time, key=avg_by_time.get)

            if (
                avg_by_time[best_time] - avg_by_time[worst_time] > 10
            ):  # Significant difference
                insight = AnalyticsInsight(
                    insight_id=f"pattern_{student_id}_{datetime.now().timestamp()}",
                    student_id=student_id,
                    insight_type=AnalyticsInsightType.LEARNING_PATTERN,
                    priority="medium",
                    title="Optimal Çalışma Zamanı",
                    description=f"En iyi performansı {best_time} saatlerinde gösteriyor",
                    evidence=[
                        f"{best_time} ortalama: {avg_by_time[best_time]:.1f}",
                        f"{worst_time} ortalama: {avg_by_time[worst_time]:.1f}",
                    ],
                    recommendations=[
                        f"{best_time} saatlerinde daha fazla çalışmaya odaklanın",
                        "Zor konuları en verimli saatlerde çalışın",
                    ],
                    confidence=0.7,
                    impact_potential=0.6,
                    urgency=0.4,
                    affected_subjects=list(set(d.subject for d in data)),
                )
                insights.append(insight)

        return insights

    async def _detect_anomalies(
        self, student_id: str, data: list[StudentPerformanceData]
    ) -> list[AnalyticsInsight]:
        """Detect performance anomalies"""
        insights = []

        if "anomaly_detector" not in self.models or len(data) < 5:
            return insights

        # Prepare features for anomaly detection
        features_list = []
        for d in data:
            features = [d.score, d.completion_time, d.attempts_count, d.attention_score]
            features_list.append(features)

        # Detect anomalies
        anomaly_scores = self.models["anomaly_detector"].decision_function(
            features_list
        )
        anomalies = self.models["anomaly_detector"].predict(features_list)

        # Find significant anomalies
        for i, (anomaly, score) in enumerate(zip(anomalies, anomaly_scores)):
            if anomaly == -1 and score < -0.5:  # Strong anomaly
                anomaly_data = data[i]
                insight = AnalyticsInsight(
                    insight_id=f"anomaly_{student_id}_{i}_{datetime.now().timestamp()}",
                    student_id=student_id,
                    insight_type=AnalyticsInsightType.ANOMALY,
                    priority="high",
                    title="Anormal Performans Tespit Edildi",
                    description=f"Olağandışı performans paterni: {anomaly_data.subject} - {anomaly_data.topic}",
                    evidence=[
                        f"Puan: {anomaly_data.score}",
                        f"Süre: {anomaly_data.completion_time} dk",
                        f"Deneme: {anomaly_data.attempts_count}",
                    ],
                    recommendations=[
                        "Bu aktiviteyi gözden geçirin",
                        "Benzer konularda ek pratik yapın",
                        "Öğrenme yaklaşımınızı değerlendirin",
                    ],
                    confidence=0.9,
                    impact_potential=0.7,
                    urgency=0.9,
                    affected_subjects=[anomaly_data.subject],
                )
                insights.append(insight)

        return insights

    async def _identify_risk_students(
        self, student_id: str, data: list[StudentPerformanceData]
    ) -> list[AnalyticsInsight]:
        """Identify students at risk"""
        insights = []

        if "risk_classifier" not in self.models:
            return insights

        # Calculate risk features
        recent_data = data[-5:] if len(data) >= 5 else data
        avg_score = np.mean([d.score for d in recent_data])
        completion_rate = len([d for d in recent_data if d.score >= 60]) / len(
            recent_data
        )

        # Simple risk assessment
        risk_score = 0
        risk_factors = []

        if avg_score < 60:
            risk_score += 0.4
            risk_factors.append("Düşük ortalama puan")

        if completion_rate < 0.6:
            risk_score += 0.3
            risk_factors.append("Düşük başarı oranı")

        if np.mean([d.help_requests for d in recent_data]) > 2:
            risk_score += 0.2
            risk_factors.append("Sık yardım talebi")

        if np.mean([d.attention_score for d in recent_data]) < 0.5:
            risk_score += 0.1
            risk_factors.append("Düşük dikkat seviyesi")

        if risk_score > 0.5:  # High risk
            insight = AnalyticsInsight(
                insight_id=f"risk_{student_id}_{datetime.now().timestamp()}",
                student_id=student_id,
                insight_type=AnalyticsInsightType.RISK_FACTOR,
                priority="high",
                title="Yüksek Risk Durumu",
                description="Öğrenci akademik başarısızlık riski taşıyor",
                evidence=risk_factors,
                recommendations=[
                    "Acil müdahale gerekli",
                    "Bireysel destek programı",
                    "Öğrenme stratejilerini yeniden değerlendir",
                    "Motivasyon artırıcı etkinlikler",
                ],
                confidence=0.8,
                impact_potential=1.0,
                urgency=1.0,
                affected_subjects=list(set(d.subject for d in data)),
            )
            insights.append(insight)

        return insights


# Global instance
ml_performance_analytics = MLPerformanceAnalytics()


async def get_performance_analytics() -> MLPerformanceAnalytics:
    """Get initialized performance analytics instance"""
    if not ml_performance_analytics.ready:
        await ml_performance_analytics.initialize()
    return ml_performance_analytics
