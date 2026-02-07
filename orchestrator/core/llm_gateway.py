"""
KIRO2 Orchestrator - LLM Gateway
================================
LLM çağrıları için unified gateway.
- Rate limiting & retry logic
- Cost tracking
- Response validation
- Model fallback support
"""

from __future__ import annotations
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, AsyncGenerator
import json

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI


class ModelProvider(str, Enum):
    """Desteklenen LLM provider'lar"""
    CLAUDE = "claude"
    OPENAI = "openai"
    CODEX = "codex"


@dataclass
class LLMConfig:
    """LLM yapılandırması"""
    provider: ModelProvider
    model: str
    max_tokens: int = 4096
    temperature: float = 0.0
    timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class LLMResponse:
    """LLM yanıt wrapper'ı"""
    content: str
    model: str
    provider: ModelProvider
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    finish_reason: str
    raw_response: Any = None


@dataclass
class LLMUsage:
    """Kullanım metrikleri"""
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    failed_calls: int = 0
    
    def add(self, response: LLMResponse):
        self.total_calls += 1
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.total_cost += response.cost
        self.total_latency_ms += response.latency_ms


# Token fiyatları (USD per 1K tokens) - Ocak 2026
MODEL_PRICING = {
    # Claude models
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    # OpenAI models
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "o1": {"input": 0.015, "output": 0.060},
    "o1-mini": {"input": 0.003, "output": 0.012},
    # Codex
    "codex-mini-latest": {"input": 0.0015, "output": 0.006},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Token maliyeti hesapla"""
    pricing = MODEL_PRICING.get(model, {"input": 0.01, "output": 0.03})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000


class LLMClient(ABC):
    """Abstract LLM client"""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass


class ClaudeClient(LLMClient):
    """Claude API client"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncAnthropic()
        self.usage = LLMUsage()
    
    async def generate(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.config.model,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    system=system or "",
                    messages=messages,
                    timeout=self.config.timeout,
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                llm_response = LLMResponse(
                    content=response.content[0].text if response.content else "",
                    model=self.config.model,
                    provider=ModelProvider.CLAUDE,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    cost=calculate_cost(
                        self.config.model,
                        response.usage.input_tokens,
                        response.usage.output_tokens
                    ),
                    latency_ms=latency_ms,
                    finish_reason=response.stop_reason or "unknown",
                    raw_response=response,
                )
                
                self.usage.add(llm_response)
                return llm_response
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    self.usage.failed_calls += 1
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        raise RuntimeError("Max retries exceeded")
    
    async def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.config.model,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            system=system or "",
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI()
        self.usage = LLMUsage()
    
    async def generate(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        # System mesajını messages'a ekle
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    messages=full_messages,
                    timeout=self.config.timeout,
                )
                
                latency_ms = (time.time() - start_time) * 1000
                choice = response.choices[0]
                
                llm_response = LLMResponse(
                    content=choice.message.content or "",
                    model=self.config.model,
                    provider=ModelProvider.OPENAI,
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                    cost=calculate_cost(
                        self.config.model,
                        response.usage.prompt_tokens if response.usage else 0,
                        response.usage.completion_tokens if response.usage else 0
                    ),
                    latency_ms=latency_ms,
                    finish_reason=choice.finish_reason or "unknown",
                    raw_response=response,
                )
                
                self.usage.add(llm_response)
                return llm_response
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    self.usage.failed_calls += 1
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        raise RuntimeError("Max retries exceeded")
    
    async def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        
        stream = await self.client.chat.completions.create(
            model=self.config.model,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            messages=full_messages,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMGateway:
    """
    Unified LLM Gateway
    - Model selection based on task
    - Automatic fallback
    - Cost tracking
    - Rate limiting
    """
    
    # Default model configurations
    DEFAULT_CONFIGS = {
        "claude-sonnet": LLMConfig(
            provider=ModelProvider.CLAUDE,
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.0,
        ),
        "claude-opus": LLMConfig(
            provider=ModelProvider.CLAUDE,
            model="claude-opus-4-20250514",
            max_tokens=8192,
            temperature=0.0,
        ),
        "gpt-4o": LLMConfig(
            provider=ModelProvider.OPENAI,
            model="gpt-4o",
            max_tokens=4096,
            temperature=0.0,
        ),
        "gpt-4o-mini": LLMConfig(
            provider=ModelProvider.OPENAI,
            model="gpt-4o-mini",
            max_tokens=4096,
            temperature=0.0,
        ),
        "o1-mini": LLMConfig(
            provider=ModelProvider.OPENAI,
            model="o1-mini",
            max_tokens=8192,
            temperature=1.0,  # o1 requires temp=1
        ),
    }
    
    def __init__(self):
        self._clients: dict[str, LLMClient] = {}
        self._total_usage = LLMUsage()
        self._cost_limit: float = 10.0  # Default $10 per run
    
    def set_cost_limit(self, limit: float):
        """Maliyet limiti ayarla"""
        self._cost_limit = limit
    
    def get_client(self, model_key: str) -> LLMClient:
        """Model için client al veya oluştur"""
        if model_key not in self._clients:
            config = self.DEFAULT_CONFIGS.get(model_key)
            if not config:
                raise ValueError(f"Unknown model key: {model_key}")
            
            if config.provider == ModelProvider.CLAUDE:
                self._clients[model_key] = ClaudeClient(config)
            elif config.provider in (ModelProvider.OPENAI, ModelProvider.CODEX):
                self._clients[model_key] = OpenAIClient(config)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
        
        return self._clients[model_key]
    
    async def generate(
        self,
        model_key: str,
        messages: list[dict],
        system: Optional[str] = None,
        fallback_model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        LLM çağrısı yap, gerekirse fallback kullan
        """
        # Cost limit kontrolü
        if self._total_usage.total_cost >= self._cost_limit:
            raise RuntimeError(
                f"Cost limit exceeded: ${self._total_usage.total_cost:.2f} >= ${self._cost_limit:.2f}"
            )
        
        try:
            client = self.get_client(model_key)
            response = await client.generate(messages, system, **kwargs)
            self._total_usage.add(response)
            return response
            
        except Exception as e:
            if fallback_model:
                # Fallback model'a geç
                client = self.get_client(fallback_model)
                response = await client.generate(messages, system, **kwargs)
                self._total_usage.add(response)
                return response
            raise
    
    def get_usage(self) -> LLMUsage:
        """Toplam kullanım metrikleri"""
        return self._total_usage
    
    def get_cost(self) -> float:
        """Toplam maliyet"""
        return self._total_usage.total_cost


# Singleton instance
_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """LLM Gateway singleton"""
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
