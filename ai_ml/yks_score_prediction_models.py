"""
KIRO2 - YKS Score Prediction Models
===================================

Bu modül, öğrencilerin TYT, AYT ve genel YKS puanlarını tahmin etmek için
gelişmiş makine öğrenmesi modellerini içerir.

YKS Puan Tahmin Modelleri:
- TYT Puan Tahmini (Temel Yeterlilik Testi)
- AYT Puan Tahmini (Alan Yeterlilik Testi)
- YKS Genel Puan Tahmini
- Üniversite Yerleştirme Tahmini
- Bölüm Tercih Optimizasyonu
- Zaman Serisi Performans Tahmini
- Ensemble Model Kombinasyonları

Türkiye YKS Sistemi Özellikleri:
- 2018 sonrası YKS sistemi (TYT + AYT)
- Puan hesaplama formülleri (SAY, SÖZ, EA, DİL)
- Yerleştirme puan türleri
- Katsayı ve taban puan hesaplamaları
- İstatistiksel normalizasyon
"""

import asyncio
import json
import logging
import math
import pickle
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
    VotingRegressor,
)
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, train_test_split
from sklearn.preprocessing import RobustScaler, StandardScaler

warnings.filterwarnings('ignore')

# Advanced ML libraries
try:
    import lightgbm as lgb
    import xgboost as xgb
    ADVANCED_ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False
    logging.warning("XGBoost/LightGBM not available")

# Deep learning
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    logging.warning("PyTorch not available")


class ExamType(Enum):
    """Sınav türleri"""
    TYT = "tyt"
    AYT_SAY = "ayt_sayisal"
    AYT_SOZ = "ayt_sozel"
    AYT_EA = "ayt_esit_agirlik"
    YDT = "ydt"
    YKS_OVERALL = "yks_genel"


class ScoreType(Enum):
    """Puan türleri"""
    HAM_PUAN = "ham_puan"          # Ham puan
    STANDART_PUAN = "standart_puan" # Standart puan
    YKS_PUAN = "yks_puan"          # YKS puanı (150-500)
    YERLESTIRME_PUAN = "yerlestirme_puan"  # Yerleştirme puanı


class PredictionConfidence(Enum):
    """Tahmin güveni seviyeleri"""
    VERY_LOW = "very_low"     # < %60
    LOW = "low"               # %60-70
    MEDIUM = "medium"         # %70-80
    HIGH = "high"             # %80-90
    VERY_HIGH = "very_high"   # > %90


@dataclass
class YKSScoreComponents:
    """YKS puan bileşenleri"""
    # TYT Ham Puanlar
    tyt_turkce_dogru: int = 0
    tyt_turkce_yanlis: int = 0
    tyt_matematik_dogru: int = 0
    tyt_matematik_yanlis: int = 0
    tyt_fen_dogru: int = 0
    tyt_fen_yanlis: int = 0
    tyt_sosyal_dogru: int = 0
    tyt_sosyal_yanlis: int = 0

    # AYT Ham Puanlar
    ayt_matematik_dogru: int = 0
    ayt_matematik_yanlis: int = 0
    ayt_fizik_dogru: int = 0
    ayt_fizik_yanlis: int = 0
    ayt_kimya_dogru: int = 0
    ayt_kimya_yanlis: int = 0
    ayt_biyoloji_dogru: int = 0
    ayt_biyoloji_yanlis: int = 0

    # AYT Sözel
    ayt_edebiyat_dogru: int = 0
    ayt_edebiyat_yanlis: int = 0
    ayt_tarih1_dogru: int = 0
    ayt_tarih1_yanlis: int = 0
    ayt_cografya1_dogru: int = 0
    ayt_cografya1_yanlis: int = 0

    # YDT (Yabancı Dil)
    ydt_dogru: int = 0
    ydt_yanlis: int = 0

    @property
    def tyt_net_turkce(self) -> float:
        return max(0, self.tyt_turkce_dogru - (self.tyt_turkce_yanlis / 4))

    @property
    def tyt_net_matematik(self) -> float:
        return max(0, self.tyt_matematik_dogru - (self.tyt_matematik_yanlis / 4))

    @property
    def tyt_net_fen(self) -> float:
        return max(0, self.tyt_fen_dogru - (self.tyt_fen_yanlis / 4))

    @property
    def tyt_net_sosyal(self) -> float:
        return max(0, self.tyt_sosyal_dogru - (self.tyt_sosyal_yanlis / 4))

    @property
    def tyt_toplam_net(self) -> float:
        return self.tyt_net_turkce + self.tyt_net_matematik + self.tyt_net_fen + self.tyt_net_sosyal

    @property
    def ayt_sayisal_net(self) -> float:
        matematik = max(0, self.ayt_matematik_dogru - (self.ayt_matematik_yanlis / 4))
        fizik = max(0, self.ayt_fizik_dogru - (self.ayt_fizik_yanlis / 4))
        kimya = max(0, self.ayt_kimya_dogru - (self.ayt_kimya_yanlis / 4))
        biyoloji = max(0, self.ayt_biyoloji_dogru - (self.ayt_biyoloji_yanlis / 4))
        return matematik + fizik + kimya + biyoloji


@dataclass
class StudentPerformanceProfile:
    """Öğrenci performans profili"""
    student_id: str

    # Demografik bilgiler
    school_type: str = "devlet"  # devlet, özel, anadolu
    city: str = "İstanbul"
    grade: int = 12

    # Çalışma alışkanlıkları
    daily_study_hours: float = 4.0
    preparation_months: int = 12
    mock_exam_count: int = 10

    # Platform kullanım istatistikleri
    total_questions_solved: int = 0
    correct_answer_rate: float = 0.0
    avg_response_time_seconds: float = 60.0
    subjects_studied: List[str] = field(default_factory=list)

    # Son performans metrikleri
    recent_tyt_performance: float = 0.0  # 0-1 arası
    recent_ayt_performance: float = 0.0
    improvement_trend: float = 0.0  # Pozitif = gelişim, Negatif = düşüş
    consistency_score: float = 0.0  # 0-1 arası tutarlılık

    # Motivasyon ve davranış
    login_frequency_per_week: float = 5.0
    goal_completion_rate: float = 0.0
    help_seeking_behavior: float = 0.0  # 0-1 arası


@dataclass
class ScorePrediction:
    """Puan tahmini sonucu"""
    student_id: str
    exam_type: ExamType
    score_type: ScoreType

    # Tahmin değerleri
    predicted_score: float
    confidence_interval: Tuple[float, float]  # (alt sınır, üst sınır)
    confidence_level: PredictionConfidence

    # Model bilgileri
    model_name: str
    model_accuracy: float
    feature_importance: Dict[str, float] = field(default_factory=dict)

    # Tahmin detayları
    prediction_date: datetime = field(default_factory=datetime.now)
    data_points_used: int = 0

    # İstatistiksel bilgiler
    percentile_estimate: float = 0.0  # 0-100 arası yüzdelik dilim
    probability_above_300: float = 0.0
    probability_above_350: float = 0.0
    probability_above_400: float = 0.0
    probability_above_450: float = 0.0


class YKSScoreCalculator:
    """YKS Puan Hesaplama Motoru"""

    def __init__(self):
        # 2024 YKS katsayıları (örnek değerler - gerçek değerler ÖSYM'den alınacak)
        self.coefficients = {
            ExamType.TYT: {
                'turkce': 3.0,
                'matematik': 3.0,
                'fen': 3.0,
                'sosyal': 3.0
            },
            ExamType.AYT_SAY: {
                'matematik': 3.0,
                'fizik': 2.0,
                'kimya': 2.0,
                'biyoloji': 2.0
            },
            ExamType.AYT_SOZ: {
                'edebiyat': 3.0,
                'tarih': 2.0,
                'cografya': 2.0
            }
        }

        # Puan dönüşüm parametreleri
        self.score_parameters = {
            'tyt_base_score': 150,
            'tyt_max_score': 500,
            'ayt_coefficient': 0.8,
            'university_placement_coefficient': 0.12
        }

    def calculate_tyt_score(self, components: YKSScoreComponents,
                          statistical_params: Optional[Dict] = None) -> float:
        """TYT puanını hesapla"""

        # Net puanları al
        net_scores = {
            'turkce': components.tyt_net_turkce,
            'matematik': components.tyt_net_matematik,
            'fen': components.tyt_net_fen,
            'sosyal': components.tyt_net_sosyal
        }

        # Ağırlıklı toplam
        weighted_sum = sum(
            net_scores[subject] * self.coefficients[ExamType.TYT][subject]
            for subject in net_scores
        )

        # Statistical normalization (gerçekte ÖSYM'den gelecek parametreler)
        if statistical_params:
            mean = statistical_params.get('mean', 50)
            std = statistical_params.get('std', 15)
            normalized_score = (weighted_sum - mean) / std
            # 150-500 arasına ölçekle
            tyt_score = 150 + (normalized_score + 3) * (500 - 150) / 6
        else:
            # Basit ölçekleme (örnek)
            max_possible = 120 * 3  # 40 soru * 3 katsayı (her ders için)
            tyt_score = 150 + (weighted_sum / max_possible) * (500 - 150)

        return max(150, min(500, tyt_score))

    def calculate_ayt_score(self, components: YKSScoreComponents,
                          ayt_type: ExamType,
                          statistical_params: Optional[Dict] = None) -> float:
        """AYT puanını hesapla"""

        if ayt_type == ExamType.AYT_SAY:
            net_scores = {
                'matematik': max(0, components.ayt_matematik_dogru - components.ayt_matematik_yanlis / 4),
                'fizik': max(0, components.ayt_fizik_dogru - components.ayt_fizik_yanlis / 4),
                'kimya': max(0, components.ayt_kimya_dogru - components.ayt_kimya_yanlis / 4),
                'biyoloji': max(0, components.ayt_biyoloji_dogru - components.ayt_biyoloji_yanlis / 4)
            }
            coeffs = self.coefficients[ExamType.AYT_SAY]
        elif ayt_type == ExamType.AYT_SOZ:
            net_scores = {
                'edebiyat': max(0, components.ayt_edebiyat_dogru - components.ayt_edebiyat_yanlis / 4),
                'tarih': max(0, components.ayt_tarih1_dogru - components.ayt_tarih1_yanlis / 4),
                'cografya': max(0, components.ayt_cografya1_dogru - components.ayt_cografya1_yanlis / 4)
            }
            coeffs = self.coefficients[ExamType.AYT_SOZ]
        else:
            return 0.0

        # Ağırlıklı toplam
        weighted_sum = sum(net_scores[subject] * coeffs[subject] for subject in net_scores)

        # Normalizasyon ve ölçekleme (basit yaklaşım)
        if ayt_type == ExamType.AYT_SAY:
            max_possible = (40 * 3) + (14 * 2) + (13 * 2) + (13 * 2)  # Matematik + Fizik + Kimya + Biyoloji
        else:
            max_possible = (24 * 3) + (10 * 2) + (6 * 2)  # Edebiyat + Tarih + Coğrafya

        ayt_score = 150 + (weighted_sum / max_possible) * (500 - 150)
        return max(150, min(500, ayt_score))

    def calculate_placement_score(self, tyt_score: float, ayt_score: float,
                                program_type: str = "sayisal") -> float:
        """Yerleştirme puanını hesapla"""

        # Program türüne göre katsayılar
        if program_type == "sayisal":
            tyt_coeff = 0.4
            ayt_coeff = 0.6
        elif program_type == "sozel":
            tyt_coeff = 0.4
            ayt_coeff = 0.6
        elif program_type == "esit_agirlik":
            tyt_coeff = 0.5
            ayt_coeff = 0.5
        else:
            tyt_coeff = 0.5
            ayt_coeff = 0.5

        placement_score = (tyt_score * tyt_coeff) + (ayt_score * ayt_coeff)
        return max(150, min(500, placement_score))


class YKSFeatureEngineering:
    """YKS özellik mühendisliği"""

    @staticmethod
    def create_features_from_profile(profile: StudentPerformanceProfile) -> Dict[str, float]:
        """Öğrenci profilinden özellikler oluştur"""
        features = {}

        # Temel demografik özellikler
        features['school_type_devlet'] = 1 if profile.school_type == 'devlet' else 0
        features['school_type_ozel'] = 1 if profile.school_type == 'özel' else 0
        features['school_type_anadolu'] = 1 if profile.school_type == 'anadolu' else 0

        # Şehir özellikleri (büyük şehir indeksi)
        major_cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya']
        features['is_major_city'] = 1 if profile.city in major_cities else 0

        # Çalışma alışkanlıkları
        features['daily_study_hours'] = profile.daily_study_hours
        features['study_intensity'] = min(1.0, profile.daily_study_hours / 8)  # Normalize to 0-1
        features['preparation_months'] = profile.preparation_months
        features['preparation_weeks'] = profile.preparation_months * 4.33

        # Platform kullanım özellikleri
        features['total_questions'] = profile.total_questions_solved
        features['questions_per_day'] = profile.total_questions_solved / max(1, profile.preparation_months * 30)
        features['accuracy_rate'] = profile.correct_answer_rate
        features['avg_response_time'] = profile.avg_response_time_seconds

        # Performans özellikleri
        features['tyt_performance'] = profile.recent_tyt_performance
        features['ayt_performance'] = profile.recent_ayt_performance
        features['improvement_trend'] = profile.improvement_trend
        features['consistency_score'] = profile.consistency_score

        # Davranışsal özellikler
        features['login_frequency'] = profile.login_frequency_per_week
        features['goal_completion'] = profile.goal_completion_rate
        features['help_seeking'] = profile.help_seeking_behavior

        # Türetilmiş özellikler
        features['study_efficiency'] = profile.correct_answer_rate * features['study_intensity']
        features['engagement_score'] = (features['login_frequency'] / 7) * features['goal_completion']
        features['readiness_score'] = (features['tyt_performance'] + features['ayt_performance']) / 2

        # Zaman bazlı özellikler
        features['days_per_question'] = max(0.01, (profile.preparation_months * 30) / max(1, profile.total_questions_solved))
        features['mock_exam_frequency'] = profile.mock_exam_count / max(1, profile.preparation_months)

        return features

    @staticmethod
    def create_features_from_components(components: YKSScoreComponents) -> Dict[str, float]:
        """YKS bileşenlerinden özellikler oluştur"""
        features = {}

        # TYT net puanlar
        features['tyt_turkce_net'] = components.tyt_net_turkce
        features['tyt_matematik_net'] = components.tyt_net_matematik
        features['tyt_fen_net'] = components.tyt_net_fen
        features['tyt_sosyal_net'] = components.tyt_net_sosyal
        features['tyt_toplam_net'] = components.tyt_toplam_net

        # AYT net puanlar
        features['ayt_matematik_net'] = max(0, components.ayt_matematik_dogru - components.ayt_matematik_yanlis / 4)
        features['ayt_fizik_net'] = max(0, components.ayt_fizik_dogru - components.ayt_fizik_yanlis / 4)
        features['ayt_kimya_net'] = max(0, components.ayt_kimya_dogru - components.ayt_kimya_yanlis / 4)
        features['ayt_biyoloji_net'] = max(0, components.ayt_biyoloji_dogru - components.ayt_biyoloji_yanlis / 4)
        features['ayt_sayisal_net'] = components.ayt_sayisal_net

        # Doğruluk oranları
        if components.tyt_turkce_dogru + components.tyt_turkce_yanlis > 0:
            features['tyt_turkce_accuracy'] = components.tyt_turkce_dogru / (components.tyt_turkce_dogru + components.tyt_turkce_yanlis)
        else:
            features['tyt_turkce_accuracy'] = 0.0

        if components.tyt_matematik_dogru + components.tyt_matematik_yanlis > 0:
            features['tyt_matematik_accuracy'] = components.tyt_matematik_dogru / (components.tyt_matematik_dogru + components.tyt_matematik_yanlis)
        else:
            features['tyt_matematik_accuracy'] = 0.0

        # Çözme oranları (kaç soru çözmüş)
        features['tyt_turkce_attempted'] = components.tyt_turkce_dogru + components.tyt_turkce_yanlis
        features['tyt_matematik_attempted'] = components.tyt_matematik_dogru + components.tyt_matematik_yanlis
        features['tyt_total_attempted'] = (features['tyt_turkce_attempted'] + features['tyt_matematik_attempted'] +
                                         components.tyt_fen_dogru + components.tyt_fen_yanlis +
                                         components.tyt_sosyal_dogru + components.tyt_sosyal_yanlis)

        # Güç indeksleri
        features['math_strength'] = (features['tyt_matematik_net'] + features['ayt_matematik_net']) / 2
        features['science_strength'] = (features['ayt_fizik_net'] + features['ayt_kimya_net'] + features['ayt_biyoloji_net']) / 3
        features['language_strength'] = features['tyt_turkce_net']

        return features


class TYTPredictionModel:
    """TYT Puan Tahmin Modeli"""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.model_metrics = {}

    def prepare_training_data(self, profiles: List[StudentPerformanceProfile],
                            actual_scores: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        """Eğitim verilerini hazırla"""

        features_list = []
        for profile in profiles:
            features = YKSFeatureEngineering.create_features_from_profile(profile)
            features_list.append(features)

        # DataFrame'e çevir
        df_features = pd.DataFrame(features_list)

        # Özellik sütunlarını kaydet
        self.feature_columns = list(df_features.columns)

        # NaN değerleri doldur
        df_features = df_features.fillna(0)

        return df_features.values, np.array(actual_scores)

    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Çoklu model eğitimi"""

        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Ölçeklendirme
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['robust'] = scaler

        # Model tanımları
        models_to_train = {
            'ridge': Ridge(alpha=1.0),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }

        # Advanced ML modelleri
        if ADVANCED_ML_AVAILABLE:
            models_to_train.update({
                'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'lightgbm': lgb.LGBMRegressor(n_estimators=100, random_state=42)
            })

        # Modelleri eğit ve değerlendir
        results = {}
        for model_name, model in models_to_train.items():
            # Eğitim
            if model_name in ['ridge', 'elastic_net']:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

            # Değerlendirme
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            results[model_name] = {
                'mae': mae,
                'mse': mse,
                'rmse': np.sqrt(mse),
                'r2': r2
            }

            # Modeli kaydet
            self.models[model_name] = model
            self.model_metrics[model_name] = results[model_name]

            logging.info(f"{model_name} - MAE: {mae:.2f}, RMSE: {np.sqrt(mse):.2f}, R²: {r2:.4f}")

        # Ensemble model oluştur
        if len(self.models) >= 3:
            ensemble_models = [(name, model) for name, model in self.models.items()
                             if name not in ['ridge', 'elastic_net']][:3]

            ensemble = VotingRegressor(ensemble_models)
            ensemble.fit(X_train, y_train)
            y_pred_ensemble = ensemble.predict(X_test)

            mae_ensemble = mean_absolute_error(y_test, y_pred_ensemble)
            r2_ensemble = r2_score(y_test, y_pred_ensemble)

            self.models['ensemble'] = ensemble
            self.model_metrics['ensemble'] = {
                'mae': mae_ensemble,
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_ensemble)),
                'r2': r2_ensemble
            }

            logging.info(f"Ensemble - MAE: {mae_ensemble:.2f}, R²: {r2_ensemble:.4f}")

        return results

    def predict_tyt_score(self, profile: StudentPerformanceProfile,
                         model_name: str = 'ensemble') -> ScorePrediction:
        """TYT puanını tahmin et"""

        if model_name not in self.models:
            model_name = 'ensemble' if 'ensemble' in self.models else list(self.models.keys())[0]

        model = self.models[model_name]

        # Özellikler oluştur
        features = YKSFeatureEngineering.create_features_from_profile(profile)

        # DataFrame'e çevir ve eksik sütunları doldur
        feature_df = pd.DataFrame([features])
        for col in self.feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0

        feature_df = feature_df[self.feature_columns]
        X = feature_df.values

        # Ölçeklendirme (gerekirse)
        if model_name in ['ridge', 'elastic_net'] and 'robust' in self.scalers:
            X = self.scalers['robust'].transform(X)

        # Tahmin
        predicted_score = model.predict(X)[0]

        # Güven aralığı hesapla
        model_rmse = self.model_metrics[model_name]['rmse']
        confidence_interval = (
            max(150, predicted_score - 1.96 * model_rmse),
            min(500, predicted_score + 1.96 * model_rmse)
        )

        # Güven seviyesi
        model_r2 = self.model_metrics[model_name]['r2']
        if model_r2 > 0.9:
            confidence_level = PredictionConfidence.VERY_HIGH
        elif model_r2 > 0.8:
            confidence_level = PredictionConfidence.HIGH
        elif model_r2 > 0.7:
            confidence_level = PredictionConfidence.MEDIUM
        elif model_r2 > 0.6:
            confidence_level = PredictionConfidence.LOW
        else:
            confidence_level = PredictionConfidence.VERY_LOW

        # Yüzdelik dilim tahmini (yaklaşık)
        percentile = self._score_to_percentile(predicted_score, ExamType.TYT)

        return ScorePrediction(
            student_id=profile.student_id,
            exam_type=ExamType.TYT,
            score_type=ScoreType.YKS_PUAN,
            predicted_score=predicted_score,
            confidence_interval=confidence_interval,
            confidence_level=confidence_level,
            model_name=model_name,
            model_accuracy=model_r2,
            percentile_estimate=percentile,
            probability_above_300=self._calculate_probability_above_threshold(predicted_score, model_rmse, 300),
            probability_above_350=self._calculate_probability_above_threshold(predicted_score, model_rmse, 350),
            probability_above_400=self._calculate_probability_above_threshold(predicted_score, model_rmse, 400),
            probability_above_450=self._calculate_probability_above_threshold(predicted_score, model_rmse, 450)
        )

    def _score_to_percentile(self, score: float, exam_type: ExamType) -> float:
        """Puanı yüzdelik dilime çevir (yaklaşık)"""
        # Yaklaşık TYT puan dağılımı
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

    def _calculate_probability_above_threshold(self, predicted: float, rmse: float, threshold: float) -> float:
        """Belirli eşiğin üstünde olma olasılığı"""
        z_score = (predicted - threshold) / rmse
        probability = 1 - stats.norm.cdf(z_score)
        return max(0.0, min(1.0, probability))


class YKSTimeSeriesPredictor:
    """YKS Zaman Serisi Tahmin Modeli"""

    def __init__(self, sequence_length: int = 30):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = None

    def prepare_time_series_data(self, student_scores: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Zaman serisi verilerini hazırla"""

        # Zaman sırasına göre sırala
        sorted_scores = sorted(student_scores, key=lambda x: x['date'])

        # Özellik vektörlerini oluştur
        features = []
        targets = []

        for i, score_data in enumerate(sorted_scores):
            feature_vector = [
                score_data.get('tyt_score', 0),
                score_data.get('ayt_score', 0),
                score_data.get('accuracy', 0),
                score_data.get('study_hours', 0),
                score_data.get('questions_solved', 0)
            ]
            features.append(feature_vector)

            # Hedef: bir sonraki sınav skoru
            if i < len(sorted_scores) - 1:
                targets.append(sorted_scores[i + 1].get('tyt_score', 0))

        # Sequence'lara böl
        X, y = [], []
        for i in range(len(features) - self.sequence_length):
            X.append(features[i:i + self.sequence_length])
            y.append(targets[i + self.sequence_length - 1])

        return np.array(X), np.array(y)

    def train_lstm_model(self, X: np.ndarray, y: np.ndarray):
        """LSTM modeli eğit"""
        if not PYTORCH_AVAILABLE:
            logging.warning("PyTorch not available for time series prediction")
            return

        # Veri ölçeklendirme
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)

        # PyTorch tensörlerine çevir
        X_tensor = torch.FloatTensor(X_scaled)
        y_tensor = torch.FloatTensor(y)

        # Model tanımı
        class LSTMPredictor(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, output_size):
                super(LSTMPredictor, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers

                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                self.fc = nn.Linear(hidden_size, output_size)
                self.dropout = nn.Dropout(0.2)

            def forward(self, x):
                h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)

                out, _ = self.lstm(x, (h0, c0))
                out = self.dropout(out[:, -1, :])  # Son time step'i al
                out = self.fc(out)
                return out

        # Model oluştur
        input_size = X.shape[2]
        hidden_size = 50
        num_layers = 2
        output_size = 1

        self.model = LSTMPredictor(input_size, hidden_size, num_layers, output_size)

        # Eğitim
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        # Veri yükleyici
        dataset = TensorDataset(X_tensor, y_tensor.unsqueeze(1))
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

        # Eğitim döngüsü
        self.model.train()
        for epoch in range(100):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if epoch % 20 == 0:
                logging.info(f"Epoch {epoch}, Loss: {total_loss / len(dataloader):.4f}")

    def predict_future_score(self, recent_scores: List[Dict[str, Any]],
                           days_ahead: int = 30) -> float:
        """Gelecek skor tahmini"""
        if not self.model or not PYTORCH_AVAILABLE:
            return 0.0

        # Son sequence_length kadar veriyi al
        recent_features = []
        for score_data in recent_scores[-self.sequence_length:]:
            feature_vector = [
                score_data.get('tyt_score', 0),
                score_data.get('ayt_score', 0),
                score_data.get('accuracy', 0),
                score_data.get('study_hours', 0),
                score_data.get('questions_solved', 0)
            ]
            recent_features.append(feature_vector)

        # Veriyi hazırla
        X = np.array([recent_features])
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled)

        # Tahmin
        self.model.eval()
        with torch.no_grad():
            prediction = self.model(X_tensor)
            return prediction.item()


class YKSPredictionEnsemble:
    """YKS Tahmin Ensemble Sistemi"""

    def __init__(self):
        self.tyt_model = TYTPredictionModel()
        self.ayt_model = TYTPredictionModel()  # AYT için ayrı model
        self.time_series_model = YKSTimeSeriesPredictor()
        self.score_calculator = YKSScoreCalculator()

        # Model ağırlıkları
        self.ensemble_weights = {
            'tyt_model': 0.4,
            'ayt_model': 0.35,
            'time_series': 0.25
        }

    async def train_all_models(self, training_data: Dict[str, Any]):
        """Tüm modelleri eğit"""

        # TYT modeli eğitimi
        tyt_profiles = training_data.get('tyt_profiles', [])
        tyt_scores = training_data.get('tyt_actual_scores', [])

        if tyt_profiles and tyt_scores:
            X_tyt, y_tyt = self.tyt_model.prepare_training_data(tyt_profiles, tyt_scores)
            self.tyt_model.train_models(X_tyt, y_tyt)

        # AYT modeli eğitimi (benzer şekilde)
        ayt_profiles = training_data.get('ayt_profiles', [])
        ayt_scores = training_data.get('ayt_actual_scores', [])

        if ayt_profiles and ayt_scores:
            X_ayt, y_ayt = self.ayt_model.prepare_training_data(ayt_profiles, ayt_scores)
            self.ayt_model.train_models(X_ayt, y_ayt)

        # Zaman serisi modeli eğitimi
        time_series_data = training_data.get('time_series_data', [])
        if time_series_data:
            X_ts, y_ts = self.time_series_model.prepare_time_series_data(time_series_data)
            self.time_series_model.train_lstm_model(X_ts, y_ts)

        logging.info("All YKS prediction models trained successfully")

    def predict_comprehensive_yks_score(self, profile: StudentPerformanceProfile,
                                      recent_performance: List[Dict[str, Any]]) -> Dict[str, ScorePrediction]:
        """Kapsamlı YKS puan tahmini"""

        predictions = {}

        # TYT tahmini
        tyt_prediction = self.tyt_model.predict_tyt_score(profile)
        predictions['TYT'] = tyt_prediction

        # AYT tahmini (ayrı model kullanarak)
        ayt_prediction = self.ayt_model.predict_tyt_score(profile, model_name='ensemble')
        ayt_prediction.exam_type = ExamType.AYT_SAY  # Tip güncelle
        predictions['AYT'] = ayt_prediction

        # Zaman serisi tahmini
        if recent_performance:
            future_score = self.time_series_model.predict_future_score(recent_performance, 30)
            if future_score > 0:
                # ScorePrediction objesine çevir
                ts_prediction = ScorePrediction(
                    student_id=profile.student_id,
                    exam_type=ExamType.YKS_OVERALL,
                    score_type=ScoreType.YKS_PUAN,
                    predicted_score=future_score,
                    confidence_interval=(future_score - 25, future_score + 25),
                    confidence_level=PredictionConfidence.MEDIUM,
                    model_name='lstm_time_series',
                    model_accuracy=0.75,
                    percentile_estimate=self.tyt_model._score_to_percentile(future_score, ExamType.YKS_OVERALL)
                )
                predictions['TIME_SERIES'] = ts_prediction

        # Ensemble tahmin
        ensemble_score = self._calculate_ensemble_score(predictions)

        # Genel YKS tahmini
        yks_prediction = ScorePrediction(
            student_id=profile.student_id,
            exam_type=ExamType.YKS_OVERALL,
            score_type=ScoreType.YKS_PUAN,
            predicted_score=ensemble_score,
            confidence_interval=(ensemble_score - 20, ensemble_score + 20),
            confidence_level=PredictionConfidence.HIGH,
            model_name='ensemble_all',
            model_accuracy=0.85,
            percentile_estimate=self.tyt_model._score_to_percentile(ensemble_score, ExamType.YKS_OVERALL),
            probability_above_300=self.tyt_model._calculate_probability_above_threshold(ensemble_score, 15, 300),
            probability_above_350=self.tyt_model._calculate_probability_above_threshold(ensemble_score, 15, 350),
            probability_above_400=self.tyt_model._calculate_probability_above_threshold(ensemble_score, 15, 400),
            probability_above_450=self.tyt_model._calculate_probability_above_threshold(ensemble_score, 15, 450)
        )

        predictions['YKS_ENSEMBLE'] = yks_prediction

        return predictions

    def _calculate_ensemble_score(self, predictions: Dict[str, ScorePrediction]) -> float:
        """Ensemble skor hesapla"""
        weighted_sum = 0.0
        total_weight = 0.0

        if 'TYT' in predictions:
            weighted_sum += predictions['TYT'].predicted_score * self.ensemble_weights['tyt_model']
            total_weight += self.ensemble_weights['tyt_model']

        if 'AYT' in predictions:
            weighted_sum += predictions['AYT'].predicted_score * self.ensemble_weights['ayt_model']
            total_weight += self.ensemble_weights['ayt_model']

        if 'TIME_SERIES' in predictions:
            weighted_sum += predictions['TIME_SERIES'].predicted_score * self.ensemble_weights['time_series']
            total_weight += self.ensemble_weights['time_series']

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 300.0  # Varsayılan değer


# === KIRO2 İçin Özelleştirilmiş YKS Tahmin Sistemi ===

class KIRO2YKSPredictionSystem:
    """KIRO2 için özelleştirilmiş YKS tahmin sistemi"""

    def __init__(self):
        self.ensemble = YKSPredictionEnsemble()
        self.models_trained = False

    async def initialize_with_historical_data(self, data_path: str = None):
        """Geçmiş verilerle sistemi başlat"""

        # Örnek eğitim verileri oluştur (gerçekte veritabanından gelecek)
        training_data = await self._generate_sample_training_data()

        # Modelleri eğit
        await self.ensemble.train_all_models(training_data)
        self.models_trained = True

        logging.info("KIRO2 YKS Prediction System initialized")

    async def _generate_sample_training_data(self) -> Dict[str, Any]:
        """Örnek eğitim verileri oluştur"""

        np.random.seed(42)
        n_students = 1000

        # TYT profilleri ve skorları
        tyt_profiles = []
        tyt_scores = []

        for i in range(n_students):
            # Rastgele öğrenci profili oluştur
            profile = StudentPerformanceProfile(
                student_id=f"student_{i}",
                school_type=np.random.choice(['devlet', 'özel', 'anadolu'], p=[0.7, 0.2, 0.1]),
                city=np.random.choice(['İstanbul', 'Ankara', 'İzmir', 'Diğer'], p=[0.25, 0.15, 0.1, 0.5]),
                daily_study_hours=np.random.exponential(4) + 1,
                preparation_months=np.random.randint(6, 24),
                total_questions_solved=np.random.randint(1000, 10000),
                correct_answer_rate=np.random.beta(7, 3),  # 0.7 civarında yoğunlaşır
                recent_tyt_performance=np.random.beta(5, 3),
                recent_ayt_performance=np.random.beta(4, 4),
                improvement_trend=np.random.normal(0.1, 0.2),
                consistency_score=np.random.beta(6, 2),
                login_frequency_per_week=np.random.poisson(5),
                goal_completion_rate=np.random.beta(6, 4)
            )

            # Gerçekçi skor hesapla (özellikler bazlı)
            base_score = 200 + profile.correct_answer_rate * 150

            # Okul türü etkisi
            if profile.school_type == 'anadolu':
                base_score += 30
            elif profile.school_type == 'özel':
                base_score += 20

            # Çalışma saati etkisi
            base_score += min(50, profile.daily_study_hours * 5)

            # Şehir etkisi
            if profile.city in ['İstanbul', 'Ankara', 'İzmir']:
                base_score += 15

            # Gürültü ekle
            final_score = max(150, min(500, base_score + np.random.normal(0, 25)))

            tyt_profiles.append(profile)
            tyt_scores.append(final_score)

        # Zaman serisi verileri
        time_series_data = []
        for i in range(100):  # 100 öğrencinin zaman serisi
            student_timeline = []
            base_performance = np.random.uniform(0.3, 0.8)

            for day in range(60):  # 60 günlük veri
                # Trend ile birlikte gelişim
                trend = day * 0.005  # Günde %0.5 gelişim
                noise = np.random.normal(0, 0.05)
                current_performance = min(0.95, base_performance + trend + noise)

                student_timeline.append({
                    'student_id': f'ts_student_{i}',
                    'date': datetime.now() - timedelta(days=60-day),
                    'tyt_score': 200 + current_performance * 200,
                    'ayt_score': 180 + current_performance * 220,
                    'accuracy': current_performance,
                    'study_hours': np.random.uniform(2, 8),
                    'questions_solved': np.random.randint(10, 100)
                })

            time_series_data.extend(student_timeline)

        return {
            'tyt_profiles': tyt_profiles,
            'tyt_actual_scores': tyt_scores,
            'ayt_profiles': tyt_profiles,  # Aynı profilleri AYT için de kullan
            'ayt_actual_scores': [score * 1.1 + np.random.normal(0, 15) for score in tyt_scores],
            'time_series_data': time_series_data
        }

    async def predict_student_yks_performance(self, student_id: str,
                                           profile_data: Dict[str, Any],
                                           recent_performance: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Öğrenci YKS performansını tahmin et"""

        if not self.models_trained:
            await self.initialize_with_historical_data()

        # Profil objesi oluştur
        profile = StudentPerformanceProfile(
            student_id=student_id,
            school_type=profile_data.get('school_type', 'devlet'),
            city=profile_data.get('city', 'İstanbul'),
            daily_study_hours=profile_data.get('daily_study_hours', 4.0),
            preparation_months=profile_data.get('preparation_months', 12),
            total_questions_solved=profile_data.get('total_questions_solved', 0),
            correct_answer_rate=profile_data.get('correct_answer_rate', 0.0),
            recent_tyt_performance=profile_data.get('recent_tyt_performance', 0.0),
            recent_ayt_performance=profile_data.get('recent_ayt_performance', 0.0),
            improvement_trend=profile_data.get('improvement_trend', 0.0),
            consistency_score=profile_data.get('consistency_score', 0.0),
            login_frequency_per_week=profile_data.get('login_frequency_per_week', 5.0),
            goal_completion_rate=profile_data.get('goal_completion_rate', 0.0)
        )

        # Kapsamlı tahmin yap
        predictions = self.ensemble.predict_comprehensive_yks_score(profile, recent_performance or [])

        # KIRO2 özel analiz ekle
        analysis = self._generate_kiro2_analysis(predictions, profile)

        # Sonuçları formatla
        result = {
            'student_id': student_id,
            'prediction_date': datetime.now().isoformat(),
            'predictions': {},
            'analysis': analysis,
            'recommendations': self._generate_recommendations(predictions, analysis)
        }

        # Tahminleri formatla
        for exam_type, prediction in predictions.items():
            result['predictions'][exam_type] = {
                'predicted_score': round(prediction.predicted_score, 1),
                'confidence_interval': {
                    'lower': round(prediction.confidence_interval[0], 1),
                    'upper': round(prediction.confidence_interval[1], 1)
                },
                'confidence_level': prediction.confidence_level.value,
                'percentile': round(prediction.percentile_estimate, 1),
                'probabilities': {
                    'above_300': round(prediction.probability_above_300, 3),
                    'above_350': round(prediction.probability_above_350, 3),
                    'above_400': round(prediction.probability_above_400, 3),
                    'above_450': round(prediction.probability_above_450, 3)
                }
            }

        return result

    def _generate_kiro2_analysis(self, predictions: Dict[str, ScorePrediction],
                               profile: StudentPerformanceProfile) -> Dict[str, Any]:
        """KIRO2 özel analiz oluştur"""

        yks_pred = predictions.get('YKS_ENSEMBLE', predictions.get('TYT'))
        predicted_score = yks_pred.predicted_score if yks_pred else 300

        analysis = {
            'readiness_level': self._assess_readiness_level(predicted_score),
            'strength_areas': self._identify_strengths(profile),
            'improvement_areas': self._identify_improvements_needed(profile, predicted_score),
            'study_plan_recommendations': self._suggest_study_plan(profile, predicted_score),
            'timeline_analysis': self._analyze_timeline(profile, predicted_score),
            'university_prospects': self._analyze_university_prospects(predicted_score)
        }

        return analysis

    def _assess_readiness_level(self, predicted_score: float) -> Dict[str, Any]:
        """Hazırlık seviyesi değerlendirmesi"""
        if predicted_score >= 450:
            level = "Excellent"
            description = "Top üniversitelere yerleşmeye çok yakınsınız!"
        elif predicted_score >= 400:
            level = "Very Good"
            description = "İyi üniversitelerde istediğiniz bölüme girebilirsiniz."
        elif predicted_score >= 350:
            level = "Good"
            description = "Orta seviye üniversitelerde şansınız yüksek."
        elif predicted_score >= 300:
            level = "Fair"
            description = "Daha fazla çalışmayla hedeflediğiniz yere gelebilirsiniz."
        else:
            level = "Needs Improvement"
            description = "Temel konulara odaklanmanız gerekiyor."

        return {
            'level': level,
            'description': description,
            'score_range': f"{predicted_score:.0f} puan"
        }

    def _identify_strengths(self, profile: StudentPerformanceProfile) -> List[str]:
        """Güçlü yönleri belirle"""
        strengths = []

        if profile.daily_study_hours >= 6:
            strengths.append("Düzenli ve uzun çalışma alışkanlığı")

        if profile.correct_answer_rate >= 0.8:
            strengths.append("Yüksek doğruluk oranı")

        if profile.consistency_score >= 0.8:
            strengths.append("Tutarlı performans")

        if profile.login_frequency_per_week >= 6:
            strengths.append("Düzenli platform kullanımı")

        if profile.goal_completion_rate >= 0.8:
            strengths.append("Hedeflere ulaşma başarısı")

        if not strengths:
            strengths.append("Gelişim potansiyeli yüksek")

        return strengths

    def _identify_improvements_needed(self, profile: StudentPerformanceProfile,
                                    predicted_score: float) -> List[str]:
        """İyileştirme alanlarını belirle"""
        improvements = []

        if predicted_score < 350:
            improvements.append("Temel konularda güçlendirme gerekli")

        if profile.daily_study_hours < 4:
            improvements.append("Günlük çalışma süresini artırın")

        if profile.correct_answer_rate < 0.6:
            improvements.append("Doğruluk oranını yükseltmeye odaklanın")

        if profile.consistency_score < 0.6:
            improvements.append("Daha tutarlı çalışma düzeni oluşturun")

        if profile.total_questions_solved < 5000:
            improvements.append("Daha fazla soru çözme pratiği yapın")

        return improvements

    def _suggest_study_plan(self, profile: StudentPerformanceProfile,
                          predicted_score: float) -> Dict[str, str]:
        """Çalışma planı önerisi"""

        if predicted_score >= 400:
            return {
                'focus': "Pekiştirme ve hız çalışması",
                'daily_hours': "4-6 saat",
                'priority': "Deneme sınavları ve zor sorular"
            }
        elif predicted_score >= 350:
            return {
                'focus': "Konu tekrarları ve orta zorluk sorular",
                'daily_hours': "5-7 saat",
                'priority': "Zayıf konuları güçlendirme"
            }
        elif predicted_score >= 300:
            return {
                'focus': "Temel konular ve kolay-orta sorular",
                'daily_hours': "6-8 saat",
                'priority': "Konu anlatımları ve temel sorular"
            }
        else:
            return {
                'focus': "Temel kavramlar ve çok kolay sorular",
                'daily_hours': "7-9 saat",
                'priority': "Konu tekrarları ve temel beceriler"
            }

    def _analyze_timeline(self, profile: StudentPerformanceProfile,
                        predicted_score: float) -> Dict[str, Any]:
        """Zaman çizelgesi analizi"""

        months_left = profile.preparation_months
        improvement_potential = max(0, (500 - predicted_score) * 0.6)  # %60'ı gerçekleşebilir

        return {
            'months_remaining': months_left,
            'current_trajectory': "İyi" if predicted_score >= 350 else "Geliştirilmeli",
            'improvement_potential': f"{improvement_potential:.0f} puan",
            'monthly_target': f"{improvement_potential/max(1, months_left):.1f} puan/ay"
        }

    def _analyze_university_prospects(self, predicted_score: float) -> Dict[str, List[str]]:
        """Üniversite yerleşme analizi"""

        prospects = {
            'high_probability': [],
            'medium_probability': [],
            'target_universities': []
        }

        if predicted_score >= 450:
            prospects['high_probability'] = ["İTÜ", "Boğaziçi", "ODTÜ", "Bilkent"]
            prospects['medium_probability'] = ["Koç", "Sabancı", "Hacettepe"]
        elif predicted_score >= 400:
            prospects['high_probability'] = ["Hacettepe", "İTÜ (bazı bölümler)", "Gazi"]
            prospects['medium_probability'] = ["ODTÜ (bazı bölümler)", "Ankara Ü."]
        elif predicted_score >= 350:
            prospects['high_probability'] = ["Devlet üniversiteleri", "Vakıf üniversiteleri"]
            prospects['medium_probability'] = ["İyi konumlu devlet üniversiteleri"]
        else:
            prospects['high_probability'] = ["Açık üniversiteler", "Meslek yüksekokulları"]
            prospects['target_universities'] = ["Gelişim için devlet üniversiteleri"]

        return prospects

    def _generate_recommendations(self, predictions: Dict[str, ScorePrediction],
                                analysis: Dict[str, Any]) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []

        yks_pred = predictions.get('YKS_ENSEMBLE', predictions.get('TYT'))
        if not yks_pred:
            return ["Daha fazla veri gerekli - daha fazla soru çözün!"]

        predicted_score = yks_pred.predicted_score

        # Genel öneriler
        if predicted_score >= 450:
            recommendations.append("[TARGET] Harika! Hedeflediğiniz üniversiteye odaklanın!")
        elif predicted_score >= 400:
            recommendations.append("👍 İyi durumdasınız. Son rötuşları yapın!")
        elif predicted_score >= 350:
            recommendations.append("[TRENDING_UP] Gelişim gösteriyorsunuz. Devam edin!")
        else:
            recommendations.append("💪 Temel konulara odaklanın. Sabırlı olun!")

        # Güven seviyesine göre
        confidence = yks_pred.confidence_level
        if confidence in [PredictionConfidence.LOW, PredictionConfidence.VERY_LOW]:
            recommendations.append("⚠️ Daha fazla veri için sistemi düzenli kullanın.")

        # Analiz bazlı öneriler
        if len(analysis['improvement_areas']) > 0:
            recommendations.append(f"[MAG] Öncelik: {analysis['improvement_areas'][0]}")

        if len(analysis['strength_areas']) > 0:
            recommendations.append(f"✨ Gücünüz: {analysis['strength_areas'][0]}")

        return recommendations[:4]  # En fazla 4 öneri


# === Örnek Kullanım ===

async def example_yks_prediction():
    """YKS tahmin sistemi örneği"""

    # Tahmin sistemini başlat
    prediction_system = KIRO2YKSPredictionSystem()

    print("[TARGET] KIRO2 YKS Tahmin Sistemi Başlatılıyor...")

    # Sistemi eğitim verilerle başlat
    await prediction_system.initialize_with_historical_data()

    print("[CHECK] Modeller eğitildi!")

    # Örnek öğrenci profili
    student_profile = {
        'school_type': 'anadolu',
        'city': 'İstanbul',
        'daily_study_hours': 5.5,
        'preparation_months': 8,
        'total_questions_solved': 7500,
        'correct_answer_rate': 0.75,
        'recent_tyt_performance': 0.8,
        'recent_ayt_performance': 0.7,
        'improvement_trend': 0.15,
        'consistency_score': 0.85,
        'login_frequency_per_week': 6.2,
        'goal_completion_rate': 0.78
    }

    # Son performans verileri
    recent_performance = [
        {'date': datetime.now() - timedelta(days=7), 'tyt_score': 380, 'ayt_score': 360, 'accuracy': 0.78, 'study_hours': 5, 'questions_solved': 50},
        {'date': datetime.now() - timedelta(days=14), 'tyt_score': 375, 'ayt_score': 355, 'accuracy': 0.76, 'study_hours': 6, 'questions_solved': 60},
        {'date': datetime.now() - timedelta(days=21), 'tyt_score': 370, 'ayt_score': 350, 'accuracy': 0.74, 'study_hours': 5.5, 'questions_solved': 55}
    ]

    # YKS tahmini yap
    result = await prediction_system.predict_student_yks_performance(
        student_id="kiro2_student_001",
        profile_data=student_profile,
        recent_performance=recent_performance
    )

    print(f"\n[CHART] YKS Tahmin Sonuçları:")
    print(f"Öğrenci ID: {result['student_id']}")
    print(f"Tahmin Tarihi: {result['prediction_date'][:10]}")

    # Ana tahmin
    yks_prediction = result['predictions'].get('YKS_ENSEMBLE', {})
    if yks_prediction:
        print(f"\n[TARGET] Genel YKS Tahmini:")
        print(f"  Tahmin Edilen Puan: {yks_prediction['predicted_score']}")
        print(f"  Güven Aralığı: {yks_prediction['confidence_interval']['lower']:.0f} - {yks_prediction['confidence_interval']['upper']:.0f}")
        print(f"  Güven Seviyesi: {yks_prediction['confidence_level']}")
        print(f"  Yüzdelik Dilim: {yks_prediction['percentile']}%")

        print(f"\n[TRENDING_UP] Başarı Olasılıkları:")
        for threshold, prob in yks_prediction['probabilities'].items():
            print(f"  {threshold.replace('above_', '')}+ puan: %{prob*100:.1f}")

    # Analiz sonuçları
    analysis = result['analysis']
    print(f"\n[MAG] Hazırlık Analizi:")
    print(f"  Seviye: {analysis['readiness_level']['level']}")
    print(f"  Açıklama: {analysis['readiness_level']['description']}")

    print(f"\n💪 Güçlü Yönler:")
    for strength in analysis['strength_areas']:
        print(f"  • {strength}")

    print(f"\n[BOOKS] Geliştirilmesi Gerekenler:")
    for improvement in analysis['improvement_areas']:
        print(f"  • {improvement}")

    print(f"\n⏰ Çalışma Planı:")
    study_plan = analysis['study_plan_recommendations']
    print(f"  Odak: {study_plan['focus']}")
    print(f"  Günlük süre: {study_plan['daily_hours']}")
    print(f"  Öncelik: {study_plan['priority']}")

    print(f"\n🏫 Üniversite Analizi:")
    prospects = analysis['university_prospects']
    if prospects['high_probability']:
        print(f"  Yüksek olasılık: {', '.join(prospects['high_probability'])}")
    if prospects['medium_probability']:
        print(f"  Orta olasılık: {', '.join(prospects['medium_probability'])}")

    print(f"\n[BULB] Öneriler:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. {rec}")

    print(f"\n✨ KIRO2 YKS Tahmin Sistemi analizi tamamlandı!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_yks_prediction())
