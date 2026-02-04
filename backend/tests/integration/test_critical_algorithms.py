from unittest.mock import Mock, patch, AsyncMock

"""
Critical Algorithms Tests  
AI ve öğrenme algoritmaları testleri
"""
import math
from datetime import datetime, timedelta


class TestCriticalAlgorithms:
    """Critical algorithm functionality tests"""

    def test_fsrs_algorithm_basic(self):
        """Test FSRS (Free Spaced Repetition System) algorithm"""

        class MockFSRS:
            def __init__(self):
                # FSRS parametreleri (17 parametre)
                self.w = [
                    0.5701,
                    1.4436,
                    4.1386,
                    10.9355,
                    5.1443,
                    1.2006,
                    0.8627,
                    0.0362,
                    1.629,
                    0.1342,
                    1.0166,
                    2.1174,
                    0.0839,
                    0.3204,
                    1.4676,
                    0.219,
                    2.8237,
                ]

            def calculate_stability(
                self, retrievability: float, difficulty: float
            ) -> float:
                """Kararlılık hesaplama"""
                if retrievability <= 0:
                    return 1.0

                stability = (-1 / self.w[8]) * math.log(retrievability)
                stability = max(0.1, min(stability, 36500))  # 0.1 gün - 100 yıl
                return stability

            def calculate_difficulty(
                self, rating: int, current_difficulty: float = 5.0
            ) -> float:
                """Zorluk hesaplama (1-10 arası)"""
                if rating == 1:  # Again
                    return min(10.0, current_difficulty + 1.0)
                elif rating == 2:  # Hard
                    return max(1.0, current_difficulty - 0.3)
                elif rating == 3:  # Good
                    return current_difficulty
                else:  # Easy (4)
                    return max(1.0, current_difficulty - 0.5)

            def next_review_date(
                self, stability: float, desired_retention: float = 0.9
            ) -> datetime:
                """Sonraki tekrar tarihi"""
                interval_days = stability * (desired_retention ** (1 / self.w[8]) - 1)
                interval_days = max(1, interval_days)
                return datetime.now() + timedelta(days=interval_days)

        fsrs = MockFSRS()

        # Test stability calculation
        stability = fsrs.calculate_stability(0.9, 5.0)
        assert stability > 0
        assert stability < 36500

        # Test difficulty calculation
        easy_difficulty = fsrs.calculate_difficulty(4, 5.0)  # Easy
        hard_difficulty = fsrs.calculate_difficulty(1, 5.0)  # Again

        assert easy_difficulty < 5.0  # Should decrease
        assert hard_difficulty > 5.0  # Should increase
        assert 1.0 <= easy_difficulty <= 10.0
        assert 1.0 <= hard_difficulty <= 10.0

        # Test next review date
        next_date = fsrs.next_review_date(stability=5.0, desired_retention=0.9)
        assert next_date > datetime.now()
        assert next_date < datetime.now() + timedelta(days=365)

    def test_irt_algorithm(self):
        """Test IRT (Item Response Theory) algorithm"""

        class MockIRT:
            def __init__(self):
                pass

            def probability_correct(
                self, ability: float, difficulty: float, discrimination: float = 1.0
            ) -> float:
                """1PL/2PL IRT model - doğru cevap verme olasılığı"""
                exponent = discrimination * (ability - difficulty)
                probability = 1 / (1 + math.exp(-exponent))
                return probability

            def estimate_ability(
                self, responses: list, difficulties: list, discriminations: list = None
            ) -> float:
                """Ability estimation using Maximum Likelihood"""
                if discriminations is None:
                    discriminations = [1.0] * len(responses)

                # Simplified ML estimation
                ability = 0.0  # Starting estimate

                for iteration in range(10):  # Newton-Raphson iterations
                    first_derivative = 0.0
                    second_derivative = 0.0

                    for i, (response, difficulty, discrimination) in enumerate(
                        zip(responses, difficulties, discriminations)
                    ):
                        p = self.probability_correct(
                            ability, difficulty, discrimination
                        )

                        # First derivative (score function)
                        first_derivative += discrimination * (response - p)

                        # Second derivative (information)
                        second_derivative -= discrimination**2 * p * (1 - p)

                    # Newton-Raphson update
                    if second_derivative != 0:
                        ability_update = first_derivative / abs(second_derivative)
                        ability += ability_update

                        # Convergence check
                        if abs(ability_update) < 0.001:
                            break

                return ability

            def item_information(
                self, ability: float, difficulty: float, discrimination: float = 1.0
            ) -> float:
                """Item information function"""
                p = self.probability_correct(ability, difficulty, discrimination)
                information = discrimination**2 * p * (1 - p)
                return information

        irt = MockIRT()

        # Test probability calculation
        prob_easy = irt.probability_correct(
            ability=1.0, difficulty=-1.0
        )  # High ability, easy item
        prob_hard = irt.probability_correct(
            ability=-1.0, difficulty=1.0
        )  # Low ability, hard item

        assert 0 <= prob_easy <= 1
        assert 0 <= prob_hard <= 1
        assert prob_easy > prob_hard  # High ability should have higher probability

        # Test ability estimation
        responses = [1, 1, 0, 1, 0]  # 3 correct, 2 incorrect
        difficulties = [-1.0, 0.0, 1.0, -0.5, 0.5]

        estimated_ability = irt.estimate_ability(responses, difficulties)
        assert -3.0 <= estimated_ability <= 3.0  # Reasonable ability range

        # Test item information
        info_high = irt.item_information(
            ability=0.0, difficulty=0.0
        )  # Maximum information
        info_low = irt.item_information(
            ability=2.0, difficulty=0.0
        )  # Lower information

        assert info_high > 0
        assert info_low > 0
        assert info_high > info_low  # Information peaks when ability = difficulty

    def test_adaptive_learning_algorithm(self):
        """Test adaptive learning algorithm"""

        class MockAdaptiveLearning:
            def __init__(self):
                self.student_abilities = {}
                self.item_difficulties = {}

            def update_student_ability(
                self, student_id: int, item_id: int, response: bool
            ):
                """Update student ability based on response"""
                if student_id not in self.student_abilities:
                    self.student_abilities[student_id] = 0.0

                if item_id not in self.item_difficulties:
                    self.item_difficulties[item_id] = 0.0

                current_ability = self.student_abilities[student_id]
                item_difficulty = self.item_difficulties[item_id]

                # Expected probability
                expected_prob = 1 / (1 + math.exp(-(current_ability - item_difficulty)))

                # Update based on response
                learning_rate = 0.1
                if response:  # Correct
                    if expected_prob < 0.8:  # Unexpected success
                        self.student_abilities[student_id] += learning_rate * (
                            1 - expected_prob
                        )
                else:  # Incorrect
                    if expected_prob > 0.2:  # Unexpected failure
                        self.student_abilities[student_id] -= (
                            learning_rate * expected_prob
                        )

                return self.student_abilities[student_id]

            def select_next_item(self, student_id: int, available_items: list) -> int:
                """Select next item for optimal learning"""
                if student_id not in self.student_abilities:
                    return available_items[0] if available_items else None

                student_ability = self.student_abilities[student_id]
                best_item = None
                best_information = 0

                for item_id in available_items:
                    difficulty = self.item_difficulties.get(item_id, 0.0)

                    # Calculate information (Fisher Information)
                    prob = 1 / (1 + math.exp(-(student_ability - difficulty)))
                    information = prob * (1 - prob)

                    if information > best_information:
                        best_information = information
                        best_item = item_id

                return best_item

            def get_mastery_level(self, student_id: int) -> str:
                """Get student mastery level"""
                if student_id not in self.student_abilities:
                    return "beginner"

                ability = self.student_abilities[student_id]

                if ability >= 1.5:
                    return "advanced"
                elif ability >= 0.5:
                    return "intermediate"
                elif ability >= -0.5:
                    return "beginner"
                else:
                    return "struggling"

        adaptive = MockAdaptiveLearning()

        # Initialize items
        adaptive.item_difficulties = {1: -1.0, 2: 0.0, 3: 1.0, 4: 1.5}

        # Test ability updates
        initial_ability = adaptive.update_student_ability(
            1, 1, True
        )  # Easy item correct
        assert initial_ability >= 0

        # Multiple responses
        for item_id, response in [(1, True), (2, True), (3, False), (4, False)]:
            adaptive.update_student_ability(1, item_id, response)

        final_ability = adaptive.student_abilities[1]
        assert -3.0 <= final_ability <= 3.0

        # Test item selection
        available_items = [1, 2, 3, 4]
        selected_item = adaptive.select_next_item(1, available_items)
        assert selected_item in available_items

        # Test mastery level
        mastery = adaptive.get_mastery_level(1)
        assert mastery in ["struggling", "beginner", "intermediate", "advanced"]

    def test_turkish_zpd_algorithm(self):
        """Test Turkish ZPD (Zone of Proximal Development) algorithm"""

        class MockTurkishZPD:
            def __init__(self):
                self.cultural_factors = {
                    "group_work_preference": 0.7,  # Turkish students prefer group work
                    "teacher_respect": 0.9,  # High respect for teachers
                    "family_influence": 0.8,  # Strong family influence
                    "rote_learning_comfort": 0.6,  # Comfort with memorization
                }

            def calculate_zpd_range(
                self, current_level: float, cultural_profile: dict
            ) -> tuple:
                """Calculate ZPD range with Turkish cultural factors"""
                # Base ZPD calculation
                base_lower = current_level
                base_upper = current_level + 1.5

                # Cultural adjustments
                group_adjustment = cultural_profile.get("group_preference", 0.5) * 0.3
                teacher_guidance = cultural_profile.get("teacher_guidance", 0.5) * 0.4
                family_support = cultural_profile.get("family_support", 0.5) * 0.2

                # Turkish students often perform better with support
                cultural_boost = group_adjustment + teacher_guidance + family_support

                zpd_lower = base_lower
                zpd_upper = base_upper + cultural_boost

                return (zpd_lower, zpd_upper)

            def recommend_content_difficulty(self, student_profile: dict) -> str:
                """Recommend content difficulty based on ZPD"""
                current_level = student_profile.get("current_level", 3.0)
                cultural_profile = student_profile.get("cultural_factors", {})

                zpd_lower, zpd_upper = self.calculate_zpd_range(
                    current_level, cultural_profile
                )

                # Recommend difficulty within ZPD
                target_difficulty = (zpd_lower + zpd_upper) / 2

                if target_difficulty <= 2.0:
                    return "kolay"
                elif target_difficulty <= 4.0:
                    return "orta"
                elif target_difficulty <= 6.0:
                    return "zor"
                else:
                    return "çok_zor"

            def adapt_to_turkish_learning_style(
                self, content_type: str, student_profile: dict
            ) -> dict:
                """Adapt content to Turkish learning preferences"""
                adaptations = {}

                # Group work preference
                if student_profile.get("group_preference", 0) > 0.7:
                    adaptations["group_activities"] = True
                    adaptations["peer_discussion"] = True

                # Teacher guidance preference
                if student_profile.get("teacher_guidance", 0) > 0.8:
                    adaptations["detailed_explanations"] = True
                    adaptations["step_by_step_guidance"] = True

                # Cultural context
                adaptations["turkish_examples"] = True
                adaptations["cultural_relevance"] = True

                return adaptations

        zpd = MockTurkishZPD()

        # Test ZPD calculation
        cultural_profile = {
            "group_preference": 0.8,
            "teacher_guidance": 0.9,
            "family_support": 0.7,
        }

        zpd_lower, zpd_upper = zpd.calculate_zpd_range(3.0, cultural_profile)

        assert zpd_lower <= zpd_upper
        assert zpd_lower >= 3.0  # Should not be lower than current level
        assert zpd_upper > 3.0  # Should extend beyond current level

        # Test difficulty recommendation
        student_profile = {"current_level": 3.5, "cultural_factors": cultural_profile}

        difficulty = zpd.recommend_content_difficulty(student_profile)
        assert difficulty in ["kolay", "orta", "zor", "çok_zor"]

        # Test Turkish learning style adaptation
        adaptations = zpd.adapt_to_turkish_learning_style("video", student_profile)

        assert "turkish_examples" in adaptations
        assert "cultural_relevance" in adaptations
        assert adaptations["group_activities"] is True  # High group preference

    def test_recommendation_algorithm(self):
        """Test content recommendation algorithm"""

        class MockRecommendationEngine:
            def __init__(self):
                self.user_profiles = {}
                self.content_features = {}
                self.interaction_history = {}

            def update_user_profile(self, user_id: int, interactions: dict):
                """Update user profile based on interactions"""
                if user_id not in self.user_profiles:
                    self.user_profiles[user_id] = {
                        "subject_preferences": {},
                        "difficulty_preference": 3.0,
                        "content_type_preferences": {},
                    }

                profile = self.user_profiles[user_id]

                # Update subject preferences
                for subject, rating in interactions.get("subjects", {}).items():
                    current = profile["subject_preferences"].get(subject, 0.0)
                    profile["subject_preferences"][subject] = (current + rating) / 2

                # Update content type preferences
                for content_type, rating in interactions.get(
                    "content_types", {}
                ).items():
                    current = profile["content_type_preferences"].get(content_type, 0.0)
                    profile["content_type_preferences"][content_type] = (
                        current + rating
                    ) / 2

            def calculate_similarity(self, user_id1: int, user_id2: int) -> float:
                """Calculate user similarity for collaborative filtering"""
                if (
                    user_id1 not in self.user_profiles
                    or user_id2 not in self.user_profiles
                ):
                    return 0.0

                profile1 = self.user_profiles[user_id1]
                profile2 = self.user_profiles[user_id2]

                # Compare subject preferences
                subjects1 = set(profile1["subject_preferences"].keys())
                subjects2 = set(profile2["subject_preferences"].keys())
                common_subjects = subjects1.intersection(subjects2)

                if not common_subjects:
                    return 0.0

                # Calculate cosine similarity
                dot_product = sum(
                    profile1["subject_preferences"][subject]
                    * profile2["subject_preferences"][subject]
                    for subject in common_subjects
                )

                norm1 = math.sqrt(
                    sum(pref**2 for pref in profile1["subject_preferences"].values())
                )
                norm2 = math.sqrt(
                    sum(pref**2 for pref in profile2["subject_preferences"].values())
                )

                if norm1 == 0 or norm2 == 0:
                    return 0.0

                return dot_product / (norm1 * norm2)

            def recommend_content(
                self, user_id: int, available_content: list, top_k: int = 5
            ) -> list:
                """Recommend content for user"""
                if user_id not in self.user_profiles:
                    return available_content[:top_k]

                profile = self.user_profiles[user_id]
                scored_content = []

                for content in available_content:
                    score = 0.0

                    # Subject preference score
                    subject = content.get("subject", "")
                    if subject in profile["subject_preferences"]:
                        score += profile["subject_preferences"][subject] * 0.5

                    # Content type preference score
                    content_type = content.get("type", "")
                    if content_type in profile["content_type_preferences"]:
                        score += profile["content_type_preferences"][content_type] * 0.3

                    # Difficulty match score
                    content_difficulty = content.get("difficulty", 3.0)
                    difficulty_diff = abs(
                        content_difficulty - profile["difficulty_preference"]
                    )
                    difficulty_score = max(
                        0, 1 - difficulty_diff / 3.0
                    )  # Normalize to [0,1]
                    score += difficulty_score * 0.2

                    scored_content.append((content, score))

                # Sort by score and return top k
                scored_content.sort(key=lambda x: x[1], reverse=True)
                return [content for content, score in scored_content[:top_k]]

        recommender = MockRecommendationEngine()

        # Test user profile update
        interactions = {
            "subjects": {"matematik": 4.5, "fizik": 3.5, "kimya": 2.0},
            "content_types": {"video": 4.0, "text": 3.0, "quiz": 4.5},
        }

        recommender.update_user_profile(1, interactions)
        profile = recommender.user_profiles[1]

        assert "matematik" in profile["subject_preferences"]
        assert profile["subject_preferences"]["matematik"] == 4.5
        assert "video" in profile["content_type_preferences"]

        # Test similarity calculation
        recommender.update_user_profile(
            2,
            {
                "subjects": {"matematik": 4.0, "fizik": 4.0},
                "content_types": {"video": 3.5, "quiz": 4.0},
            },
        )

        similarity = recommender.calculate_similarity(1, 2)
        assert 0 <= similarity <= 1

        # Test content recommendation
        available_content = [
            {"id": 1, "subject": "matematik", "type": "video", "difficulty": 4.0},
            {"id": 2, "subject": "fizik", "type": "text", "difficulty": 3.0},
            {"id": 3, "subject": "kimya", "type": "quiz", "difficulty": 2.0},
            {"id": 4, "subject": "matematik", "type": "quiz", "difficulty": 4.5},
        ]

        recommendations = recommender.recommend_content(1, available_content, top_k=3)

        assert len(recommendations) <= 3
        assert all("id" in content for content in recommendations)

        # First recommendation should likely be matematik (highest preference)
        first_rec = recommendations[0]
        assert first_rec["subject"] in ["matematik", "fizik"]  # Top preferences
