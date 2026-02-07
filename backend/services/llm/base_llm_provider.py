"""
Base LLM Provider Interface
Abstract class for all LLM providers (OpenAI, Claude, Qwen)

Author: KIRO AI Team
Date: 2025-10-19
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from pydantic import BaseModel, ConfigDict

from services.llm.multi_llm_config import LLMProvider, LLMModelConfig, LLMCapability


class LLMRequest(BaseModel):
    """LLM Request Model"""

    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    json_mode: bool = False
    metadata: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """LLM Response Model"""

    provider: LLMProvider
    model_name: str
    content: str
    raw_response: Optional[Dict[str, Any]] = None

    # Performance metrics
    latency_ms: float
    tokens_used: int
    cost_usd: float

    # Quality metrics
    confidence_score: Optional[float] = None

    # Metadata
    timestamp: datetime = datetime.now()
    request_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers

    All LLM providers must implement this interface
    """

    def __init__(self, config: LLMModelConfig):
        """
        Initialize LLM Provider

        Args:
            config: LLM model configuration
        """
        self.config = config
        self.provider = config.provider
        self.model_name = config.model_name
        self.api_key = config.api_key
        self.api_base = config.api_base

        # Performance tracking
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._avg_latency = 0.0

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text from LLM

        Args:
            request: LLM request with prompt and parameters

        Returns:
            LLM response with generated text and metadata
        """
        pass

    @abstractmethod
    async def generate_batch(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """
        Generate text for multiple requests (batch processing)

        Args:
            requests: List of LLM requests

        Returns:
            List of LLM responses
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if LLM provider is healthy and accessible

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def supports_capability(self, capability: LLMCapability) -> bool:
        """
        Check if provider supports specific capability

        Args:
            capability: LLM capability to check

        Returns:
            True if supported, False otherwise
        """
        pass

    @abstractmethod
    async def fine_tune(
        self, training_file: str, validation_file: Optional[str] = None, **kwargs
    ) -> str:
        """
        Fine-tune the model with custom data

        Args:
            training_file: Path to training data (JSONL format)
            validation_file: Path to validation data (optional)
            **kwargs: Provider-specific fine-tuning parameters

        Returns:
            Fine-tuned model ID
        """
        pass

    def _calculate_cost(self, tokens_used: int) -> float:
        """
        Calculate cost for token usage

        Args:
            tokens_used: Number of tokens used

        Returns:
            Cost in USD
        """
        return (tokens_used / 1000) * self.config.cost_per_1k_tokens

    def _update_metrics(self, latency_ms: float, tokens_used: int, cost: float):
        """
        Update provider performance metrics

        Args:
            latency_ms: Request latency in milliseconds
            tokens_used: Number of tokens used
            cost: Request cost in USD
        """
        self._total_requests += 1
        self._total_tokens += tokens_used
        self._total_cost += cost

        # Update rolling average latency
        self._avg_latency = (
            self._avg_latency * (self._total_requests - 1) + latency_ms
        ) / self._total_requests

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get provider performance metrics

        Returns:
            Dictionary with performance metrics
        """
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost, 4),
            "avg_latency_ms": round(self._avg_latency, 2),
            "tokens_per_request": (
                round(self._total_tokens / self._total_requests, 2)
                if self._total_requests > 0
                else 0
            ),
        }

    def reset_metrics(self):
        """Reset all performance metrics"""
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._avg_latency = 0.0

    async def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ):
        """
        Retry function with exponential backoff

        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Backoff multiplier

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

        raise last_exception

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider.value}, model={self.model_name})"
