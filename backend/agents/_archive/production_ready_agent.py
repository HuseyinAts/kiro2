"""
Production-Ready Agent Implementation
Teknofest 2025 - Complete refactored agent with all improvements
"""

import asyncio
import logging
import os

# Import improved components
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..core.content_manager import ContentProvider
from ..core.improved_base_agent import (
    BaseAgent,
    CircuitBreaker,
    ConversationContext,
    LLMConnectionPool,
)
from ..core.llm_service import llm_service
from ..core.metrics_collector import HealthChecker, PerformanceMonitor, global_metrics

logger = logging.getLogger(__name__)


class ProductionLearningAgent(BaseAgent):
    """
    Production-ready learning agent with all improvements:
    - Content management
    - Metrics collection
    - Circuit breaker
    - Context awareness
    - Security middleware
    - Connection pooling
    - Response caching
    """

    def __init__(self):
        super().__init__("ProductionLearningAgent")

        # Initialize components
        self.content_provider = ContentProvider()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.health_checker = HealthChecker(global_metrics)

        # Agent configuration
        self.max_context_length = 1000
        self.response_timeout = 10.0

        logger.info(f"Initialized {self.name} with production settings")

    async def process(
        self, message: str, context: ConversationContext | None = None
    ) -> str:
        """
        Enhanced process method with monitoring and error handling
        """

        # Record request metric
        global_metrics.record_request(self.name)

        # Use performance monitor
        async with PerformanceMonitor(global_metrics, self.name, "process"):
            try:
                # Call parent process with security and caching
                response = await super().process(message, context)
                return response

            except Exception as e:
                logger.error(f"Processing error: {e}")
                global_metrics.record_error(self.name, type(e).__name__)
                return await self._get_fallback_response(message)

    async def _process_mock(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """
        Process with dynamic content from content manager
        """

        message_lower = message.lower()

        # Check for LGS content
        if "lgs" in message_lower:
            if "matematik" in message_lower:
                response = await self.content_provider.get_lgs_math_content()
            elif "plan" in message_lower or "program" in message_lower:
                # Get personalized plan based on context
                available_hours = 20  # Default
                if context and "available_hours" in context.metadata:
                    available_hours = context.metadata["available_hours"]

                response = await self.content_provider.get_personalized_plan(
                    "lgs_matematik", available_hours=available_hours
                )
            elif "kaynak" in message_lower or "resource" in message_lower:
                response = await self.content_provider.get_study_resources(
                    "lgs_matematik"
                )
            else:
                response = await self._get_general_lgs_info()
        else:
            # Default educational response
            response = await self._get_educational_response(message, context)

        return response

    async def _process_with_llm(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """
        Process with LLM using circuit breaker and connection pool
        """

        # Check cache first
        cache_key = f"{self.name}:{message}"
        cached = self.cache.get(self.name, message)
        if cached:
            global_metrics.record_cache_hit(self.name)
            return cached

        global_metrics.record_cache_miss(self.name)

        # Prepare context-aware prompt
        prompt = self._build_enhanced_prompt(message, context)

        # Try LLM with circuit breaker
        try:
            start_time = time.perf_counter()

            response = await self.circuit_breaker.call(
                self._call_llm_with_timeout, prompt, context
            )

            duration = time.perf_counter() - start_time
            global_metrics.record_llm_call(self.name, success=True, duration=duration)

            return response

        except Exception as e:
            logger.warning(f"LLM call failed: {e}, using fallback")
            global_metrics.record_fallback_used(self.name)

            # Try to get content from content manager
            return await self._get_content_based_response(message)

    async def _call_llm_with_timeout(
        self, prompt: str, context: ConversationContext | None
    ) -> str:
        """
        Call LLM with timeout protection
        """

        try:
            # Use asyncio timeout
            async with asyncio.timeout(self.response_timeout):
                result = await llm_service.generate(
                    prompt=prompt,
                    system_prompt=self._get_system_prompt(context),
                    temperature=0.7,
                    max_tokens=1000,
                )

                if result.get("success") and result.get("text"):
                    return result["text"]
                raise Exception("LLM returned empty response")

        except TimeoutError:
            raise Exception(f"LLM timeout after {self.response_timeout}s")

    def _build_enhanced_prompt(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """
        Build context-aware prompt with relevant information
        """

        parts = []

        # Add context if available
        if context:
            # Add conversation history
            if context.history:
                parts.append("Önceki konuşma özeti:")
                parts.append(context.get_context_summary())
                parts.append("")

            # Add student information if available
            if context.student_id:
                parts.append(f"Öğrenci ID: {context.student_id}")

                # Add any metadata
                if context.metadata:
                    if "grade" in context.metadata:
                        parts.append(f"Sınıf: {context.metadata['grade']}")
                    if "exam_target" in context.metadata:
                        parts.append(f"Hedef: {context.metadata['exam_target']}")
                parts.append("")

        # Add the actual message
        parts.append(f"Öğrenci sorusu: {message}")

        return "\n".join(parts)

    def _get_system_prompt(self, context: ConversationContext | None) -> str:
        """
        Get dynamic system prompt based on context
        """

        base_prompt = """Sen Türkiye'deki öğrenciler için geliştirilmiş bir eğitim asistanısın.
        Özellikle LGS ve YKS sınavlarına hazırlanan öğrencilere yardımcı oluyorsun.
        MEB müfredatına uygun, güncel ve doğru bilgiler vermelisin.
        Açıklamalarını net, anlaşılır ve öğrenci dostu bir dille yapmalısın.
        """

        # Customize based on context
        if context and context.metadata:
            exam = context.metadata.get("exam_target", "")
            if "LGS" in exam:
                base_prompt += (
                    "\nÖğrenci LGS'ye hazırlanıyor, 8. sınıf seviyesinde açıklama yap."
                )
            elif "YKS" in exam:
                base_prompt += "\nÖğrenci YKS'ye hazırlanıyor, lise seviyesinde detaylı açıklama yap."

        return base_prompt

    async def _get_content_based_response(self, message: str) -> str:
        """
        Get response from content manager when LLM fails
        """

        message_lower = message.lower()

        # Try to match keywords with content
        if any(word in message_lower for word in ["matematik", "mat", "sayı"]):
            return await self.content_provider.get_lgs_math_content()
        if any(word in message_lower for word in ["plan", "program", "çalışma"]):
            return await self.content_provider.get_personalized_plan("lgs_matematik")
        if any(word in message_lower for word in ["kaynak", "video", "kitap"]):
            return await self.content_provider.get_study_resources("lgs_matematik")
        return await self._get_fallback_response(message)

    async def _get_fallback_response(self, message: str) -> str:
        """
        Ultimate fallback response
        """

        responses = [
            "Özür dilerim, şu anda bu soruya yanıt veremiyorum. Lütfen daha sonra tekrar deneyin.",
            "Teknik bir sorun yaşıyoruz. Size yardımcı olmak için farklı bir soru sorabilir misiniz?",
            f"'{message}' konusunda size yardımcı olamadım. Başka bir konuda yardım isteyebilirsiniz.",
        ]

        import random

        return random.choice(responses)

    async def _get_educational_response(
        self, message: str, context: ConversationContext | None
    ) -> str:
        """
        Generate educational response based on message patterns
        """

        # This would contain educational logic
        return f"Eğitim konusunda size yardımcı olmak için buradayım. {message} hakkında detaylı bilgi verebilirim."

    async def _get_general_lgs_info(self) -> str:
        """
        Get general LGS information
        """

        return """[BOOKS] **LGS HAKKINDA GENEL BİLGİLER**

LGS (Liselere Geçiş Sınavı), 8. sınıf öğrencilerinin gireceği merkezi sınavdır.

**Sınav İçeriği:**
• Sözel Bölüm (75 dakika): Türkçe, İnkılap Tarihi, Din Kültürü, İngilizce
• Sayısal Bölüm (80 dakika): Matematik, Fen Bilimleri

Hangi ders hakkında detaylı bilgi almak istersiniz?"""

    async def get_health_status(self) -> dict:
        """
        Get agent health status
        """

        health = await self.health_checker.get_health_status()

        # Add agent-specific checks
        health["checks"]["circuit_breaker"] = {
            "status": "open" if self.circuit_breaker.is_open() else "closed",
            "failures": self.circuit_breaker.failure_count,
        }

        return health

    async def cleanup(self):
        """
        Cleanup resources
        """

        logger.info(f"Cleaning up {self.name}")
        # Connection pool is shared, don't close here


# Factory pattern for creating agents
class AgentFactory:
    """
    Factory for creating production-ready agents
    """

    _agents = {}

    @classmethod
    def create_agent(cls, agent_type: str) -> BaseAgent:
        """
        Create or get existing agent instance
        """

        if agent_type not in cls._agents:
            if agent_type == "learning":
                cls._agents[agent_type] = ProductionLearningAgent()
            # Add other agent types here
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")

        return cls._agents[agent_type]

    @classmethod
    async def cleanup_all(cls):
        """
        Cleanup all agents
        """

        for agent in cls._agents.values():
            if hasattr(agent, "cleanup"):
                await agent.cleanup()

        # Close connection pool
        await LLMConnectionPool.close()


# Example usage
async def main():
    """
    Example of using production-ready agent
    """

    # Create agent
    agent = AgentFactory.create_agent("learning")

    # Create context
    context = ConversationContext(
        session_id="prod-session-001",
        student_id="student-456",
        metadata={"grade": 8, "exam_target": "LGS", "available_hours": 25},
    )

    # Process messages
    messages = [
        "LGS matematik konuları nelerdir?",
        "Bana kişisel çalışma planı oluştur",
        "Matematik için hangi kaynakları önerirsin?",
    ]

    for msg in messages:
        print(f"\n[MEMO] Soru: {msg}")
        response = await agent.process(msg, context)
        print(f"🤖 Yanıt: {response[:200]}...")  # Show first 200 chars

    # Get metrics
    metrics = global_metrics.get_metrics_summary()
    print("\n[CHART] Metrics Summary:")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Error Rate: {metrics['error_rate']:.2%}")

    # Get health status
    health = await agent.get_health_status()
    print(f"\n❤️ Health Status: {health['status']}")

    # Cleanup
    await AgentFactory.cleanup_all()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run example
    asyncio.run(main())
