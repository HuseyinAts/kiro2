"""
Multi-LLM Ensemble Manager
Coordinates multiple LLM providers for ÖSYM question generation
and sequential thinking/reasoning

Author: KIRO AI Team
Date: 2025-10-19 (Updated: 2026-01-16)
"""

import asyncio
import logging
from typing import Any

from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMCapability, LLMProvider, MultiLLMConfig
from services.llm.sequential_thinking_mixin import (
    ReasoningResult,
)

logger = logging.getLogger(__name__)

# Lazy imports for providers - avoid import failures when packages are missing
# These are imported inside try/except blocks in __init__
#
# NOT: durum mesajlari `print()` yerine `logger` kullanir (bkz. S255+1) --
# eski surum emoji karakterler icin (U+2705 vb.) `print()` kullaniyordu ve
# Windows'ta UTF-8 olmayan konsol code page'lerinde (ör. cp1254) modul
# IMPORT ANINDA `UnicodeEncodeError` ile cokuyordu -- ilk provider init
# hatasinda soft-fail yerine hard-crash. Olculdu:
# services/ai_mentor_service.py'nin modul-seviyesi singleton'i bu yuzden
# hicbir saglayici anahtari olmayan bir gelistirme ortaminda import bile
# edilemiyordu.


class EnsembleStrategy:
    """
    Ensemble voting strategies for multi-LLM consensus
    """

    @staticmethod
    def majority_voting(
        responses: list[LLMResponse], weights: dict[LLMProvider, float] | None = None
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
        responses: list[LLMResponse], min_quality: float = 0.7
    ) -> list[LLMResponse]:
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
        responses: list[LLMResponse], quality_threshold: float = 0.7
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
        responses: list[LLMResponse], quality_threshold: float = 0.7
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
        enable_gemini: bool = True,
        qwen_use_local: bool = False,
        gemini_thinking_mode: bool = True,
    ) -> None:
        """Initialize ensemble manager.

        Args:
            enable_openai: Enable OpenAI GPT-4
            enable_claude: Enable Claude Sonnet
            enable_qwen: Enable Qwen
            enable_gemini: Enable Gemini (with thinking mode)
            qwen_use_local: Use local Qwen deployment
            gemini_thinking_mode: Enable Gemini thinking mode

        Raises:
            RuntimeError: If no providers can be initialized
        """
        self.providers: dict[LLMProvider, BaseLLMProvider] = {}

        # Initialize Gemini first (best for sequential thinking)
        if enable_gemini:
            try:
                from services.llm.gemini_provider import GeminiProvider

                self.providers[LLMProvider.GEMINI] = GeminiProvider(
                    MultiLLMConfig.GEMINI_CONFIG, thinking_mode=gemini_thinking_mode
                )
                logger.info("Gemini initialized (thinking mode)")
            except Exception as e:
                logger.warning("Gemini initialization failed: %s", e)

        # Initialize providers (lazy imports)
        if enable_openai:
            try:
                from services.llm.openai_provider import OpenAIProvider

                self.providers[LLMProvider.OPENAI] = OpenAIProvider(
                    MultiLLMConfig.OPENAI_CONFIG
                )
                logger.info("OpenAI GPT-4 initialized")
            except Exception as e:
                logger.warning("OpenAI initialization failed: %s", e)

        if enable_claude:
            try:
                from services.llm.claude_provider import ClaudeProvider

                self.providers[LLMProvider.CLAUDE] = ClaudeProvider(
                    MultiLLMConfig.CLAUDE_CONFIG
                )
                logger.info("Claude Sonnet initialized")
            except Exception as e:
                logger.warning("Claude initialization failed: %s", e)

        if enable_qwen:
            try:
                from services.llm.qwen_provider import QwenProvider

                self.providers[LLMProvider.QWEN] = QwenProvider(
                    MultiLLMConfig.QWEN_CONFIG, use_local=qwen_use_local
                )
                logger.info(
                    "Qwen initialized (%s)", "local" if qwen_use_local else "cloud"
                )
            except Exception as e:
                logger.warning("Qwen initialization failed: %s", e)

        if not self.providers:
            raise RuntimeError("No LLM providers initialized successfully")

        logger.info("Ensemble Manager ready with %d provider(s)", len(self.providers))

    async def generate_with_ensemble(
        self,
        request: LLMRequest,
        strategy: str = "majority_voting",
        fallback: bool = True,
    ) -> LLMResponse:
        """
        Generate response using ensemble of LLMs.
        [OPTIMIZED: Avoids 4x API costs by delegating to fallback chain instead of concurrent requests]

        Args:
            request: LLM request
            strategy: Voting strategy (majority_voting, cost_optimized, latency_optimized)
            fallback: Use fallback if primary fails

        Returns:
            Best response according to strategy
        """
        logger.info(
            "[Token Optimization] generate_with_ensemble intercepted! Delegating to fallback chain to prevent 4x cost inflation."
        )
        return await self.generate_with_fallback(request)

    async def generate_with_fallback(
        self, request: LLMRequest, preferred_provider: LLMProvider | None = None
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
                logger.info("Success with %s", provider_type.value)
                return response

            except Exception as e:
                logger.warning("%s failed: %s", provider_type.value, e)
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def check_health_all(self) -> dict[LLMProvider, bool]:
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

        for provider_type, result in zip(provider_types, results, strict=False):
            if isinstance(result, bool):
                health_status[provider_type] = result
            else:
                health_status[provider_type] = False

        return health_status

    def get_metrics_all(self) -> dict[LLMProvider, dict[str, Any]]:
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
    ) -> BaseLLMProvider | None:
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
    ) -> dict[str, Any]:
        """
        Generate ÖSYM question using ensemble.
        [OPTIMIZED: Avoids 4x API costs by using the best single provider]

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
        logger.info(
            "[Token Optimization] generate_osym_question_ensemble intercepted! Using primary provider only."
        )

        # Try finding a provider with the create_osym_question capability
        for provider in self.providers.values():
            if hasattr(provider, "create_osym_question"):
                try:
                    result = await provider.create_osym_question(
                        topic, subtopic, difficulty, bloom_level, exam_type
                    )
                    if isinstance(result, dict) and "stem" in result:
                        return result
                except Exception as e:
                    logger.warning("Provider %s failed: %s", provider, e)
                    continue

        raise RuntimeError("All providers failed to generate question")

    def __repr__(self) -> str:
        """Return string representation."""
        provider_names = ", ".join([p.value for p in self.providers])
        return f"<MultiLLMEnsembleManager providers=[{provider_names}]>"

    # =========================================================================
    # Sequential Thinking Methods
    # =========================================================================

    async def sequential_thinking_ensemble(
        self,
        problem: str,
        max_steps: int = 10,
        use_voting: bool = True,
        preferred_provider: LLMProvider | None = None,
    ) -> dict[str, Any]:
        """
        Solve problem with sequential thinking using multiple providers.
        [OPTIMIZED: Evaluates sequentially and short-circuits on first success]

        Args:
            problem: Problem to solve
            max_steps: Maximum reasoning steps
            use_voting: Use ensemble voting for best result
            preferred_provider: Preferred provider (optional)

        Returns:
            Best reasoning result from ensemble
        """
        logger.info(
            "[Token Optimization] sequential_thinking_ensemble intercepted! Short-circuiting on first success."
        )
        thinking_order = MultiLLMConfig.ENSEMBLE_STRATEGY.get(
            "sequential_thinking_order",
            [
                LLMProvider.GEMINI,
                LLMProvider.CLAUDE,
                LLMProvider.OPENAI,
                LLMProvider.QWEN,
            ],
        )

        if preferred_provider:
            thinking_order = [preferred_provider] + [
                p for p in thinking_order if p != preferred_provider
            ]

        last_error = None
        for provider_type in thinking_order:
            if provider_type not in self.providers:
                continue

            provider = self.providers[provider_type]
            try:
                if hasattr(provider, "think_step_by_step"):
                    result = await provider.think_step_by_step(
                        problem, max_steps=max_steps
                    )
                else:
                    result = await self._generate_with_thinking_prompt(
                        provider, problem, max_steps
                    )

                if isinstance(result, dict):
                    result["provider"] = provider_type.value
                    return result
                if isinstance(result, ReasoningResult):
                    res_dict: dict[str, Any] = result.to_dict()
                    res_dict["provider"] = provider_type.value
                    return res_dict
            except Exception as e:
                logger.warning("%s failed: %s", provider_type.value, e)
                last_error = e
                continue

        raise RuntimeError(
            f"All providers failed for sequential thinking. Last error: {last_error}"
        )

    async def _generate_with_thinking_prompt(
        self, provider: BaseLLMProvider, problem: str, max_steps: int
    ) -> dict[str, Any]:
        """Generate with thinking prompt for providers without native support"""
        prompt = f"""Asagidaki problemi adim adim coz.

Problem: {problem}

Her adimda:
1. Bu adimda ne yaptigini acikla
2. Neden bu adimi attigini soyle
3. Ara sonucu ver

Maksimum {max_steps} adim kullan.

Cozum:"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir mantik ve problem cozme uzmanisin. Adim adim dusun.",
            max_tokens=4096,
            temperature=0.3,
        )

        response = await provider.generate(request)

        return {
            "problem": problem,
            "understanding": "Generated with thinking prompt",
            "steps": [{"description": response.content}],
            "final_answer": response.content,
            "provider": str(provider.provider),
            "latency_ms": response.latency_ms,
        }

    def _vote_on_reasoning_results(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Vote on multiple reasoning results to select best"""
        if not results:
            raise ValueError("No results to vote on")

        if len(results) == 1:
            return results[0]

        # Score each result
        scored_results = []
        for result in results:
            score = 0.0

            # Provider weight
            provider = result.get("provider", "unknown")
            weights = MultiLLMConfig.ENSEMBLE_STRATEGY["voting"]["weights"]
            provider_enum = (
                LLMProvider(provider)
                if provider in [p.value for p in LLMProvider]
                else None
            )
            if provider_enum:
                score += weights.get(provider_enum, 0.2) * 10

            # Step count (prefer detailed reasoning)
            steps = result.get("steps", [])
            if 3 <= len(steps) <= 10:
                score += 5  # Ideal step count
            elif len(steps) > 0:
                score += 2

            # Confidence score
            confidence = result.get("confidence", 0.5)
            score += confidence * 5

            # Has verification
            if result.get("verification"):
                score += 3

            # Latency penalty (prefer faster)
            latency = result.get("latency_ms", 5000)
            if latency < 2000:
                score += 2
            elif latency < 5000:
                score += 1

            scored_results.append((score, result))

        # Sort by score and return best
        scored_results.sort(key=lambda x: x[0], reverse=True)

        best_result = scored_results[0][1]
        best_result["ensemble_scores"] = {
            r.get("provider", "unknown"): s for s, r in scored_results
        }
        best_result["voting_winner"] = True

        return best_result

    async def solve_with_best_provider(
        self,
        problem: str,
        capability: LLMCapability = LLMCapability.SEQUENTIAL_THINKING,
    ) -> dict[str, Any]:
        """
        Solve problem with best available provider for capability

        Args:
            problem: Problem to solve
            capability: Required capability

        Returns:
            Solution result
        """
        # Find best provider for capability
        best_provider_type = MultiLLMConfig.get_best_provider_for_capability(
            capability, prefer_cost_effective=True
        )

        if best_provider_type not in self.providers:
            # Fallback to any available
            available = list(self.providers.keys())
            if not available:
                raise RuntimeError("No providers available")
            best_provider_type = available[0]

        provider = self.providers[best_provider_type]

        # Use appropriate method based on capability
        if capability == LLMCapability.SEQUENTIAL_THINKING and hasattr(
            provider, "think_step_by_step"
        ):
            thinking_result: dict[str, Any] = await provider.think_step_by_step(problem)
            return thinking_result
        if capability == LLMCapability.MATH_REASONING and hasattr(
            provider, "solve_math_problem"
        ):
            math_result: dict[str, Any] = await provider.solve_math_problem(problem)
            return math_result
        # Generic generation
        request = LLMRequest(
            prompt=problem,
            max_tokens=4096,
            temperature=0.3,
        )
        response = await provider.generate(request)
        return {
            "problem": problem,
            "answer": response.content,
            "provider": best_provider_type.value,
            "latency_ms": response.latency_ms,
        }

    async def compare_providers(self, problem: str) -> dict[str, Any]:
        """
        Compare all providers on same problem

        Args:
            problem: Problem to solve

        Returns:
            Comparison results from all providers
        """
        tasks = []
        provider_types = []

        for provider_type, provider in self.providers.items():
            if hasattr(provider, "think_step_by_step"):
                task = provider.think_step_by_step(problem)
            else:
                task = self._generate_with_thinking_prompt(provider, problem, 10)

            tasks.append(task)
            provider_types.append(provider_type)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        comparison: dict[str, Any] = {
            "problem": problem,
            "providers": {},
            "best_provider": None,
            "fastest_provider": None,
        }

        min_latency = float("inf")
        best_score = 0

        for i, result in enumerate(results):
            provider_name = provider_types[i].value

            if isinstance(result, Exception):
                comparison["providers"][provider_name] = {
                    "error": str(result),
                    "success": False,
                }
                continue

            if isinstance(result, dict):
                result_dict = result
            elif isinstance(result, ReasoningResult):
                result_dict = result.to_dict()
            else:
                result_dict = {"raw": str(result)}

            result_dict["success"] = True
            comparison["providers"][provider_name] = result_dict

            # Track best and fastest
            latency = result_dict.get("latency_ms", float("inf"))
            if latency < min_latency:
                min_latency = latency
                comparison["fastest_provider"] = provider_name

            steps = len(result_dict.get("steps", []))
            if steps > best_score:
                best_score = steps
                comparison["best_provider"] = provider_name

        return comparison
