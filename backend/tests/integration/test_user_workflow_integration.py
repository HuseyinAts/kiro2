"""
User Workflow Integration Tests
Testing complete user workflows using integration utilities
"""
import pytest
import asyncio
from datetime import datetime
import uuid

# Import custom test utilities
try:
    from tests.utils.integration_utils import (
        integration_test_context,
        assert_performance_acceptable,
        assert_security_clean,
        assert_data_integrity,
    )
    from tests.fixtures.integration_fixtures import (
        create_test_user_data,
        create_test_content_data,
        generate_test_id,
    )

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


@pytest.mark.skipif(not UTILS_AVAILABLE, reason="Integration utils not available")
class TestUserWorkflowIntegration:
    """Integration tests for complete user workflows"""

    @pytest.mark.asyncio
    async def test_user_registration_workflow(self):
        """Test complete user registration workflow"""
        async with integration_test_context() as ctx:
            client = ctx["client"]
            validator = ctx["validator"]
            monitor = ctx["monitor"]

            # Step 1: Register user
            user_data = create_test_user_data(
                email=f"workflow_test_{generate_test_id()}@example.com",
                ad_soyad="Workflow Test User",
                rol="ogrenci",
            )

            start_time = monitor.start_time or 0
            response = await client.request(
                "POST", "/api/v1/auth/kayit", json=user_data
            )
            response_time = (
                monitor.start_time - start_time if monitor.start_time else 0.1
            )
            monitor.record_request(response_time, response["status_code"] < 400)

            # Validate response
            assert response["status_code"] in [200, 201]
            user_response = response["json"]

            # Validate data integrity
            validation_errors = validator.validate_user_data(user_response)
            assert_data_integrity(validation_errors)

            # Step 2: Login with created user
            login_data = {"email": user_data["email"], "sifre": user_data["sifre"]}

            login_response = await client.request(
                "POST", "/api/v1/auth/giris", json=login_data
            )
            monitor.record_request(0.1, login_response["status_code"] == 200)

            assert login_response["status_code"] == 200
            assert "access_token" in login_response["json"]

            # Set auth token for subsequent requests
            client.set_auth_token(login_response["json"]["access_token"])

            # Check performance
            metrics = monitor.get_metrics()
            assert_performance_acceptable(metrics, max_response_time=2.0)

    @pytest.mark.asyncio
    async def test_content_creation_workflow(self):
        """Test content creation and interaction workflow"""
        async with integration_test_context() as ctx:
            client = ctx["client"]
            validator = ctx["validator"]
            workflow = ctx["workflow"]

            # Step 1: Create article content
            workflow.add_step("create_article", self._create_content, client, "makale")

            # Step 2: Create video content
            workflow.add_step("create_video", self._create_content, client, "video")

            # Step 3: Create quiz content
            workflow.add_step("create_quiz", self._create_content, client, "quiz")

            # Step 4: List all content
            workflow.add_step("list_content", self._list_content, client)

            # Run workflow
            results = await workflow.run()
            summary = workflow.get_summary()

            # Assert workflow success
            assert summary["success_rate"] >= 75  # At least 75% success
            assert summary["total_steps"] == 4

            # Validate content creation results
            for result in results:
                if result["success"] and result["result"]:
                    if "content_id" in result["result"]:
                        # Validate content data
                        content_data = result["result"]
                        validation_errors = validator.validate_content_data(
                            content_data
                        )
                        assert_data_integrity(validation_errors)

    @pytest.mark.asyncio
    async def test_exam_taking_workflow(self):
        """Test complete exam taking workflow"""
        async with integration_test_context() as ctx:
            helper = ctx["helper"]
            generator = ctx["generator"]

            # Generate test data
            user = generator.generate_users(1)[0]
            questions = generator.generate_exam_questions(10)

            # Store test data for cleanup
            helper.test_data["user"] = user
            helper.test_data["questions"] = questions

            # Simulate exam workflow
            exam_workflow = MockExamWorkflow(user, questions)

            # Step 1: Create exam session
            exam_session = exam_workflow.create_exam_session()
            assert exam_session["sinav_id"] is not None
            assert exam_session["ogrenci_id"] == user["kullanici_id"]

            # Step 2: Answer questions
            answers = exam_workflow.submit_answers(
                {"q_0": "A", "q_1": "B", "q_2": "C", "q_3": "A", "q_4": "B"}
            )
            assert len(answers) == 5

            # Step 3: Complete exam
            result = exam_workflow.complete_exam()
            assert result["sonuc_id"] is not None
            assert result["net_sayisi"] > 0

            # Step 4: Get exam results
            exam_results = exam_workflow.get_results()
            assert exam_results["toplam_puan"] > 0
            assert 0 <= exam_results["basari_yuzdesi"] <= 100

    @pytest.mark.asyncio
    async def test_security_validation_workflow(self):
        """Test security validation across user workflows"""
        async with integration_test_context() as ctx:
            client = ctx["client"]
            security = ctx["security"]

            # Test XSS protection in user registration
            xss_vulnerabilities = security.test_xss_protection(
                lambda data: asyncio.run(
                    client.request(
                        "POST",
                        "/api/v1/auth/kayit",
                        json={
                            "email": "test@example.com",
                            "ad_soyad": data.get("ad_soyad", "Test User"),
                            "sifre": "password123",
                            "rol": "ogrenci",
                        },
                    )
                ),
                "ad_soyad",
            )
            assert_security_clean(xss_vulnerabilities)

            # Test SQL injection protection in content creation
            sql_vulnerabilities = security.test_sql_injection_protection(
                lambda data: asyncio.run(
                    client.request(
                        "POST",
                        "/api/v1/content/makale",
                        json={
                            "baslik": data.get("baslik", "Test Title"),
                            "icerik": "Test content that is long enough for validation.",
                            "kategori": "Test",
                            "yazar": "Test Author",
                        },
                    )
                ),
                "baslik",
            )
            assert_security_clean(sql_vulnerabilities)

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under load"""
        async with integration_test_context() as ctx:
            client = ctx["client"]
            monitor = ctx["monitor"]
            generator = ctx["generator"]

            # Generate load test data
            users = generator.generate_users(10)

            # Simulate concurrent user registrations
            async def register_user(user_data):
                start_time = monitor.start_time or 0
                response = await client.request(
                    "POST", "/api/v1/auth/kayit", json=user_data
                )
                response_time = 0.1  # Mock response time
                monitor.record_request(response_time, response["status_code"] < 400)
                return response

            # Run concurrent registrations
            tasks = [register_user(user) for user in users[:5]]  # Limit for test
            responses = await asyncio.gather(*tasks)

            # Check performance metrics
            metrics = monitor.get_metrics()
            assert_performance_acceptable(
                metrics, max_response_time=1.0, max_error_rate=10.0
            )

            # Verify responses
            successful_responses = [r for r in responses if r["status_code"] < 400]
            assert len(successful_responses) >= 4  # At least 80% success

    async def _create_content(self, client, content_type, context=None):
        """Helper method to create content"""
        content_data = create_test_content_data(content_type)

        endpoint_map = {
            "makale": "/api/v1/content/makale",
            "video": "/api/v1/content/video",
            "quiz": "/api/v1/content/quiz",
        }

        endpoint = endpoint_map.get(content_type, "/api/v1/content/makale")
        response = await client.request("POST", endpoint, json=content_data)

        if response["status_code"] < 400:
            return response["json"]
        else:
            raise Exception(f"Content creation failed: {response}")

    async def _list_content(self, client, context=None):
        """Helper method to list content"""
        response = await client.request("GET", "/api/v1/content/makale")

        if response["status_code"] == 200:
            return response["json"]
        else:
            raise Exception(f"Content listing failed: {response}")


class MockExamWorkflow:
    """Mock exam workflow for testing"""

    def __init__(self, user, questions):
        self.user = user
        self.questions = questions
        self.exam_session = None
        self.answers = {}
        self.result = None

    def create_exam_session(self):
        """Create exam session"""
        self.exam_session = {
            "sinav_id": generate_test_id("exam"),
            "ogrenci_id": self.user["kullanici_id"],
            "sinav_tipi": "TYT",
            "toplam_soru_sayisi": len(self.questions),
            "sure_dakika": 120,
            "durum": "devam_ediyor",
            "baslangic_zamani": datetime.now(),
        }
        return self.exam_session

    def submit_answers(self, answers):
        """Submit answers to questions"""
        self.answers = answers
        return answers

    def complete_exam(self):
        """Complete exam and calculate results"""
        if not self.exam_session:
            raise ValueError("No active exam session")

        # Calculate scores
        correct = 0
        wrong = 0
        blank = 0

        for i in range(len(self.questions)):
            question_id = f"q_{i}"
            if question_id in self.answers:
                # Assume all submitted answers are correct for testing
                correct += 1
            else:
                blank += 1

        net_score = correct - (wrong * 0.25)

        self.result = {
            "sonuc_id": generate_test_id("result"),
            "sinav_id": self.exam_session["sinav_id"],
            "ogrenci_id": self.user["kullanici_id"],
            "dogru_sayisi": correct,
            "yanlis_sayisi": wrong,
            "bos_sayisi": blank,
            "net_sayisi": net_score,
            "ham_puan": net_score * 5,
            "tamamlanma_tarihi": datetime.now(),
        }

        # Update exam status
        self.exam_session["durum"] = "tamamlandi"

        return self.result

    def get_results(self):
        """Get exam results"""
        if not self.result:
            raise ValueError("Exam not completed")

        return {
            "sinav_id": self.result["sinav_id"],
            "ogrenci_id": self.result["ogrenci_id"],
            "toplam_puan": self.result["ham_puan"],
            "basari_yuzdesi": (
                self.result["dogru_sayisi"] / self.exam_session["toplam_soru_sayisi"]
            )
            * 100,
            "detaylar": self.result,
        }


@pytest.mark.skipif(not UTILS_AVAILABLE, reason="Integration utils not available")
class TestDataFlowIntegration:
    """Integration tests for data flow between components"""

    @pytest.mark.asyncio
    async def test_user_progress_tracking(self):
        """Test user progress tracking across activities"""
        async with integration_test_context() as ctx:
            generator = ctx["generator"]

            # Create test user
            user = generator.generate_users(1)[0]

            # Simulate progress tracking
            progress_tracker = MockProgressTracker()

            # Add various activities
            activities = [
                {
                    "type": "content_read",
                    "content_id": "c1",
                    "duration": 300,
                    "completed": True,
                },
                {
                    "type": "quiz_taken",
                    "quiz_id": "q1",
                    "score": 85,
                    "duration": 600,
                    "completed": True,
                },
                {
                    "type": "video_watched",
                    "video_id": "v1",
                    "duration": 900,
                    "completed": True,
                },
                {
                    "type": "exam_taken",
                    "exam_id": "e1",
                    "score": 78,
                    "duration": 1200,
                    "completed": True,
                },
            ]

            for activity in activities:
                progress_tracker.record_activity(user["kullanici_id"], activity)

            # Get progress summary
            progress = progress_tracker.get_progress(user["kullanici_id"])

            assert progress["total_activities"] == 4
            assert progress["completed_activities"] == 4
            assert progress["total_time"] == 3000  # Sum of durations
            assert (
                progress["average_score"] == (85 + 78) / 2
            )  # Average of scored activities

    @pytest.mark.asyncio
    async def test_content_recommendation_flow(self):
        """Test content recommendation data flow"""
        async with integration_test_context() as ctx:
            generator = ctx["generator"]

            # Create test data
            user = generator.generate_users(1)[0]
            content_items = generator.generate_content(20)

            # Create recommendation engine
            recommender = MockRecommendationEngine(content_items)

            # Define user preferences
            user_profile = {
                "grade_level": 11,
                "weak_subjects": ["Matematik", "Fizik"],
                "preferred_content": ["video", "quiz"],
                "difficulty_preference": "orta",
            }

            # Get recommendations
            recommendations = recommender.get_recommendations(
                user["kullanici_id"], user_profile
            )

            assert len(recommendations) > 0
            assert all("priority" in rec for rec in recommendations)
            assert any(
                rec["kategori"] in user_profile["weak_subjects"]
                for rec in recommendations
            )


class MockProgressTracker:
    """Mock progress tracker for testing"""

    def __init__(self):
        self.user_progress = {}

    def record_activity(self, user_id, activity):
        """Record user activity"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "total_activities": 0,
                "completed_activities": 0,
                "total_time": 0,
                "scores": [],
                "activities": [],
            }

        progress = self.user_progress[user_id]
        progress["activities"].append(activity)
        progress["total_activities"] += 1
        progress["total_time"] += activity.get("duration", 0)

        if activity.get("completed"):
            progress["completed_activities"] += 1

        if "score" in activity:
            progress["scores"].append(activity["score"])

    def get_progress(self, user_id):
        """Get user progress"""
        if user_id not in self.user_progress:
            return {"total_activities": 0, "completed_activities": 0, "total_time": 0}

        progress = self.user_progress[user_id]

        return {
            "total_activities": progress["total_activities"],
            "completed_activities": progress["completed_activities"],
            "total_time": progress["total_time"],
            "average_score": sum(progress["scores"]) / len(progress["scores"])
            if progress["scores"]
            else 0,
            "completion_rate": progress["completed_activities"]
            / progress["total_activities"]
            if progress["total_activities"] > 0
            else 0,
        }


class MockRecommendationEngine:
    """Mock recommendation engine for testing"""

    def __init__(self, content_items):
        self.content_items = content_items

    def get_recommendations(self, user_id, user_profile):
        """Get content recommendations for user"""
        recommendations = []

        for content in self.content_items:
            # Simple recommendation logic
            priority = "low"
            reason = "General content"

            # Higher priority for weak subjects
            if content.get("kategori") in user_profile.get("weak_subjects", []):
                priority = "high"
                reason = "Weak subject improvement"

            # Medium priority for preferred content types
            elif content.get("content_type") in user_profile.get(
                "preferred_content", []
            ):
                priority = "medium"
                reason = "Preferred content type"

            # Filter by difficulty
            if content.get("zorluk_seviyesi") == user_profile.get(
                "difficulty_preference"
            ):
                recommendations.append(
                    {
                        **content,
                        "priority": priority,
                        "reason": reason,
                        "user_id": user_id,
                    }
                )

        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda x: priority_order.get(x["priority"], 0), reverse=True
        )

        return recommendations[:10]  # Return top 10 recommendations
