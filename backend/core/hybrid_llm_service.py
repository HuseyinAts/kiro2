"""
Hybrid LLM Service - Gerçek API Entegrasyonu
Gemini 3 Pro + Claude Sonnet 4.5 + OpenAI GPT-4

Bu servis optimal_hybrid_system.py'yi gerçek API'larla entegre eder.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
import structlog

# API clients
from google import genai
from google.genai import types as genai_types
from anthropic import AsyncAnthropic
import openai

logger = structlog.get_logger()


class HybridLLMService:
    """
    Hibrit LLM servisi - Gerçek API entegrasyonu

    Özellikleri:
    - Gemini 3 Pro (thinking mode için)
    - Claude Sonnet 4.5 (hızlı yanıtlar için)
    - OpenAI GPT-4 (fallback)
    """

    def __init__(self) -> None:
        """Servisi başlat ve API client'ları yapılandır"""
        # API Keys
        self.google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

        # Clients
        self.gemini_client: Optional[genai.Client] = None
        self.gemini_model_name: str = "gemini-2.5-flash"
        self.claude_client: Optional[AsyncAnthropic] = None
        self.openai_client: Optional[openai.AsyncOpenAI] = None

        # Initialize
        self._initialize_clients()

        logger.info(
            "hybrid_llm_service_initialized",
            gemini=bool(self.gemini_client),
            claude=bool(self.claude_client),
            openai=bool(self.openai_client)
        )

    def _initialize_clients(self) -> None:
        """API client'ları başlat"""
        # Gemini (google-genai SDK)
        if self.google_api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.google_api_key)
                self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                logger.info("gemini_client_initialized", model=self.gemini_model_name)
            except Exception as e:
                logger.error("gemini_initialization_failed", error=str(e))

        # Claude
        if self.anthropic_api_key:
            try:
                self.claude_client = AsyncAnthropic(api_key=self.anthropic_api_key)
                logger.info("claude_client_initialized")
            except Exception as e:
                logger.error("claude_initialization_failed", error=str(e))

        # OpenAI
        if self.openai_api_key:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
                logger.info("openai_client_initialized")
            except Exception as e:
                logger.error("openai_initialization_failed", error=str(e))

    async def generate_with_claude(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Claude ile yanıt üret (hızlı, basit sorgular için)

        Args:
            prompt: Kullanıcı sorusu
            temperature: Yaratıcılık seviyesi (0.0-1.0)
            max_tokens: Maksimum token sayısı
            system_prompt: Sistem prompt'u

        Returns:
            Claude'un yanıtı

        Raises:
            ValueError: Claude API key yapılandırılmamışsa
        """
        if not self.claude_client:
            raise ValueError("Claude API key yapılandırılmamış")

        try:
            messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]

            kwargs: Dict[str, Any] = {
                "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.claude_client.messages.create(**kwargs)

            result: str = response.content[0].text

            logger.info(
                "claude_generation_complete",
                prompt_length=len(prompt),
                response_length=len(result),
                model=kwargs["model"]
            )

            return result

        except Exception as e:
            logger.error("claude_generation_failed", error=str(e))
            raise

    async def generate_with_gemini(
        self,
        prompt: str,
        thinking_mode: bool = True,
        context: Optional[str] = None
    ) -> str:
        """
        Gemini ile yanıt üret (karmaşık analiz için)

        Args:
            prompt: Kullanıcı sorusu
            thinking_mode: Adım adım düşünme modu
            context: Ek bağlam

        Returns:
            Gemini'nin yanıtı

        Raises:
            ValueError: Gemini API key yapılandırılmamışsa
        """
        if not self.gemini_client:
            raise ValueError("Gemini API key yapılandırılmamış")

        try:
            # Prompt'u hazırla
            full_prompt = prompt

            if context:
                full_prompt = f"Bağlam:\n{context}\n\nGörev:\n{prompt}"

            if thinking_mode:
                full_prompt = (
                    "Lütfen adım adım düşünerek ve akıl yürütme sürecini göstererek yanıtla.\n\n"
                    + full_prompt
                )

            # Gemini'ye istek gönder (new google-genai SDK)
            response = await asyncio.to_thread(
                self.gemini_client.models.generate_content,
                model=self.gemini_model_name,
                contents=full_prompt,
            )

            result: str = response.text

            logger.info(
                "gemini_generation_complete",
                prompt_length=len(prompt),
                response_length=len(result),
                thinking_mode=thinking_mode
            )

            return result

        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e))
            raise

    async def generate_with_openai(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        OpenAI ile yanıt üret (fallback)

        Args:
            prompt: Kullanıcı sorusu
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token sayısı
            system_prompt: Sistem prompt'u

        Returns:
            GPT'nin yanıtı

        Raises:
            ValueError: OpenAI API key yapılandırılmamışsa
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key yapılandırılmamış")

        try:
            messages: List[Dict[str, str]] = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = await self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens
            )

            result: str = response.choices[0].message.content or ""

            logger.info(
                "openai_generation_complete",
                prompt_length=len(prompt),
                response_length=len(result)
            )

            return result

        except Exception as e:
            logger.error("openai_generation_failed", error=str(e))
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Sohbet tamamlama (conversation history ile)

        Args:
            messages: Mesaj listesi [{"role": "user/assistant", "content": "..."}]
            model: Kullanılacak model (claude, gemini, openai)
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token sayısı

        Returns:
            Asistan yanıtı
        """
        # Son mesajı al
        last_message: str = messages[-1]["content"] if len(messages) > 0 else ""

        # Önceki mesajları context olarak kullan
        context: str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages[:-1]
        ]) if len(messages) > 1 else ""

        if model == "gemini":
            return await self.generate_with_gemini(
                last_message,
                context=context
            )
        elif model == "openai":
            return await self.openai_client.chat.completions.create(  # type: ignore[return-value, union-attr]
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens
            ) if self.openai_client else await self.generate_with_claude(
                last_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:  # default: claude
            return await self.generate_with_claude(
                last_message,
                temperature=temperature,
                max_tokens=max_tokens
            )

    def get_available_models(self) -> Dict[str, bool]:
        """
        Kullanılabilir modelleri döndür

        Returns:
            Model durumları {"gemini": bool, "claude": bool, "openai": bool}
        """
        return {
            "gemini": bool(self.gemini_client),
            "claude": bool(self.claude_client),
            "openai": bool(self.openai_client)
        }

    def is_ready(self) -> bool:
        """
        En az bir model hazır mı?

        Returns:
            True eğer en az bir provider yapılandırılmışsa
        """
        available = self.get_available_models()
        return any(available.values())

    async def generate_with_fallback(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Fallback chain ile yanıt üret: Claude -> Gemini -> OpenAI -> Ollama

        Args:
            prompt: Kullanıcı sorusu
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token sayısı
            system_prompt: Sistem prompt'u

        Returns:
            Başarılı provider'ın yanıtı

        Raises:
            RuntimeError: Hiçbir provider çalışmazsa
        """
        errors: List[str] = []

        # 1. Claude
        if self.claude_client:
            try:
                return await self.generate_with_claude(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt
                )
            except Exception as e:
                errors.append(f"Claude: {e}")
                logger.warning("claude_fallback_failed", error=str(e))

        # 2. Gemini
        if self.gemini_model:
            try:
                return await self.generate_with_gemini(prompt)
            except Exception as e:
                errors.append(f"Gemini: {e}")
                logger.warning("gemini_fallback_failed", error=str(e))

        # 3. OpenAI
        if self.openai_client:
            try:
                return await self.generate_with_openai(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt
                )
            except Exception as e:
                errors.append(f"OpenAI: {e}")
                logger.warning("openai_fallback_failed", error=str(e))

        # 4. Ollama (local fallback - always available)
        try:
            from core.llm_service import llm_service
            return await llm_service.generate(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
        except Exception as e:
            errors.append(f"Ollama: {e}")
            logger.error("ollama_fallback_failed", error=str(e))

        # Tüm providerlar başarısız
        raise RuntimeError(f"Tüm LLM provider'ları başarısız: {'; '.join(errors)}")


# Global singleton instance
_hybrid_llm_service: Optional[HybridLLMService] = None


def get_hybrid_llm_service() -> HybridLLMService:
    """
    Global HybridLLMService instance'ını döndür

    Returns:
        HybridLLMService singleton instance
    """
    global _hybrid_llm_service
    if _hybrid_llm_service is None:
        _hybrid_llm_service = HybridLLMService()
    return _hybrid_llm_service
