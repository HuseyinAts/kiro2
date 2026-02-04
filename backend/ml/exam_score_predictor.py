"""
Exam Score Predictor - P3.1
ML model to predict TYT/AYT scores based on practice test performance

Features:
- Score prediction with confidence intervals
- Feature importance analysis
- Recommendation engine
- Performance tracking

Technology:
- Scikit-learn (Random Forest, Gradient Boosting)
- Statistical analysis
- Time-series forecasting
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logger = logging.getLogger(__name__)


class ExamScorePredictor:
    """
    Predicts TYT/AYT scores based on practice test performance

    Uses ensemble methods (Random Forest + Gradient Boosting) for robust predictions
    """

    def __init__(self, model_type: str = "ensemble"):
        """
        Args:
            model_type: "rf" (Random Forest), "gb" (Gradient Boosting), "ensemble" (both)
        """
        self.model_type = model_type
        self.rf_model = RandomForestRegressor(
            n_estimators=100, max_depth=10, min_samples_split=5, random_state=42
        )
        self.gb_model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, student_data: Dict) -> np.ndarray:
        """
        Prepare features from student practice test data

        Args:
            student_data: {
                "practice_tests": [
                    {"date": "2025-01-01", "score": 85, "subject": "matematik", ...},
                    ...
                ],
                "study_hours_total": 500,
                "attendance_rate": 0.95,
                "grade_level": 12,
                ...
            }

        Returns:
            Feature vector (27 features)
        """
        practice_tests = student_data.get("practice_tests", [])

        # Sort by date
        practice_tests = sorted(practice_tests, key=lambda x: x["date"])

        # Feature 1-5: Recent performance (last 5 tests)
        recent_scores = [t["score"] for t in practice_tests[-5:]]
        recent_scores += [0] * (5 - len(recent_scores))  # Pad if < 5 tests

        # Feature 6: Average score
        avg_score = (
            np.mean([t["score"] for t in practice_tests]) if practice_tests else 0
        )

        # Feature 7: Score trend (linear regression slope)
        if len(practice_tests) >= 2:
            x = np.arange(len(practice_tests))
            y = np.array([t["score"] for t in practice_tests])
            trend = np.polyfit(x, y, 1)[0]  # Slope
        else:
            trend = 0

        # Feature 8: Score variance (consistency)
        score_variance = (
            np.var([t["score"] for t in practice_tests])
            if len(practice_tests) > 1
            else 0
        )

        # Feature 9-12: Subject-specific averages (matematik, fen, turkce, sosyal)
        subjects = ["matematik", "fen", "turkce", "sosyal"]
        subject_avgs = []
        for subject in subjects:
            subject_scores = [
                t["score"] for t in practice_tests if t.get("subject") == subject
            ]
            subject_avgs.append(np.mean(subject_scores) if subject_scores else 0)

        # Feature 13: Total practice tests taken
        test_count = len(practice_tests)

        # Feature 14: Study hours
        study_hours = student_data.get("study_hours_total", 0)

        # Feature 15: Attendance rate
        attendance = student_data.get("attendance_rate", 0.8)

        # Feature 16: Grade level
        grade_level = student_data.get("grade_level", 12)

        # Feature 17-20: Last test performance by question type
        if practice_tests:
            last_test = practice_tests[-1]
            question_type_scores = [
                last_test.get("multiple_choice_accuracy", 0),
                last_test.get("problem_solving_accuracy", 0),
                last_test.get("reading_comp_accuracy", 0),
                last_test.get("geometry_accuracy", 0),
            ]
        else:
            question_type_scores = [0, 0, 0, 0]

        # Feature 21: Days since first test
        if practice_tests:
            first_date = datetime.fromisoformat(practice_tests[0]["date"])
            last_date = datetime.fromisoformat(practice_tests[-1]["date"])
            days_studying = (last_date - first_date).days
        else:
            days_studying = 0

        # Feature 22: Test frequency (tests per week)
        test_frequency = (
            (test_count / max(days_studying / 7, 1)) if days_studying > 0 else 0
        )

        # Feature 23: Time management score (avg time per question)
        time_management = (
            np.mean([t.get("avg_time_per_question", 120) for t in practice_tests])
            if practice_tests
            else 120
        )

        # Feature 24: Improvement rate (recent vs early tests)
        if len(practice_tests) >= 4:
            early_avg = np.mean([t["score"] for t in practice_tests[:2]])
            recent_avg = np.mean([t["score"] for t in practice_tests[-2:]])
            improvement_rate = (
                (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
            )
        else:
            improvement_rate = 0

        # Feature 25: Consistency score (inverse of coefficient of variation)
        if avg_score > 0 and score_variance > 0:
            consistency = 1 / (np.sqrt(score_variance) / avg_score)
        else:
            consistency = 0

        # Feature 26: Peak performance (best score achieved)
        peak_score = max([t["score"] for t in practice_tests]) if practice_tests else 0

        # Feature 27: Exam readiness (composite score)
        exam_readiness = (
            avg_score * 0.4 + peak_score * 0.3 + consistency * 0.2 + attendance * 10
        )

        # Combine all features
        features = (
            recent_scores
            + [avg_score, trend, score_variance]
            + subject_avgs
            + [test_count, study_hours, attendance, grade_level]
            + question_type_scores
            + [
                days_studying,
                test_frequency,
                time_management,
                improvement_rate,
                consistency,
                peak_score,
                exam_readiness,
            ]
        )

        return np.array(features).reshape(1, -1)

    def train(self, training_data: List[Dict], labels: List[float]):
        """
        Train the prediction model

        Args:
            training_data: List of student_data dictionaries
            labels: Actual exam scores achieved
        """
        logger.info(f"Training exam score predictor with {len(training_data)} samples")

        # Prepare features
        X = np.vstack([self.prepare_features(data) for data in training_data])
        y = np.array(labels)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train models
        if self.model_type in ["rf", "ensemble"]:
            self.rf_model.fit(X_scaled, y)
            rf_score = cross_val_score(self.rf_model, X_scaled, y, cv=5).mean()
            logger.info(f"Random Forest CV Score: {rf_score:.4f}")

        if self.model_type in ["gb", "ensemble"]:
            self.gb_model.fit(X_scaled, y)
            gb_score = cross_val_score(self.gb_model, X_scaled, y, cv=5).mean()
            logger.info(f"Gradient Boosting CV Score: {gb_score:.4f}")

        self.is_trained = True
        logger.info("Training complete")

    def predict(
        self, student_data: Dict, return_confidence: bool = True
    ) -> Dict[str, float]:
        """
        Predict exam score for a student

        Args:
            student_data: Student practice test data
            return_confidence: Whether to return confidence interval

        Returns:
            {
                "predicted_score": 450.5,
                "confidence_lower": 430.0,
                "confidence_upper": 470.0,
                "confidence_level": 0.95,
                "model_confidence": 0.85
            }
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        # Prepare features
        X = self.prepare_features(student_data)
        X_scaled = self.scaler.transform(X)

        # Get predictions from models
        predictions = []

        if self.model_type in ["rf", "ensemble"]:
            rf_pred = self.rf_model.predict(X_scaled)[0]
            predictions.append(rf_pred)

        if self.model_type in ["gb", "ensemble"]:
            gb_pred = self.gb_model.predict(X_scaled)[0]
            predictions.append(gb_pred)

        # Ensemble prediction (average)
        predicted_score = np.mean(predictions)

        # Confidence interval (based on model variance)
        if return_confidence:
            if len(predictions) > 1:
                prediction_std = np.std(predictions)
            else:
                # Use 10% of predicted score as std if single model
                prediction_std = predicted_score * 0.1

            # 95% confidence interval (±1.96 std)
            confidence_lower = predicted_score - 1.96 * prediction_std
            confidence_upper = predicted_score + 1.96 * prediction_std

            # Model confidence (inverse of std, normalized)
            model_confidence = 1 / (1 + prediction_std / 100)

            return {
                "predicted_score": round(predicted_score, 2),
                "confidence_lower": round(confidence_lower, 2),
                "confidence_upper": round(confidence_upper, 2),
                "confidence_level": 0.95,
                "model_confidence": round(model_confidence, 2),
            }
        else:
            return {"predicted_score": round(predicted_score, 2)}

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance for interpretation"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        feature_names = [
            "recent_score_1",
            "recent_score_2",
            "recent_score_3",
            "recent_score_4",
            "recent_score_5",
            "avg_score",
            "trend",
            "score_variance",
            "matematik_avg",
            "fen_avg",
            "turkce_avg",
            "sosyal_avg",
            "test_count",
            "study_hours",
            "attendance",
            "grade_level",
            "multiple_choice_acc",
            "problem_solving_acc",
            "reading_comp_acc",
            "geometry_acc",
            "days_studying",
            "test_frequency",
            "time_management",
            "improvement_rate",
            "consistency",
            "peak_score",
            "exam_readiness",
        ]

        if self.model_type == "rf":
            importances = self.rf_model.feature_importances_
        elif self.model_type == "gb":
            importances = self.gb_model.feature_importances_
        else:  # ensemble
            importances = (
                self.rf_model.feature_importances_ + self.gb_model.feature_importances_
            ) / 2

        return dict(zip(feature_names, importances))

    def generate_recommendations(
        self, student_data: Dict, prediction: Dict
    ) -> List[str]:
        """
        Generate study recommendations based on prediction

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        features = self.prepare_features(student_data)[0]
        predicted_score = prediction["predicted_score"]

        # Check recent performance trend
        recent_scores = features[:5]
        if len([s for s in recent_scores if s > 0]) >= 2:
            trend = features[6]  # Trend feature
            if trend < 0:
                recommendations.append(
                    "📉 Son performansınızda düşüş var. Çalışma yönteminizi gözden geçirin."
                )

        # Check subject weaknesses
        subject_scores = features[8:12]  # matematik, fen, turkce, sosyal
        subjects = ["Matematik", "Fen", "Türkçe", "Sosyal"]
        for subject, score in zip(subjects, subject_scores):
            if score < predicted_score * 0.7 and score > 0:
                recommendations.append(
                    f"⚠️ {subject} alanında güçlenmelisiniz (Mevcut: {score:.1f}, Hedef: {predicted_score*0.9:.1f})"
                )

        # Check test frequency
        test_frequency = features[21]
        if test_frequency < 2:  # Less than 2 tests per week
            recommendations.append(
                "📝 Daha fazla deneme sınavı çözün (Haftada en az 2 deneme öneriyoruz)"
            )

        # Check consistency
        consistency = features[24]
        if consistency < 0.5:
            recommendations.append(
                "🎯 Tutarlılığınızı artırın. Düzenli çalışma programına bağlı kalın."
            )

        # Check time management
        time_management = features[22]
        if time_management > 150:  # More than 2.5 min per question
            recommendations.append(
                "⏱️ Zaman yönetiminizi geliştirin. Soru başına ortalama süreyi azaltın."
            )

        # Check improvement rate
        improvement_rate = features[23]
        if improvement_rate > 0.2:
            recommendations.append("🎉 Harika ilerleme! Mevcut temponuzu koruyun.")
        elif improvement_rate < 0:
            recommendations.append(
                "💪 İlerlemeniz durdu. Çalışma stratejinizi değiştirmeyi deneyin."
            )

        # Predicted score recommendations
        if predicted_score < 400:
            recommendations.append(
                "🔥 Temel konuları pekiştirin. Günlük çalışma sürenizi artırın."
            )
        elif predicted_score < 450:
            recommendations.append("📚 Orta seviye soruları çözmeye odaklanın.")
        elif predicted_score < 490:
            recommendations.append("🚀 İleri seviye sorularla kendinizi zorlayın.")
        else:
            recommendations.append(
                "🏆 Mükemmel! Performansınızı koruyun ve zor sorulara odaklanın."
            )

        return recommendations[:5]  # Return top 5 recommendations

    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")

        model_data = {
            "rf_model": self.rf_model
            if self.model_type in ["rf", "ensemble"]
            else None,
            "gb_model": self.gb_model
            if self.model_type in ["gb", "ensemble"]
            else None,
            "scaler": self.scaler,
            "model_type": self.model_type,
            "is_trained": self.is_trained,
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load trained model from disk"""
        model_data = joblib.load(filepath)

        if model_data["rf_model"]:
            self.rf_model = model_data["rf_model"]
        if model_data["gb_model"]:
            self.gb_model = model_data["gb_model"]

        self.scaler = model_data["scaler"]
        self.model_type = model_data["model_type"]
        self.is_trained = model_data["is_trained"]

        logger.info(f"Model loaded from {filepath}")


# Global instance
_predictor: Optional[ExamScorePredictor] = None


def get_exam_score_predictor() -> ExamScorePredictor:
    """Get or create exam score predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = ExamScorePredictor(model_type="ensemble")
        # Try to load pre-trained model
        try:
            _predictor.load_model("models/exam_score_predictor.pkl")
        except:
            logger.warning("Pre-trained model not found. Model needs training.")
    return _predictor
