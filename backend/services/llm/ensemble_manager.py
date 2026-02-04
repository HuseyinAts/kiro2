"""
Multi-LLM Ensemble Manager
Coordinates multiple LLM providers for ÖSYM question generation

Author: KIRO AI Team
Date: 2025-10-19
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import statistics

from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMProvider, LLMCapability, MultiLLMConfig
from services.llm.openai_provider import OpenAIProvider
from services.llm.claude_provider import ClaudeProvider
from services.llm.qwen_provider import QwenProvider


class EnsembleStrategy:
    """
    Ensemble voting strategies for multi-LLM consensus
    """

    @staticmethod
    def majority_voting(
        responses: List[LLMResponse], weights: Optional[Dict[LLMProvider, float]] = None
    ) -> LLMResponse:
        """
        Weighted majority voting

        Args:
            responses: List of LLM responses
            weights: Provider weights (optional)

        Returns:
            Best response based on weighted voting
        """
        if not weights:
            weights = MultiLLMConfig.ENSEMBLE_STRATEGY["voting"]["weights"]

        # Calculate weighted scores
        scored_responses = []
        for response in responses:
            weight = weights.get(response.provider, 0.33)
            # Use confidence score if available, otherwise use inverse latency
            confidence = response.confidence_score or (
                1000.0 / max(response.latency_ms, 1)
            )
            score = weight * confidence
            scored_responses.append((score, response))

        # Sort by score and return best
        scored_responses.sort(key=lambda x: x[0], reverse=True)
        return scored_responses[0][1]

    @staticmethod
    def quality_threshold_filter(
        responses: List[LLMResponse], min_quality: float = 0.7
    ) -> List[LLMResponse]:
        """
        Filter responses by quality threshold

        Args:
            responses: List of responses
            min_quality: Minimum quality score

        Returns:
            Filtered responses
        """
        return [r for r in responses if (r.confidence_score or 0.5) >= min_quality]

    @staticmethod
    def cost_optimized_selection(
        responses: List[LLMResponse], quality_threshold: float = 0.7
    ) -> LLMResponse:
        """
        Select most cost-effective response above quality threshold

        Args:
            responses: List of responses
            quality_threshold: Minimum acceptable quality

        Returns:
            Most cost-effective quality response
        """
        # Filter by quality
        quality_responses = [
            r for r in responses if (r.confidence_score or 0.5) >= quality_threshold
        ]

        if not quality_responses:
            # If no response meets threshold, return best quality
            return max(responses, key=lambda r: r.confidence_score or 0)

        # Return cheapest among quality responses
        return min(quality_responses, key=lambda r: r.cost_usd)

    @staticmethod
    def latency_optimized_selection(
        responses: List[LLMResponse], quality_threshold: float = 0.7
    ) -> LLMResponse:
        """
        Select fastest response above quality threshold

        Args:
            responses: List of responses
            quality_threshold: Minimum acceptable quality

        Returns:
            Fastest quality response
        """
        quality_responses = [
            r for r in responses if (r.confidence_score or 0.5) >= quality_threshold
        ]

        if not quality_responses:
            return max(responses, key=lambda r: r.confidence_score or 0)

        return min(quality_responses, key=lambda r: r.latency_ms)


class MultiLLMEnsembleManager:
    """
    Multi-LLM Ensemble Manager

    Coordinates OpenAI GPT-4, Claude Sonnet, and Qwen models
    for ÖSYM question generation
    """

    def __init__(
        self,
        enable_openai: bool = True,
        enable_claude: bool = True,
        enable_qwen: bool = True,
        qwen_use_local: bool = False,
    ):
        """
        Initialize ensemble manager

        Args:
            enable_openai: Enable OpenAI GPT-4
            enable_claude: Enable Claude Sonnet
            enable_qwen: Enable Qwen
            qwen_use_local: Use local Qwen deployment
        """
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}

        # Initialize providers
        if enable_openai:
            try:
                self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                    MultiLLMConfig.OPENAI_CONFIG
                )
                print("✅ OpenAI GPT-4 initialized")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")

        if enable_claude:
            try:
                self.providers[LLMProvider.CLAUDE] = ClaudeProvider(
                    MultiLLMConfig.CLAUDE_CONFIG
                )
                print("✅ Claude Sonnet initialized")
            except Exception as e:
                print(f"⚠️  Claude initialization failed: {e}")

        if enable_qwen:
            try:
                self.providers[LLMProvider.QWEN] = QwenProvider(
                    MultiLLMConfig.QWEN_CONFIG, use_local=qwen_use_local
                )
                print(f"✅ Qwen initialized ({'local' if qwen_use_local else 'cloud'})")
            except Exception as e:
                print(f"⚠️  Qwen initialization failed: {e}")

        if not self.providers:
            raise RuntimeError("No LLM providers initialized successfully")

        print(f"\n🤖 Ensemble Manager ready with {len(self.providers)} provider(s)")

    async def generate_with_ensemble(
        self,
        request: LLMRequest,
        strategy: str = "majority_voting",
        fallback: bool = True,
    ) -> LLMResponse:
        """
        Generate response using ensemble of LLMs

        Args:
            request: LLM request
            strategy: Voting strategy (majority_voting, cost_optimized, latency_optimized)
            fallback: Use fallback if primary fails

        Returns:
            Best response according to strategy
        """
        # Generate from all available providers concurrently
        tasks = []
        provider_map = {}

        for provider_type, provider in self.providers.items():
            task = provider.generate(request)
            tasks.append(task)
            provider_map[task] = provider_type

        # Wait for all with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=30.0
            )
        except asyncio.TimeoutError:
            print("⚠️  Ensemble generation timeout")
            results = [asyncio.TimeoutError()] * len(tasks)

        # Filter successful responses
        successful_responses = []
        for result in results:
            if isinstance(result, LLMResponse):
                successful_responses.append(result)
            elif isinstance(result, Exception):
                print(f"⚠️  Provider error: {result}")

        if not successful_responses:
            raise RuntimeError("All providers failed to generate response")

        # Apply strategy
        if strategy == "majority_voting":
            return EnsembleStrategy.majority_voting(successful_responses)
        elif strategy == "cost_optimized":
            return EnsembleStrategy.cost_optimized_selection(successful_responses)
        elif strategy == "latency_optimized":
            return EnsembleStrategy.latency_optimized_selection(successful_responses)
        else:
            return successful_responses[0]

    async def generate_with_fallback(
        self, request: LLMRequest, preferred_provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """
        Generate with fallback chain

        Args:
            request: LLM request
            preferred_provider: Preferred provider (optional)

        Returns:
            Response from first successful provider
        """
        fallback_order = MultiLLMConfig.ENSEMBLE_STRATEGY["fallback_order"]

        # Add preferred provider to front if specified
        if preferred_provider and preferred_provider in self.providers:
            fallback_order = [preferred_provider] + [
                p for p in fallback_order if p != preferred_provider
            ]

        # Try each provider in order
        last_error = None
        for provider_type in fallback_order:
            if provider_type not in self.providers:
                continue

            try:
                provider = self.providers[provider_type]
                response = await provider.generate(request)
                print(f"✅ Success with {provider_type.value}")
                return response

            except Exception as e:
                print(f"⚠️  {provider_type.value} failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def check_health_all(self) -> Dict[LLMProvider, bool]:
        """
        Check health of all providers

        Returns:
            Health status for each provider
        """
        health_status = {}

        tasks = []
        provider_types = []

        for provider_type, provider in self.providers.items():
            tasks.append(provider.check_health())
            provider_types.append(provider_type)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for provider_type, result in zip(provider_types, results):
            if isinstance(result, bool):
                health_status[provider_type] = result
            else:
                health_status[provider_type] = False

        return health_status

    def get_metrics_all(self) -> Dict[LLMProvider, Dict[str, Any]]:
        """
        Get performance metrics from all providers

        Returns:
            Metrics dictionary for each provider
        """
        return {
            provider_type: provider.get_metrics()
            for provider_type, provider in self.providers.items()
        }

    def get_best_provider_for_capability(
        self, capability: LLMCapability, prefer_cost_effective: bool = False
    ) -> Optional[BaseLLMProvider]:
        """
        Get best available provider for specific capability

        Args:
            capability: Required capability
            prefer_cost_effective: Prefer cheaper providers

        Returns:
            Best provider instance or None
        """
        best_provider_type = MultiLLMConfig.get_best_provider_for_capability(
            capability, prefer_cost_effective
        )

        return self.providers.get(best_provider_type)

    async def generate_osym_question_ensemble(
        self,
        topic: str,
        subtopic: str,
        difficulty: float,
        bloom_level: int,
        exam_type: str,
        use_voting: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate ÖSYM question using ensemble

        Args:
            topic: Main topic
            subtopic: Subtopic
            difficulty: Difficulty 0-1
            bloom_level: Bloom level 1-6
            exam_type: TYT/AYT/YDT
            use_voting: Use ensemble voting vs single best

        Returns:
            Generated question with metadata
        """
        # Generate from all providers
        tasks = []
        for provider in self.providers.values():
            if hasattr(provider, "create_osym_question"):
                task = provider.create_osym_question(
                    topic, subtopic, difficulty, bloom_level, exam_type
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_questions = []
        for result in results:
            if isinstance(result, dict) and "stem" in result:
                successful_questions.append(result)

        if not successful_questions:
            raise RuntimeError("All providers failed to generate question")

        if use_voting and len(successful_questions) > 1:
            # Ensemble voting: return best based on quality
            # For now, return first (can be enhanced with similarity comparison)
            return successful_questions[0]
        else:
            return successful_questions[0]

    def __repr__(self):
        provider_names = ", ".join([p.value for p in self.providers.keys()])
        return f"<MultiLLMEnsembleManager providers=[{provider_names}]>"
