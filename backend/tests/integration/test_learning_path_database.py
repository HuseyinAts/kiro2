"""
Database Integration Tests for Learning Path System
P1 Gap Fix: Test database persistence, CRUD operations, and data integrity

Tests cover:
- Learning path creation and retrieval from database
- Student profile persistence
- Progress tracking database operations
- Topic completion storage
- Quiz submission persistence
- Concurrent database writes
- Connection failure handling
"""

import pytest
import asyncio
import uuid


try:
    from database.connection import get_async_session_context
    from database.learning_path_repository import learning_path_repository
except (ImportError, ModuleNotFoundError):
    pytest.skip("database dependencies not available", allow_module_level=True)


class TestLearningPathDatabaseIntegration:
    """Integration tests for Learning Path database operations"""

    @pytest.fixture
    async def db_session(self):
        """Provide clean database session for each test"""
        async with get_async_session_context() as session:
            yield session
            # Cleanup after test
            await session.rollback()

    @pytest.fixture
    def sample_student_profile(self):
        """Sample student profile data"""
        return {
            "student_id": f"STU_TEST_{uuid.uuid4().hex[:8]}",
            "name": "Test Student",
            "grade": "11",
            "exam_target": "YKS",
            "learning_style": "visual",
            "knowledge_level": "intermediate",
            "interests": ["matematik", "fizik"],
            "goals": ["YKS başarısı", "üniversite kazanmak"],
            "available_time": 120,
        }

    @pytest.fixture
    def sample_learning_path(self, sample_student_profile):
        """Sample learning path data"""
        return {
            "path_id": f"PATH_TEST_{uuid.uuid4().hex[:8]}",
            "student_id": sample_student_profile["student_id"],
            "subject": "matematik",
            "difficulty_level": "intermediate",
            "duration_weeks": 12,
            "modules": [
                {
                    "module_id": "MOD_001",
                    "title": "Türev",
                    "topics": ["Türev tanımı", "Türev kuralları"],
                    "duration_hours": 10,
                }
            ],
            "phases": ["Temel kavramlar", "İleri seviye"],
            "resources": [
                {
                    "resource_id": "RES_001",
                    "title": "Türev videosu",
                    "type": "video",
                    "url": "https://example.com/video1",
                }
            ],
            "ai_generated": True,
            "reasoning": "AI generated path based on student profile",
            "total_modules": 1,
            "total_topics": 2,
        }

    # ==================== STUDENT PROFILE TESTS ====================

    @pytest.mark.asyncio
    async def test_create_student_profile_saves_to_database(
        self, db_session, sample_student_profile
    ):
        """Test that student profile is correctly saved to database"""
        # Create student profile
        profile = await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Verify saved
        assert profile is not None
        assert profile.student_id == sample_student_profile["student_id"]
        assert profile.name == sample_student_profile["name"]
        assert profile.grade == sample_student_profile["grade"]
        assert profile.exam_target == sample_student_profile["exam_target"]
        assert profile.learning_style == sample_student_profile["learning_style"]

        # Verify can retrieve from database
        retrieved = await learning_path_repository.get_student_profile(
            db_session, sample_student_profile["student_id"]
        )

        assert retrieved is not None
        assert retrieved.student_id == profile.student_id
        assert retrieved.name == profile.name

    @pytest.mark.asyncio
    async def test_update_student_profile_persists_changes(
        self, db_session, sample_student_profile
    ):
        """Test that student profile updates are persisted"""
        # Create initial profile
        profile = await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Update profile
        updated_data = {
            "learning_style": "kinesthetic",
            "knowledge_level": "advanced",
            "available_time": 180,
        }

        updated_profile = await learning_path_repository.update_student_profile(
            db_session, profile.student_id, updated_data
        )

        # Verify updates persisted
        assert updated_profile.learning_style == "kinesthetic"
        assert updated_profile.knowledge_level == "advanced"
        assert updated_profile.available_time == 180

        # Verify by re-fetching
        refetched = await learning_path_repository.get_student_profile(
            db_session, profile.student_id
        )
        assert refetched.learning_style == "kinesthetic"

    # ==================== LEARNING PATH TESTS ====================

    @pytest.mark.asyncio
    async def test_create_learning_path_saves_to_database(
        self, db_session, sample_student_profile, sample_learning_path
    ):
        """Test that learning path is correctly saved to database"""
        # First create student profile
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Create learning path
        path = await learning_path_repository.create_learning_path(
            db_session, sample_learning_path
        )

        # Verify saved
        assert path is not None
        assert path.path_id == sample_learning_path["path_id"]
        assert path.student_id == sample_learning_path["student_id"]
        assert path.subject == sample_learning_path["subject"]
        assert path.ai_generated is True
        assert len(path.modules) == 1

        # Verify can retrieve
        retrieved = await learning_path_repository.get_learning_path(
            db_session, path.path_id
        )

        assert retrieved is not None
        assert retrieved.path_id == path.path_id

    @pytest.mark.asyncio
    async def test_retrieve_learning_paths_by_student_id(
        self, db_session, sample_student_profile, sample_learning_path
    ):
        """Test retrieving all learning paths for a student"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Create multiple learning paths
        path1 = sample_learning_path.copy()
        path1["path_id"] = f"PATH_TEST_{uuid.uuid4().hex[:8]}"
        path1["subject"] = "matematik"

        path2 = sample_learning_path.copy()
        path2["path_id"] = f"PATH_TEST_{uuid.uuid4().hex[:8]}"
        path2["subject"] = "fizik"

        await learning_path_repository.create_learning_path(db_session, path1)
        await learning_path_repository.create_learning_path(db_session, path2)

        # Retrieve all paths for student
        paths = await learning_path_repository.get_student_learning_paths(
            db_session, sample_student_profile["student_id"]
        )

        assert len(paths) >= 2
        subjects = [p.subject for p in paths]
        assert "matematik" in subjects
        assert "fizik" in subjects

    @pytest.mark.asyncio
    async def test_update_learning_path_progress(
        self, db_session, sample_student_profile, sample_learning_path
    ):
        """Test updating learning path progress"""
        # Create student and path
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        path = await learning_path_repository.create_learning_path(
            db_session, sample_learning_path
        )

        # Update progress
        updated_path = await learning_path_repository.update_learning_path_progress(
            db_session,
            path.path_id,
            {"completed_modules": 1, "completed_topics": 2, "overall_progress": 50.0},
        )

        assert updated_path.completed_modules == 1
        assert updated_path.completed_topics == 2
        assert updated_path.overall_progress == 50.0

    # ==================== TOPIC COMPLETION TESTS ====================

    @pytest.mark.asyncio
    async def test_upsert_topic_completion(self, db_session, sample_student_profile):
        """Test upserting topic completion status"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # First completion
        completion = await learning_path_repository.upsert_topic_completion(
            db_session,
            sample_student_profile["student_id"],
            "TOPIC_001",
            completed=True,
        )

        assert completion.completed is True
        assert completion.completion_date is not None

        # Update completion (upsert)
        completion2 = await learning_path_repository.upsert_topic_completion(
            db_session,
            sample_student_profile["student_id"],
            "TOPIC_001",
            completed=False,
        )

        assert completion2.completed is False

    @pytest.mark.asyncio
    async def test_get_student_completions(self, db_session, sample_student_profile):
        """Test retrieving all completions for a student"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Create multiple completions
        await learning_path_repository.upsert_topic_completion(
            db_session, sample_student_profile["student_id"], "TOPIC_001", True
        )

        await learning_path_repository.upsert_topic_completion(
            db_session, sample_student_profile["student_id"], "TOPIC_002", True
        )

        # Retrieve completions
        completions = await learning_path_repository.get_student_completions(
            db_session, sample_student_profile["student_id"]
        )

        assert len(completions) >= 2
        completed_topics = [c.node_id for c in completions if c.completed]
        assert "TOPIC_001" in completed_topics
        assert "TOPIC_002" in completed_topics

    # ==================== TOPIC PROGRESS TESTS ====================

    @pytest.mark.asyncio
    async def test_update_topic_progress(self, db_session, sample_student_profile):
        """Test updating topic progress"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Update progress
        progress = await learning_path_repository.update_topic_progress(
            db_session,
            sample_student_profile["student_id"],
            "TOPIC_001",
            progress=75,
            time_spent=3600,  # 1 hour
        )

        assert progress.progress == 75
        assert progress.time_spent == 3600
        assert progress.completed is False

        # Complete topic
        progress2 = await learning_path_repository.update_topic_progress(
            db_session,
            sample_student_profile["student_id"],
            "TOPIC_001",
            progress=100,
            time_spent=7200,
        )

        assert progress2.progress == 100
        assert progress2.time_spent == 7200
        assert progress2.completed is True

    # ==================== QUIZ SUBMISSION TESTS ====================

    @pytest.mark.asyncio
    async def test_create_quiz_submission(self, db_session, sample_student_profile):
        """Test creating quiz submission"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Submit quiz
        submission = await learning_path_repository.create_quiz_submission(
            db_session,
            {
                "student_id": sample_student_profile["student_id"],
                "quiz_id": "QUIZ_001",
                "question_count": 10,
                "correct_count": 8,
                "score": 80.0,
                "passing_score": 70.0,
                "passed": True,
                "answers": [{"question_id": "Q1", "answer": "A", "correct": True}],
                "total_time_seconds": 600,
            },
        )

        assert submission.score == 80.0
        assert submission.passed is True
        assert submission.correct_count == 8

    @pytest.mark.asyncio
    async def test_get_quiz_history(self, db_session, sample_student_profile):
        """Test retrieving quiz history"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Submit multiple quizzes
        await learning_path_repository.create_quiz_submission(
            db_session,
            {
                "student_id": sample_student_profile["student_id"],
                "quiz_id": "QUIZ_001",
                "question_count": 10,
                "correct_count": 8,
                "score": 80.0,
                "passing_score": 70.0,
                "passed": True,
                "answers": [],
                "total_time_seconds": 600,
            },
        )

        await learning_path_repository.create_quiz_submission(
            db_session,
            {
                "student_id": sample_student_profile["student_id"],
                "quiz_id": "QUIZ_002",
                "question_count": 15,
                "correct_count": 10,
                "score": 66.67,
                "passing_score": 70.0,
                "passed": False,
                "answers": [],
                "total_time_seconds": 900,
            },
        )

        # Get history
        history = await learning_path_repository.get_quiz_history(
            db_session, sample_student_profile["student_id"], "QUIZ_001"
        )

        assert len(history) >= 1
        assert history[0].quiz_id == "QUIZ_001"

    # ==================== FALLBACK VIDEO TESTS ====================

    @pytest.mark.asyncio
    async def test_get_fallback_videos(self, db_session):
        """Test retrieving fallback videos by subject"""
        # Get matematik videos
        videos = await learning_path_repository.get_fallback_videos(
            db_session, subject="matematik", topic=None, limit=5
        )

        # Should have videos from seed data
        assert len(videos) > 0
        for video in videos:
            assert video.subject == "matematik"
            assert video.is_example is True

    @pytest.mark.asyncio
    async def test_fallback_videos_sorted_by_score(self, db_session):
        """Test that fallback videos are sorted by final_score"""
        videos = await learning_path_repository.get_fallback_videos(
            db_session, subject="fizik", topic=None, limit=10
        )

        if len(videos) > 1:
            # Verify sorted descending by final_score
            for i in range(len(videos) - 1):
                assert videos[i].final_score >= videos[i + 1].final_score

    # ==================== CONCURRENT ACCESS TESTS ====================

    @pytest.mark.asyncio
    async def test_concurrent_learning_path_creation(
        self, db_session, sample_student_profile
    ):
        """Test concurrent learning path creation doesn't cause conflicts"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Create multiple paths concurrently
        async def create_path(subject: str):
            async with get_async_session_context() as session:
                path_data = {
                    "path_id": f"PATH_TEST_{uuid.uuid4().hex[:8]}",
                    "student_id": sample_student_profile["student_id"],
                    "subject": subject,
                    "difficulty_level": "intermediate",
                    "duration_weeks": 12,
                    "modules": [],
                    "phases": [],
                    "resources": [],
                    "ai_generated": True,
                    "total_modules": 0,
                    "total_topics": 0,
                }
                return await learning_path_repository.create_learning_path(
                    session, path_data
                )

        # Create 5 paths concurrently
        tasks = [create_path(f"subject_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all succeeded (no exceptions)
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) == 5

    # ==================== ERROR HANDLING TESTS ====================

    @pytest.mark.asyncio
    async def test_create_learning_path_without_student_fails(
        self, db_session, sample_learning_path
    ):
        """Test that creating path without student fails gracefully"""
        # Try to create path without creating student first
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            await learning_path_repository.create_learning_path(
                db_session, sample_learning_path
            )

    @pytest.mark.asyncio
    async def test_duplicate_student_profile_fails(
        self, db_session, sample_student_profile
    ):
        """Test that duplicate student_id fails"""
        # Create first profile
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Try to create duplicate
        with pytest.raises(Exception):  # Should raise unique constraint error
            await learning_path_repository.create_student_profile(
                db_session, sample_student_profile
            )

    # ==================== DATA INTEGRITY TESTS ====================

    @pytest.mark.asyncio
    async def test_cascading_delete_student_profile(
        self, db_session, sample_student_profile, sample_learning_path
    ):
        """Test that deleting student cascades to learning paths"""
        # Create student and path
        profile = await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        path = await learning_path_repository.create_learning_path(
            db_session, sample_learning_path
        )

        # Delete student
        await learning_path_repository.delete_student_profile(
            db_session, profile.student_id
        )

        # Verify learning path also deleted
        deleted_path = await learning_path_repository.get_learning_path(
            db_session, path.path_id
        )

        assert deleted_path is None

    @pytest.mark.asyncio
    async def test_progress_percentage_constraint(
        self, db_session, sample_student_profile
    ):
        """Test that progress percentage is constrained to 0-100"""
        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Try invalid progress (>100)
        with pytest.raises(Exception):  # Should raise check constraint error
            await learning_path_repository.update_topic_progress(
                db_session,
                sample_student_profile["student_id"],
                "TOPIC_001",
                progress=150,  # Invalid!
            )

    # ==================== PERFORMANCE TESTS ====================

    @pytest.mark.asyncio
    async def test_bulk_topic_completion_update_performance(
        self, db_session, sample_student_profile
    ):
        """Test performance of bulk topic completion updates"""
        import time

        # Create student
        await learning_path_repository.create_student_profile(
            db_session, sample_student_profile
        )

        # Prepare bulk completions
        completions = [
            {
                "student_id": sample_student_profile["student_id"],
                "node_id": f"TOPIC_{i:03d}",
                "completed": True,
            }
            for i in range(50)
        ]

        # Measure time
        start_time = time.time()

        await learning_path_repository.batch_update_topic_completions(
            db_session, completions
        )

        elapsed = time.time() - start_time

        # Should complete in < 2 seconds for 50 items
        assert elapsed < 2.0, f"Bulk update took {elapsed:.2f}s, expected < 2.0s"

        # Verify all saved
        saved_completions = await learning_path_repository.get_student_completions(
            db_session, sample_student_profile["student_id"]
        )

        assert len(saved_completions) >= 50


# ==================== FIXTURES ====================

# Note: event_loop fixture removed - pytest-asyncio auto mode handles this
# Duplicate fixtures cause conflicts with pytest-asyncio>=0.21


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
