"""
AutoIRT Model Training
Train AutoML models to predict IRT parameters (discrimination and difficulty) from question features
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Check if autogluon is available
try:
    from autogluon.tabular import TabularPredictor

    AUTOGLUON_AVAILABLE = True
except ImportError:
    AUTOGLUON_AVAILABLE = False
    print("WARNING: autogluon not installed. Install with: pip install autogluon")

# Fallback to sklearn if autogluon not available
try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AutoIRTTrainer:
    """Train AutoML models for IRT parameter prediction"""

    def __init__(self, models_dir: str = "models"):
        """Initialize trainer"""
        self.models_dir = Path(__file__).parent / models_dir
        self.models_dir.mkdir(exist_ok=True)

        self.predictor_a = None  # Discrimination (a)
        self.predictor_b = None  # Difficulty (b)

    def extract_question_features(
        self, question_text: str, question_data: dict
    ) -> dict:
        """
        Extract features from question for IRT prediction

        Features:
        - Text-based: word_count, sentence_count, avg_word_length
        - Content-based: formula_count, figure_count
        - Metadata: bloom_level_numeric, topic_difficulty
        - Historical: usage_count, correct_rate

        Args:
            question_text: Question text
            question_data: Additional question metadata

        Returns:
            Feature dictionary
        """
        import re

        # Text features
        words = question_text.split()
        sentences = re.split(r"[.!?]+", question_text)

        features = {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_length": np.mean([len(w) for w in words]) if words else 0,
            "char_count": len(question_text),
        }

        # Content features
        features["formula_count"] = question_text.count("$") // 2  # LaTeX formulas
        features["figure_count"] = (
            1
            if "şekil" in question_text.lower() or "grafik" in question_text.lower()
            else 0
        )

        # Bloom's taxonomy (numeric encoding)
        bloom_levels = {
            "remember": 1,
            "understand": 2,
            "apply": 3,
            "analyze": 4,
            "evaluate": 5,
            "create": 6,
        }
        features["bloom_level_numeric"] = bloom_levels.get(
            question_data.get("bloom_level", "apply"), 3
        )

        # Topic difficulty (mock - would come from historical data)
        topic_difficulties = {
            "Matematik": 0.65,
            "Fizik": 0.70,
            "Kimya": 0.60,
            "Biyoloji": 0.55,
            "Türkçe": 0.50,
            "Tarih": 0.45,
            "Coğrafya": 0.50,
            "Felsefe": 0.55,
        }
        features["topic_difficulty"] = topic_difficulties.get(
            question_data.get("konu", "Matematik"), 0.5
        )

        # Historical features (mock - would come from actual usage data)
        features["usage_count"] = question_data.get("usage_count", 0)
        features["correct_rate"] = question_data.get("correct_rate", 0.5)

        return features

    def load_training_data_mock(self) -> pd.DataFrame:
        """
        Load training data with calibrated IRT parameters (MOCK)
        In production, this would load from database with real student responses
        """
        # Generate synthetic training data
        np.random.seed(42)

        n_samples = 1000
        data = []

        for i in range(n_samples):
            # Generate features
            word_count = np.random.randint(20, 200)
            sentence_count = np.random.randint(1, 5)
            formula_count = np.random.randint(0, 5)
            bloom_numeric = np.random.randint(1, 7)
            topic_diff = np.random.uniform(0.3, 0.8)
            usage_count = np.random.randint(50, 500)
            correct_rate = np.random.uniform(0.2, 0.9)

            # Generate IRT parameters (with realistic correlations)
            # Discrimination (a): 0.5 to 2.5
            # - Higher for questions with formulas, higher Bloom level
            irt_a = (
                1.0
                + 0.3 * (bloom_numeric / 6)
                + 0.2 * (formula_count / 5)
                + np.random.normal(0, 0.2)
            )
            irt_a = np.clip(irt_a, 0.5, 2.5)

            # Difficulty (b): -3 to +3
            # - Correlated with topic difficulty, word count, Bloom level
            # - Validated by correct_rate
            irt_b = (
                (topic_diff - 0.5) * 4
                + (bloom_numeric - 3.5) * 0.5
                + np.random.normal(0, 0.5)
            )
            irt_b = np.clip(irt_b, -3, 3)

            # Ensure correct_rate is consistent with difficulty
            # (higher difficulty -> lower correct rate)
            correct_rate = 0.5 + (1 - (irt_b + 3) / 6) * 0.4 + np.random.normal(0, 0.1)
            correct_rate = np.clip(correct_rate, 0.1, 0.95)

            data.append(
                {
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "avg_word_length": word_count / sentence_count
                    if sentence_count > 0
                    else 0,
                    "char_count": word_count * 5,  # rough estimate
                    "formula_count": formula_count,
                    "figure_count": np.random.choice([0, 1], p=[0.7, 0.3]),
                    "bloom_level_numeric": bloom_numeric,
                    "topic_difficulty": topic_diff,
                    "usage_count": usage_count,
                    "correct_rate": correct_rate,
                    "actual_irt_a": irt_a,
                    "actual_irt_b": irt_b,
                }
            )

        df = pd.DataFrame(data)

        print(f"📊 Generated {len(df)} synthetic training samples")
        print(f"   Features: {len(df.columns) - 2}")
        print(
            f"   IRT-a range: [{df['actual_irt_a'].min():.2f}, {df['actual_irt_a'].max():.2f}]"
        )
        print(
            f"   IRT-b range: [{df['actual_irt_b'].min():.2f}, {df['actual_irt_b'].max():.2f}]"
        )

        return df

    def train_with_autogluon(self, df: pd.DataFrame, time_limit: int = 600) -> dict:
        """
        Train models using AutoGluon (if available)

        Args:
            df: Training dataframe
            time_limit: Training time limit in seconds (default: 10 min)

        Returns:
            Training results
        """
        if not AUTOGLUON_AVAILABLE:
            print("❌ AutoGluon not available")
            return None

        print("\n🤖 Training with AutoGluon...")

        # Split data
        train_df = df.copy()

        # Train discrimination (a) model
        print("\n📈 Training IRT-a (discrimination) predictor...")
        self.predictor_a = TabularPredictor(
            label="actual_irt_a",
            path=str(self.models_dir / "autoirt_discrimination"),
            eval_metric="root_mean_squared_error",
        ).fit(
            train_data=train_df,
            time_limit=time_limit,
            presets="best_quality",
            verbosity=2,
        )

        # Train difficulty (b) model
        print("\n📈 Training IRT-b (difficulty) predictor...")
        self.predictor_b = TabularPredictor(
            label="actual_irt_b",
            path=str(self.models_dir / "autoirt_difficulty"),
            eval_metric="root_mean_squared_error",
        ).fit(
            train_data=train_df,
            time_limit=time_limit,
            presets="best_quality",
            verbosity=2,
        )

        # Evaluate
        results = {
            "model_a_rmse": self.predictor_a.evaluate(train_df, silent=True)[
                "root_mean_squared_error"
            ],
            "model_b_rmse": self.predictor_b.evaluate(train_df, silent=True)[
                "root_mean_squared_error"
            ],
            "training_time_limit": time_limit,
            "framework": "AutoGluon",
        }

        return results

    def train_with_sklearn(self, df: pd.DataFrame) -> dict:
        """
        Train models using sklearn RandomForest + GradientBoosting ensemble (fallback)

        Args:
            df: Training dataframe

        Returns:
            Training results
        """
        if not SKLEARN_AVAILABLE:
            print("❌ scikit-learn not available")
            return None

        print("\n🌲 Training with scikit-learn (RandomForest + GradientBoosting)...")

        # Split data
        feature_cols = [
            c for c in df.columns if c not in ["actual_irt_a", "actual_irt_b"]
        ]
        X = df[feature_cols]
        y_a = df["actual_irt_a"]
        y_b = df["actual_irt_b"]

        X_train, X_test, y_a_train, y_a_test = train_test_split(
            X, y_a, test_size=0.2, random_state=42
        )
        _, _, y_b_train, y_b_test = train_test_split(
            X, y_b, test_size=0.2, random_state=42
        )

        # Train discrimination (a) model - ensemble
        print("\n📈 Training IRT-a (discrimination) model...")
        rf_a = RandomForestRegressor(
            n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
        )
        gb_a = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)

        rf_a.fit(X_train, y_a_train)
        gb_a.fit(X_train, y_a_train)

        # Ensemble predictions
        pred_a_rf = rf_a.predict(X_test)
        pred_a_gb = gb_a.predict(X_test)
        pred_a = (pred_a_rf + pred_a_gb) / 2

        rmse_a = np.sqrt(mean_squared_error(y_a_test, pred_a))
        r2_a = r2_score(y_a_test, pred_a)

        # Train difficulty (b) model - ensemble
        print("📈 Training IRT-b (difficulty) model...")
        rf_b = RandomForestRegressor(
            n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
        )
        gb_b = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)

        rf_b.fit(X_train, y_b_train)
        gb_b.fit(X_train, y_b_train)

        # Ensemble predictions
        pred_b_rf = rf_b.predict(X_test)
        pred_b_gb = gb_b.predict(X_test)
        pred_b = (pred_b_rf + pred_b_gb) / 2

        rmse_b = np.sqrt(mean_squared_error(y_b_test, pred_b))
        r2_b = r2_score(y_b_test, pred_b)

        # Save models
        import joblib

        joblib.dump({"rf": rf_a, "gb": gb_a}, self.models_dir / "sklearn_irt_a.pkl")
        joblib.dump({"rf": rf_b, "gb": gb_b}, self.models_dir / "sklearn_irt_b.pkl")

        results = {
            "model_a_rmse": round(rmse_a, 4),
            "model_a_r2": round(r2_a, 4),
            "model_b_rmse": round(rmse_b, 4),
            "model_b_r2": round(r2_b, 4),
            "framework": "scikit-learn (RF + GB ensemble)",
            "test_samples": len(X_test),
        }

        print("\n✅ Training complete!")
        print(f"   IRT-a: RMSE={rmse_a:.4f}, R²={r2_a:.4f}")
        print(f"   IRT-b: RMSE={rmse_b:.4f}, R²={r2_b:.4f}")

        return results

    def train_models(self, use_autogluon: bool = False, time_limit: int = 600) -> dict:
        """
        Train IRT prediction models

        Args:
            use_autogluon: Use AutoGluon (better but slower) vs sklearn (faster)
            time_limit: AutoGluon training time limit (seconds)

        Returns:
            Training results
        """
        print("=" * 80)
        print("AutoIRT MODEL TRAINING")
        print("=" * 80)
        print()

        # Load training data
        print("STEP 1: Load Training Data")
        print("-" * 80)
        df = self.load_training_data_mock()
        print()

        # Train models
        print("STEP 2: Train Models")
        print("-" * 80)

        if use_autogluon and AUTOGLUON_AVAILABLE:
            results = self.train_with_autogluon(df, time_limit)
        else:
            if use_autogluon and not AUTOGLUON_AVAILABLE:
                print(
                    "⚠️  AutoGluon requested but not available. Falling back to sklearn..."
                )
            results = self.train_with_sklearn(df)

        print()

        # Save metadata
        print("STEP 3: Save Model Metadata")
        print("-" * 80)

        metadata = {
            "training_date": datetime.now().isoformat(),
            "training_samples": len(df),
            "features": [
                c for c in df.columns if c not in ["actual_irt_a", "actual_irt_b"]
            ],
            "results": results,
        }

        metadata_path = self.models_dir / "autoirt_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"💾 Saved metadata to: {metadata_path}")
        print()

        # Print results
        print("=" * 80)
        print("✅ TRAINING COMPLETE!")
        print("=" * 80)
        print()
        print("📊 Results:")
        for key, value in results.items():
            print(f"   {key}: {value}")
        print()

        # Quality check
        if (
            results.get("model_a_rmse", 1.0) < 0.2
            and results.get("model_b_rmse", 1.0) < 0.2
        ):
            print("✅ Quality check: PASS (RMSE < 0.2)")
        else:
            print("⚠️  Quality check: Models may need more training data")

        print()
        print("Next steps:")
        print("1. Integrate models into adaptive_testing_service.py")
        print("2. Collect real student response data for better calibration")
        print("3. Re-train with production data")
        print()

        return results


def main():
    """Main entry point"""
    trainer = AutoIRTTrainer()

    # Train models (use sklearn by default for speed)
    results = trainer.train_models(use_autogluon=False)

    if results:
        print("🚀 AutoIRT models are ready!")
    else:
        print("❌ Training failed. Check errors above.")


if __name__ == "__main__":
    main()
