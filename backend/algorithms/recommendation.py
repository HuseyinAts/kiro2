"""
Öneri Algoritmaları
Collaborative Filtering ve Content-Based Filtering
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class User:
    """Kullanıcı modeli"""

    user_id: str
    profile: Dict[str, Any]  # Demografik bilgiler
    preferences: Dict[str, float]  # Tercihler
    interaction_history: List[Dict[str, Any]]  # Etkileşim geçmişi
    learning_style: str
    knowledge_level: str


@dataclass
class Item:
    """İçerik/kaynak modeli"""

    item_id: str
    title: str
    description: str
    features: Dict[str, Any]  # İçerik özellikleri
    tags: List[str]
    difficulty_level: str
    item_type: str  # video, article, quiz, etc.
    metadata: Dict[str, Any]


@dataclass
class Recommendation:
    """Öneri"""

    user_id: str
    item_id: str
    score: float
    method: str  # collaborative, content-based, hybrid
    reasoning: str
    timestamp: datetime


class CollaborativeFiltering:
    """İşbirlikçi filtreleme algoritması"""

    def __init__(self, n_factors: int = 50):
        """
        Args:
            n_factors: Matrix factorization için faktör sayısı
        """
        self.n_factors = n_factors
        self.user_item_matrix = None
        self.user_features = None
        self.item_features = None
        self.svd = TruncatedSVD(n_components=n_factors)

    def build_user_item_matrix(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        """
        Kullanıcı-içerik etkileşim matrisini oluştur

        Args:
            interactions: Etkileşim verileri

        Returns:
            User-item matrix
        """
        try:
            # Benzersiz kullanıcı ve içerikleri bul
            users = list(set([i["user_id"] for i in interactions]))
            items = list(set([i["item_id"] for i in interactions]))

            # Matris oluştur
            matrix = np.zeros((len(users), len(items)))

            # Etkileşimleri matrise doldur
            user_idx_map = {u: i for i, u in enumerate(users)}
            item_idx_map = {it: i for i, it in enumerate(items)}

            for interaction in interactions:
                user_idx = user_idx_map.get(interaction["user_id"])
                item_idx = item_idx_map.get(interaction["item_id"])
                if user_idx is not None and item_idx is not None:
                    # Etkileşim skorunu hesapla
                    score = self._calculate_interaction_score(interaction)
                    matrix[user_idx, item_idx] = score

            self.user_item_matrix = matrix
            self.user_idx_map = user_idx_map
            self.item_idx_map = item_idx_map

            logger.info(f"User-item matrix built: {matrix.shape}")
            return matrix

        except Exception as e:
            logger.error(f"Build matrix error: {str(e)}")
            return np.array([])

    def _calculate_interaction_score(self, interaction: Dict[str, Any]) -> float:
        """Etkileşim skorunu hesapla"""
        # Etkileşim tipine göre skor
        action = interaction.get("action", "view")
        scores = {
            "view": 1.0,
            "like": 2.0,
            "complete": 3.0,
            "share": 4.0,
            "quiz_high_score": 5.0,
        }
        base_score = scores.get(action, 1.0)

        # Zaman faktörü (yeni etkileşimler daha değerli)
        time_decay = interaction.get("time_decay", 1.0)

        # Performans faktörü (varsa)
        performance = interaction.get("performance", 1.0)

        return base_score * time_decay * performance

    def fit(self, interactions: List[Dict[str, Any]]):
        """
        Matrix factorization modelini eğit

        Args:
            interactions: Etkileşim verileri
        """
        try:
            # Matrisi oluştur
            matrix = self.build_user_item_matrix(interactions)

            if matrix.size > 0:
                # SVD ile faktörizasyon
                self.user_features = self.svd.fit_transform(matrix)
                self.item_features = self.svd.components_.T

                logger.info(f"Collaborative filtering model trained")

        except Exception as e:
            logger.error(f"Fit error: {str(e)}")

    def predict(
        self, user_id: str, item_ids: List[str], n_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Kullanıcı için öneriler üret

        Args:
            user_id: Kullanıcı ID
            item_ids: Aday içerik ID'leri
            n_recommendations: Öneri sayısı

        Returns:
            [(item_id, score)] listesi
        """
        try:
            if self.user_features is None:
                return []

            # Kullanıcı indeksini bul
            user_idx = self.user_idx_map.get(user_id)
            if user_idx is None:
                # Yeni kullanıcı - ortalama özellikler kullan
                user_feature = np.mean(self.user_features, axis=0)
            else:
                user_feature = self.user_features[user_idx]

            # Her içerik için skor hesapla
            scores = []
            for item_id in item_ids:
                item_idx = self.item_idx_map.get(item_id)
                if item_idx is not None:
                    item_feature = self.item_features[item_idx]
                    score = np.dot(user_feature, item_feature)
                    scores.append((item_id, float(score)))

            # Skorlara göre sırala
            scores.sort(key=lambda x: x[1], reverse=True)

            return scores[:n_recommendations]

        except Exception as e:
            logger.error(f"Predict error: {str(e)}")
            return []


class ContentBasedFiltering:
    """İçerik tabanlı filtreleme algoritması"""

    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=1000)
        self.content_features = None
        self.item_ids = []

    def build_content_features(self, items: List[Item]):
        """
        İçerik özellik vektörlerini oluştur

        Args:
            items: İçerik listesi
        """
        try:
            # Metin içeriklerini birleştir
            texts = []
            self.item_ids = []

            for item in items:
                # Başlık, açıklama ve etiketleri birleştir
                text = f"{item.title} {item.description} {' '.join(item.tags)}"
                texts.append(text)
                self.item_ids.append(item.item_id)

            # TF-IDF vektörleri oluştur
            if texts:
                self.content_features = self.tfidf.fit_transform(texts)
                logger.info(f"Content features built: {self.content_features.shape}")

        except Exception as e:
            logger.error(f"Build content features error: {str(e)}")

    def get_user_profile(self, user: User, interaction_items: List[Item]) -> np.ndarray:
        """
        Kullanıcı profil vektörü oluştur

        Args:
            user: Kullanıcı
            interaction_items: Kullanıcının etkileşimde bulunduğu içerikler

        Returns:
            Kullanıcı profil vektörü
        """
        try:
            if not interaction_items or self.content_features is None:
                return np.zeros(self.content_features.shape[1])

            # Etkileşimde bulunulan içeriklerin özellik vektörlerini al
            item_vectors = []
            for item in interaction_items:
                if item.item_id in self.item_ids:
                    idx = self.item_ids.index(item.item_id)
                    item_vectors.append(self.content_features[idx].toarray()[0])

            if item_vectors:
                # Ortalama vektör (ağırlıklı ortalama da olabilir)
                user_profile = np.mean(item_vectors, axis=0)
            else:
                user_profile = np.zeros(self.content_features.shape[1])

            return user_profile

        except Exception as e:
            logger.error(f"Get user profile error: {str(e)}")
            return np.zeros(self.content_features.shape[1])

    def recommend(
        self,
        user: User,
        candidate_items: List[Item],
        interaction_items: List[Item],
        n_recommendations: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        İçerik tabanlı öneriler üret

        Args:
            user: Kullanıcı
            candidate_items: Aday içerikler
            interaction_items: Kullanıcının geçmiş etkileşimleri
            n_recommendations: Öneri sayısı

        Returns:
            [(item_id, score)] listesi
        """
        try:
            if self.content_features is None:
                return []

            # Kullanıcı profilini oluştur
            user_profile = self.get_user_profile(user, interaction_items)

            # Her aday içerik için benzerlik hesapla
            scores = []
            for item in candidate_items:
                if item.item_id in self.item_ids:
                    idx = self.item_ids.index(item.item_id)
                    item_vector = self.content_features[idx].toarray()[0]

                    # Cosine similarity
                    similarity = cosine_similarity(
                        user_profile.reshape(1, -1), item_vector.reshape(1, -1)
                    )[0][0]

                    # Zorluk seviyesi uyumu
                    difficulty_match = 1.0
                    if user.knowledge_level == item.difficulty_level:
                        difficulty_match = 1.2
                    elif (
                        abs(
                            self._level_to_num(user.knowledge_level)
                            - self._level_to_num(item.difficulty_level)
                        )
                        > 1
                    ):
                        difficulty_match = 0.5

                    # Öğrenme stili uyumu
                    style_match = 1.0
                    if user.learning_style in item.features.get("suitable_styles", []):
                        style_match = 1.3

                    # Final skor
                    final_score = similarity * difficulty_match * style_match
                    scores.append((item.item_id, float(final_score)))

            # Sırala ve döndür
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:n_recommendations]

        except Exception as e:
            logger.error(f"Recommend error: {str(e)}")
            return []

    def _level_to_num(self, level: str) -> int:
        """Seviyeyi sayıya çevir"""
        levels = {
            "beginner": 1,
            "elementary": 2,
            "intermediate": 3,
            "advanced": 4,
            "expert": 5,
        }
        return levels.get(level, 3)


class HybridRecommender:
    """Hibrit öneri sistemi (Collaborative + Content-Based)"""

    def __init__(self, alpha: float = 0.5):
        """
        Args:
            alpha: CF ve CBF ağırlık dengesi (0-1)
        """
        self.cf = CollaborativeFiltering()
        self.cbf = ContentBasedFiltering()
        self.alpha = alpha  # CF ağırlığı
        self.recommendations_cache = {}

    def train(self, interactions: List[Dict[str, Any]], items: List[Item]):
        """
        Modelleri eğit

        Args:
            interactions: Etkileşim verileri
            items: İçerik verileri
        """
        # Collaborative filtering eğit
        self.cf.fit(interactions)

        # Content-based filtering hazırla
        self.cbf.build_content_features(items)

        logger.info("Hybrid recommender trained")

    def recommend(
        self,
        user: User,
        candidate_items: List[Item],
        interaction_items: List[Item],
        interactions: List[Dict[str, Any]],
        n_recommendations: int = 10,
    ) -> List[Recommendation]:
        """
        Hibrit öneriler üret

        Args:
            user: Kullanıcı
            candidate_items: Aday içerikler
            interaction_items: Kullanıcının geçmiş içerikleri
            interactions: Tüm etkileşimler
            n_recommendations: Öneri sayısı

        Returns:
            Öneri listesi
        """
        try:
            # CF önerileri
            item_ids = [item.item_id for item in candidate_items]
            cf_scores = self.cf.predict(user.user_id, item_ids, n_recommendations * 2)
            cf_dict = dict(cf_scores)

            # CBF önerileri
            cbf_scores = self.cbf.recommend(
                user, candidate_items, interaction_items, n_recommendations * 2
            )
            cbf_dict = dict(cbf_scores)

            # Skorları birleştir
            hybrid_scores = {}
            all_item_ids = set(cf_dict.keys()) | set(cbf_dict.keys())

            for item_id in all_item_ids:
                cf_score = cf_dict.get(item_id, 0)
                cbf_score = cbf_dict.get(item_id, 0)

                # Normalize et
                cf_norm = cf_score / max(cf_dict.values()) if cf_dict else 0
                cbf_norm = cbf_score / max(cbf_dict.values()) if cbf_dict else 0

                # Hibrit skor
                hybrid_score = self.alpha * cf_norm + (1 - self.alpha) * cbf_norm
                hybrid_scores[item_id] = hybrid_score

            # Öneri objelerini oluştur
            recommendations = []
            sorted_items = sorted(
                hybrid_scores.items(), key=lambda x: x[1], reverse=True
            )

            for item_id, score in sorted_items[:n_recommendations]:
                rec = Recommendation(
                    user_id=user.user_id,
                    item_id=item_id,
                    score=score,
                    method="hybrid",
                    reasoning=f"CF: {cf_dict.get(item_id, 0):.2f}, CBF: {cbf_dict.get(item_id, 0):.2f}",
                    timestamp=datetime.now(),
                )
                recommendations.append(rec)

            # Cache'e kaydet
            cache_key = f"{user.user_id}_{datetime.now().date()}"
            self.recommendations_cache[cache_key] = recommendations

            logger.info(
                f"Generated {len(recommendations)} hybrid recommendations for user {user.user_id}"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Hybrid recommend error: {str(e)}")
            return []

    def update_weights(self, feedback: Dict[str, Any]):
        """
        Geri bildirime göre ağırlıkları güncelle

        Args:
            feedback: Kullanıcı geri bildirimi
        """
        # Hangi yöntemin daha başarılı olduğunu analiz et
        cf_success = feedback.get("cf_success_rate", 0.5)
        cbf_success = feedback.get("cbf_success_rate", 0.5)

        # Alpha'yı güncelle
        total = cf_success + cbf_success
        if total > 0:
            self.alpha = cf_success / total
            logger.info(f"Updated alpha to {self.alpha:.2f}")


# Test için örnek kullanım
if __name__ == "__main__":
    # Örnek veriler
    users = [
        User("user1", {}, {"math": 0.8}, [], "visual", "intermediate"),
        User("user2", {}, {"science": 0.9}, [], "reading", "advanced"),
    ]

    items = [
        Item(
            "item1",
            "Matematik Temelleri",
            "Temel matematik konuları",
            {"duration": 30},
            ["matematik", "temel"],
            "beginner",
            "video",
            {},
        ),
        Item(
            "item2",
            "Fizik 101",
            "Fizik giriş dersi",
            {"duration": 45},
            ["fizik", "bilim"],
            "intermediate",
            "article",
            {},
        ),
    ]

    interactions = [
        {"user_id": "user1", "item_id": "item1", "action": "complete"},
        {"user_id": "user2", "item_id": "item2", "action": "view"},
    ]

    # Hibrit öneri sistemi
    recommender = HybridRecommender()
    recommender.train(interactions, items)

    # Öneriler
    recommendations = recommender.recommend(
        users[0], items, [items[0]], interactions, n_recommendations=5
    )

    for rec in recommendations:
        print(f"Item: {rec.item_id}, Score: {rec.score:.2f}, Method: {rec.method}")
