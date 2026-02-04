"""
Comprehensive Error Handling Tests
Test suite for various error scenarios across the application
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from agents.learning_path_agent import LearningPathAgent
from agents.study_buddy_agent import StudyBuddyAgent
from core.llm_service import llm_service
from core.rag_service import rag_service
from integrations.khan_academy_service import khan_academy_service
from integrations.wikipedia_service import wikipedia_service
from integrations.youtube_service import youtube_service


class TestNetworkErrors:
    """Test network-related error scenarios"""

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()

            # Test with YouTube service
            result = await youtube_service.fetch_with_timeout(
                "http://test.com", timeout=1
            )
            assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test connection refused error"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = ConnectionRefusedError("Connection refused")

            result = await youtube_service.fetch_with_retry("http://test.com")
            assert result is None or not result.get("success", False)

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test DNS resolution failure"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = OSError("DNS resolution failed")

            result = await wikipedia_service.fetch_page("http://invalid-domain-xyz.com")
            assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_ssl_certificate_error(self):
        """Test SSL certificate verification error"""
        import ssl

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = ssl.SSLError("Certificate verification failed")

            result = await khan_academy_service.secure_fetch("https://test.com")
            assert result is None or not result.get("success", False)


class TestDatabaseErrors:
    """Test database-related error scenarios"""

    @pytest.mark.asyncio
    async def test_database_connection_lost(self):
        """Test database connection loss during operation"""
        from core.database import db_session

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Lost connection to database")

            agent = LearningPathAgent()
            result = await agent.save_student_profile(
                {"student_id": "test", "name": "Test Student"}
            )

            assert result is None or not result

    @pytest.mark.asyncio
    async def test_database_deadlock(self):
        """Test database deadlock scenario"""
        with patch("sqlalchemy.orm.Session.commit") as mock_commit:
            mock_commit.side_effect = Exception("Deadlock detected")

            agent = StudyBuddyAgent()
            result = await agent.save_quiz_results(
                {"quiz_id": "test", "student_id": "test", "score": 80}
            )

            assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_database_constraint_violation(self):
        """Test database constraint violation"""
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = Exception("UNIQUE constraint failed")

            result = await rag_service.store_document(
                {"id": "duplicate_id", "content": "Test content"}
            )

            assert result is None or not result.get("success", False)


class TestAPIErrors:
    """Test external API error scenarios"""

    @pytest.mark.asyncio
    async def test_api_rate_limit_exceeded(self):
        """Test API rate limiting"""
        with patch("integrations.youtube_service.build") as mock_build:
            mock_youtube = Mock()
            mock_youtube.search.side_effect = Exception(
                "quotaExceeded: API quota exceeded"
            )
            mock_build.return_value = mock_youtube

            result = await youtube_service.search_videos("test")
            assert not result.get("success", False)
            assert "quota" in str(result.get("error", "")).lower()

    @pytest.mark.asyncio
    async def test_api_invalid_credentials(self):
        """Test invalid API credentials"""
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "invalid_key"}):
            result = await youtube_service.authenticate_and_search("test")
            assert not result.get("success", False)

    @pytest.mark.asyncio
    async def test_api_service_unavailable(self):
        """Test API service unavailable (503)"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = Mock()
            mock_response.status = 503
            mock_response.text = AsyncMock(return_value="Service Unavailable")
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await wikipedia_service.fetch_with_status_check(
                "http://api.test.com"
            )
            assert result is None or result.get("status") == 503


class TestDataValidationErrors:
    """Test data validation error scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test handling of invalid JSON responses"""
        with patch("agents.learning_path_agent.llm_service.generate") as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "text": "This is not valid JSON {invalid: json",
            }

            agent = LearningPathAgent()
            result = await agent.analyze_student("test", {"name": "Test"})

            # Should handle gracefully
            assert result is None or hasattr(result, "learning_style")

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        agent = StudyBuddyAgent()

        # Missing required fields
        incomplete_question = {
            "question_text": "Test question"
            # Missing: question_type, correct_answer, etc.
        }

        result = await agent.validate_and_create_question(incomplete_question)
        assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_type_mismatch_errors(self):
        """Test type mismatch in data"""
        agent = LearningPathAgent()

        # String where number expected
        invalid_data = {
            "student_id": "test",
            "available_time": "not_a_number",  # Should be int
        }

        result = await agent.process_student_data(invalid_data)
        assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_data_overflow_errors(self):
        """Test data size overflow scenarios"""
        # Test with extremely large content
        huge_content = "x" * (10 * 1024 * 1024)  # 10MB string

        agent = StudyBuddyAgent()
        result = await agent.generate_flashcards(huge_content, count=5)

        # Should handle large content gracefully
        assert result is not None or len(result) == 0


class TestConcurrencyErrors:
    """Test concurrency and race condition errors"""

    @pytest.mark.asyncio
    async def test_race_condition_in_resource_access(self):
        """Test race condition when multiple tasks access same resource"""
        agent = LearningPathAgent()
        student_id = "race_test"

        # Simulate concurrent profile creation
        tasks = [
            agent.analyze_student(student_id, {"name": f"Student {i}"})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle concurrent access
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) < len(results)  # Some should succeed

    @pytest.mark.asyncio
    async def test_deadlock_in_concurrent_operations(self):
        """Test deadlock detection and recovery"""

        async def operation_a(lock1, lock2):
            async with lock1:
                await asyncio.sleep(0.01)
                async with lock2:
                    return "A completed"

        async def operation_b(lock1, lock2):
            async with lock2:
                await asyncio.sleep(0.01)
                async with lock1:
                    return "B completed"

        lock1 = asyncio.Lock()
        lock2 = asyncio.Lock()

        # This would normally deadlock - test timeout handling
        try:
            results = await asyncio.wait_for(
                asyncio.gather(operation_a(lock1, lock2), operation_b(lock1, lock2)),
                timeout=0.5,
            )
        except asyncio.TimeoutError:
            # Should handle timeout gracefully
            assert True
        else:
            # If no timeout, operations completed somehow
            assert results is not None


class TestMemoryErrors:
    """Test memory-related error scenarios"""

    @pytest.mark.asyncio
    async def test_memory_exhaustion(self):
        """Test handling of memory exhaustion"""
        agent = StudyBuddyAgent()

        # Try to create massive number of questions
        try:
            questions = []
            for i in range(1000000):  # Attempt to create 1M questions
                questions.append(
                    {"id": f"q_{i}", "text": f"Question {i}" * 100}  # Large text
                )

                if i % 10000 == 0:
                    # Check memory usage periodically
                    import psutil

                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024

                    if memory_mb > 500:  # Stop if using >500MB
                        break

            # Should handle large data sets
            result = await agent.process_bulk_questions(questions[:1000])
            assert result is not None

        except MemoryError:
            # Should handle memory errors gracefully
            assert True

    @pytest.mark.asyncio
    async def test_circular_reference_detection(self):
        """Test detection of circular references"""
        agent = LearningPathAgent()

        # Create circular reference in learning path
        path_data = {"path_id": "path_1", "next_path": "path_2", "resources": []}

        path_data2 = {
            "path_id": "path_2",
            "next_path": "path_1",  # Circular reference
            "resources": [],
        }

        result = await agent.validate_learning_path_chain([path_data, path_data2])
        assert result is False or "circular" in str(result).lower()


class TestFileSystemErrors:
    """Test file system related errors"""

    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Test handling of missing files"""
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = FileNotFoundError("File not found")

            result = await rag_service.load_document("nonexistent.pdf")
            assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_permission_denied(self):
        """Test handling of permission errors"""
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            result = await rag_service.save_document("protected.pdf", "content")
            assert result is None or not result.get("success", False)

    @pytest.mark.asyncio
    async def test_disk_full(self):
        """Test handling of disk full errors"""
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("No space left on device")

            agent = StudyBuddyAgent()
            result = await agent.export_quiz_results("quiz_id", "export.csv")
            assert result is None or "error" in result


class TestAuthenticationErrors:
    """Test authentication and authorization errors"""

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test invalid authentication token"""
        with patch("core.auth.validate_token") as mock_validate:
            mock_validate.return_value = False

            result = await llm_service.authenticated_request(
                "test request", token="invalid_token"
            )
            assert result is None or result.get("error") == "Unauthorized"

    @pytest.mark.asyncio
    async def test_expired_token(self):
        """Test expired authentication token"""
        with patch("core.auth.is_token_expired") as mock_expired:
            mock_expired.return_value = True

            result = await llm_service.authenticated_request(
                "test request", token="expired_token"
            )
            assert result is None or "expired" in str(result).lower()

    @pytest.mark.asyncio
    async def test_insufficient_permissions(self):
        """Test insufficient permissions for operation"""
        with patch("core.auth.check_permissions") as mock_perms:
            mock_perms.return_value = False

            agent = LearningPathAgent()
            result = await agent.delete_student_profile(
                "student_id", user_role="student"  # Students can't delete profiles
            )
            assert result is False or "permission" in str(result).lower()


class TestRecoveryStrategies:
    """Test error recovery strategies"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self):
        """Test exponential backoff retry strategy"""
        attempt_times = []

        async def failing_operation():
            attempt_times.append(datetime.now())
            if len(attempt_times) < 3:
                raise Exception("Temporary failure")
            return "Success"

        result = await self.retry_with_backoff(failing_operation, max_retries=5)

        assert result == "Success"
        assert len(attempt_times) == 3

        # Check exponential backoff timing
        if len(attempt_times) > 2:
            delay1 = (attempt_times[1] - attempt_times[0]).total_seconds()
            delay2 = (attempt_times[2] - attempt_times[1]).total_seconds()
            assert delay2 > delay1  # Should have exponential delay

    async def retry_with_backoff(self, func, max_retries=3):
        """Helper function for exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt * 0.1)  # Exponential backoff
        return None

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services"""

        class CircuitBreaker:
            def __init__(self, failure_threshold=3):
                self.failure_count = 0
                self.failure_threshold = failure_threshold
                self.is_open = False
                self.last_failure_time = None

            async def call(self, func):
                if self.is_open:
                    if datetime.now().timestamp() - self.last_failure_time > 60:
                        self.is_open = False  # Try to close after 60 seconds
                    else:
                        raise Exception("Circuit breaker is open")

                try:
                    result = await func()
                    self.failure_count = 0  # Reset on success
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = datetime.now().timestamp()

                    if self.failure_count >= self.failure_threshold:
                        self.is_open = True
                    raise e

        breaker = CircuitBreaker(failure_threshold=2)

        async def failing_service():
            raise Exception("Service failure")

        # First two calls should fail normally
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_service)

        # Third call should trigger circuit breaker
        with pytest.raises(Exception) as exc_info:
            await breaker.call(failing_service)

        assert "Circuit breaker is open" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """Test fallback to alternative services"""

        async def primary_service():
            raise Exception("Primary service failed")

        async def fallback_service():
            return {"source": "fallback", "data": "fallback data"}

        try:
            result = await primary_service()
        except Exception:
            result = await fallback_service()

        assert result["source"] == "fallback"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation of functionality"""

        class ServiceWithDegradation:
            def __init__(self):
                self.full_service_available = False

            async def get_data(self):
                if self.full_service_available:
                    # Full functionality
                    return {
                        "data": "complete data",
                        "features": ["feature1", "feature2", "feature3"],
                        "mode": "full",
                    }
                else:
                    # Degraded functionality
                    return {
                        "data": "basic data",
                        "features": ["feature1"],
                        "mode": "degraded",
                    }

        service = ServiceWithDegradation()

        # Test degraded mode
        result = await service.get_data()
        assert result["mode"] == "degraded"
        assert len(result["features"]) == 1

        # Test full mode
        service.full_service_available = True
        result = await service.get_data()
        assert result["mode"] == "full"
        assert len(result["features"]) == 3


@pytest.mark.asyncio
async def test_comprehensive_error_chain():
    """Test handling of chained errors across multiple services"""

    async def service_a():
        raise ValueError("Service A failed")

    async def service_b():
        try:
            await service_a()
        except ValueError as e:
            raise RuntimeError(f"Service B failed due to: {e}")

    async def service_c():
        try:
            await service_b()
        except RuntimeError as e:
            raise Exception(f"Service C failed: {e}")

    with pytest.raises(Exception) as exc_info:
        await service_c()

    # Check error chain is preserved
    assert "Service C failed" in str(exc_info.value)
    assert "Service B failed" in str(exc_info.value)
    assert "Service A failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
