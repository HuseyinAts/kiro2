"""
Comprehensive Tests for Learning Style System
Öğrenme Stili Sistemi Kapsamlı Testleri

Tests:
- VARK model (Visual, Auditory, Reading/Writing, Kinesthetic)
- Gardner's Multiple Intelligences (8 zeka türü)
- Learning preference detection
- Adaptive content recommendation
- Performance analysis by learning style
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List


# Mock learning style models
class LearningStyleProfile:
    """Öğrenci öğrenme stili profili"""

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.vark_scores = {
            "visual": 0.0,
            "auditory": 0.0,
            "reading": 0.0,
            "kinesthetic": 0.0,
        }
        self.multiple_intelligences = {
            "linguistic": 0.0,
            "logical_mathematical": 0.0,
            "spatial": 0.0,
            "bodily_kinesthetic": 0.0,
            "musical": 0.0,
            "interpersonal": 0.0,
            "intrapersonal": 0.0,
            "naturalistic": 0.0,
        }
        self.dominant_style = None
        self.last_updated = datetime.now(timezone.utc)


class LearningStyleDetector:
    """Öğrenme stili tespit sistemi"""

    def __init__(self):
        self.profiles = {}

    def analyze_behavior(
        self, student_id: str, activities: List[Dict]
    ) -> LearningStyleProfile:
        """Öğrenci davranışlarından öğrenme stilini analiz et"""
        profile = LearningStyleProfile(student_id)

        for activity in activities:
            activity_type = activity.get("type")
            duration = activity.get("duration", 0)
            success_rate = activity.get("success_rate", 0.0)

            # VARK puanlaması
            if activity_type in ["video", "diagram", "chart"]:
                profile.vark_scores["visual"] += duration * success_rate
            elif activity_type in ["audio", "lecture", "discussion"]:
                profile.vark_scores["auditory"] += duration * success_rate
            elif activity_type in ["reading", "article", "text"]:
                profile.vark_scores["reading"] += duration * success_rate
            elif activity_type in ["experiment", "practice", "simulation"]:
                profile.vark_scores["kinesthetic"] += duration * success_rate

        # Normalize scores
        total = sum(profile.vark_scores.values())
        if total > 0:
            for key in profile.vark_scores:
                profile.vark_scores[key] = profile.vark_scores[key] / total

        # Dominant style belirleme
        profile.dominant_style = max(profile.vark_scores, key=profile.vark_scores.get)

        self.profiles[student_id] = profile
        return profile

    def update_from_quiz_performance(
        self, student_id: str, question_types: List[str], scores: List[float]
    ) -> LearningStyleProfile:
        """Quiz performansından öğrenme stilini güncelle"""
        profile = self.profiles.get(student_id, LearningStyleProfile(student_id))

        for q_type, score in zip(question_types, scores):
            if "visual" in q_type.lower():
                profile.vark_scores["visual"] += score * 0.1
            elif "verbal" in q_type.lower():
                profile.vark_scores["auditory"] += score * 0.1
            elif "text" in q_type.lower():
                profile.vark_scores["reading"] += score * 0.1
            elif "practical" in q_type.lower():
                profile.vark_scores["kinesthetic"] += score * 0.1

        # Re-normalize
        total = sum(profile.vark_scores.values())
        if total > 0:
            for key in profile.vark_scores:
                profile.vark_scores[key] = profile.vark_scores[key] / total

        profile.dominant_style = max(profile.vark_scores, key=profile.vark_scores.get)
        profile.last_updated = datetime.now(timezone.utc)

        self.profiles[student_id] = profile
        return profile


class AdaptiveContentRecommender:
    """Öğrenme stiline göre içerik önericisi"""

    def __init__(self, detector: LearningStyleDetector):
        self.detector = detector

    def recommend_content(
        self, student_id: str, topic: str, available_content: List[Dict]
    ) -> List[Dict]:
        """Öğrencinin öğrenme stiline göre içerik öner"""
        profile = self.detector.profiles.get(student_id)

        if not profile:
            return available_content[:5]  # Default: ilk 5 içerik

        # İçeriği öğrenme stiline göre skorla
        scored_content = []
        for content in available_content:
            score = 0.0
            content_type = content.get("type", "")

            # VARK skorlarına göre ağırlıklandır
            if content_type in ["video", "image", "diagram"]:
                score = profile.vark_scores["visual"]
            elif content_type in ["audio", "podcast"]:
                score = profile.vark_scores["auditory"]
            elif content_type in ["article", "book"]:
                score = profile.vark_scores["reading"]
            elif content_type in ["simulation", "lab"]:
                score = profile.vark_scores["kinesthetic"]

            scored_content.append({**content, "recommendation_score": score})

        # Skora göre sırala
        scored_content.sort(key=lambda x: x["recommendation_score"], reverse=True)

        return scored_content[:10]  # Top 10 öneri

    def recommend_study_method(self, student_id: str) -> Dict:
        """Öğrenme stiline göre çalışma metodu öner"""
        profile = self.detector.profiles.get(student_id)

        if not profile:
            return {"method": "mixed", "tips": ["Farklı yöntemler deneyin"]}

        methods = {
            "visual": {
                "method": "visual_learning",
                "tips": [
                    "Zihin haritaları kullanın",
                    "Diyagramlar ve grafikler oluşturun",
                    "Renkli notlar alın",
                    "Video dersler izleyin",
                ],
            },
            "auditory": {
                "method": "auditory_learning",
                "tips": [
                    "Sesli okuyun",
                    "Podcast dinleyin",
                    "Grup tartışmalarına katılın",
                    "Müzikle çalışmayı deneyin",
                ],
            },
            "reading": {
                "method": "reading_writing",
                "tips": [
                    "Detaylı notlar alın",
                    "Özet metinler yazın",
                    "Liste ve taslaklar oluşturun",
                    "Yazarak pekiştirin",
                ],
            },
            "kinesthetic": {
                "method": "kinesthetic_learning",
                "tips": [
                    "Pratik uygulamalar yapın",
                    "Yürüyerek çalışın",
                    "Model ve deney kullanın",
                    "Rol yapma egzersizleri",
                ],
            },
        }

        return methods.get(profile.dominant_style, methods["visual"])


# ==================== TESTS ====================


@pytest.fixture
def detector():
    """Learning style detector fixture"""
    return LearningStyleDetector()


@pytest.fixture
def recommender(detector):
    """Content recommender fixture"""
    return AdaptiveContentRecommender(detector)


@pytest.fixture
def sample_activities():
    """Sample student activities"""
    return [
        {"type": "video", "duration": 30, "success_rate": 0.9},
        {"type": "video", "duration": 25, "success_rate": 0.85},
        {"type": "reading", "duration": 20, "success_rate": 0.7},
        {"type": "practice", "duration": 15, "success_rate": 0.8},
        {"type": "audio", "duration": 10, "success_rate": 0.6},
    ]


@pytest.fixture
def sample_content():
    """Sample learning content"""
    return [
        {"id": "1", "type": "video", "title": "Math Video 1", "topic": "algebra"},
        {"id": "2", "type": "article", "title": "Math Article 1", "topic": "algebra"},
        {"id": "3", "type": "simulation", "title": "Math Lab 1", "topic": "algebra"},
        {"id": "4", "type": "audio", "title": "Math Podcast 1", "topic": "algebra"},
        {"id": "5", "type": "image", "title": "Math Diagram 1", "topic": "algebra"},
        {"id": "6", "type": "video", "title": "Math Video 2", "topic": "algebra"},
    ]


class TestLearningStyleDetection:
    """Test learning style detection"""

    def test_analyze_behavior_creates_profile(self, detector, sample_activities):
        """Test behavior analysis creates a valid profile"""
        profile = detector.analyze_behavior("student_1", sample_activities)

        assert profile is not None
        assert profile.student_id == "student_1"
        assert profile.dominant_style is not None

    def test_vark_scores_normalized(self, detector, sample_activities):
        """Test VARK scores are normalized to sum to 1"""
        profile = detector.analyze_behavior("student_1", sample_activities)

        total = sum(profile.vark_scores.values())
        assert abs(total - 1.0) < 0.01  # Should sum to ~1.0

    def test_visual_learner_detection(self, detector):
        """Test detection of visual learner"""
        activities = [
            {"type": "video", "duration": 50, "success_rate": 0.95},
            {"type": "diagram", "duration": 30, "success_rate": 0.90},
            {"type": "chart", "duration": 20, "success_rate": 0.85},
            {"type": "reading", "duration": 10, "success_rate": 0.5},
        ]

        profile = detector.analyze_behavior("visual_student", activities)

        assert profile.dominant_style == "visual"
        assert profile.vark_scores["visual"] > 0.5

    def test_auditory_learner_detection(self, detector):
        """Test detection of auditory learner"""
        activities = [
            {"type": "audio", "duration": 50, "success_rate": 0.95},
            {"type": "lecture", "duration": 40, "success_rate": 0.90},
            {"type": "discussion", "duration": 30, "success_rate": 0.85},
            {"type": "video", "duration": 10, "success_rate": 0.5},
        ]

        profile = detector.analyze_behavior("auditory_student", activities)

        assert profile.dominant_style == "auditory"
        assert profile.vark_scores["auditory"] > 0.5

    def test_kinesthetic_learner_detection(self, detector):
        """Test detection of kinesthetic learner"""
        activities = [
            {"type": "experiment", "duration": 60, "success_rate": 0.95},
            {"type": "practice", "duration": 50, "success_rate": 0.90},
            {"type": "simulation", "duration": 40, "success_rate": 0.88},
            {"type": "reading", "duration": 5, "success_rate": 0.4},
        ]

        profile = detector.analyze_behavior("kinesthetic_student", activities)

        assert profile.dominant_style == "kinesthetic"
        assert profile.vark_scores["kinesthetic"] > 0.5

    def test_empty_activities_returns_zero_scores(self, detector):
        """Test empty activities list returns zero scores"""
        profile = detector.analyze_behavior("student_empty", [])

        assert all(score == 0.0 for score in profile.vark_scores.values())
        assert profile.dominant_style is not None  # Should still pick one


class TestQuizPerformanceUpdate:
    """Test learning style updates from quiz performance"""

    def test_update_from_quiz_performance(self, detector):
        """Test profile update from quiz performance"""
        question_types = ["visual_question", "text_question", "practical_question"]
        scores = [0.9, 0.7, 0.8]

        profile = detector.update_from_quiz_performance(
            "student_quiz", question_types, scores
        )

        assert profile is not None
        assert profile.student_id == "student_quiz"
        assert profile.last_updated is not None

    def test_quiz_updates_existing_profile(self, detector, sample_activities):
        """Test quiz performance updates existing profile"""
        # Create initial profile
        detector.analyze_behavior("student_update", sample_activities)

        # Update with quiz
        question_types = ["visual_question", "visual_question"]
        scores = [1.0, 1.0]

        updated = detector.update_from_quiz_performance(
            "student_update", question_types, scores
        )

        # Visual score should be higher now
        assert updated.vark_scores["visual"] > 0
        assert updated.dominant_style == "visual"

    def test_profile_timestamp_updated(self, detector):
        """Test profile timestamp is updated"""
        before = datetime.now(timezone.utc)

        profile = detector.update_from_quiz_performance(
            "student_time", ["text_question"], [0.8]
        )

        after = datetime.now(timezone.utc)

        assert before <= profile.last_updated <= after


class TestContentRecommendation:
    """Test adaptive content recommendation"""

    def test_recommend_content_for_visual_learner(
        self, detector, recommender, sample_content
    ):
        """Test content recommendation for visual learner"""
        # Create visual learner profile
        activities = [{"type": "video", "duration": 100, "success_rate": 0.95}]
        detector.analyze_behavior("visual_student", activities)

        recommendations = recommender.recommend_content(
            "visual_student", "algebra", sample_content
        )

        assert len(recommendations) > 0
        # First recommendation should be visual content
        assert recommendations[0]["type"] in ["video", "image"]

    def test_recommend_content_without_profile(self, recommender, sample_content):
        """Test recommendation without existing profile"""
        recommendations = recommender.recommend_content(
            "new_student", "algebra", sample_content
        )

        # Should return default recommendations
        assert len(recommendations) == 5

    def test_recommendation_scores_sorted(self, detector, recommender, sample_content):
        """Test recommendations are sorted by score"""
        # Create profile
        activities = [{"type": "video", "duration": 50, "success_rate": 0.9}]
        detector.analyze_behavior("student_sort", activities)

        recommendations = recommender.recommend_content(
            "student_sort", "algebra", sample_content
        )

        # Check scores are in descending order
        scores = [r["recommendation_score"] for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_empty_content_returns_empty_list(self, detector, recommender):
        """Test empty content list returns empty recommendations"""
        activities = [{"type": "video", "duration": 50, "success_rate": 0.9}]
        detector.analyze_behavior("student_empty_content", activities)

        recommendations = recommender.recommend_content(
            "student_empty_content", "algebra", []
        )

        assert recommendations == []


class TestStudyMethodRecommendation:
    """Test study method recommendations"""

    def test_recommend_visual_study_method(self, detector, recommender):
        """Test visual learning method recommendation"""
        activities = [{"type": "video", "duration": 100, "success_rate": 0.95}]
        detector.analyze_behavior("visual_method", activities)

        method = recommender.recommend_study_method("visual_method")

        assert method["method"] == "visual_learning"
        assert len(method["tips"]) > 0
        assert any(
            "diyagram" in tip.lower() or "video" in tip.lower()
            for tip in method["tips"]
        )

    def test_recommend_auditory_study_method(self, detector, recommender):
        """Test auditory learning method recommendation"""
        activities = [{"type": "audio", "duration": 100, "success_rate": 0.95}]
        detector.analyze_behavior("auditory_method", activities)

        method = recommender.recommend_study_method("auditory_method")

        assert method["method"] == "auditory_learning"
        assert any(
            "sesli" in tip.lower() or "podcast" in tip.lower() for tip in method["tips"]
        )

    def test_recommend_kinesthetic_study_method(self, detector, recommender):
        """Test kinesthetic learning method recommendation"""
        activities = [{"type": "practice", "duration": 100, "success_rate": 0.95}]
        detector.analyze_behavior("kinesthetic_method", activities)

        method = recommender.recommend_study_method("kinesthetic_method")

        assert method["method"] == "kinesthetic_learning"
        assert any(
            "pratik" in tip.lower() or "uygulama" in tip.lower()
            for tip in method["tips"]
        )

    def test_recommend_without_profile(self, recommender):
        """Test method recommendation without profile"""
        method = recommender.recommend_study_method("no_profile_student")

        assert "method" in method
        assert "tips" in method
        assert len(method["tips"]) > 0


class TestMultipleIntelligences:
    """Test Gardner's Multiple Intelligences support"""

    def test_profile_has_multiple_intelligences(self):
        """Test profile includes all 8 intelligence types"""
        profile = LearningStyleProfile("student_mi")

        expected_intelligences = [
            "linguistic",
            "logical_mathematical",
            "spatial",
            "bodily_kinesthetic",
            "musical",
            "interpersonal",
            "intrapersonal",
            "naturalistic",
        ]

        for intelligence in expected_intelligences:
            assert intelligence in profile.multiple_intelligences
            assert profile.multiple_intelligences[intelligence] == 0.0

    def test_intelligence_scores_independent(self):
        """Test multiple intelligence scores are independent"""
        profile = LearningStyleProfile("student_ind")

        # Set different scores
        profile.multiple_intelligences["linguistic"] = 0.8
        profile.multiple_intelligences["logical_mathematical"] = 0.9
        profile.multiple_intelligences["musical"] = 0.3

        # Other scores should remain 0
        assert profile.multiple_intelligences["spatial"] == 0.0
        assert profile.multiple_intelligences["bodily_kinesthetic"] == 0.0


class TestProfilePersistence:
    """Test learning style profile persistence"""

    def test_profile_stored_in_detector(self, detector, sample_activities):
        """Test profile is stored in detector"""
        detector.analyze_behavior("student_persist", sample_activities)

        assert "student_persist" in detector.profiles
        assert detector.profiles["student_persist"].student_id == "student_persist"

    def test_profile_can_be_retrieved(self, detector, sample_activities):
        """Test stored profile can be retrieved"""
        detector.analyze_behavior("student_retrieve", sample_activities)

        profile = detector.profiles.get("student_retrieve")

        assert profile is not None
        assert profile.dominant_style is not None

    def test_multiple_profiles_stored(self, detector, sample_activities):
        """Test multiple student profiles can be stored"""
        detector.analyze_behavior("student_1", sample_activities)
        detector.analyze_behavior("student_2", sample_activities)
        detector.analyze_behavior("student_3", sample_activities)

        assert len(detector.profiles) >= 3
        assert "student_1" in detector.profiles
        assert "student_2" in detector.profiles
        assert "student_3" in detector.profiles


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_all_activities_zero_duration(self, detector):
        """Test activities with zero duration"""
        activities = [
            {"type": "video", "duration": 0, "success_rate": 0.9},
            {"type": "audio", "duration": 0, "success_rate": 0.8},
        ]

        profile = detector.analyze_behavior("zero_duration", activities)

        assert profile is not None
        assert all(score == 0.0 for score in profile.vark_scores.values())

    def test_activities_with_missing_fields(self, detector):
        """Test activities with missing fields"""
        activities = [
            {"type": "video"},  # Missing duration and success_rate
            {"duration": 30},  # Missing type
        ]

        profile = detector.analyze_behavior("missing_fields", activities)

        assert profile is not None

    def test_negative_scores_handled(self, detector):
        """Test negative scores are handled gracefully"""
        question_types = ["visual_question"]
        scores = [-0.5]  # Negative score

        profile = detector.update_from_quiz_performance(
            "negative_score", question_types, scores
        )

        assert profile is not None

    def test_very_large_activity_count(self, detector):
        """Test performance with large number of activities"""
        activities = [
            {"type": "video", "duration": i % 50, "success_rate": 0.8}
            for i in range(1000)
        ]

        profile = detector.analyze_behavior("large_count", activities)

        assert profile is not None
        assert profile.dominant_style is not None
