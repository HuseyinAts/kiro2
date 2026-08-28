"""
KIRO2 - Unified Machine Learning Pipeline
=========================================

Bu modül, KIRO2 platformu için birleşik makine öğrenmesi altyapısını sağlar.
TYT, AYT, YKS sınavları için Türkçe eğitim verilerine özel tasarlanmıştır.

Ana ML Pipeline Bileşenleri:
- Veri toplama ve ön işleme
- Feature engineering (özellik mühendisliği)
- Model eğitimi ve validasyonu
- Model deployment ve serving
- A/B testing ve model monitoring
- AutoML ve hyperparameter optimization
- Explainable AI (açıklanabilir yapay zeka)

Türkiye Üniversite Sınavları İçin Özelleştirilmiş:
- TYT/AYT/YKS performans tahmini
- Adaptif öğrenme algoritmaları
- Türkçe NLP ve metin analizi
- Öğrenci davranış analizi
- Üniversite yerleştirme tahmini
"""

import asyncio
import json
import logging
import time
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

warnings.filterwarnings('ignore')

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

# Advanced ML libraries
try:
    import lightgbm as lgb
    import xgboost as xgb
    ADVANCED_ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False
    logging.warning("Advanced ML libraries (XGBoost, LightGBM) not available")

# Deep learning libraries
try:
    import torch.nn as nn
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    logging.warning("PyTorch not available for deep learning models")


class ModelType(Enum):
    """Makine öğrenmesi model türleri"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    NEURAL_NETWORK = "neural_network"
    LSTM = "lstm"
    TRANSFORMER = "transformer"


class TaskType(Enum):
    """ML görev türleri"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    RECOMMENDATION = "recommendation"
    TIME_SERIES = "time_series"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"


class DataType(Enum):
    """Veri türleri"""
    STUDENT_PERFORMANCE = "student_performance"
    EXAM_RESULTS = "exam_results"
    STUDY_BEHAVIOR = "study_behavior"
    CONTENT_INTERACTION = "content_interaction"
    ASSESSMENT_DATA = "assessment_data"
    DEMOGRAPHIC = "demographic"
    TEMPORAL = "temporal"


class ModelStatus(Enum):
    """Model durumları"""
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class MLExperiment:
    """ML deneyi metadata'sı"""
    experiment_id: str
    name: str
    task_type: TaskType
    model_type: ModelType
    dataset_version: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.TRAINING
    created_at: datetime = field(default_factory=datetime.now)
    training_time: Optional[float] = None
    model_size_mb: Optional[float] = None

    def __post_init__(self):
        if not self.experiment_id:
            self.experiment_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:8]}"


@dataclass
class FeatureDefinition:
    """Özellik tanımı"""
    name: str
    feature_type: str  # numerical, categorical, text, datetime
    description: str
    source_columns: List[str] = field(default_factory=list)
    transformation: Optional[str] = None  # log, sqrt, normalize, etc.
    importance_score: Optional[float] = None


@dataclass
class ModelArtifact:
    """Model artifactı"""
    model_id: str
    model_type: ModelType
    task_type: TaskType
    model_object: Any
    scaler: Optional[Any] = None
    feature_columns: List[str] = field(default_factory=list)
    target_column: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class DataProcessor:
    """Veri işleme ve özellik mühendisliği sınıfı"""

    def __init__(self):
        self.feature_definitions: Dict[str, FeatureDefinition] = {}
        self.scalers: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}

    def add_feature_definition(self, feature_def: FeatureDefinition):
        """Özellik tanımı ekle"""
        self.feature_definitions[feature_def.name] = feature_def

    def preprocess_student_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Öğrenci verilerini ön işle"""
        processed_df = df.copy()

        # Temel temizlik
        processed_df = self._clean_basic_data(processed_df)

        # Türkiye'ye özel özellikler
        processed_df = self._engineer_turkish_education_features(processed_df)

        # Zaman bazlı özellikler
        processed_df = self._engineer_temporal_features(processed_df)

        # Davranışsal özellikler
        processed_df = self._engineer_behavioral_features(processed_df)

        return processed_df

    def _clean_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Temel veri temizliği"""
        # Eksik değerleri doldur
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        categorical_columns = df.select_dtypes(include=['object']).columns

        # Sayısal sütunlar için medyan
        for col in numeric_columns:
            df[col] = df[col].fillna(df[col].median())

        # Kategorik sütunlar için mod
        for col in categorical_columns:
            df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else 'unknown')

        # Outlier'ları temizle (IQR yöntemi)
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[col] = df[col].clip(lower_bound, upper_bound)

        return df

    def _engineer_turkish_education_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Türk eğitim sistemine özel özellik mühendisliği"""

        # TYT/AYT puan hesaplamaları
        if 'tyt_turkce' in df.columns and 'tyt_matematik' in df.columns:
            df['tyt_total_raw'] = (
                df.get('tyt_turkce', 0) + df.get('tyt_matematik', 0) +
                df.get('tyt_sosyal', 0) + df.get('tyt_fen', 0)
            )
            df['tyt_net_efficiency'] = df['tyt_total_raw'] / 120.0  # 120 TYT sorusu

        if 'ayt_matematik' in df.columns:
            df['ayt_total_raw'] = (
                df.get('ayt_matematik', 0) + df.get('ayt_fizik', 0) +
                df.get('ayt_kimya', 0) + df.get('ayt_biyoloji', 0)
            )
            df['ayt_net_efficiency'] = df['ayt_total_raw'] / 80.0  # 80 AYT sorusu

        # Bölüm tercih analizi
        if 'department_preference' in df.columns:
            df['prefers_engineering'] = df['department_preference'].str.contains(
                'mühendislik|engineering', case=False, na=False
            ).astype(int)
            df['prefers_medicine'] = df['department_preference'].str.contains(
                'tıp|medicine', case=False, na=False
            ).astype(int)
            df['prefers_social'] = df['department_preference'].str.contains(
                'sosyal|edebiyat|hukuk', case=False, na=False
            ).astype(int)

        # Okul türü özellikleri
        if 'school_type' in df.columns:
            df['is_state_school'] = (df['school_type'] == 'devlet').astype(int)
            df['is_private_school'] = (df['school_type'] == 'özel').astype(int)
            df['is_anadolu_high'] = df['school_type'].str.contains(
                'anadolu|science', case=False, na=False
            ).astype(int)

        # Coğrafi özellikler
        if 'city' in df.columns:
            major_cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya']
            df['is_major_city'] = df['city'].isin(major_cities).astype(int)
            df['city_education_index'] = df['city'].map(self._get_city_education_index())

        return df

    def _engineer_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Zaman bazlı özellik mühendisliği"""

        # Çalışma süresi özellikleri
        if 'study_start_date' in df.columns and 'exam_date' in df.columns:
            df['study_start_date'] = pd.to_datetime(df['study_start_date'])
            df['exam_date'] = pd.to_datetime(df['exam_date'])
            df['preparation_days'] = (df['exam_date'] - df['study_start_date']).dt.days
            df['preparation_weeks'] = df['preparation_days'] / 7

        # Aktivite zamanlaması
        if 'daily_study_hours' in df.columns:
            df['total_study_hours'] = df['daily_study_hours'] * df.get('preparation_days', 365)
            df['study_intensity'] = df['daily_study_hours'] / 24.0  # Günlük oranı

        # Sınav tarihi özellikleri
        if 'exam_date' in df.columns:
            df['exam_date'] = pd.to_datetime(df['exam_date'])
            df['exam_month'] = df['exam_date'].dt.month
            df['exam_quarter'] = df['exam_date'].dt.quarter
            df['is_june_exam'] = (df['exam_month'] == 6).astype(int)  # Ana YKS zamanı

        return df

    def _engineer_behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Davranışsal özellik mühendisliği"""

        # Test çözme davranışları
        if 'tests_completed' in df.columns and 'tests_assigned' in df.columns:
            df['test_completion_rate'] = df['tests_completed'] / df['tests_assigned'].clip(lower=1)
            df['is_consistent_student'] = (df['test_completion_rate'] > 0.8).astype(int)

        # Video ders takip davranışları
        if 'videos_watched' in df.columns and 'video_watch_time' in df.columns:
            df['avg_video_duration'] = df['video_watch_time'] / df['videos_watched'].clip(lower=1)
            df['video_engagement_score'] = np.minimum(df['avg_video_duration'] / 30, 1.0)  # 30dk max

        # Hata analizi davranışları
        if 'wrong_answers' in df.columns and 'total_answers' in df.columns:
            df['error_rate'] = df['wrong_answers'] / df['total_answers'].clip(lower=1)
            df['improvement_potential'] = 1 - df['error_rate']

        # Platform kullanım davranışları
        if 'login_count' in df.columns and 'preparation_days' in df.columns:
            df['avg_daily_logins'] = df['login_count'] / df['preparation_days'].clip(lower=1)
            df['is_regular_user'] = (df['avg_daily_logins'] > 0.7).astype(int)

        return df

    def _get_city_education_index(self) -> Dict[str, float]:
        """Şehir eğitim indeksi (örnek değerler)"""
        return {
            'İstanbul': 0.95, 'Ankara': 0.93, 'İzmir': 0.90, 'Bursa': 0.85,
            'Antalya': 0.83, 'Adana': 0.80, 'Konya': 0.78, 'Gaziantep': 0.76,
            'Kayseri': 0.75, 'Eskişehir': 0.88, 'Trabzon': 0.77, 'Samsun': 0.76
        }

    def scale_features(self, df: pd.DataFrame, scaler_type: str = "standard") -> pd.DataFrame:
        """Özellikleri ölçeklendir"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        if scaler_type == "standard":
            scaler = StandardScaler()
        elif scaler_type == "minmax":
            scaler = MinMaxScaler()
        elif scaler_type == "robust":
            scaler = RobustScaler()
        else:
            raise ValueError(f"Unsupported scaler type: {scaler_type}")

        scaled_data = scaler.fit_transform(df[numeric_columns])
        scaled_df = df.copy()
        scaled_df[numeric_columns] = scaled_data

        # Scaler'ı sakla
        scaler_id = f"scaler_{scaler_type}_{int(time.time())}"
        self.scalers[scaler_id] = scaler

        return scaled_df, scaler_id


class ModelTrainer:
    """Model eğitim sınıfı"""

    def __init__(self):
        self.models: Dict[str, ModelArtifact] = {}
        self.experiments: Dict[str, MLExperiment] = {}

    def train_model(self, experiment: MLExperiment, X_train: pd.DataFrame,
                   y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> ModelArtifact:
        """Model eğit"""
        start_time = time.time()

        try:
            # Model seç ve oluştur
            model = self._create_model(experiment.model_type, experiment.parameters)

            # Modeli eğit
            model.fit(X_train, y_train)

            # Validation tahminleri
            y_pred = model.predict(X_val)

            # Metrikleri hesapla
            metrics = self._calculate_metrics(y_val, y_pred, experiment.task_type)
            experiment.metrics = metrics
            experiment.training_time = time.time() - start_time
            experiment.status = ModelStatus.TRAINED

            # Model artifactı oluştur
            artifact = ModelArtifact(
                model_id=f"model_{experiment.experiment_id}",
                model_type=experiment.model_type,
                task_type=experiment.task_type,
                model_object=model,
                feature_columns=list(X_train.columns),
                target_column=y_train.name,
                metrics=metrics,
                metadata={
                    "experiment_id": experiment.experiment_id,
                    "training_samples": len(X_train),
                    "validation_samples": len(X_val),
                    "parameters": experiment.parameters
                }
            )

            # Saklama
            self.models[artifact.model_id] = artifact
            self.experiments[experiment.experiment_id] = experiment

            logging.info(f"Model trained successfully: {artifact.model_id}")
            logging.info(f"Training metrics: {metrics}")

            return artifact

        except Exception as e:
            experiment.status = ModelStatus.FAILED
            logging.error(f"Model training failed: {e}")
            raise

    def _create_model(self, model_type: ModelType, parameters: Dict[str, Any]):
        """Model oluştur"""
        if model_type == ModelType.LINEAR_REGRESSION:
            return LinearRegression(**parameters)

        elif model_type == ModelType.RANDOM_FOREST:
            return RandomForestRegressor(
                n_estimators=parameters.get('n_estimators', 100),
                max_depth=parameters.get('max_depth', None),
                min_samples_split=parameters.get('min_samples_split', 2),
                min_samples_leaf=parameters.get('min_samples_leaf', 1),
                random_state=42
            )

        elif model_type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingRegressor(
                n_estimators=parameters.get('n_estimators', 100),
                learning_rate=parameters.get('learning_rate', 0.1),
                max_depth=parameters.get('max_depth', 3),
                random_state=42
            )

        elif model_type == ModelType.XGBOOST and ADVANCED_ML_AVAILABLE:
            return xgb.XGBRegressor(
                n_estimators=parameters.get('n_estimators', 100),
                learning_rate=parameters.get('learning_rate', 0.1),
                max_depth=parameters.get('max_depth', 6),
                random_state=42
            )

        elif model_type == ModelType.LIGHTGBM and ADVANCED_ML_AVAILABLE:
            return lgb.LGBMRegressor(
                n_estimators=parameters.get('n_estimators', 100),
                learning_rate=parameters.get('learning_rate', 0.1),
                max_depth=parameters.get('max_depth', -1),
                random_state=42
            )

        elif model_type == ModelType.NEURAL_NETWORK and DEEP_LEARNING_AVAILABLE:
            return self._create_neural_network(parameters)

        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def _create_neural_network(self, parameters: Dict[str, Any]):
        """Neural network oluştur"""
        class SimpleNN(nn.Module):
            def __init__(self, input_size, hidden_sizes, output_size):
                super(SimpleNN, self).__init__()
                layers = []

                # Input layer
                layers.append(nn.Linear(input_size, hidden_sizes[0]))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.2))

                # Hidden layers
                for i in range(len(hidden_sizes) - 1):
                    layers.append(nn.Linear(hidden_sizes[i], hidden_sizes[i + 1]))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(0.2))

                # Output layer
                layers.append(nn.Linear(hidden_sizes[-1], output_size))

                self.network = nn.Sequential(*layers)

            def forward(self, x):
                return self.network(x)

        return SimpleNN(
            input_size=parameters.get('input_size', 10),
            hidden_sizes=parameters.get('hidden_sizes', [64, 32]),
            output_size=parameters.get('output_size', 1)
        )

    def _calculate_metrics(self, y_true, y_pred, task_type: TaskType) -> Dict[str, float]:
        """Metrikleri hesapla"""
        metrics = {}

        if task_type == TaskType.REGRESSION:
            metrics['mse'] = float(mean_squared_error(y_true, y_pred))
            metrics['rmse'] = float(np.sqrt(metrics['mse']))
            metrics['r2'] = float(r2_score(y_true, y_pred))
            metrics['mae'] = float(np.mean(np.abs(y_true - y_pred)))

            # YKS'ye özel metrikler
            metrics['score_difference_mean'] = float(np.mean(np.abs(y_true - y_pred)))
            metrics['within_10_points'] = float(np.mean(np.abs(y_true - y_pred) <= 10))
            metrics['within_25_points'] = float(np.mean(np.abs(y_true - y_pred) <= 25))

        elif task_type == TaskType.CLASSIFICATION:
            metrics['accuracy'] = float(accuracy_score(y_true, (y_pred > 0.5).astype(int)))
            # Diğer classification metrikleri eklenebilir

        return metrics

    def hyperparameter_optimization(self, model_type: ModelType, X_train: pd.DataFrame,
                                  y_train: pd.Series, task_type: TaskType,
                                  param_grid: Dict[str, List], cv_folds: int = 5) -> Dict[str, Any]:
        """Hyperparameter optimizasyonu"""
        base_model = self._create_model(model_type, {})

        grid_search = GridSearchCV(
            base_model, param_grid, cv=cv_folds,
            scoring='neg_mean_squared_error' if task_type == TaskType.REGRESSION else 'accuracy',
            n_jobs=-1, verbose=1
        )

        grid_search.fit(X_train, y_train)

        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }


class ModelInference:
    """Model çıkarım sınıfı"""

    def __init__(self):
        self.loaded_models: Dict[str, ModelArtifact] = {}

    def load_model(self, model_path: str) -> str:
        """Model yükle"""
        try:
            artifact = joblib.load(model_path)
            model_id = artifact.model_id
            self.loaded_models[model_id] = artifact
            logging.info(f"Model loaded: {model_id}")
            return model_id
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            raise

    def predict(self, model_id: str, features: Union[pd.DataFrame, Dict[str, Any]]) -> np.ndarray:
        """Tahmin yap"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Model not loaded: {model_id}")

        artifact = self.loaded_models[model_id]

        # Features'ları DataFrame'e çevir
        if isinstance(features, dict):
            features = pd.DataFrame([features])

        # Özellik sıralamasını kontrol et
        if list(features.columns) != artifact.feature_columns:
            features = features[artifact.feature_columns]

        # Scaling varsa uygula
        if artifact.scaler:
            features_scaled = artifact.scaler.transform(features)
            features = pd.DataFrame(features_scaled, columns=features.columns)

        # Tahmin yap
        predictions = artifact.model_object.predict(features)
        return predictions

    def batch_predict(self, model_id: str, features_batch: pd.DataFrame,
                     batch_size: int = 1000) -> np.ndarray:
        """Toplu tahmin"""
        all_predictions = []

        for i in range(0, len(features_batch), batch_size):
            batch = features_batch.iloc[i:i+batch_size]
            predictions = self.predict(model_id, batch)
            all_predictions.extend(predictions)

        return np.array(all_predictions)


class MLPipeline:
    """Ana ML Pipeline sınıfı"""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.data_processor = DataProcessor()
        self.model_trainer = ModelTrainer()
        self.model_inference = ModelInference()

        # Pipeline yapılandırması
        self.config = {
            "data_split": {"train": 0.7, "val": 0.15, "test": 0.15},
            "scaling_method": "standard",
            "cross_validation_folds": 5,
            "random_seed": 42
        }

        # Model kayıt dizini
        self.model_registry_path = Path("models/registry")
        self.model_registry_path.mkdir(parents=True, exist_ok=True)

    async def run_experiment(self, experiment_config: Dict[str, Any]) -> MLExperiment:
        """ML deneyi çalıştır"""
        # Deney oluştur
        experiment = MLExperiment(
            experiment_id="",
            name=experiment_config["name"],
            task_type=TaskType(experiment_config["task_type"]),
            model_type=ModelType(experiment_config["model_type"]),
            dataset_version=experiment_config.get("dataset_version", "v1.0"),
            parameters=experiment_config.get("parameters", {})
        )

        logging.info(f"Starting ML experiment: {experiment.name}")

        try:
            # 1. Veri yükleme ve ön işleme
            data = await self._load_and_preprocess_data(experiment_config["data_source"])

            # 2. Veri bölme
            X_train, X_val, X_test, y_train, y_val, y_test = self._split_data(
                data, experiment_config["target_column"]
            )

            # 3. Özellik mühendisliği
            X_train_processed = self.data_processor.preprocess_student_data(X_train)
            X_val_processed = self.data_processor.preprocess_student_data(X_val)
            X_test_processed = self.data_processor.preprocess_student_data(X_test)

            # 4. Ölçeklendirme
            X_train_scaled, scaler_id = self.data_processor.scale_features(
                X_train_processed, self.config["scaling_method"]
            )
            X_val_scaled, _ = self.data_processor.scale_features(X_val_processed)
            X_test_scaled, _ = self.data_processor.scale_features(X_test_processed)

            # 5. Model eğitimi
            artifact = self.model_trainer.train_model(
                experiment, X_train_scaled, y_train, X_val_scaled, y_val
            )

            # 6. Test seti değerlendirmesi
            test_predictions = artifact.model_object.predict(X_test_scaled)
            test_metrics = self.model_trainer._calculate_metrics(
                y_test, test_predictions, experiment.task_type
            )

            # Test metriklerini experiment'e ekle
            for key, value in test_metrics.items():
                experiment.metrics[f"test_{key}"] = value

            # 7. Model kaydetme
            await self._save_model_artifact(artifact, scaler_id)

            logging.info(f"Experiment completed: {experiment.experiment_id}")
            logging.info(f"Test metrics: {test_metrics}")

            return experiment

        except Exception as e:
            experiment.status = ModelStatus.FAILED
            logging.error(f"Experiment failed: {e}")
            raise

    async def _load_and_preprocess_data(self, data_source: str) -> pd.DataFrame:
        """Veri yükleme ve temel ön işleme"""
        if data_source.endswith('.csv'):
            data = pd.read_csv(data_source)
        elif data_source.endswith('.parquet'):
            data = pd.read_parquet(data_source)
        else:
            # Veritabanı veya API'den veri yükleme
            data = await self._load_from_database(data_source)

        return data

    async def _load_from_database(self, data_source: str) -> pd.DataFrame:
        """Veritabanından veri yükleme (placeholder)"""
        # Gerçek implementasyonda database bağlantısı kullanılacak
        logging.info(f"Loading data from database: {data_source}")

        # Örnek veri oluştur
        np.random.seed(self.config["random_seed"])
        n_samples = 10000

        data = pd.DataFrame({
            'student_id': range(n_samples),
            'tyt_turkce': np.random.normal(25, 8, n_samples).clip(0, 40),
            'tyt_matematik': np.random.normal(20, 10, n_samples).clip(0, 40),
            'tyt_sosyal': np.random.normal(15, 7, n_samples).clip(0, 20),
            'tyt_fen': np.random.normal(12, 6, n_samples).clip(0, 20),
            'ayt_matematik': np.random.normal(15, 8, n_samples).clip(0, 40),
            'ayt_fizik': np.random.normal(8, 5, n_samples).clip(0, 14),
            'ayt_kimya': np.random.normal(7, 4, n_samples).clip(0, 13),
            'ayt_biyoloji': np.random.normal(9, 5, n_samples).clip(0, 13),
            'daily_study_hours': np.random.exponential(3, n_samples).clip(0.5, 12),
            'preparation_days': np.random.normal(300, 100, n_samples).clip(30, 730),
            'school_type': np.random.choice(['devlet', 'özel', 'anadolu'], n_samples, p=[0.7, 0.2, 0.1]),
            'city': np.random.choice(['İstanbul', 'Ankara', 'İzmir', 'Diğer'], n_samples, p=[0.3, 0.15, 0.1, 0.45]),
            'target_score': np.random.normal(350, 80, n_samples).clip(150, 500)
        })

        return data

    def _split_data(self, data: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, ...]:
        """Veriyi train/val/test olarak böl"""
        X = data.drop(columns=[target_column])
        y = data[target_column]

        # İlk bölme: train + val, test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=self.config["data_split"]["test"],
            random_state=self.config["random_seed"]
        )

        # İkinci bölme: train, val
        val_size = self.config["data_split"]["val"] / (1 - self.config["data_split"]["test"])
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size,
            random_state=self.config["random_seed"]
        )

        logging.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

        return X_train, X_val, X_test, y_train, y_val, y_test

    async def _save_model_artifact(self, artifact: ModelArtifact, scaler_id: str):
        """Model artifactını kaydet"""
        # Scaler'ı artifact'a ekle
        if scaler_id in self.data_processor.scalers:
            artifact.scaler = self.data_processor.scalers[scaler_id]

        # Model dosya yolu
        model_path = self.model_registry_path / f"{artifact.model_id}.joblib"

        # Model kaydet
        joblib.dump(artifact, model_path)

        # Metadata kaydet
        metadata = {
            'model_id': artifact.model_id,
            'model_type': artifact.model_type.value,
            'task_type': artifact.task_type.value,
            'metrics': artifact.metrics,
            'feature_columns': artifact.feature_columns,
            'created_at': artifact.created_at.isoformat(),
            'file_path': str(model_path)
        }

        metadata_path = self.model_registry_path / f"{artifact.model_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logging.info(f"Model artifact saved: {model_path}")

    def get_model_leaderboard(self, task_type: Optional[TaskType] = None,
                             metric: str = "r2") -> pd.DataFrame:
        """Model liderlik tablosu"""
        models_data = []

        for artifact in self.model_trainer.models.values():
            if task_type and artifact.task_type != task_type:
                continue

            models_data.append({
                'model_id': artifact.model_id,
                'model_type': artifact.model_type.value,
                'task_type': artifact.task_type.value,
                'metric_value': artifact.metrics.get(metric, 0),
                'created_at': artifact.created_at,
                'training_samples': artifact.metadata.get('training_samples', 0)
            })

        df = pd.DataFrame(models_data)
        if not df.empty:
            df = df.sort_values('metric_value', ascending=False)

        return df


# === KIRO2 İçin Özelleştirilmiş Pipeline ===

class KIRO2MLPipeline(MLPipeline):
    """KIRO2 için özelleştirilmiş ML Pipeline"""

    def __init__(self):
        super().__init__("kiro2_main_pipeline")
        self._initialize_kiro2_features()

    def _initialize_kiro2_features(self):
        """KIRO2'ye özel özellik tanımları"""

        # TYT özellikleri
        self.data_processor.add_feature_definition(FeatureDefinition(
            name="tyt_efficiency_score",
            feature_type="numerical",
            description="TYT sorularını doğru çözme oranı",
            source_columns=["tyt_turkce", "tyt_matematik", "tyt_sosyal", "tyt_fen"],
            transformation="normalize"
        ))

        # AYT özellikleri
        self.data_processor.add_feature_definition(FeatureDefinition(
            name="ayt_sayisal_strength",
            feature_type="numerical",
            description="AYT sayısal bölüm güçlülük skoru",
            source_columns=["ayt_matematik", "ayt_fizik", "ayt_kimya"]
        ))

        # Davranışsal özellikler
        self.data_processor.add_feature_definition(FeatureDefinition(
            name="study_consistency",
            feature_type="numerical",
            description="Çalışma tutarlılık skoru",
            source_columns=["daily_study_hours", "login_frequency", "test_completion_rate"]
        ))

    async def predict_yks_score(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """YKS puan tahmini"""
        # En iyi modeli bul
        leaderboard = self.get_model_leaderboard(TaskType.REGRESSION, "r2")
        if leaderboard.empty:
            raise ValueError("No trained models available for YKS score prediction")

        best_model_id = leaderboard.iloc[0]['model_id']

        # Tahmin yap
        features_df = pd.DataFrame([student_data])
        processed_features = self.data_processor.preprocess_student_data(features_df)

        prediction = self.model_inference.predict(best_model_id, processed_features)

        # Sonuçları yorumla
        predicted_score = float(prediction[0])
        confidence_interval = self._calculate_confidence_interval(predicted_score, best_model_id)
        recommendations = self._generate_recommendations(student_data, predicted_score)

        return {
            'predicted_yks_score': predicted_score,
            'confidence_interval': confidence_interval,
            'score_range': {
                'min': max(150, predicted_score - confidence_interval),
                'max': min(500, predicted_score + confidence_interval)
            },
            'percentile_estimate': self._score_to_percentile(predicted_score),
            'improvement_potential': self._calculate_improvement_potential(student_data),
            'recommendations': recommendations,
            'model_info': {
                'model_id': best_model_id,
                'model_accuracy': leaderboard.iloc[0]['metric_value']
            }
        }

    def _calculate_confidence_interval(self, predicted_score: float, model_id: str) -> float:
        """Güven aralığı hesapla"""
        artifact = self.model_trainer.models.get(model_id)
        if artifact and 'rmse' in artifact.metrics:
            return artifact.metrics['rmse'] * 1.96  # %95 güven aralığı
        return 25.0  # Varsayılan değer

    def _score_to_percentile(self, score: float) -> float:
        """YKS puanını yüzdelik dilime çevir (yaklaşık)"""
        # Yaklaşık YKS puan dağılımı
        if score >= 450:
            return 99.0
        elif score >= 400:
            return 95.0 + (score - 400) / 50 * 4
        elif score >= 350:
            return 80.0 + (score - 350) / 50 * 15
        elif score >= 300:
            return 50.0 + (score - 300) / 50 * 30
        elif score >= 250:
            return 20.0 + (score - 250) / 50 * 30
        else:
            return max(1.0, (score - 150) / 100 * 19)

    def _calculate_improvement_potential(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """İyileştirme potansiyeli hesapla"""
        current_efficiency = (
            student_data.get('tyt_turkce', 0) + student_data.get('tyt_matematik', 0) +
            student_data.get('ayt_matematik', 0)
        ) / 120  # Toplam ana sorular

        study_intensity = student_data.get('daily_study_hours', 0) / 8  # 8 saat max
        time_remaining = max(0, student_data.get('days_to_exam', 100)) / 365

        improvement_score = (1 - current_efficiency) * study_intensity * time_remaining

        return {
            'improvement_score': min(1.0, improvement_score),
            'potential_score_gain': improvement_score * 100,  # Puan artış potansiyeli
            'focus_areas': self._identify_focus_areas(student_data)
        }

    def _identify_focus_areas(self, student_data: Dict[str, Any]) -> List[str]:
        """Odaklanması gereken alanları belirle"""
        areas = []

        # TYT analizi
        tyt_scores = {
            'Türkçe': student_data.get('tyt_turkce', 0) / 40,
            'Matematik': student_data.get('tyt_matematik', 0) / 40,
            'Sosyal': student_data.get('tyt_sosyal', 0) / 20,
            'Fen': student_data.get('tyt_fen', 0) / 20
        }

        avg_tyt = sum(tyt_scores.values()) / len(tyt_scores)
        for subject, score in tyt_scores.items():
            if score < avg_tyt - 0.15:  # %15'ten fazla geride
                areas.append(f"TYT {subject}")

        # AYT analizi
        if student_data.get('ayt_matematik', 0) < 20:  # 40'ın yarısı
            areas.append("AYT Matematik")

        return areas[:3]  # En fazla 3 alan

    def _generate_recommendations(self, student_data: Dict[str, Any], predicted_score: float) -> List[str]:
        """Kişiselleştirilmiş öneriler oluştur"""
        recommendations = []

        # Puan bazlı öneriler
        if predicted_score < 300:
            recommendations.append("Temel konulara odaklanın ve günlük çalışma sürenizi artırın")
            recommendations.append("TYT sorularında daha fazla pratik yapın")
        elif predicted_score < 400:
            recommendations.append("AYT konularına daha fazla zaman ayırın")
            recommendations.append("Zayıf olduğunuz konularda derinlemesine çalışma yapın")
        else:
            recommendations.append("Mevcut seviyenizi koruyun ve hız odaklı çalışın")
            recommendations.append("Deneme sınavlarına odaklanarak sınav stratejinizi geliştirin")

        # Çalışma süresi önerileri
        daily_hours = student_data.get('daily_study_hours', 0)
        if daily_hours < 4:
            recommendations.append("Günlük çalışma sürenizi en az 6 saate çıkarın")
        elif daily_hours > 10:
            recommendations.append("Çalışma sürenizi optimize edin, kalite odaklı çalışma yapın")

        return recommendations[:4]  # En fazla 4 öneri


# === Örnek Kullanım ===

async def example_kiro2_ml_pipeline():
    """KIRO2 ML Pipeline örnek kullanımı"""

    # Pipeline'ı başlat
    pipeline = KIRO2MLPipeline()

    # Deney yapılandırması
    experiment_config = {
        "name": "YKS Score Prediction - Random Forest",
        "task_type": "regression",
        "model_type": "random_forest",
        "data_source": "student_performance_data.csv",
        "target_column": "target_score",
        "parameters": {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_split": 5
        }
    }

    print("[ROCKET] KIRO2 ML Pipeline başlatılıyor...")

    # Deney çalıştır
    experiment = await pipeline.run_experiment(experiment_config)

    print(f"[CHECK] Deney tamamlandı: {experiment.name}")
    print(f"[CHART] R² Skoru: {experiment.metrics.get('r2', 0):.4f}")
    print(f"📏 RMSE: {experiment.metrics.get('rmse', 0):.2f}")
    print(f"⏱️ Eğitim süresi: {experiment.training_time:.2f} saniye")

    # Model liderlik tablosu
    leaderboard = pipeline.get_model_leaderboard()
    print("\n[CLIPBOARD] Model Liderlik Tablosu:")
    print(leaderboard.head())

    # Örnek öğrenci verisi ile tahmin
    sample_student = {
        'tyt_turkce': 32,
        'tyt_matematik': 28,
        'tyt_sosyal': 16,
        'tyt_fen': 14,
        'ayt_matematik': 25,
        'ayt_fizik': 10,
        'ayt_kimya': 8,
        'ayt_biyoloji': 11,
        'daily_study_hours': 6,
        'preparation_days': 240,
        'school_type': 'anadolu',
        'city': 'İstanbul',
        'days_to_exam': 90
    }

    # YKS puan tahmini
    try:
        prediction_result = await pipeline.predict_yks_score(sample_student)

        print(f"\n[TARGET] YKS Puan Tahmini:")
        print(f"Tahmin edilen puan: {prediction_result['predicted_yks_score']:.1f}")
        print(f"Puan aralığı: {prediction_result['score_range']['min']:.0f} - {prediction_result['score_range']['max']:.0f}")
        print(f"Yüzdelik dilim: {prediction_result['percentile_estimate']:.1f}")
        print(f"İyileştirme potansiyeli: {prediction_result['improvement_potential']['potential_score_gain']:.0f} puan")

        print(f"\n[BULB] Öneriler:")
        for i, rec in enumerate(prediction_result['recommendations'], 1):
            print(f"{i}. {rec}")

        print(f"\n[MAG] Odaklanılması gereken alanlar:")
        for area in prediction_result['improvement_potential']['focus_areas']:
            print(f"• {area}")

    except ValueError as e:
        print(f"⚠️ Tahmin hatası: {e}")

    print("\n✨ KIRO2 ML Pipeline örneği tamamlandı!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_kiro2_ml_pipeline())
