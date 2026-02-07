"""
LLM Services Package
Multi-LLM support for ÖSYM question generation and sequential thinking

Author: KIRO AI Team
Date: 2025-10-19 (Updated: 2026-01-16)
"""

# Core imports (no dependencies)
from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import (
    LLMProvider,
    LLMCapability,
    LLMModelConfig,
    MultiLLMConfig,
)
from services.llm.sequential_thinking_mixin import (
    SequentialThinkingMixin,
    ReasoningResult,
    ReasoningStep,
    ReasoningStepType,
)


# Lazy imports for providers (require external dependencies)
def get_openai_provider():
    from services.llm.openai_provider import OpenAIProvider

    return OpenAIProvider


def get_claude_provider():
    from services.llm.claude_provider import ClaudeProvider

    return ClaudeProvider


def get_qwen_provider():
    from services.llm.qwen_provider import QwenProvider

    return QwenProvider


def get_gemini_provider():
    from services.llm.gemini_provider import GeminiProvider

    return GeminiProvider


def get_ensemble_manager():
    from services.llm.ensemble_manager import MultiLLMEnsembleManager, EnsembleStrategy

    return MultiLLMEnsembleManager, EnsembleStrategy


__all__ = [
    # Base classes
    "BaseLLMProvider",
    "LLMRequest",
    "LLMResponse",
    # Configuration
    "LLMProvider",
    "LLMCapability",
    "LLMModelConfig",
    "MultiLLMConfig",
    # Sequential Thinking
    "SequentialThinkingMixin",
    "ReasoningResult",
    "ReasoningStep",
    "ReasoningStepType",
    # Lazy loaders
    "get_openai_provider",
    "get_claude_provider",
    "get_qwen_provider",
    "get_gemini_provider",
    "get_ensemble_manager",
]
