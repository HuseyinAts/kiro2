"""
KIRO2 - Intelligent Recommendation Systems
==========================================

Bu modül, öğrenciler için kişiselleştirilmiş ve akıllı öneri sistemlerini içerir.
TYT, AYT ve YKS hazırlığında öğrencilerin ihtiyaçlarına göre özelleştirilmiştir.

Akıllı Öneri Sistemleri:
- Collaborative Filtering (İşbirlikçi Filtreleme)
- Content-Based Filtering (İçerik Tabanlı Filtreleme)
- Hybrid Recommendation Systems
- Deep Learning Recommendation Models
- Knowledge-Based Recommendations
- Context-Aware Recommendations
- Multi-Armed Bandit Algorithms
- Reinforcement Learning Recommendations

KIRO2 Özel Öneri Türleri:
- Soru önerileri (zorluk seviyesine göre)
- Konu çalışma sırası önerileri
- Video ders önerileri
- Test ve deneme sınavı önerileri
- Çalışma materyali önerileri
- Üniversite ve bölüm önerileri
- Çalışma arkadaşı önerileri
- Motivasyon ve hedef önerileri
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Advanced ML libraries
try:
    from surprise import SVD, Dataset, Reader
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    logging.warning("Surprise library not available - collaborative filtering limited")

try:
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    logging.warning("PyTorch not available - deep learning recommendations disabled")


class RecommendationType(Enum):
    """Öneri türleri"""
    QUESTION = "soru_onerisi"
    TOPIC = "konu_onerisi"
    VIDEO = "video_onerisi"
    TEST = "test_onerisi"
    MATERIAL = "materyal_onerisi"
    UNIVERSITY = "universite_onerisi"
    STUDY_PLAN = "calisma_plani"
    PEER = "arkadas_onerisi"
    MOTIVATION = "motivasyon_onerisi"


class RecommendationStrategy(Enum):
    """Öneri stratejileri"""
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    KNOWLEDGE_BASED = "knowledge_based"
    CONTEXT_AWARE = "context_aware"
    DEEP_LEARNING = "deep_learning"


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


@dataclass
class RecommendationItem:
    """Öneri öğesi"""
    item_id: str
    item_type: RecommendationType
    title: str
    description: str
    subject: str
    topic: str = ""
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    estimated_time_minutes: int = 30
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Kullanıcı profili"""
    user_id: str

    # Akademik bilgiler
    current_grade: int = 12
    target_exam: str = "YKS"
    strong_subjects: List[str] = field(default_factory=list)
    weak_subjects: List[str] = field(default_factory=list)

    # Performans metrikleri
    overall_accuracy: float = 0.0
    subject_accuracies: Dict[str, float] = field(default_factory=dict)
    average_response_time: float = 60.0
    consistency_score: float = 0.0

    # Davranışsal özellikler
    preferred_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    study_pace: str = "normal"  # slow, normal, fast
    learning_style: str = "visual"  # visual, auditory, kinesthetic
    preferred_subjects: List[str] = field(default_factory=list)

    # Zaman ve hedef bilgileri
    daily_study_hours: float = 4.0
    exam_date: Optional[datetime] = None
    target_score: int = 400

    # Etkileşim geçmişi
    completed_items: List[str] = field(default_factory=list)
    liked_items: List[str] = field(default_factory=list)
    disliked_items: List[str] = field(default_factory=list)
    bookmarked_items: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """Öneri sonucu"""
    user_id: str
    item: RecommendationItem
    score: float
    strategy: RecommendationStrategy
    reasoning: List[str] = field(default_factory=list)
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InteractionData:
    """Etkileşim verisi"""
    user_id: str
    item_id: str
    interaction_type: str  # view, like, complete, bookmark, skip
    rating: Optional[float] = None  # 1-5 arası
    time_spent: float = 0.0  # dakika
    completion_rate: float = 0.0  # 0-1 arası
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class CollaborativeFilteringRecommender:
    """İşbirlikçi filtreleme öneri sistemi"""

    def __init__(self, n_factors: int = 50):
        self.n_factors = n_factors
        self.model = None
        self.user_item_matrix = None
        self.item_encoder = {}
        self.user_encoder = {}

    def prepare_data(self, interactions: List[InteractionData]) -> None:
        """Veriyi hazırla"""
        # Rating verisi oluştur
        ratings_data = []
        for interaction in interactions:
            if interaction.rating is not None:
                ratings_data.append({
                    'user_id': interaction.user_id,
                    'item_id': interaction.item_id,
                    'rating': interaction.rating
                })
            else:
                # Implicit feedback'i explicit'e çevir
                rating = self._convert_implicit_to_rating(interaction)
                ratings_data.append({
                    'user_id': interaction.user_id,
                    'item_id': interaction.item_id,
                    'rating': rating
                })

        self.ratings_df = pd.DataFrame(ratings_data)

        if SURPRISE_AVAILABLE and not self.ratings_df.empty:
            # Surprise dataset oluştur
            reader = Reader(rating_scale=(1, 5))
            self.dataset = Dataset.load_from_df(
                self.ratings_df[['user_id', 'item_id', 'rating']],
                reader
            )

    def _convert_implicit_to_rating(self, interaction: InteractionData) -> float:
        """Implicit feedback'i rating'e çevir"""
        base_rating = 3.0

        # Etkileşim türüne göre ayarlama
        if interaction.interaction_type == 'like':
            base_rating += 1.5
        elif interaction.interaction_type == 'bookmark':
            base_rating += 1.0
        elif interaction.interaction_type == 'complete':
            base_rating += 0.5 * interaction.completion_rate
        elif interaction.interaction_type == 'skip':
            base_rating -= 1.0

        # Zaman faktörü
        if interaction.time_spent > 0:
            time_factor = min(1.0, interaction.time_spent / 30.0)  # 30 dk normalize
            base_rating += time_factor * 0.5

        return max(1.0, min(5.0, base_rating))

    def train(self) -> None:
        """Modeli eğit"""
        if not SURPRISE_AVAILABLE or not hasattr(self, 'dataset'):
            logging.warning("Cannot train collaborative filtering model")
            return

        # SVD algoritması kullan
        self.model = SVD(n_factors=self.n_factors)
        trainset = self.dataset.build_full_trainset()
        self.model.fit(trainset)

        logging.info("Collaborative filtering model trained")

    def get_recommendations(self, user_id: str, n_recommendations: int = 10,
                          exclude_seen: bool = True) -> List[Tuple[str, float]]:
        """Kullanıcı için öneriler al"""
        if not self.model or not SURPRISE_AVAILABLE:
            return []

        # Kullanıcının daha önce etkileşimde bulunduğu öğeler
        user_items = set()
        if exclude_seen and hasattr(self, 'ratings_df'):
            user_items = set(
                self.ratings_df[self.ratings_df['user_id'] == user_id]['item_id'].tolist()
            )

        # Tüm öğeler için tahmin yap
        all_items = set(self.ratings_df['item_id'].unique()) if hasattr(self, 'ratings_df') else set()
        recommendations = []

        for item_id in all_items:
            if exclude_seen and item_id in user_items:
                continue

            prediction = self.model.predict(user_id, item_id)
            recommendations.append((item_id, prediction.est))

        # Skorlara göre sırala
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    def get_item_similarity(self, item1_id: str, item2_id: str) -> float:
        """İki öğe arasındaki benzerlik"""
        if not self.model or not SURPRISE_AVAILABLE:
            return 0.0

        try:
            # İç ürün (inner product) benzerliği
            item1_factors = self.model.qi[self.model.trainset.to_inner_iid(item1_id)]
            item2_factors = self.model.qi[self.model.trainset.to_inner_iid(item2_id)]
            similarity = np.dot(item1_factors, item2_factors)
            return float(similarity)
        except (ValueError, IndexError, KeyError) as e:
            # to_inner_iid raises ValueError for unseen ids; qi indexing can
            # raise IndexError/KeyError. Item not in trainset -> no similarity.
            logging.debug(f"get_item_similarity fallback for ({item1_id}, {item2_id}): {e}")
            return 0.0


class ContentBasedRecommender:
    """İçerik tabanlı öneri sistemi"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',  # Türkçe stopwords eklenebilir
            ngram_range=(1, 2)
        )
        self.item_vectors = None
        self.items_df = None

    def prepare_data(self, items: List[RecommendationItem]) -> None:
        """İçerik verilerini hazırla"""
        items_data = []
        for item in items:
            # Metin özelliklerini birleştir
            content_text = f"{item.title} {item.description} {item.subject} {item.topic} {' '.join(item.tags)}"

            items_data.append({
                'item_id': item.item_id,
                'content_text': content_text,
                'item_type': item.item_type.value,
                'subject': item.subject,
                'topic': item.topic,
                'difficulty_level': item.difficulty_level.value,
                'estimated_time': item.estimated_time_minutes,
                'prerequisites': ','.join(item.prerequisites),
                'learning_objectives': ','.join(item.learning_objectives)
            })

        self.items_df = pd.DataFrame(items_data)

        if not self.items_df.empty:
            # TF-IDF vektörlerini oluştur
            self.item_vectors = self.vectorizer.fit_transform(self.items_df['content_text'])
            logging.info(f"Content-based model prepared with {len(items)} items")

    def get_recommendations(self, user_profile: UserProfile,
                          n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """Kullanıcı profili için içerik tabanlı öneriler"""
        if self.item_vectors is None or self.items_df.empty:
            return []

        # Kullanıcı profilini vektöre çevir
        user_content = f"{' '.join(user_profile.preferred_subjects)} {' '.join(user_profile.strong_subjects)}"
        if not user_content.strip():
            user_content = "matematik türkçe fen sosyal"  # Varsayılan

        user_vector = self.vectorizer.transform([user_content])

        # Cosine similarity hesapla
        similarities = cosine_similarity(user_vector, self.item_vectors).flatten()

        # Kullanıcı tercihlerine göre filtreleme ve ağırlıklandırma
        recommendations = []
        for idx, similarity in enumerate(similarities):
            item_row = self.items_df.iloc[idx]

            # Zorluk seviyesi filtresi
            difficulty_penalty = self._calculate_difficulty_penalty(
                item_row['difficulty_level'], user_profile.preferred_difficulty.value
            )

            # Konu tercihi bonusu
            subject_bonus = 0.0
            if item_row['subject'] in user_profile.preferred_subjects:
                subject_bonus = 0.2
            elif item_row['subject'] in user_profile.strong_subjects:
                subject_bonus = 0.1

            # Final skor
            final_score = similarity + subject_bonus - difficulty_penalty

            # Daha önce tamamlanmış öğeleri filtrele
            if item_row['item_id'] not in user_profile.completed_items:
                recommendations.append((item_row['item_id'], final_score))

        # Sırala ve döndür
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

    def _calculate_difficulty_penalty(self, item_difficulty: int, preferred_difficulty: int) -> float:
        """Zorluk seviyesi cezası hesapla"""
        diff = abs(item_difficulty - preferred_difficulty)
        if diff == 0:
            return 0.0
        elif diff == 1:
            return 0.05
        elif diff == 2:
            return 0.15
        else:
            return 0.3

    def get_similar_items(self, item_id: str, n_similar: int = 5) -> List[Tuple[str, float]]:
        """Benzer öğeler bul"""
        if self.item_vectors is None or self.items_df.empty:
            return []

        # Öğe index'ini bul
        try:
            item_idx = self.items_df[self.items_df['item_id'] == item_id].index[0]
        except IndexError:
            # item_id not found in items_df -> no similar items to return.
            logging.debug(f"get_similar_items: item_id {item_id} not found")
            return []

        # Benzerlik hesapla
        item_vector = self.item_vectors[item_idx]
        similarities = cosine_similarity(item_vector, self.item_vectors).flatten()

        # Kendisini hariç tut
        similarities[item_idx] = -1

        # En benzer öğeleri döndür
        similar_indices = similarities.argsort()[::-1][:n_similar]
        similar_items = []

        for idx in similar_indices:
            if similarities[idx] > 0:
                similar_item_id = self.items_df.iloc[idx]['item_id']
                similar_items.append((similar_item_id, similarities[idx]))

        return similar_items


class HybridRecommender:
    """Hibrit öneri sistemi"""

    def __init__(self, weights: Dict[str, float] = None):
        self.collaborative = CollaborativeFilteringRecommender()
        self.content_based = ContentBasedRecommender()

        # Algoritma ağırlıkları
        self.weights = weights or {
            'collaborative': 0.6,
            'content_based': 0.4
        }

    def prepare_data(self, interactions: List[InteractionData],
                   items: List[RecommendationItem]) -> None:
        """Her iki sistem için veri hazırla"""
        self.collaborative.prepare_data(interactions)
        self.content_based.prepare_data(items)

    def train(self) -> None:
        """Her iki sistemi eğit"""
        self.collaborative.train()
        # Content-based sistem eğitim gerektirmiyor

    def get_recommendations(self, user_id: str, user_profile: UserProfile,
                          n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """Hibrit öneriler al"""

        # Collaborative filtering önerileri
        cf_recs = self.collaborative.get_recommendations(user_id, n_recommendations * 2)
        cf_dict = {item_id: score for item_id, score in cf_recs}

        # Content-based öneriler
        cb_recs = self.content_based.get_recommendations(user_profile, n_recommendations * 2)
        cb_dict = {item_id: score for item_id, score in cb_recs}

        # Hibrit skorlama
        all_items = set(cf_dict.keys()) | set(cb_dict.keys())
        hybrid_scores = []

        for item_id in all_items:
            cf_score = cf_dict.get(item_id, 0.0)
            cb_score = cb_dict.get(item_id, 0.0)

            # Ağırlıklı kombinasyon
            hybrid_score = (
                self.weights['collaborative'] * cf_score +
                self.weights['content_based'] * cb_score
            )

            hybrid_scores.append((item_id, hybrid_score))

        # Sırala ve döndür
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores[:n_recommendations]


class KnowledgeBasedRecommender:
    """Bilgi tabanlı öneri sistemi"""

    def __init__(self):
        self.rules = []
        self.knowledge_base = {}

    def add_rule(self, condition_func, recommendation_func, priority: int = 1):
        """Kural ekle"""
        self.rules.append({
            'condition': condition_func,
            'recommendation': recommendation_func,
            'priority': priority
        })

    def initialize_yks_knowledge(self):
        """YKS için bilgi tabanını başlat"""

        # Konu önkoşul ilişkileri
        self.knowledge_base['prerequisites'] = {
            'tyt_matematik_cebir': ['tyt_matematik_temel_islemler'],
            'tyt_matematik_geometri': ['tyt_matematik_cebir'],
            'ayt_matematik_turev': ['ayt_matematik_fonksiyon'],
            'ayt_matematik_integral': ['ayt_matematik_turev'],
            'ayt_fizik_elektrik': ['ayt_fizik_mekanik'],
            'ayt_kimya_organik': ['ayt_kimya_genel']
        }

        # Zorluk progresyonu
        self.knowledge_base['difficulty_progression'] = {
            'TYT Matematik': [
                'temel_islemler', 'cebir', 'geometri', 'olasilik'
            ],
            'AYT Matematik': [
                'fonksiyon', 'turev', 'integral', 'analitik_geometri'
            ]
        }

        # Kural tanımları
        self._add_yks_rules()

    def _add_yks_rules(self):
        """YKS özel kuralları ekle"""

        # Kural 1: Zayıf konulara odaklan
        def weak_subject_condition(user_profile: UserProfile, context: Dict) -> bool:
            return len(user_profile.weak_subjects) > 0

        def weak_subject_recommendation(user_profile: UserProfile, items: List[RecommendationItem]) -> List[str]:
            recommendations = []
            for item in items:
                if (item.subject in user_profile.weak_subjects and
                    item.difficulty_level.value <= user_profile.preferred_difficulty.value + 1):
                    recommendations.append(item.item_id)
            return recommendations[:3]

        self.add_rule(weak_subject_condition, weak_subject_recommendation, priority=5)

        # Kural 2: Önkoşul kontrolü
        def prerequisite_condition(user_profile: UserProfile, context: Dict) -> bool:
            return True  # Her zaman kontrol et

        def prerequisite_recommendation(user_profile: UserProfile, items: List[RecommendationItem]) -> List[str]:
            recommendations = []
            for item in items:
                # Önkoşulları karşılıyor mu?
                prerequisites_met = all(
                    prereq in user_profile.completed_items
                    for prereq in item.prerequisites
                )
                if prerequisites_met:
                    recommendations.append(item.item_id)
            return recommendations

        self.add_rule(prerequisite_condition, prerequisite_recommendation, priority=3)

        # Kural 3: Sınav tarihine göre öncelik
        def exam_urgency_condition(user_profile: UserProfile, context: Dict) -> bool:
            return (user_profile.exam_date and
                   user_profile.exam_date - datetime.now() < timedelta(days=60))

        def exam_urgency_recommendation(user_profile: UserProfile, items: List[RecommendationItem]) -> List[str]:
            # Sınava yakın - test ve deneme önceliği
            recommendations = []
            for item in items:
                if item.item_type in [RecommendationType.TEST, RecommendationType.QUESTION]:
                    recommendations.append(item.item_id)
            return recommendations[:5]

        self.add_rule(exam_urgency_condition, exam_urgency_recommendation, priority=4)

    def get_recommendations(self, user_profile: UserProfile, items: List[RecommendationItem],
                          context: Dict[str, Any] = None) -> List[str]:
        """Bilgi tabanlı öneriler al"""
        context = context or {}
        all_recommendations = []

        # Kuralları öncelik sırasına göre uygula
        sorted_rules = sorted(self.rules, key=lambda x: x['priority'], reverse=True)

        for rule in sorted_rules:
            if rule['condition'](user_profile, context):
                rule_recs = rule['recommendation'](user_profile, items)
                all_recommendations.extend(rule_recs)

        # Tekrarları kaldır ve sırala
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        return unique_recommendations[:10]


class ContextAwareRecommender:
    """Bağlam farkında öneri sistemi"""

    def __init__(self):
        self.context_factors = {
            'time_of_day': self._time_of_day_factor,
            'day_of_week': self._day_of_week_factor,
            'study_session_duration': self._study_duration_factor,
            'recent_performance': self._performance_factor,
            'mood': self._mood_factor
        }

    def _time_of_day_factor(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Günün saatine göre faktör"""
        hour = context.get('current_time', datetime.now()).hour

        if 6 <= hour < 12:  # Sabah
            return {'difficulty_boost': 0.1, 'video_preference': 0.2}
        elif 12 <= hour < 18:  # Öğleden sonra
            return {'practice_preference': 0.2, 'test_preference': 0.1}
        elif 18 <= hour < 22:  # Akşam
            return {'review_preference': 0.2, 'easy_content': 0.1}
        else:  # Gece
            return {'difficulty_penalty': 0.2, 'short_content': 0.3}

    def _day_of_week_factor(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Haftanın gününe göre faktör"""
        day = context.get('current_time', datetime.now()).weekday()

        if day < 5:  # Hafta içi
            return {'intensive_study': 0.1, 'long_content': 0.1}
        else:  # Hafta sonu
            return {'review_preference': 0.2, 'fun_content': 0.1}

    def _study_duration_factor(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Çalışma süresi faktörü"""
        session_minutes = context.get('session_duration_minutes', 30)

        if session_minutes < 30:
            return {'quick_questions': 0.3, 'short_videos': 0.2}
        elif session_minutes < 60:
            return {'balanced_content': 0.1}
        else:
            return {'comprehensive_tests': 0.2, 'long_topics': 0.1}

    def _performance_factor(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Son performansa göre faktör"""
        recent_accuracy = context.get('recent_accuracy', 0.5)

        if recent_accuracy > 0.8:
            return {'difficulty_boost': 0.2, 'advanced_topics': 0.1}
        elif recent_accuracy < 0.4:
            return {'easier_content': 0.3, 'review_topics': 0.2}
        else:
            return {'current_level': 0.1}

    def _mood_factor(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Ruh haline göre faktör"""
        mood = context.get('mood', 'neutral')

        mood_factors = {
            'motivated': {'challenging_content': 0.2, 'new_topics': 0.1},
            'tired': {'easy_content': 0.3, 'review_preference': 0.2},
            'frustrated': {'confidence_building': 0.3, 'easier_content': 0.2},
            'confident': {'difficult_content': 0.2, 'test_preference': 0.1},
            'neutral': {'balanced_content': 0.1}
        }

        return mood_factors.get(mood, {})

    def adjust_recommendations(self, base_recommendations: List[Tuple[str, float]],
                             items: List[RecommendationItem],
                             context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Bağlam faktörlerine göre önerileri ayarla"""

        # Bağlam faktörlerini hesapla
        context_adjustments = {}
        for factor_name, factor_func in self.context_factors.items():
            factor_result = factor_func(context)
            context_adjustments.update(factor_result)

        # Öğe dictionary'si oluştur
        items_dict = {item.item_id: item for item in items}

        # Ayarlanmış skorlar
        adjusted_recommendations = []

        for item_id, base_score in base_recommendations:
            if item_id not in items_dict:
                continue

            item = items_dict[item_id]
            adjusted_score = base_score

            # Bağlam ayarlamaları uygula
            for adjustment, value in context_adjustments.items():
                if adjustment == 'difficulty_boost' and item.difficulty_level.value >= 4:
                    adjusted_score += value
                elif adjustment == 'difficulty_penalty' and item.difficulty_level.value >= 4:
                    adjusted_score -= value
                elif adjustment == 'easier_content' and item.difficulty_level.value <= 2:
                    adjusted_score += value
                elif adjustment == 'video_preference' and item.item_type == RecommendationType.VIDEO:
                    adjusted_score += value
                elif adjustment == 'test_preference' and item.item_type == RecommendationType.TEST:
                    adjusted_score += value
                elif adjustment == 'quick_questions' and item.estimated_time_minutes <= 15:
                    adjusted_score += value
                elif adjustment == 'short_content' and item.estimated_time_minutes <= 30:
                    adjusted_score += value

            adjusted_recommendations.append((item_id, adjusted_score))

        # Yeniden sırala
        adjusted_recommendations.sort(key=lambda x: x[1], reverse=True)
        return adjusted_recommendations


class IntelligentRecommendationEngine:
    """Ana akıllı öneri motoru"""

    def __init__(self):
        self.hybrid_recommender = HybridRecommender()
        self.knowledge_based = KnowledgeBasedRecommender()
        self.context_aware = ContextAwareRecommender()

        # Recommendation tracking
        self.recommendation_history = []
        self.user_feedback = []
        self.performance_metrics = {}

        # A/B testing için
        self.strategy_weights = {
            RecommendationStrategy.HYBRID: 0.4,
            RecommendationStrategy.KNOWLEDGE_BASED: 0.3,
            RecommendationStrategy.CONTEXT_AWARE: 0.3
        }

    def initialize(self, interactions: List[InteractionData],
                  items: List[RecommendationItem]) -> None:
        """Sistemleri başlat"""
        self.items = items
        self.items_dict = {item.item_id: item for item in items}

        # Alt sistemleri başlat
        self.hybrid_recommender.prepare_data(interactions, items)
        self.hybrid_recommender.train()
        self.knowledge_based.initialize_yks_knowledge()

        logging.info(f"Recommendation engine initialized with {len(items)} items")

    def get_personalized_recommendations(self, user_id: str, user_profile: UserProfile,
                                       context: Dict[str, Any] = None,
                                       n_recommendations: int = 10,
                                       recommendation_type: RecommendationType = None) -> List[Recommendation]:
        """Kişiselleştirilmiş öneriler al"""

        context = context or {}
        all_recommendations = []

        # Hibrit öneriler
        hybrid_recs = self.hybrid_recommender.get_recommendations(
            user_id, user_profile, n_recommendations * 2
        )

        for item_id, score in hybrid_recs:
            if item_id in self.items_dict:
                item = self.items_dict[item_id]
                # Tip filtresi
                if recommendation_type is None or item.item_type == recommendation_type:
                    recommendation = Recommendation(
                        user_id=user_id,
                        item=item,
                        score=score,
                        strategy=RecommendationStrategy.HYBRID,
                        reasoning=["Diğer benzer öğrencilerin tercihleri", "İçerik benzerliği"],
                        confidence=min(0.9, score * 2)
                    )
                    all_recommendations.append(recommendation)

        # Bilgi tabanlı öneriler
        kb_items = self.knowledge_based.get_recommendations(user_profile, self.items, context)
        for item_id in kb_items:
            if item_id in self.items_dict and item_id not in [r.item.item_id for r in all_recommendations]:
                item = self.items_dict[item_id]
                if recommendation_type is None or item.item_type == recommendation_type:
                    recommendation = Recommendation(
                        user_id=user_id,
                        item=item,
                        score=0.8,  # Sabit yüksek skor
                        strategy=RecommendationStrategy.KNOWLEDGE_BASED,
                        reasoning=["Eğitim uzmanı kuralları", "Öğrenme yolu optimizasyonu"],
                        confidence=0.9
                    )
                    all_recommendations.append(recommendation)

        # Bağlam farkındalığı uygula
        base_recs = [(r.item.item_id, r.score) for r in all_recommendations]
        context_adjusted = self.context_aware.adjust_recommendations(
            base_recs, self.items, context
        )

        # Final öneriler listesi
        final_recommendations = []
        for item_id, adjusted_score in context_adjusted:
            # Mevcut recommendation'ı bul ve güncelle
            for rec in all_recommendations:
                if rec.item.item_id == item_id:
                    rec.score = adjusted_score
                    rec.strategy = RecommendationStrategy.CONTEXT_AWARE
                    rec.reasoning.append("Mevcut bağlam ve çalışma durumuna göre ayarlandı")
                    rec.context = context
                    final_recommendations.append(rec)
                    break

        # Skor sıralaması ve filtrele
        final_recommendations.sort(key=lambda x: x.score, reverse=True)
        selected_recommendations = final_recommendations[:n_recommendations]

        # Geçmişe kaydet
        self.recommendation_history.extend(selected_recommendations)

        return selected_recommendations

    def get_next_question_recommendation(self, user_id: str, user_profile: UserProfile,
                                       current_subject: str, current_topic: str = None,
                                       target_difficulty: DifficultyLevel = None) -> Optional[Recommendation]:
        """Sonraki soru önerisi"""

        context = {
            'current_subject': current_subject,
            'current_topic': current_topic,
            'session_type': 'question_solving'
        }

        # Hedef zorluk seviyesi belirleme
        if target_difficulty is None:
            # Adaptive difficulty
            recent_accuracy = user_profile.subject_accuracies.get(current_subject, 0.5)
            if recent_accuracy > 0.8:
                target_difficulty = DifficultyLevel(min(5, user_profile.preferred_difficulty.value + 1))
            elif recent_accuracy < 0.5:
                target_difficulty = DifficultyLevel(max(1, user_profile.preferred_difficulty.value - 1))
            else:
                target_difficulty = user_profile.preferred_difficulty

        # Uygun soruları filtrele
        suitable_questions = []
        for item in self.items:
            if (item.item_type == RecommendationType.QUESTION and
                item.subject == current_subject and
                item.difficulty_level == target_difficulty and
                item.item_id not in user_profile.completed_items):

                # Konu eşleşmesi bonus
                score = 0.5
                if current_topic and item.topic == current_topic:
                    score += 0.3

                suitable_questions.append((item.item_id, score))

        if not suitable_questions:
            return None

        # En uygun soruyu seç
        suitable_questions.sort(key=lambda x: x[1], reverse=True)
        best_item_id = suitable_questions[0][0]
        best_item = self.items_dict[best_item_id]

        return Recommendation(
            user_id=user_id,
            item=best_item,
            score=suitable_questions[0][1],
            strategy=RecommendationStrategy.KNOWLEDGE_BASED,
            reasoning=[
                f"Mevcut {current_subject} performansınıza uygun zorluk",
                "Adaptif öğrenme algoritması önerisi",
                f"Hedef seviye: {target_difficulty.name}"
            ],
            confidence=0.85,
            context=context
        )

    def get_study_plan_recommendations(self, user_profile: UserProfile,
                                     days_until_exam: int) -> List[Recommendation]:
        """Çalışma planı önerileri"""

        recommendations = []
        daily_hours = user_profile.daily_study_hours

        # Zayıf konular için yoğun çalışma
        for subject in user_profile.weak_subjects[:3]:  # En fazla 3 zayıf konu
            study_plan_item = RecommendationItem(
                item_id=f"study_plan_{subject}",
                item_type=RecommendationType.STUDY_PLAN,
                title=f"{subject} Yoğunlaştırma Programı",
                description=f"{subject} konusunda {days_until_exam} günlük yoğunlaştırma çalışması",
                subject=subject,
                difficulty_level=DifficultyLevel.MEDIUM,
                estimated_time_minutes=int(daily_hours * 60 * 0.4),  # %40 zayıf konulara
                metadata={
                    'daily_time_minutes': int(daily_hours * 60 * 0.4 / len(user_profile.weak_subjects)),
                    'focus_areas': ['temel_kavramlar', 'coktan_secmeli_sorular', 'hiz_calismasi'],
                    'success_criteria': f"{subject} doğruluk oranını %80'e çıkar"
                }
            )

            recommendation = Recommendation(
                user_id=user_profile.user_id,
                item=study_plan_item,
                score=0.9,
                strategy=RecommendationStrategy.KNOWLEDGE_BASED,
                reasoning=[
                    f"Zayıf konu - öncelikli çalışma gerekli",
                    f"{days_until_exam} gün kaldı - yoğunlaştırma öneriliyor"
                ],
                confidence=0.95
            )
            recommendations.append(recommendation)

        # Deneme sınav programı
        test_frequency = max(1, days_until_exam // 7)  # Haftada bir deneme
        test_plan_item = RecommendationItem(
            item_id="test_plan_yks",
            item_type=RecommendationType.STUDY_PLAN,
            title="YKS Deneme Sınav Programı",
            description=f"{test_frequency} adet deneme sınavı ile gerçek sınav simülasyonu",
            subject="Genel",
            difficulty_level=DifficultyLevel.HARD,
            estimated_time_minutes=180,  # 3 saat deneme
            metadata={
                'test_count': test_frequency,
                'schedule': 'haftalik',
                'includes': ['TYT', 'AYT'],
                'analysis_included': True
            }
        )

        test_recommendation = Recommendation(
            user_id=user_profile.user_id,
            item=test_plan_item,
            score=0.85,
            strategy=RecommendationStrategy.KNOWLEDGE_BASED,
            reasoning=[
                "Sınav deneyimi kazanımı",
                "Zaman yönetimi pratiği",
                "Performans ölçümü ve analiz"
            ],
            confidence=0.9
        )
        recommendations.append(test_recommendation)

        return recommendations

    def record_user_feedback(self, user_id: str, item_id: str,
                           feedback_type: str, rating: float = None) -> None:
        """Kullanıcı geri bildirimini kaydet"""
        feedback = {
            'user_id': user_id,
            'item_id': item_id,
            'feedback_type': feedback_type,  # like, dislike, helpful, not_helpful
            'rating': rating,
            'timestamp': datetime.now()
        }
        self.user_feedback.append(feedback)

        # Performans metriklerini güncelle
        self._update_performance_metrics(feedback)

    def _update_performance_metrics(self, feedback: Dict[str, Any]) -> None:
        """Performans metriklerini güncelle"""
        if 'precision' not in self.performance_metrics:
            self.performance_metrics = {
                'precision': 0.0,
                'user_satisfaction': 0.0,
                'engagement_rate': 0.0,
                'total_feedback': 0
            }

        # Basit metrikleri güncelle
        self.performance_metrics['total_feedback'] += 1

        if feedback['feedback_type'] in ['like', 'helpful']:
            positive_feedback = sum(1 for f in self.user_feedback
                                  if f['feedback_type'] in ['like', 'helpful'])
            self.performance_metrics['user_satisfaction'] = positive_feedback / len(self.user_feedback)

    def get_recommendation_explanation(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Öneri açıklaması oluştur"""
        explanation = {
            'why_recommended': recommendation.reasoning,
            'strategy_used': recommendation.strategy.value,
            'confidence_level': f"{recommendation.confidence*100:.0f}%",
            'estimated_benefit': self._estimate_learning_benefit(recommendation),
            'alternative_options': self._get_alternative_recommendations(recommendation),
            'learning_path_position': self._get_learning_path_position(recommendation)
        }

        return explanation

    def _estimate_learning_benefit(self, recommendation: Recommendation) -> str:
        """Öğrenme fayda tahmini"""
        item = recommendation.item

        if item.item_type == RecommendationType.QUESTION:
            return f"Bu soru, {item.subject} konusunda becerilerinizi %{recommendation.score*20:.0f} artırabilir"
        elif item.item_type == RecommendationType.VIDEO:
            return f"Bu video ile {item.topic} konusunu %{recommendation.score*15:.0f} daha iyi anlayabilirsiniz"
        elif item.item_type == RecommendationType.TEST:
            return f"Bu test, genel YKS hazırlığınıza %{recommendation.score*10:.0f} katkı sağlayabilir"
        else:
            return f"Bu içerik, öğrenme hedefinize %{recommendation.score*18:.0f} yaklaştırabilir"

    def _get_alternative_recommendations(self, recommendation: Recommendation) -> List[str]:
        """Alternatif öneriler"""
        # Basit alternatifler - gerçekte daha sofistike olmalı
        alternatives = []
        item = recommendation.item

        # Aynı konuda farklı türde içerik
        for other_item in self.items:
            if (other_item.subject == item.subject and
                other_item.topic == item.topic and
                other_item.item_type != item.item_type and
                other_item.item_id != item.item_id):
                alternatives.append(f"{other_item.title} ({other_item.item_type.value})")

                if len(alternatives) >= 2:
                    break

        return alternatives

    def _get_learning_path_position(self, recommendation: Recommendation) -> str:
        """Öğrenme yolundaki konumu"""
        item = recommendation.item

        if item.prerequisites:
            return f"Önkoşul: {', '.join(item.prerequisites)} tamamlanmalı"
        elif item.difficulty_level == DifficultyLevel.VERY_EASY:
            return "Başlangıç seviyesi - temelleri atmak için ideal"
        elif item.difficulty_level == DifficultyLevel.VERY_HARD:
            return "İleri seviye - kavramları pekiştirdikten sonra öneriliyor"
        else:
            return "Mevcut seviyenize uygun - şimdi çalışabilirsiniz"

    def get_system_performance(self) -> Dict[str, Any]:
        """Sistem performansı raporla"""
        total_recommendations = len(self.recommendation_history)
        total_feedback = len(self.user_feedback)

        # Strategy dağılımı
        strategy_distribution = {}
        for rec in self.recommendation_history:
            strategy = rec.strategy.value
            strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1

        return {
            'total_recommendations_made': total_recommendations,
            'total_user_feedback': total_feedback,
            'feedback_rate': total_feedback / max(1, total_recommendations),
            'strategy_distribution': strategy_distribution,
            'performance_metrics': self.performance_metrics,
            'average_confidence': np.mean([r.confidence for r in self.recommendation_history]) if self.recommendation_history else 0,
            'recommendation_types': {
                item_type.value: sum(1 for r in self.recommendation_history if r.item.item_type == item_type)
                for item_type in RecommendationType
            }
        }


# === KIRO2 İçin Özelleştirilmiş Öneri Sistemi ===

class KIRO2RecommendationSystem:
    """KIRO2 için özelleştirilmiş öneri sistemi"""

    def __init__(self):
        self.engine = IntelligentRecommendationEngine()
        self.initialized = False

    async def initialize_for_kiro2(self, historical_data: Dict[str, Any]):
        """KIRO2 için sistemi başlat"""

        # Örnek eğitim içerikleri oluştur
        sample_items = self._create_sample_kiro2_items()

        # Örnek kullanıcı etkileşimleri oluştur
        sample_interactions = self._create_sample_interactions()

        # Sistemi başlat
        self.engine.initialize(sample_interactions, sample_items)
        self.initialized = True

        logging.info("KIRO2 Recommendation System initialized")

    def _create_sample_kiro2_items(self) -> List[RecommendationItem]:
        """Örnek KIRO2 içerikleri oluştur"""
        items = []

        # TYT Matematik soruları
        for i in range(50):
            item = RecommendationItem(
                item_id=f"tyt_mat_soru_{i+1}",
                item_type=RecommendationType.QUESTION,
                title=f"TYT Matematik Soru {i+1}",
                description="Temel düzeyde matematik sorusu",
                subject="TYT Matematik",
                topic=random.choice(["Cebir", "Geometri", "Sayılar", "Fonksiyonlar"]),
                difficulty_level=DifficultyLevel(random.randint(1, 4)),
                estimated_time_minutes=random.randint(2, 8),
                tags=["tyt", "matematik", "çoktan-seçmeli"]
            )
            items.append(item)

        # AYT Fizik soruları
        for i in range(30):
            item = RecommendationItem(
                item_id=f"ayt_fiz_soru_{i+1}",
                item_type=RecommendationType.QUESTION,
                title=f"AYT Fizik Soru {i+1}",
                description="AYT seviyesi fizik sorusu",
                subject="AYT Fizik",
                topic=random.choice(["Mekanik", "Elektrik", "Optik", "Modern Fizik"]),
                difficulty_level=DifficultyLevel(random.randint(2, 5)),
                estimated_time_minutes=random.randint(3, 12),
                tags=["ayt", "fizik", "sayısal"]
            )
            items.append(item)

        # Video dersler
        for i in range(20):
            item = RecommendationItem(
                item_id=f"video_ders_{i+1}",
                item_type=RecommendationType.VIDEO,
                title=f"Video Ders {i+1}",
                description="Konu anlatım videosu",
                subject=random.choice(["TYT Matematik", "TYT Türkçe", "AYT Fizik"]),
                topic="Temel Kavramlar",
                difficulty_level=DifficultyLevel.MEDIUM,
                estimated_time_minutes=random.randint(15, 45),
                tags=["video", "anlatım", "görsel"]
            )
            items.append(item)

        return items

    def _create_sample_interactions(self) -> List[InteractionData]:
        """Örnek kullanıcı etkileşimleri oluştur"""
        interactions = []

        # 100 öğrenci için etkileşim verileri
        for user_id in range(1, 101):
            user_id_str = f"student_{user_id}"

            # Her öğrenci için 10-50 etkileşim
            num_interactions = random.randint(10, 50)

            for _ in range(num_interactions):
                interaction = InteractionData(
                    user_id=user_id_str,
                    item_id=f"tyt_mat_soru_{random.randint(1, 50)}",
                    interaction_type=random.choice(['view', 'complete', 'like', 'bookmark']),
                    rating=random.uniform(1, 5),
                    time_spent=random.uniform(1, 30),
                    completion_rate=random.uniform(0.5, 1.0),
                    timestamp=datetime.now() - timedelta(days=random.randint(1, 90))
                )
                interactions.append(interaction)

        return interactions

    async def get_personalized_study_recommendations(self, student_id: str,
                                                   study_profile: Dict[str, Any],
                                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Kişiselleştirilmiş çalışma önerileri"""

        if not self.initialized:
            await self.initialize_for_kiro2({})

        # Kullanıcı profili oluştur
        user_profile = UserProfile(
            user_id=student_id,
            target_exam=study_profile.get('target_exam', 'YKS'),
            strong_subjects=study_profile.get('strong_subjects', []),
            weak_subjects=study_profile.get('weak_subjects', []),
            overall_accuracy=study_profile.get('overall_accuracy', 0.6),
            preferred_difficulty=DifficultyLevel(study_profile.get('preferred_difficulty', 3)),
            daily_study_hours=study_profile.get('daily_study_hours', 4.0),
            target_score=study_profile.get('target_score', 400)
        )

        # Bağlam bilgileri
        current_context = {
            'current_time': datetime.now(),
            'session_duration_minutes': context.get('session_duration', 60),
            'recent_accuracy': study_profile.get('recent_accuracy', 0.6),
            'mood': context.get('mood', 'neutral')
        }

        # Genel öneriler al
        general_recommendations = self.engine.get_personalized_recommendations(
            student_id, user_profile, current_context, n_recommendations=8
        )

        # Soru önerileri
        question_recommendations = self.engine.get_personalized_recommendations(
            student_id, user_profile, current_context,
            n_recommendations=5, recommendation_type=RecommendationType.QUESTION
        )

        # Video önerileri
        video_recommendations = self.engine.get_personalized_recommendations(
            student_id, user_profile, current_context,
            n_recommendations=3, recommendation_type=RecommendationType.VIDEO
        )

        # Sonraki soru önerisi
        next_question = None
        current_subject = context.get('current_subject')
        if current_subject:
            next_question = self.engine.get_next_question_recommendation(
                student_id, user_profile, current_subject
            )

        # Çalışma planı
        days_until_exam = context.get('days_until_exam', 180)
        study_plan = self.engine.get_study_plan_recommendations(user_profile, days_until_exam)

        return {
            'student_id': student_id,
            'recommendation_timestamp': datetime.now().isoformat(),
            'general_recommendations': [
                {
                    'item_id': r.item.item_id,
                    'title': r.item.title,
                    'type': r.item.item_type.value,
                    'subject': r.item.subject,
                    'difficulty': r.item.difficulty_level.name,
                    'estimated_time': r.item.estimated_time_minutes,
                    'score': round(r.score, 3),
                    'reasoning': r.reasoning,
                    'confidence': round(r.confidence, 2)
                }
                for r in general_recommendations
            ],
            'question_recommendations': [
                {
                    'item_id': r.item.item_id,
                    'title': r.item.title,
                    'subject': r.item.subject,
                    'topic': r.item.topic,
                    'difficulty': r.item.difficulty_level.name,
                    'estimated_time': r.item.estimated_time_minutes,
                    'score': round(r.score, 3)
                }
                for r in question_recommendations
            ],
            'video_recommendations': [
                {
                    'item_id': r.item.item_id,
                    'title': r.item.title,
                    'subject': r.item.subject,
                    'estimated_time': r.item.estimated_time_minutes,
                    'score': round(r.score, 3)
                }
                for r in video_recommendations
            ],
            'next_question': {
                'item_id': next_question.item.item_id,
                'title': next_question.item.title,
                'subject': next_question.item.subject,
                'difficulty': next_question.item.difficulty_level.name,
                'reasoning': next_question.reasoning
            } if next_question else None,
            'study_plan_suggestions': [
                {
                    'plan_id': r.item.item_id,
                    'title': r.item.title,
                    'description': r.item.description,
                    'focus_time_minutes': r.item.estimated_time_minutes,
                    'reasoning': r.reasoning,
                    'metadata': r.item.metadata
                }
                for r in study_plan
            ],
            'personalization_factors': {
                'strong_subjects': user_profile.strong_subjects,
                'weak_subjects': user_profile.weak_subjects,
                'preferred_difficulty': user_profile.preferred_difficulty.name,
                'daily_study_hours': user_profile.daily_study_hours,
                'context_factors': list(current_context.keys())
            }
        }

    def record_student_feedback(self, student_id: str, item_id: str,
                              feedback_type: str, additional_data: Dict[str, Any] = None):
        """Öğrenci geri bildirimini kaydet"""
        rating = None

        # Feedback türüne göre rating ata
        if feedback_type == 'helpful':
            rating = 5.0
        elif feedback_type == 'somewhat_helpful':
            rating = 3.0
        elif feedback_type == 'not_helpful':
            rating = 1.0
        elif feedback_type == 'completed_successfully':
            rating = 4.0

        self.engine.record_user_feedback(student_id, item_id, feedback_type, rating)

        logging.info(f"Recorded feedback: {student_id} -> {item_id} ({feedback_type})")

    def get_recommendation_explanation(self, student_id: str, item_id: str) -> Dict[str, Any]:
        """Öneri açıklaması al"""
        # İlgili öneriyi bul
        recommendation = None
        for rec in self.engine.recommendation_history:
            if rec.user_id == student_id and rec.item.item_id == item_id:
                recommendation = rec
                break

        if not recommendation:
            return {'error': 'Recommendation not found'}

        explanation = self.engine.get_recommendation_explanation(recommendation)

        # KIRO2 özel açıklamalar ekle
        kiro2_explanation = {
            'why_this_content': self._generate_kiro2_explanation(recommendation),
            'learning_impact': explanation['estimated_benefit'],
            'best_time_to_study': self._suggest_study_time(recommendation),
            'preparation_tips': self._generate_study_tips(recommendation),
            'success_probability': f"{recommendation.confidence * 100:.0f}%"
        }

        explanation.update(kiro2_explanation)
        return explanation

    def _generate_kiro2_explanation(self, recommendation: Recommendation) -> str:
        """KIRO2 özel açıklama oluştur"""
        item = recommendation.item

        if item.item_type == RecommendationType.QUESTION:
            return f"Bu soru, {item.subject} alanındaki performansınızı artırmak için özel olarak seçildi. Zorluk seviyesi mevcut becerilerinize uygun."

        elif item.item_type == RecommendationType.VIDEO:
            return f"Bu video ders, {item.subject} konusundaki eksiklerinizi gidermek ve kavramsal anlayışınızı derinleştirmek için öneriliyor."

        elif item.item_type == RecommendationType.TEST:
            return f"Bu test, YKS hazırlığınızın hangi aşamasında olduğunuzu ölçmeniz ve eksik alanları tespit etmeniz için öneriliyor."

        else:
            return f"Bu içerik, öğrenme hedefinize ulaşmanızda size yardımcı olacak şekilde kişiselleştirilmiş."

    def _suggest_study_time(self, recommendation: Recommendation) -> str:
        """Çalışma zamanı önerisi"""
        item = recommendation.item

        if item.estimated_time_minutes <= 15:
            return "Kısa molalarda çalışılabilir - ara zamanlarda ideal"
        elif item.estimated_time_minutes <= 45:
            return "Odaklanabileceğiniz bir zaman diliminde çalışın - sabah saatleri öneriliyor"
        else:
            return "Uzun bir çalışma seansı için planlayın - hafta sonları uygun olabilir"

    def _generate_study_tips(self, recommendation: Recommendation) -> List[str]:
        """Çalışma ipuçları oluştur"""
        tips = []
        item = recommendation.item

        if item.item_type == RecommendationType.QUESTION:
            tips.extend([
                "Soruyu okuduktan sonra ne sorulduğunu kendi kelimelerinizle ifade edin",
                "Yanıtınızdan emin değilseniz eleme yöntemi kullanın",
                "Zaman ölçerek çalışma alışkanlığı edinin"
            ])

        elif item.item_type == RecommendationType.VIDEO:
            tips.extend([
                "Not alarak izleyin - önemli noktaları yazın",
                "Anlamadığınız yerlerde videoyu duraklatın",
                "İzlediğiniz konuyla ilgili sorular çözün"
            ])

        if item.difficulty_level.value >= 4:
            tips.append("Zor seviye - acele etmeyin, temelden başlayın")

        return tips[:3]  # En fazla 3 ipucu

    def get_system_analytics(self) -> Dict[str, Any]:
        """Sistem analitikleri"""
        performance = self.engine.get_system_performance()

        kiro2_analytics = {
            'active_students': len(set(r.user_id for r in self.engine.recommendation_history)),
            'total_recommendations': performance['total_recommendations_made'],
            'average_confidence': performance['average_confidence'],
            'most_recommended_subjects': self._get_popular_subjects(),
            'recommendation_success_rate': self._calculate_success_rate(),
            'personalization_effectiveness': self._measure_personalization_effectiveness()
        }

        return {
            'kiro2_analytics': kiro2_analytics,
            'engine_performance': performance,
            'system_health': 'Optimal' if kiro2_analytics['recommendation_success_rate'] > 0.7 else 'Needs Attention'
        }

    def _get_popular_subjects(self) -> Dict[str, int]:
        """Popüler konular"""
        subject_counts = {}
        for rec in self.engine.recommendation_history:
            subject = rec.item.subject
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

        return dict(sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:5])

    def _calculate_success_rate(self) -> float:
        """Başarı oranı hesapla"""
        if not self.engine.user_feedback:
            return 0.0

        positive_feedback = sum(
            1 for feedback in self.engine.user_feedback
            if feedback['feedback_type'] in ['like', 'helpful', 'completed_successfully']
        )

        return positive_feedback / len(self.engine.user_feedback)

    def _measure_personalization_effectiveness(self) -> float:
        """Kişiselleştirme etkinliği ölç"""
        if not self.engine.recommendation_history:
            return 0.0

        # Ortalama güven skorunu etkinlik olarak kullan
        avg_confidence = np.mean([r.confidence for r in self.engine.recommendation_history])
        return float(avg_confidence)


# === Örnek Kullanım ===

async def example_kiro2_recommendations():
    """KIRO2 öneri sistemi örneği"""

    # Öneri sistemini başlat
    kiro2_recommendations = KIRO2RecommendationSystem()

    print("[TARGET] KIRO2 Akıllı Öneri Sistemi Başlatılıyor...")

    # Sistemi başlat
    await kiro2_recommendations.initialize_for_kiro2({})

    print("[CHECK] Öneri sistemi hazır!")

    # Örnek öğrenci profili
    student_profile = {
        'target_exam': 'YKS',
        'strong_subjects': ['TYT Matematik', 'AYT Fizik'],
        'weak_subjects': ['TYT Türkçe', 'TYT Sosyal'],
        'overall_accuracy': 0.72,
        'recent_accuracy': 0.68,
        'preferred_difficulty': 3,  # Orta seviye
        'daily_study_hours': 5.5,
        'target_score': 420
    }

    # Bağlam bilgileri
    context = {
        'current_subject': 'TYT Matematik',
        'session_duration': 90,  # 90 dakikalık çalışma seansı
        'mood': 'motivated',
        'days_until_exam': 45
    }

    # Kişiselleştirilmiş öneriler al
    print("\n[MAG] Kişiselleştirilmiş öneriler alınıyor...")

    recommendations = await kiro2_recommendations.get_personalized_study_recommendations(
        student_id="kiro2_student_123",
        study_profile=student_profile,
        context=context
    )

    print(f"\n[BOOKS] Genel Öneriler ({len(recommendations['general_recommendations'])}):")
    for i, rec in enumerate(recommendations['general_recommendations'][:3], 1):
        print(f"  {i}. {rec['title']}")
        print(f"     Konu: {rec['subject']} | Zorluk: {rec['difficulty']}")
        print(f"     Süre: {rec['estimated_time']} dk | Skor: {rec['score']:.3f}")
        print(f"     Sebep: {', '.join(rec['reasoning'][:2])}")

    print(f"\n❓ Soru Önerileri ({len(recommendations['question_recommendations'])}):")
    for i, rec in enumerate(recommendations['question_recommendations'][:3], 1):
        print(f"  {i}. {rec['title']} - {rec['subject']} ({rec['difficulty']})")

    print(f"\n🎥 Video Önerileri ({len(recommendations['video_recommendations'])}):")
    for i, rec in enumerate(recommendations['video_recommendations'], 1):
        print(f"  {i}. {rec['title']} - {rec['estimated_time']} dakika")

    # Sonraki soru önerisi
    if recommendations['next_question']:
        next_q = recommendations['next_question']
        print(f"\n[STAR] Sonraki Önerilen Soru:")
        print(f"  {next_q['title']} ({next_q['difficulty']})")
        print(f"  Sebep: {', '.join(next_q['reasoning'])}")

    # Çalışma planı
    if recommendations['study_plan_suggestions']:
        print(f"\n[CLIPBOARD] Çalışma Planı Önerileri:")
        for plan in recommendations['study_plan_suggestions']:
            print(f"  • {plan['title']}")
            print(f"    {plan['description']}")
            print(f"    Odak süresi: {plan['focus_time_minutes']} dakika/gün")

    # Kişiselleştirme faktörleri
    factors = recommendations['personalization_factors']
    print(f"\n[PALETTE] Kişiselleştirme Faktörleri:")
    print(f"  Güçlü konular: {', '.join(factors['strong_subjects']) if factors['strong_subjects'] else 'Tespit edilmedi'}")
    print(f"  Gelişim alanları: {', '.join(factors['weak_subjects']) if factors['weak_subjects'] else 'Yok'}")
    print(f"  Tercih edilen zorluk: {factors['preferred_difficulty']}")
    print(f"  Günlük çalışma: {factors['daily_study_hours']} saat")

    # Geri bildirim simülasyonu
    print(f"\n👍 Geri bildirim kaydediliyor...")
    first_recommendation = recommendations['general_recommendations'][0]
    kiro2_recommendations.record_student_feedback(
        student_id="kiro2_student_123",
        item_id=first_recommendation['item_id'],
        feedback_type="helpful"
    )

    # Öneri açıklaması
    print(f"\n[BULB] Öneri Açıklaması:")
    explanation = kiro2_recommendations.get_recommendation_explanation(
        student_id="kiro2_student_123",
        item_id=first_recommendation['item_id']
    )

    if 'error' not in explanation:
        print(f"  Neden öneriliyor: {explanation['why_this_content']}")
        print(f"  Öğrenme etkisi: {explanation['learning_impact']}")
        print(f"  En iyi çalışma zamanı: {explanation['best_time_to_study']}")
        print(f"  Başarı olasılığı: {explanation['success_probability']}")

        if explanation['preparation_tips']:
            print(f"  Çalışma ipuçları:")
            for tip in explanation['preparation_tips']:
                print(f"    • {tip}")

    # Sistem analitikleri
    analytics = kiro2_recommendations.get_system_analytics()
    print(f"\n[CHART] Sistem Analitikleri:")
    kiro2_data = analytics['kiro2_analytics']
    print(f"  Aktif öğrenci sayısı: {kiro2_data['active_students']}")
    print(f"  Toplam öneri: {kiro2_data['total_recommendations']}")
    print(f"  Ortalama güven: {kiro2_data['average_confidence']:.2f}")
    print(f"  Başarı oranı: %{kiro2_data['recommendation_success_rate']*100:.1f}")
    print(f"  Sistem durumu: {analytics['system_health']}")

    print(f"\n✨ KIRO2 Akıllı Öneri Sistemi analizi tamamlandı!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_kiro2_recommendations())
