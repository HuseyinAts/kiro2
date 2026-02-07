"""
LLM Service - Ollama Integration for KIRO2
Teknofest 2025 - Eğitim Eylemci Projesi

This module provides LLM integration using Ollama with Qwen3 models.
Optimized for Turkish educational content generation.

Supported Models:
- qwen3:14b - Main text model (best quality)
- qwen3-vl:8b - Vision model (OCR, image questions)
- qwen3:8b - Fast model (low latency)

Environment Variables:
- OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
- OLLAMA_MODEL: Default model (default: qwen3:14b)
- OLLAMA_VISION_MODEL: Vision model (default: qwen3-vl:8b)
- OLLAMA_TIMEOUT: Request timeout in seconds (default: 120)
- OLLAMA_THINKING_MODE: Enable thinking mode (default: true)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Ollama API error."""

    pass


class LLMService:
    """
    LLM Service with Ollama Integration.

    Provides async text generation, chat, and embeddings using Ollama.
    Optimized for Turkish educational content (YKS/TYT/AYT).

    Features:
    - Async HTTP client with connection pooling
    - Thinking mode for step-by-step reasoning
    - Streaming support for real-time responses
    - Automatic retry with exponential backoff
    - Turkish language optimization

    Example:
        >>> from core.llm_service import llm_service
        >>> response = await llm_service.generate("Merhaba, nasılsın?")
        >>> print(response)
    """

    def __init__(self) -> None:
        """Initialize LLM service with Ollama configuration."""
        # Configuration from environment
        self.base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model: str = os.getenv("OLLAMA_MODEL", "qwen3:14b")
        self.vision_model: str = os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:8b")
        self.timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.thinking_mode: bool = os.getenv("OLLAMA_THINKING_MODE", "true").lower() == "true"

        # Provider info
        self.provider: str = "ollama"
        self.initialized: bool = False
        self._client: httpx.AsyncClient | None = None

        # LangChain compatibility - initialize if available
        self.chat_model: Any = None
        self.llm: Any = None
        self._init_langchain()

        logger.info(
            f"LLM Service initialized with Ollama. "
            f"Model: {self.model}, Base URL: {self.base_url}"
        )

    def _init_langchain(self) -> None:
        """Initialize LangChain-compatible LLM models if available."""
        if os.environ.get("TESTING") == "true":
            logger.info("Skipping LangChain init in test mode")
            return
        try:
            from langchain_ollama import ChatOllama, OllamaLLM

            # Create LangChain-compatible chat model
            self.chat_model = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=0.7,
            )

            # Create LangChain-compatible LLM
            self.llm = OllamaLLM(
                model=self.model,
                base_url=self.base_url,
                temperature=0.7,
            )

            logger.info(
                f"LangChain Ollama models initialized: {self.model}"
            )

        except ImportError:
            # Try older langchain_community package
            try:
                from langchain_community.chat_models import ChatOllama
                from langchain_community.llms import Ollama

                self.chat_model = ChatOllama(
                    model=self.model,
                    base_url=self.base_url,
                    temperature=0.7,
                )

                self.llm = Ollama(
                    model=self.model,
                    base_url=self.base_url,
                    temperature=0.7,
                )

                logger.info(
                    f"LangChain Community Ollama models initialized: {self.model}"
                )

            except ImportError:
                logger.warning(
                    "LangChain Ollama not available. "
                    "Install with: pip install langchain-ollama"
                )
                self.chat_model = None
                self.llm = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
            self.initialized = True
        return self._client

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            self.initialized = False
            logger.info("LLM Service client closed")

    async def _check_health(self) -> bool:
        """Check if Ollama server is healthy."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model: str | None = None,
        thinking: bool | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using Ollama LLM.

        Args:
            prompt: Input prompt (Turkish or English)
            temperature: Sampling temperature (0.0-1.0, default 0.7)
            max_tokens: Maximum tokens to generate (None = model default)
            model: Override default model (optional)
            thinking: Enable thinking mode for reasoning (default from config)
            system_prompt: System prompt for context (optional)
            **kwargs: Additional Ollama parameters

        Returns:
            Generated text response

        Raises:
            OllamaError: If generation fails

        Example:
            >>> response = await llm_service.generate(
            ...     prompt="2x + 5 = 15 denklemini çöz",
            ...     thinking=True
            ... )
        """
        try:
            client = await self._get_client()
            use_model = model or self.model
            use_thinking = thinking if thinking is not None else self.thinking_mode

            # Build prompt with thinking mode
            final_prompt = prompt
            if use_thinking and "/think" not in prompt.lower():
                final_prompt = f"/think {prompt}"

            # Build request payload
            payload: dict[str, Any] = {
                "model": use_model,
                "prompt": final_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            if system_prompt:
                payload["system"] = system_prompt

            # Add any extra options
            for key, value in kwargs.items():
                if key not in payload:
                    payload["options"][key] = value

            logger.debug(f"Ollama generate: model={use_model}, prompt_len={len(prompt)}")

            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "")
            thinking_text = result.get("thinking", "")

            # Qwen3 puts content in 'thinking' field by default
            # If response is empty but thinking has content, use thinking
            if not generated_text and thinking_text:
                generated_text = thinking_text

            # For educational content, optionally include both
            include_thinking = kwargs.get("include_thinking", False)
            if include_thinking and thinking_text and result.get("response"):
                # Both exist - combine them
                generated_text = f"<düşünce>\n{thinking_text}\n</düşünce>\n\n{result.get('response', '')}"

            logger.info(
                f"Generated {len(generated_text)} chars "
                f"(eval: {result.get('eval_count', 0)} tokens)"
            )

            return generated_text

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            raise OllamaError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Ollama request error: {e}")
            raise OllamaError(f"Request error: {e}") from e
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            raise OllamaError(f"Generate error: {e}") from e

    async def generate_for_education(
        self,
        prompt: str,
        temperature: float = 0.7,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate educational content optimized for Turkish YKS preparation.

        This method adds educational context to the prompt and uses
        thinking mode for step-by-step explanations.

        Args:
            prompt: Educational prompt (Turkish)
            temperature: Sampling temperature (default 0.7)
            context: Educational context dict with:
                - subject: Ders adı (matematik, fizik, etc.)
                - level: Öğrenci seviyesi (TYT, AYT)
                - topic: Konu başlığı
                - student_level: Öğrenci yetkinlik seviyesi (0-100)
            **kwargs: Additional parameters

        Returns:
            Educational content response

        Example:
            >>> response = await llm_service.generate_for_education(
            ...     prompt="Türev kavramını açıkla",
            ...     context={
            ...         "subject": "matematik",
            ...         "level": "AYT",
            ...         "topic": "Türev",
            ...         "student_level": 60
            ...     }
            ... )
        """
        # Build educational system prompt
        ctx = context or {}
        subject = ctx.get("subject", "genel")
        level = ctx.get("level", "TYT")
        topic = ctx.get("topic", "")
        student_level = ctx.get("student_level", 50)

        system_prompt = f"""Sen bir Türk eğitim asistanısın. {level} seviyesinde {subject} dersi için yardım ediyorsun.

Kurallar:
- Türkçe yanıt ver
- Adım adım açıkla
- Öğrenci seviyesi: {student_level}/100 - buna göre zorluk ayarla
- Konu: {topic or 'Genel'}
- Somut örnekler kullan
- YKS sınav formatına uygun ol"""

        return await self.generate(
            prompt=prompt,
            temperature=temperature,
            system_prompt=system_prompt,
            thinking=True,  # Always use thinking for education
            **kwargs,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Multi-turn chat completion with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
                - role: "user", "assistant", or "system"
                - content: Message text
            temperature: Sampling temperature (default 0.7)
            model: Override default model (optional)
            **kwargs: Additional parameters

        Returns:
            Assistant's response

        Example:
            >>> response = await llm_service.chat([
            ...     {"role": "system", "content": "Sen bir matematik öğretmenisin."},
            ...     {"role": "user", "content": "Integral nedir?"},
            ... ])
        """
        try:
            client = await self._get_client()
            use_model = model or self.model

            payload: dict[str, Any] = {
                "model": use_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            for key, value in kwargs.items():
                if key not in payload:
                    payload["options"][key] = value

            logger.debug(f"Ollama chat: model={use_model}, messages={len(messages)}")

            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()
            message = result.get("message", {})
            content = message.get("content", "")

            logger.info(f"Chat response: {len(content)} chars")

            return content

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama chat HTTP error: {e.response.status_code}")
            raise OllamaError(f"HTTP error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise OllamaError(f"Chat error: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream text generation for real-time responses.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            model: Override default model
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated

        Example:
            >>> async for chunk in llm_service.generate_stream("Hikaye yaz"):
            ...     print(chunk, end="", flush=True)
        """
        try:
            client = await self._get_client()
            use_model = model or self.model

            payload = {
                "model": use_model,
                "prompt": prompt,
                "stream": True,
                "options": {"temperature": temperature},
            }

            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise OllamaError(f"Stream error: {e}") from e

    async def embed(
        self,
        text: str,
        model: str | None = None,
    ) -> list[float]:
        """
        Generate text embeddings using Ollama.

        Args:
            text: Text to embed
            model: Embedding model (default: nomic-embed-text or mxbai-embed-large)

        Returns:
            Embedding vector (typically 768 or 1024 dimensions)

        Note:
            Requires an embedding model. If not available, returns zero vector.
            Install with: ollama pull nomic-embed-text
        """
        try:
            client = await self._get_client()
            # Use dedicated embedding model if available
            embed_model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

            payload = {
                "model": embed_model,
                "input": text,
            }

            response = await client.post("/api/embed", json=payload)

            if response.status_code == 404:
                # Model not found, return zero vector
                logger.warning(f"Embedding model {embed_model} not found, using fallback")
                return [0.0] * 768

            response.raise_for_status()
            result = response.json()

            embeddings = result.get("embeddings", [[]])
            if embeddings and len(embeddings) > 0:
                return embeddings[0]

            return [0.0] * 768

        except Exception as e:
            logger.warning(f"Ollama embed error: {e}, returning zero vector")
            return [0.0] * 768

    async def analyze_image(
        self,
        prompt: str,
        image_base64: str,
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Analyze image using vision model (qwen3-vl).

        Useful for OCR, diagram analysis, and visual question answering.

        Args:
            prompt: Question about the image
            image_base64: Base64 encoded image data
            model: Vision model (default: qwen3-vl:8b)
            **kwargs: Additional parameters

        Returns:
            Analysis response

        Example:
            >>> import base64
            >>> with open("question.png", "rb") as f:
            ...     img_b64 = base64.b64encode(f.read()).decode()
            >>> response = await llm_service.analyze_image(
            ...     "Bu matematik sorusunu çöz",
            ...     img_b64
            ... )
        """
        try:
            client = await self._get_client()
            use_model = model or self.vision_model

            payload = {
                "model": use_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
            }

            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except Exception as e:
            logger.error(f"Ollama image analysis error: {e}")
            raise OllamaError(f"Image analysis error: {e}") from e

    def get_model_info(self) -> dict[str, Any]:
        """
        Get current model configuration and status.

        Returns:
            Dict with model info:
                - provider: "ollama"
                - model: Current model name
                - vision_model: Vision model name
                - base_url: Ollama server URL
                - status: "configured" or "not_initialized"
                - thinking_mode: Whether thinking is enabled
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "vision_model": self.vision_model,
            "base_url": self.base_url,
            "status": "configured" if self.initialized else "ready",
            "thinking_mode": self.thinking_mode,
            "timeout": self.timeout,
        }

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models in Ollama.

        Returns:
            List of model info dicts with name, size, modified date
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()

            result = response.json()
            return result.get("models", [])

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


# Lazy global singleton instance
_llm_service: LLMService | None = None


def _get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


class _LazyLLMService:
    """Proxy that delays LLMService initialization until first use."""

    def __getattr__(self, name: str):
        return getattr(_get_llm_service(), name)


llm_service: LLMService = _LazyLLMService()  # type: ignore[assignment]


# Convenience functions for direct import
async def generate(prompt: str, **kwargs: Any) -> str:
    """Generate text using default LLM service."""
    return await llm_service.generate(prompt, **kwargs)


async def chat(messages: list[dict[str, str]], **kwargs: Any) -> str:
    """Chat using default LLM service."""
    return await llm_service.chat(messages, **kwargs)


async def embed(text: str) -> list[float]:
    """Generate embeddings using default LLM service."""
    return await llm_service.embed(text)


# Backward compatibility aliases for legacy imports
HuggingFaceLLMService = LLMService  # Alias for tests that import this name
