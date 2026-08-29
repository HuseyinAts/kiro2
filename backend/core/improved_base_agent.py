"""
Improved Base Agent Architecture
Teknofest 2025 - Refactored Agent System
"""

import asyncio
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

import bleach
import httpx

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Input sanitization and security controls"""

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Remove potentially harmful HTML/Script content"""
        if not text:
            return ""
        # Remove HTML tags and scripts
        clean_text = bleach.clean(text, tags=[], strip=True)
        # Limit input length to prevent DoS
        return clean_text[:5000]

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Mask API keys and tokens in logs"""
        import re

        # Mask Bearer tokens
        text = re.sub(r"Bearer\s+[\w\-\.]+", "Bearer [MASKED]", text)
        # Mask API keys
        text = re.sub(
            r'(api[_\-]?key["\']?\s*[:=]\s*["\']?)[\w\-\.]+',
            r"\1[MASKED]",
            text,
            flags=re.IGNORECASE,
        )
        return text


class ResponseCache:
    """Simple in-memory cache for responses"""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_size = max_size

    def _generate_key(self, agent: str, message: str) -> str:
        """Generate cache key from agent and message"""
        content = f"{agent}:{message}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def get(self, agent: str, message: str) -> str | None:
        """Get cached response if exists and not expired"""
        key = self._generate_key(agent, message)
        if key in self.cache:
            cached_at, response = self.cache[key]
            if datetime.now() - cached_at < self.ttl:
                logger.debug(f"Cache hit for key: {key}")
                return response
            # Remove expired entry
            del self.cache[key]
        return None

    def set(self, agent: str, message: str, response: str):
        """Store response in cache"""
        # Implement simple LRU by removing oldest if at max size
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]

        key = self._generate_key(agent, message)
        self.cache[key] = (datetime.now(), response)
        logger.debug(f"Cached response for key: {key}")


class LLMConnectionPool:
    """Singleton connection pool for LLM requests"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_client()
        return cls._instance

    @classmethod
    def _initialize_client(cls):
        """Initialize the HTTP client with proper settings"""
        cls._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=5, max_connections=10, keepalive_expiry=30
            ),
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=30.0),
        )
        logger.info("Initialized LLM connection pool")

    @classmethod
    async def close(cls):
        """Properly close the client"""
        if cls._client:
            await cls._client.aclose()
            cls._client = None
            cls._instance = None
            logger.info("Closed LLM connection pool")

    def get_client(self) -> httpx.AsyncClient:
        """Get the shared client instance"""
        if not self._client:
            self._initialize_client()
        return self._client


@dataclass
class ConversationContext:
    """Maintain conversation context for better responses"""

    session_id: str
    student_id: str | None = None
    history: list[dict] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.metadata is None:
            self.metadata = {}

    def add_interaction(self, message: str, response: str, agent: str):
        """Add new interaction to history"""
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "message": message,
                "response": response,
            }
        )
        # Keep only last 10 interactions to limit memory usage
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def get_context_summary(self) -> str:
        """Get summary of recent conversation"""
        if not self.history:
            return ""

        recent = self.history[-3:]  # Last 3 interactions
        summary = []
        for item in recent:
            summary.append(f"User: {item['message'][:100]}...")
            summary.append(f"Agent: {item['response'][:100]}...")

        return "\n".join(summary)


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, name: str):
        self.name = name
        self.security = SecurityMiddleware()
        self.cache = ResponseCache()
        self.llm_pool = LLMConnectionPool()
        self.use_mock = os.getenv("USE_MOCK_RESPONSES", "false").lower() == "true"

    async def process(
        self, message: str, context: ConversationContext | None = None
    ) -> str:
        """Main processing method with security and caching"""

        # 1. Sanitize input
        clean_message = self.security.sanitize_input(message)
        if not clean_message:
            return "Geçersiz mesaj. Lütfen tekrar deneyin."

        # 2. Check cache
        cached_response = self.cache.get(self.name, clean_message)
        if cached_response:
            return cached_response

        # 3. Process message
        try:
            if self.use_mock:
                response = await self._process_mock(clean_message, context)
            else:
                response = await self._process_with_llm(clean_message, context)

            # 4. Cache successful response
            if response:
                self.cache.set(self.name, clean_message, response)

            # 5. Update context
            if context:
                context.add_interaction(clean_message, response, self.name)

            return response

        except Exception as e:
            logger.error(
                f"Error in {self.name}: {self.security.mask_sensitive_data(str(e))}"
            )
            return await self._get_fallback_response(clean_message)

    @abstractmethod
    async def _process_mock(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """Process with mock responses - must be implemented by subclasses"""

    @abstractmethod
    async def _process_with_llm(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """Process with LLM - must be implemented by subclasses"""

    @abstractmethod
    async def _get_fallback_response(self, message: str) -> str:
        """Get fallback response when errors occur"""

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, _):
        """Context manager exit - cleanup resources"""
        # Connection pool is singleton, don't close here


class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state == "open":
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = "half_open"
                return False
            return True
        return False

    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.is_open():
            raise Exception("Circuit breaker is open - service unavailable")

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


# Example implementation
class ImprovedLearningAgent(BaseAgent):
    """Improved learning agent with better architecture"""

    def __init__(self):
        super().__init__("LearningAgent")
        self.circuit_breaker = CircuitBreaker()

    async def _process_mock(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """Process with mock responses"""
        # Load from external file instead of hardcoding
        return self._get_mock_response_from_file(message)

    async def _process_with_llm(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """Process with LLM using connection pool"""
        client = self.llm_pool.get_client()

        # Prepare context-aware prompt
        prompt = self._build_prompt(message, context)

        try:
            response = await self.circuit_breaker.call(self._call_llm, client, prompt)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return await self._get_fallback_response(message)

    async def _call_llm(self, client: httpx.AsyncClient, prompt: str) -> str:
        """Make actual LLM API call"""
        # Implementation here

    async def _get_fallback_response(self, message: str) -> str:
        """Fallback response when LLM fails"""
        return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."

    def _build_prompt(self, message: str, context: ConversationContext | None) -> str:
        """Build context-aware prompt"""
        base_prompt = f"Sen bir eğitim asistanısın. Öğrencinin sorusu: {message}"

        if context and context.history:
            base_prompt = f"Önceki konuşma özeti:\n{context.get_context_summary()}\n\n{base_prompt}"

        return base_prompt

    @lru_cache(maxsize=100)
    def _get_mock_response_from_file(self, message: str) -> str:
        """Load mock responses from external configuration"""
        # This would load from YAML/JSON file
        return f"Mock response for: {message}"


# Usage example
async def main():
    """Example usage of improved agent"""

    # Create context for conversation
    context = ConversationContext(session_id="test-session", student_id="student-123")

    # Use agent with context manager for proper cleanup
    async with ImprovedLearningAgent() as agent:
        response = await agent.process("LGS matematik konuları", context)
        print(response)

    # Cleanup connection pool when application shuts down
    await LLMConnectionPool.close()


if __name__ == "__main__":
    asyncio.run(main())
