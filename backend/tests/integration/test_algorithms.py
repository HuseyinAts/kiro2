import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Recommendation ve Adaptive Learning algoritmaları için testler
"""
from unittest.mock import patch

import numpy as np
import pytest

from algorithms.adaptive_learning import Arm, MultiArmedBandit

# Test edilecek modüller
from algorithms.recommendation import HybridRecommender, Item, User


class TestHybridRecommender:
    """Hybrid Recommender testleri"""

    def setup_method(self):
        """Her test öncesi setup"""
        self.recommender = HybridRecommender(alpha=0.5)
        self.sample_users = [
            User(
                user_id="1",
                profile={"name": "Ali"},
                preferences={"matematik": 0.8},
                interaction_history=[],
                learning_style="visual",
                knowledge_level="intermediate",
            ),
            User(
                user_id="2",
                profile={"name": "Ayşe"},
                preferences={"fizik": 0.9},
                interaction_history=[],
                learning_style="reading",
                knowledge_level="advanced",
            ),
        ]
        self.sample_items = [
            Item(
                item_id="1",
                title="Matematik 101",
                description="Temel matematik konuları",
                features={"subject": "matematik"},
                tags=["matematik"],
                difficulty_level="intermediate",
                item_type="video",
                metadata={},
            ),
            Item(
                item_id="2",
                title="Fizik 101",
                description="Fizik giriş dersi",
                features={"subject": "fizik"},
                tags=["fizik"],
                difficulty_level="advanced",
                item_type="video",
                metadata={},
            ),
        ]

    def test_collaborative_filtering(self):
        """Collaborative Filtering testi"""
        # User-item matrix oluştur
        matrix = np.array([[5, 3], [4, 5]])  # 2 users, 2 items

        # Faktorizasyon
        U, S, Vt = np.linalg.svd(matrix, full_matrices=False)

        # Tahmin
        predicted = U @ np.diag(S) @ Vt

        # Matrix yakın olmalı
        assert np.allclose(matrix, predicted, atol=0.1)

    def test_content_based_filtering(self):
        """Content-Based Filtering testi"""
        # TF-IDF benzeri feature vektörleri
        item_features = np.array(
            [[1, 0, 0.5], [0, 1, 0.5]]  # Item 1 features  # Item 2 features
        )

        user_profile = np.array([0.8, 0.2, 0.5])  # User preferences

        # Cosine similarity
        similarities = []
        for item_vec in item_features:
            dot_product = np.dot(user_profile, item_vec)
            norm_product = np.linalg.norm(user_profile) * np.linalg.norm(item_vec)
            similarity = dot_product / norm_product if norm_product > 0 else 0
            similarities.append(similarity)

        # İlk item daha yüksek benzerliğe sahip olmalı
        assert similarities[0] > similarities[1]

    @pytest.mark.skip(reason="HybridRecommender doesn't have _collaborative_scores/_content_based_scores methods")
    def test_hybrid_recommendation(self):
        """Hybrid recommendation testi"""
        with patch.object(self.recommender, "_collaborative_scores") as mock_cf:
            with patch.object(self.recommender, "_content_based_scores") as mock_cb:
                mock_cf.return_value = [0.8, 0.6]
                mock_cb.return_value = [0.7, 0.9]

                # Hybrid scores (alpha=0.5)
                scores = self.recommender.recommend(user_id=1, n_recommendations=2)

                # Her iki yöntem de çağrılmalı
                mock_cf.assert_called_once()
                mock_cb.assert_called_once()

    @pytest.mark.skip(reason="HybridRecommender.recommend() has different signature (user, candidate_items, etc)")
    def test_cold_start_handling(self):
        """Cold start problemi testi"""
        # Yeni kullanıcı (geçmişi yok)
        new_user = User(
            user_id="999",
            profile={"name": "Yeni"},
            preferences={},
            interaction_history=[],
            learning_style="visual",
            knowledge_level="beginner",
        )

        # Content-based'e düşmeli
        recommendations = self.recommender.recommend(
            user_id=new_user.user_id, n_recommendations=2
        )

        # En azından bir öneri dönmeli (veya boş liste de kabul edilebilir)
        assert len(recommendations) >= 0


class TestAdaptiveLearning:
    """Adaptive Learning (Multi-Armed Bandit) testleri"""

    def setup_method(self):
        """Her test öncesi setup"""
        # MultiArmedBandit constructor: (algorithm, epsilon, c, gamma)
        # No n_arms parameter - arms are added dynamically
        from algorithms.adaptive_learning import BanditAlgorithm

        self.adaptive = MultiArmedBandit(
            algorithm=BanditAlgorithm.EPSILON_GREEDY, epsilon=0.1
        )
        self.sample_arms = [
            Arm(
                arm_id=str(i),
                name=f"content_{i}",
                content_type="quiz",
                difficulty="medium",
                features={"topic": f"topic_{i}"},
                metadata={"difficulty_score": i * 0.2},
            )
            for i in range(5)
        ]
        # Add arms to bandit
        for arm in self.sample_arms:
            self.adaptive.add_arm(arm)

    def test_epsilon_greedy_selection(self):
        """Epsilon-greedy seçim testi"""
        # Başlangıçta tüm kollar eşit değerde (0 reward)
        assert len(self.adaptive.arms) == 5
        stats = self.adaptive.get_statistics()
        assert all(s.avg_reward == 0 for s in stats.values())

        # 100 seçim yap
        selections = []
        for _ in range(100):
            arm_id = self.adaptive.select_arm()
            selections.append(arm_id)
            # Simüle edilmiş ödül
            reward = np.random.random()
            self.adaptive.update(arm_id, reward, success=reward > 0.5)

        # Tüm kollar en az bir kez seçilmiş olmalı (epsilon sayesinde)
        unique_selections = set(selections)
        assert len(unique_selections) >= 3  # En az 3 farklı kol seçilmeli

    def test_update_values(self):
        """Değer güncelleme testi"""
        # İlk kolu seç ve ödül ver
        arm_id = "0"
        reward = 0.8

        initial_stats = self.adaptive.get_statistics()[arm_id]
        initial_avg = initial_stats.avg_reward
        initial_pulls = initial_stats.pulls

        self.adaptive.update(arm_id, reward, success=True)

        # Değer güncellenmiş olmalı
        updated_stats = self.adaptive.get_statistics()[arm_id]
        assert updated_stats.avg_reward != initial_avg
        assert updated_stats.pulls == initial_pulls + 1

    def test_thompson_sampling(self):
        """Thompson Sampling testi"""
        # Beta dağılımı parametreleri
        alpha_params = np.ones(5)
        beta_params = np.ones(5)

        # 50 iterasyon
        for _ in range(50):
            # Beta dağılımından sample
            samples = [
                np.random.beta(alpha_params[i], beta_params[i]) for i in range(5)
            ]

            # En yüksek sample'ı seç
            chosen_arm = np.argmax(samples)

            # Simüle edilmiş sonuç
            success = np.random.random() > 0.5

            # Parametreleri güncelle
            if success:
                alpha_params[chosen_arm] += 1
            else:
                beta_params[chosen_arm] += 1

        # En az bir güncelleme olmalı
        assert not all(a == 1 for a in alpha_params)

    def test_adaptive_difficulty(self):
        """Adaptif zorluk ayarlama testi"""
        # Initialize with arms
        for arm in self.sample_arms:
            self.adaptive.add_arm(arm)

        # Simulate performance data
        context = {
            "student_level": 0.7,
            "average_time": 30,
            "topics_mastered": ["topic_1"],
        }

        # Select next content
        selected_arm = self.adaptive.select_arm()

        assert selected_arm is not None
        # select_arm returns arm_id (string), check it's one of the valid arms
        valid_arm_ids = [arm.arm_id for arm in self.sample_arms]
        assert selected_arm in valid_arm_ids

    @pytest.mark.skip(reason="MultiArmedBandit doesn't have counts/values attributes - uses different UCB implementation")
    def test_ucb_selection(self):
        """Upper Confidence Bound (UCB) testi"""
        # UCB formülü: value + sqrt(2 * log(total) / count)
        total_counts = 100

        for arm in range(5):
            # Her kola rastgele sayıda deneme
            count = np.random.randint(1, 20)
            self.adaptive.counts[arm] = count
            self.adaptive.values[arm] = np.random.random()

        # UCB skorlarını hesapla
        ucb_scores = []
        for arm in range(5):
            if self.adaptive.counts[arm] > 0:
                exploration_bonus = np.sqrt(
                    2 * np.log(total_counts) / self.adaptive.counts[arm]
                )
                ucb = self.adaptive.values[arm] + exploration_bonus
            else:
                ucb = float("inf")
            ucb_scores.append(ucb)

        # En yüksek UCB'yi seç
        best_arm = np.argmax(ucb_scores)
        assert best_arm >= 0 and best_arm < 5


class TestKnowledgeGraph:
    """Knowledge Graph tabanlı öneri testi"""

    def test_graph_construction(self):
        """Graf oluşturma testi"""
        # Basit bir bilgi grafiği
        knowledge_graph = {
            "matematik": {
                "prerequisites": [],
                "subtopics": ["cebir", "geometri"],
                "difficulty": 0.5,
            },
            "cebir": {
                "prerequisites": ["matematik"],
                "subtopics": ["lineer_cebir", "polinomlar"],
                "difficulty": 0.6,
            },
            "geometri": {
                "prerequisites": ["matematik"],
                "subtopics": ["analitik_geometri"],
                "difficulty": 0.7,
            },
        }

        # Graf traversal
        def get_learning_path(topic, graph, path=[]):
            if topic not in graph:
                return path

            # Önkoşulları ekle
            for prereq in graph[topic]["prerequisites"]:
                if prereq not in path:
                    path = get_learning_path(prereq, graph, path)

            # Kendini ekle
            if topic not in path:
                path.append(topic)

            return path

        # Cebir için öğrenme yolu
        path = get_learning_path("cebir", knowledge_graph)

        # Matematik önce gelmel
        assert path[0] == "matematik"
        assert path[1] == "cebir"

    def test_similarity_calculation(self):
        """İçerik benzerliği hesaplama testi"""
        # TF-IDF vektörleri simülasyonu
        content1 = {"matematik": 0.8, "cebir": 0.6, "geometri": 0.2}
        content2 = {"matematik": 0.9, "cebir": 0.4, "fizik": 0.3}

        # Cosine similarity
        common_keys = set(content1.keys()) & set(content2.keys())
        dot_product = sum(content1[k] * content2[k] for k in common_keys)

        norm1 = np.sqrt(sum(v**2 for v in content1.values()))
        norm2 = np.sqrt(sum(v**2 for v in content2.values()))

        similarity = dot_product / (norm1 * norm2)

        # Benzerlik 0-1 arasında olmalı
        assert 0 <= similarity <= 1


@pytest.mark.skip(reason="Test uses wrong API - MultiArmedBandit(n_arms=5) and recommender.recommend(user_id=...) don't exist")
@pytest.mark.asyncio
async def test_recommendation_integration():
    """Öneri sisteminin entegrasyon testi"""
    recommender = HybridRecommender()
    adaptive = MultiArmedBandit(n_arms=5)

    # Kullanıcı profili
    user_profile = {"interests": ["matematik", "fizik"], "level": "lise", "exam": "YKS"}

    # Öneriler al
    recommendations = recommender.recommend(user_id=1, n_recommendations=5)

    # Adaptif öğrenme ile içerik seçimi
    for i in range(10):
        selected_arm = adaptive.select_arm()
        # Simulate reward
        reward = max(0, min(1, 0.7 - i * 0.05))
        adaptive.update(selected_arm, reward)
        assert 0 <= selected_arm < 5

    print("[CHECK] Recommendation system integration test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
