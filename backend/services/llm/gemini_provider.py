"""
Google Gemini Provider Implementation
Supports Gemini 2.0 Flash Thinking and sequential reasoning

Author: KIRO AI Team
Date: 2026-01-16
"""

import asyncio
import json
import time
import uuid
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from services.llm.base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse
from services.llm.multi_llm_config import LLMCapability, LLMModelConfig, LLMProvider


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider

    Features:
    - Gemini 2.0 Flash Thinking mode
    - Sequential reasoning
    - Step-by-step problem solving
    - Math reasoning
    - Turkish language support
    """

    def __init__(self, config: LLMModelConfig, thinking_mode: bool = True):
        """
        Initialize Gemini provider

        Args:
            config: LLM model configuration
            thinking_mode: Enable thinking mode for sequential reasoning
        """
        super().__init__(config)

        if not self.api_key:
            raise ValueError("Google API key is required (GOOGLE_API_KEY)")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Thinking mode configuration
        self.thinking_mode = thinking_mode

        # Initialize model with fallback
        self.model = self._initialize_model()

        # Sequential thinking parameters
        self.max_thinking_steps = 10
        self.thinking_timeout = 30.0

    def _initialize_model(self) -> genai.GenerativeModel:
        """Initialize Gemini model with fallback chain"""
        model_names = [
            "gemini-2.0-flash-thinking-exp",  # Primary: Thinking mode
            "gemini-exp-1206",  # Fallback: Experimental
            "gemini-2.0-flash-exp",  # Fallback: Flash experimental
            "gemini-1.5-pro",  # Fallback: Stable
        ]

        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test model availability
                print(f"[Gemini] Model loaded: {model_name}")
                self.model_name = model_name
                return model
            except Exception as e:
                print(f"[Gemini] Model {model_name} unavailable: {e}")
                continue

        raise RuntimeError("No Gemini model available")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Gemini API

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Build prompt with optional thinking mode
            full_prompt = self._build_prompt(request)

            # Make API call
            response = await self._generate_with_retry(full_prompt)

            # Extract response
            content = response.text if response.text else ""

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000

            # Estimate tokens (Gemini doesn't always return token count)
            tokens_used = len(content.split()) * 1.3  # Rough estimate
            cost = self._calculate_cost(int(tokens_used))

            # Update metrics
            self._update_metrics(latency_ms, int(tokens_used), cost)

            return LLMResponse(
                provider=LLMProvider.GEMINI,
                model_name=self.model_name,
                content=content,
                raw_response={"text": content},
                latency_ms=latency_ms,
                tokens_used=int(tokens_used),
                cost_usd=cost,
                request_id=request_id,
            )

        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e!s}")

    def _build_prompt(self, request: LLMRequest) -> str:
        """Build prompt with optional thinking mode prefix"""
        parts = []

        # System prompt
        if request.system_prompt:
            parts.append(f"System: {request.system_prompt}\n")

        # Thinking mode prefix for sequential reasoning
        if self.thinking_mode:
            parts.append(
                "Lutfen adim adim dusun ve akil yurutme surecini acikla:\n"
                "1. Problemi anla\n"
                "2. Alt problemlere ayir\n"
                "3. Her adimi acikla\n"
                "4. Sonucu dogrula\n\n"
            )

        # User prompt
        parts.append(request.prompt)

        return "".join(parts)

    async def _generate_with_retry(
        self, prompt: str, max_retries: int = 3
    ) -> GenerateContentResponse:
        """Generate with exponential backoff retry"""

        async def _call():
            # Run synchronous Gemini API in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )

        return await self._retry_with_backoff(_call, max_retries=max_retries)

    async def generate_batch(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """
        Generate text for multiple requests concurrently

        Args:
            requests: List of LLM requests

        Returns:
            List of LLM responses
        """
        tasks = [self.generate(request) for request in requests]
        return await asyncio.gather(*tasks)

    async def check_health(self) -> bool:
        """
        Check Gemini API health

        Returns:
            True if healthy, False otherwise
        """
        try:
            test_request = LLMRequest(prompt="Merhaba", max_tokens=10)
            response = await self.generate(test_request)
            return len(response.content) > 0
        except Exception:
            return False

    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if capability is supported"""
        return capability in self.config.capabilities

    async def fine_tune(
        self, training_file: str, validation_file: str | None = None, **kwargs
    ) -> str:
        """
        Fine-tune Gemini model (not supported yet)

        Args:
            training_file: Path to training file
            validation_file: Path to validation file

        Returns:
            Model ID (raises NotImplementedError)
        """
        raise NotImplementedError("Gemini fine-tuning not yet supported via API")

    # =========================================================================
    # Sequential Thinking Methods
    # =========================================================================

    async def think_step_by_step(
        self,
        problem: str,
        max_steps: int | None = None,
        include_verification: bool = True,
    ) -> dict[str, Any]:
        """
        Solve problem with step-by-step thinking

        Args:
            problem: Problem to solve
            max_steps: Maximum reasoning steps
            include_verification: Include verification step

        Returns:
            Structured reasoning result
        """
        max_steps = max_steps or self.max_thinking_steps

        prompt = f"""Asagidaki problemi adim adim coz.

Problem: {problem}

Cozum formatı (JSON):
{{
    "understanding": "Problemi anlama",
    "steps": [
        {{
            "step_number": 1,
            "description": "Adim aciklamasi",
            "reasoning": "Neden bu adimi atiyoruz",
            "result": "Adim sonucu"
        }}
    ],
    "final_answer": "Son cevap",
    "verification": "Dogrulama (opsiyonel)",
    "confidence": 0.95
}}

Maksimum {max_steps} adim kullan. JSON formatinda yanit ver."""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir matematik ve mantik uzmanisin. Adim adim dusun.",
            max_tokens=4096,
            temperature=0.3,
        )

        response = await self.generate(request)

        # Parse JSON response
        try:
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["provider"] = "gemini"
            result["model"] = self.model_name
            result["latency_ms"] = response.latency_ms
            return result

        except json.JSONDecodeError:
            # Return unstructured response
            return {
                "understanding": "Parse error",
                "steps": [{"step_number": 1, "description": response.content}],
                "final_answer": response.content,
                "provider": "gemini",
                "model": self.model_name,
                "parse_error": True,
            }

    async def decompose_problem(self, problem: str) -> dict[str, Any]:
        """
        Decompose complex problem into sub-problems

        Args:
            problem: Complex problem

        Returns:
            Decomposed sub-problems with dependencies
        """
        prompt = f"""Asagidaki karmasik problemi alt problemlere ayir.

Problem: {problem}

Cikti formati (JSON):
{{
    "main_problem": "Ana problem",
    "sub_problems": [
        {{
            "id": 1,
            "description": "Alt problem aciklamasi",
            "dependencies": [],  // Bagli oldugu alt problem ID'leri
            "difficulty": 0.5,   // 0-1 arasi zorluk
            "estimated_steps": 3
        }}
    ],
    "solving_order": [1, 2, 3],  // Cozum sirasi (topolojik siralama)
    "total_estimated_steps": 10
}}

JSON formatinda yanit ver."""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir problem analiz uzmanisin.",
            max_tokens=2048,
            temperature=0.3,
        )

        response = await self.generate(request)

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["provider"] = "gemini"
            return result

        except json.JSONDecodeError:
            return {
                "main_problem": problem,
                "sub_problems": [],
                "solving_order": [],
                "error": "Parse error",
                "raw_response": response.content,
            }

    async def solve_math_problem(
        self, problem: str, show_all_steps: bool = True
    ) -> dict[str, Any]:
        """
        Solve mathematical problem with detailed steps

        Args:
            problem: Math problem
            show_all_steps: Show all algebraic steps

        Returns:
            Solution with steps
        """
        prompt = f"""Asagidaki matematik problemini coz.

Problem: {problem}

Detayli cozum (JSON):
{{
    "problem_type": "algebra/geometry/calculus/other",
    "given": ["Verilenler"],
    "find": "Istenen",
    "solution_steps": [
        {{
            "step": 1,
            "operation": "Islem adi",
            "expression": "Matematiksel ifade",
            "explanation": "Aciklama"
        }}
    ],
    "answer": "Sonuc",
    "verification": "Dogrulama",
    "alternative_methods": ["Alternatif cozum yolu (varsa)"]
}}

{'Tum ara adimlari goster.' if show_all_steps else 'Ozet adimlar yeterli.'}
JSON formatinda yanit ver."""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="Sen bir matematik ogretmenisin. Adim adim acikla.",
            max_tokens=4096,
            temperature=0.2,
        )

        response = await self.generate(request)

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            result["provider"] = "gemini"
            result["model"] = self.model_name
            return result

        except json.JSONDecodeError:
            return {
                "problem_type": "unknown",
                "answer": response.content,
                "provider": "gemini",
                "parse_error": True,
            }

    async def create_osym_question(
        self,
        topic: str,
        subtopic: str,
        difficulty: float,
        bloom_level: int,
        exam_type: str,
    ) -> dict[str, Any]:
        """
        Generate OSYM question with sequential thinking

        Args:
            topic: Main topic
            subtopic: Subtopic
            difficulty: Difficulty level (0.0-1.0)
            bloom_level: Bloom taxonomy level (1-6)
            exam_type: Exam type (TYT, AYT, YDT)

        Returns:
            Generated question as dictionary
        """
        from services.llm.multi_llm_config import MultiLLMConfig

        prompt_template = MultiLLMConfig.TURKISH_OSYM_PROMPTS[
            "question_generation_prompt"
        ]
        system_prompt = MultiLLMConfig.TURKISH_OSYM_PROMPTS["system_prompt"]

        prompt = prompt_template.format(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            bloom_level=bloom_level,
            exam_type=exam_type,
        )

        # Add thinking mode for better question generation
        if self.thinking_mode:
            prompt = (
                "Adim adim dusun:\n"
                "1. Konuyu anla\n"
                "2. Zorluk seviyesini belirle\n"
                "3. Soru kokunu olustur\n"
                "4. Dogru cevabi yaz\n"
                "5. Celdiricileri olustur\n\n" + prompt
            )

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.8,
        )

        response = await self.generate(request)

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            question_data = json.loads(content.strip())
            question_data["provider"] = "gemini"
            return question_data

        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response.content}")


# Convenience function for quick access
def get_gemini_provider(thinking_mode: bool = True) -> GeminiProvider:
    """Get configured Gemini provider instance"""
    from services.llm.multi_llm_config import MultiLLMConfig

    return GeminiProvider(MultiLLMConfig.GEMINI_CONFIG, thinking_mode=thinking_mode)
