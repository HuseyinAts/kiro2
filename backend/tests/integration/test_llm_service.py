"""
Comprehensive tests for HuggingFace LLM Service
Target: 80%+ test coverage
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

import aiohttp

from core.llm_service import HuggingFaceLLMService, llm_service


class TestHuggingFaceLLMService:
    """Test HuggingFaceLLMService class"""

    def test_service_initialization(self):
        """Test service initialization"""
        service = HuggingFaceLLMService()

        assert service.endpoint_url is not None
        assert service.headers["Content-Type"] == "application/json"
        assert service._session is None
        assert service._redis_client is None
        assert isinstance(service._cache, dict)
        assert service._initialized is False
        assert service._cache_ttl > 0
        assert service._max_cache_size > 0

    @patch.dict(
        "os.environ",
        {
            "HUGGINGFACE_ENDPOINT": "https://test.endpoint.com",
            "HUGGINGFACE_API_TOKEN": "test_token",
            "LLM_CACHE_TTL": "7200",
            "LLM_MAX_CACHE_SIZE": "2000",
        },
    )
    def test_service_initialization_with_env(self):
        """Test service initialization with environment variables"""
        service = HuggingFaceLLMService()

        assert service.endpoint_url == "https://test.endpoint.com"
        assert service.api_token == "test_token"
        assert "Authorization" in service.headers
        assert service.headers["Authorization"] == "Bearer test_token"
        assert service._cache_ttl == 7200
        assert service._max_cache_size == 2000

    def test_generate_cache_key(self):
        """Test cache key generation"""
        service = HuggingFaceLLMService()

        key1 = service._generate_cache_key(
            "test prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            system_prompt="system",
        )

        key2 = service._generate_cache_key(
            "test prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            system_prompt="system",
        )

        key3 = service._generate_cache_key(
            "different prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            system_prompt="system",
        )

        # Same inputs should generate same key
        assert key1 == key2
        # Different inputs should generate different keys
        assert key1 != key3
        # Keys should be hex strings
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

    def test_prepare_prompt_with_system(self):
        """Test prompt preparation with system prompt"""
        service = HuggingFaceLLMService()

        result = service._prepare_prompt("user message", "system message")

        assert "### System:" in result
        assert "system message" in result
        assert "### User:" in result
        assert "user message" in result
        assert "### Assistant:" in result

    def test_prepare_prompt_without_system(self):
        """Test prompt preparation without system prompt"""
        service = HuggingFaceLLMService()

        result = service._prepare_prompt("user message", None)

        assert result == "user message"
        assert "### System:" not in result
        assert "### Assistant:" not in result

    def test_generate_educational_response_python(self):
        """Test educational response generation for Python"""
        service = HuggingFaceLLMService()

        response = service._generate_educational_response("Python öğrenmek istiyorum")

        assert "Python" in response
        assert "Temel Kavramlar" in response
        assert "Veri Yapıları" in response
        assert "Fonksiyonlar" in response
        assert "pratik" in response.lower()

    def test_generate_educational_response_math(self):
        """Test educational response generation for math"""
        service = HuggingFaceLLMService()

        response = service._generate_educational_response(
            "matematik çalışmak istiyorum"
        )

        assert "matematik" in response.lower() or "Matematik" in response
        assert "problem" in response.lower()
        assert "formül" in response.lower() or "Formül" in response

    def test_generate_educational_response_exam(self):
        """Test educational response generation for exams"""
        service = HuggingFaceLLMService()

        response_lgs = service._generate_educational_response("LGS'ye hazırlanıyorum")
        response_yks = service._generate_educational_response(
            "YKS sınavına hazırlanmak istiyorum"
        )

        assert "sınav" in response_lgs.lower() or "Sınav" in response_lgs
        assert "hazırlık" in response_lgs.lower() or "Hazırlık" in response_lgs
        assert "sınav" in response_yks.lower() or "Sınav" in response_yks
        assert "deneme" in response_lgs.lower() or "test" in response_lgs.lower()

    def test_generate_educational_response_general(self):
        """Test educational response generation for general queries"""
        service = HuggingFaceLLMService()

        response = service._generate_educational_response("genel bir soru")

        assert "yardım" in response.lower() or "Yardım" in response
        assert "öğrenme" in response.lower() or "Öğrenme" in response
        assert "plan" in response.lower() or "Plan" in response

    @pytest.mark.asyncio
    async def test_get_cached_response_memory_hit(self):
        """Test getting cached response from memory"""
        service = HuggingFaceLLMService()

        # Set up cache
        cache_key = "test_key"
        response_data = {"success": True, "text": "cached response"}
        service._cache[cache_key] = (response_data, time.time())

        result = await service._get_cached_response(cache_key)

        assert result == response_data

    @pytest.mark.asyncio
    async def test_get_cached_response_memory_expired(self):
        """Test getting expired cached response from memory"""
        service = HuggingFaceLLMService()

        # Set up expired cache
        cache_key = "test_key"
        response_data = {"success": True, "text": "cached response"}
        service._cache[cache_key] = (
            response_data,
            time.time() - service._cache_ttl - 1,
        )

        result = await service._get_cached_response(cache_key)

        assert result is None
        assert cache_key not in service._cache  # Should be removed

    @pytest.mark.asyncio
    async def test_get_cached_response_no_cache(self):
        """Test getting cached response when no cache exists"""
        service = HuggingFaceLLMService()

        result = await service._get_cached_response("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_get_cached_response_redis_hit(self, mock_redis):
        """Test getting cached response from Redis"""
        service = HuggingFaceLLMService()

        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.get.return_value = json.dumps(
            {"success": True, "text": "redis cached"}
        )
        mock_redis.return_value = mock_client
        service._redis_client = mock_client

        result = await service._get_cached_response("test_key")

        assert result == {"success": True, "text": "redis cached"}
        mock_client.get.assert_called_once_with("llm_cache:test_key")

    @pytest.mark.asyncio
    async def test_set_cached_response_memory(self):
        """Test setting cached response in memory"""
        service = HuggingFaceLLMService()
        service._max_cache_size = 2

        response_data = {"success": True, "text": "test response"}

        await service._set_cached_response("test_key", response_data)

        assert "test_key" in service._cache
        cached_data, timestamp = service._cache["test_key"]
        assert cached_data == response_data
        assert isinstance(timestamp, float)

    @pytest.mark.asyncio
    async def test_set_cached_response_memory_lru_eviction(self):
        """Test LRU eviction in memory cache"""
        service = HuggingFaceLLMService()
        service._max_cache_size = 2

        # Fill cache
        await service._set_cached_response("key1", {"text": "response1"})
        await service._set_cached_response("key2", {"text": "response2"})

        # Add third item, should evict oldest
        await service._set_cached_response("key3", {"text": "response3"})

        assert len(service._cache) == 2
        assert "key3" in service._cache
        assert "key2" in service._cache
        assert "key1" not in service._cache  # Should be evicted

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_set_cached_response_redis(self, mock_redis):
        """Test setting cached response in Redis"""
        service = HuggingFaceLLMService()

        # Mock Redis client
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        service._redis_client = mock_client

        response_data = {"success": True, "text": "test response"}

        await service._set_cached_response("test_key", response_data)

        mock_client.setex.assert_called_once_with(
            "llm_cache:test_key", service._cache_ttl, json.dumps(response_data)
        )

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_success_list_format(self, mock_post):
        """Test successful generation with list format response"""
        service = HuggingFaceLLMService()

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"generated_text": "test prompt\n\nGenerated response"}
        ]
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert "Generated response" in result["text"]
        assert result["metadata"]["model"] == "huggingface-endpoint"
        assert result["metadata"]["cache_hit"] is False

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_success_dict_format(self, mock_post):
        """Test successful generation with dict format response"""
        service = HuggingFaceLLMService()

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"generated_text": "Generated response"}
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert result["text"] == "Generated response"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_predictions_format(self, mock_post):
        """Test generation with predictions format response"""
        service = HuggingFaceLLMService()

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [{"predictions": "Predicted response"}]
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert result["text"] == "Predicted response"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_fallback_placeholder(self, mock_post):
        """Test generation with placeholder response triggers fallback"""
        service = HuggingFaceLLMService()

        # Mock HTTP response with placeholder
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [{"predictions": "model çıktısı"}]
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("Python öğrenmek istiyorum", use_cache=False)

        assert result["success"] is True
        assert "Python" in result["text"]  # Should use educational fallback

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_401_auth_error(self, mock_post):
        """Test generation with 401 authentication error"""
        service = HuggingFaceLLMService()

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Unauthorized"
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert result["metadata"]["model"] == "fallback-educational"
        assert isinstance(result["text"], str)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_other_http_error(self, mock_post):
        """Test generation with other HTTP errors"""
        service = HuggingFaceLLMService()

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert result["metadata"]["model"] == "fallback-educational"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_timeout_error(self, mock_post):
        """Test generation with timeout error"""
        service = HuggingFaceLLMService()

        # Mock timeout
        mock_post.side_effect = asyncio.TimeoutError()

        # Mock session
        mock_session = AsyncMock()
        service._session = mock_session
        service._initialized = True

        result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is True
        assert result["metadata"]["model"] == "fallback-timeout"

    @pytest.mark.asyncio
    async def test_generate_with_cache_hit(self):
        """Test generation with cache hit"""
        service = HuggingFaceLLMService()

        # Set up cache
        cached_response = {
            "success": True,
            "text": "cached response",
            "metadata": {"model": "cached"},
        }
        cache_key = service._generate_cache_key("test prompt")
        service._cache[cache_key] = (cached_response, time.time())

        result = await service.generate("test prompt", use_cache=True)

        assert result == cached_response
        assert result["metadata"]["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_generate_exception_handling(self):
        """Test generation with general exception"""
        service = HuggingFaceLLMService()

        # Force an exception by not setting up session properly
        with patch.object(
            service, "_ensure_session", side_effect=Exception("Test error")
        ):
            result = await service.generate("test prompt", use_cache=False)

        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_for_education_question_generation(self):
        """Test educational generation for question generation"""
        service = HuggingFaceLLMService()

        # Mock the generate method
        with patch.object(
            service,
            "generate",
            return_value={"success": True, "text": "Test question generated"},
        ):
            result = await service.generate_for_education(
                "question_generation", "Sample content for questions"
            )

        assert result["success"] is True
        assert result["task_type"] == "question_generation"
        assert result["content"] == "Test question generated"
        assert "Sample content" in result["original_content"]

    @pytest.mark.asyncio
    async def test_generate_for_education_summarization(self):
        """Test educational generation for summarization"""
        service = HuggingFaceLLMService()

        with patch.object(
            service,
            "generate",
            return_value={"success": True, "text": "Summarized content"},
        ):
            result = await service.generate_for_education(
                "summarization", "Long content to summarize"
            )

        assert result["success"] is True
        assert result["task_type"] == "summarization"
        assert result["content"] == "Summarized content"

    @pytest.mark.asyncio
    async def test_generate_for_education_unknown_task(self):
        """Test educational generation for unknown task type"""
        service = HuggingFaceLLMService()

        with patch.object(
            service,
            "generate",
            return_value={"success": True, "text": "General analysis"},
        ):
            result = await service.generate_for_education(
                "unknown_task", "Some content"
            )

        assert result["success"] is True
        assert result["task_type"] == "unknown_task"

    @pytest.mark.asyncio
    async def test_generate_for_education_failure(self):
        """Test educational generation with failure"""
        service = HuggingFaceLLMService()

        with patch.object(
            service,
            "generate",
            return_value={"success": False, "error": "Generation failed"},
        ):
            result = await service.generate_for_education("summarization", "Content")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_chat_single_message(self):
        """Test chat with single message"""
        service = HuggingFaceLLMService()

        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(
            service,
            "generate",
            return_value={"success": True, "text": "Hello! How can I help you?"},
        ):
            result = await service.chat(messages)

        assert result["success"] is True
        assert "Hello" in result["text"]

    @pytest.mark.asyncio
    async def test_chat_multiple_messages(self):
        """Test chat with multiple messages"""
        service = HuggingFaceLLMService()

        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "How do I learn it?"},
        ]

        with patch.object(
            service,
            "generate",
            return_value={"success": True, "text": "Start with basics..."},
        ):
            result = await service.chat(messages)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_chat_missing_fields(self):
        """Test chat with messages missing role or content"""
        service = HuggingFaceLLMService()

        messages = [
            {"role": "user"},  # Missing content
            {"content": "Hello"},  # Missing role
        ]

        with patch.object(
            service, "generate", return_value={"success": True, "text": "Response"}
        ):
            result = await service.chat(messages)

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.close")
    @patch("redis.asyncio.Redis.close")
    async def test_close(self, mock_redis_close, mock_session_close):
        """Test resource cleanup"""
        service = HuggingFaceLLMService()

        # Set up mock session and redis
        mock_session = AsyncMock()
        mock_session.closed = False
        service._session = mock_session

        mock_redis = AsyncMock()
        service._redis_client = mock_redis

        await service.close()

        mock_session.close.assert_called_once()
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_resources(self):
        """Test cleanup when no resources are initialized"""
        service = HuggingFaceLLMService()

        # Should not raise exception
        await service.close()

    @pytest.mark.asyncio
    async def test_close_with_exception(self):
        """Test cleanup with exception handling"""
        service = HuggingFaceLLMService()

        # Set up session that raises exception on close
        mock_session = AsyncMock()
        mock_session.close.side_effect = Exception("Close error")
        service._session = mock_session

        # Should not raise exception
        await service.close()

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis.keys")
    @patch("redis.asyncio.Redis.delete")
    async def test_clear_cache_redis(self, mock_delete, mock_keys):
        """Test clearing Redis cache"""
        service = HuggingFaceLLMService()

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_keys.return_value = ["llm_cache:key1", "llm_cache:key2"]
        mock_delete.return_value = 2
        service._redis_client = mock_redis

        # Also add memory cache
        service._cache = {"key3": ("data", time.time()), "key4": ("data", time.time())}

        cleared_count = await service.clear_cache()

        assert cleared_count == 4  # 2 from Redis + 2 from memory
        assert len(service._cache) == 0

    @pytest.mark.asyncio
    async def test_clear_cache_memory_only(self):
        """Test clearing memory cache only"""
        service = HuggingFaceLLMService()

        # Set up memory cache
        service._cache = {"key1": ("data", time.time()), "key2": ("data", time.time())}

        cleared_count = await service.clear_cache()

        assert cleared_count == 2
        assert len(service._cache) == 0

    @pytest.mark.asyncio
    async def test_clear_cache_pattern(self):
        """Test clearing cache with specific pattern"""
        service = HuggingFaceLLMService()

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["llm_cache:test_key"]
        mock_redis.delete.return_value = 1
        service._redis_client = mock_redis

        cleared_count = await service.clear_cache("test_*")

        assert cleared_count == 1
        mock_redis.keys.assert_called_once_with("llm_cache:test_*")

    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        service = HuggingFaceLLMService()

        # Set up some cache data
        service._cache = {"key1": ("data", time.time())}

        stats = service.get_cache_stats()

        assert stats["memory_cache_size"] == 1
        assert stats["memory_cache_max_size"] == service._max_cache_size
        assert stats["cache_ttl"] == service._cache_ttl
        assert stats["redis_available"] is False
        assert stats["session_active"] is False

    def test_get_cache_stats_with_session(self):
        """Test getting cache statistics with active session"""
        service = HuggingFaceLLMService()

        # Mock active session
        mock_session = Mock()
        mock_session.closed = False
        service._session = mock_session

        stats = service.get_cache_stats()

        assert stats["session_active"] is True

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    @patch("aiohttp.TCPConnector")
    @patch("aiohttp.ClientSession")
    async def test_initialize_async_components_success(
        self, mock_session, mock_connector, mock_redis
    ):
        """Test successful initialization of async components"""
        service = HuggingFaceLLMService()

        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = None
        mock_redis.return_value = mock_redis_client

        # Mock HTTP session
        mock_session_instance = AsyncMock()
        mock_session.return_value = mock_session_instance

        await service._initialize_async_components()

        assert service._redis_client == mock_redis_client
        assert service._session == mock_session_instance

    @pytest.mark.asyncio
    @patch("redis.asyncio.from_url")
    async def test_initialize_async_components_redis_failure(self, mock_redis):
        """Test initialization with Redis failure"""
        service = HuggingFaceLLMService()

        # Mock Redis failure
        mock_redis.side_effect = Exception("Redis connection failed")

        # Should not raise exception
        await service._initialize_async_components()

    @pytest.mark.asyncio
    async def test_ensure_session_first_time(self):
        """Test ensuring session for the first time"""
        service = HuggingFaceLLMService()

        with patch.object(service, "_initialize_async_components") as mock_init:
            await service._ensure_session()

        assert service._initialized is True
        mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_session_already_initialized(self):
        """Test ensuring session when already initialized"""
        service = HuggingFaceLLMService()
        service._initialized = True
        service._session = Mock()
        service._session.closed = False

        with patch.object(service, "_initialize_async_components") as mock_init:
            await service._ensure_session()

        mock_init.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_session_closed_session(self):
        """Test ensuring session when session is closed"""
        service = HuggingFaceLLMService()
        service._initialized = True
        service._session = Mock()
        service._session.closed = True

        with patch.object(service, "_initialize_async_components") as mock_init:
            await service._ensure_session()

        mock_init.assert_called_once()


class TestSingletonInstance:
    """Test the singleton llm_service instance"""

    def test_singleton_instance_exists(self):
        """Test that singleton instance exists"""
        assert llm_service is not None
        assert isinstance(llm_service, HuggingFaceLLMService)

    def test_singleton_instance_properties(self):
        """Test singleton instance properties"""
        assert hasattr(llm_service, "endpoint_url")
        assert hasattr(llm_service, "headers")
        assert hasattr(llm_service, "_cache")


@pytest.mark.integration
class TestLLMServiceIntegration:
    """Integration tests for LLM Service"""

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self):
        """Test complete generation workflow"""
        service = HuggingFaceLLMService()

        try:
            # Test with cache disabled to ensure we hit the API path
            with patch("aiohttp.ClientSession.post") as mock_post:
                # Mock successful response
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = [{"generated_text": "Test response"}]
                mock_post.return_value.__aenter__.return_value = mock_response

                # Mock session initialization
                with patch.object(service, "_initialize_async_components"):
                    service._session = AsyncMock()
                    service._initialized = True

                    result = await service.generate(
                        prompt="Test prompt",
                        max_tokens=100,
                        temperature=0.7,
                        use_cache=False,
                    )

                assert result["success"] is True
                assert "text" in result
                assert "metadata" in result

        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_educational_workflow(self):
        """Test educational generation workflow"""
        service = HuggingFaceLLMService()

        try:
            with patch.object(service, "generate") as mock_generate:
                mock_generate.return_value = {
                    "success": True,
                    "text": "Generated educational content",
                }

                result = await service.generate_for_education(
                    "question_generation", "Sample educational content"
                )

                assert result["success"] is True
                assert result["task_type"] == "question_generation"
                assert "content" in result

                # Verify the generate method was called with proper system prompt
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args
                assert "system_prompt" in call_args.kwargs
                assert "eğitim" in call_args.kwargs["system_prompt"].lower()

        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_chat_workflow(self):
        """Test chat workflow"""
        service = HuggingFaceLLMService()

        try:
            with patch.object(service, "generate") as mock_generate:
                mock_generate.return_value = {"success": True, "text": "Chat response"}

                messages = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ]

                result = await service.chat(messages)

                assert result["success"] is True
                assert "text" in result

                # Verify conversation format
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args
                conversation = call_args.kwargs["prompt"]
                assert "### User:" in conversation
                assert "### Assistant:" in conversation

        finally:
            await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=core.llm_service", "--cov-report=term-missing"])
